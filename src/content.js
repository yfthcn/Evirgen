/*
 * Evirgen — content script (the timer lives HERE, not in the service worker)
 *
 * Why a Web Worker: Chrome throttles window timers in background tabs
 * (intensive throttling = one wakeup per minute), which would wreck short
 * intervals on exactly the tabs people auto-refresh (dashboards left in the
 * background). Worker timers are not throttled. If page CSP blocks blob
 * workers, we fall back to a self-correcting chunked setTimeout.
 *
 * Badge updates are sparse on purpose (minute boundaries + 60/30/10 s marks)
 * so the service worker is woken only a handful of times per cycle.
 */
'use strict';

(() => {
  if (window.__evirgenLoaded) return;
  window.__evirgenLoaded = true;

  let config = null;      // { intervalSec, enabled, bypassCache }
  let deadline = 0;       // epoch ms of next reload
  let worker = null;
  let watchdogId = null;
  let badgeTimers = [];
  let fired = false;

  const MIN_INTERVAL_SEC = 5;

  function sendBg(msg) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(msg, (res) => {
          void chrome.runtime.lastError; // swallow "receiving end" errors
          resolve(res);
        });
      } catch {
        resolve(null); // extension context invalidated (update/reload)
      }
    });
  }

  // ---- timer backends ----------------------------------------------------

  /*
   * Two layers, both armed on every cycle:
   *   1. Worker timer  — precision layer, immune to background-tab throttling.
   *      NOTE: CSP violations on blob workers are ASYNC (the constructor does
   *      not throw; the script load fails later via the `error` event), so a
   *      try/catch alone is not enough — we must handle worker.onerror too.
   *   2. Watchdog      — chunked main-thread setTimeout that self-corrects
   *      against Date.now(). Guarantees the reload fires even if the worker
   *      silently dies. First layer to reach the deadline wins (`fired` guard).
   */
  function makeWorker() {
    try {
      const src = 'onmessage=(e)=>{setTimeout(()=>postMessage(1),e.data)}';
      const url = URL.createObjectURL(new Blob([src], { type: 'text/javascript' }));
      const w = new Worker(url);
      URL.revokeObjectURL(url);
      return w;
    } catch {
      return null; // synchronous rejection (rare)
    }
  }

  function armTimer(ms) {
    worker = makeWorker();
    if (worker) {
      worker.onmessage = fire;
      worker.onerror = () => {
        // async CSP failure — drop the worker, watchdog still covers us
        console.debug('[evirgen] blob worker blocked by page CSP, watchdog active');
        worker.terminate();
        worker = null;
      };
      worker.postMessage(ms);
    }
    watchdogTick();
  }

  function watchdogTick() {
    const remaining = deadline - Date.now();
    if (remaining <= 500) return fire();
    watchdogId = setTimeout(watchdogTick, Math.min(remaining, 20000));
  }

  function disarm() {
    if (worker) { worker.terminate(); worker = null; }
    if (watchdogId) { clearTimeout(watchdogId); watchdogId = null; }
    for (const id of badgeTimers) clearTimeout(id);
    badgeTimers = [];
    deadline = 0;
  }

  // ---- badge (sparse) ------------------------------------------------------

  const MIN_MS = 60000;
  const HOUR_MS = 3600000;

  function badgeText(remainingMs) {
    const s = Math.round(remainingMs / 1000);
    if (s < 90) return s + 's';
    const m = Math.round(s / 60);
    if (m < 90) return m + 'm';
    const h = s / 3600;
    return (h < 10 ? Math.round(h * 10) / 10 : Math.round(h)) + 'h';
  }

  /*
   * Tiered marks keep SW wakeups bounded regardless of interval length:
   *   > 90 min out : hour boundaries
   *   90–10 min out: every 5 minutes
   *   < 10 min out : every minute
   *   final stretch: 30 s and 10 s
   * An 8 h interval costs ~33 wakeups instead of 480 with flat minute marks.
   */
  function scheduleBadge(totalMs) {
    const marks = new Set();
    for (let t = HOUR_MS; t < totalMs; t += HOUR_MS) {
      if (t >= 90 * MIN_MS) marks.add(t);
    }
    for (let t = 10 * MIN_MS; t < Math.min(totalMs, 90 * MIN_MS); t += 5 * MIN_MS) {
      marks.add(t);
    }
    for (let t = MIN_MS; t < Math.min(totalMs, 10 * MIN_MS); t += MIN_MS) {
      marks.add(t);
    }
    for (const t of [30000, 10000]) if (t < totalMs) marks.add(t);

    for (const remainingAtMark of marks) {
      badgeTimers.push(setTimeout(() => {
        sendBg({ type: 'badge', text: badgeText(deadline - Date.now()) });
      }, totalMs - remainingAtMark));
    }
    sendBg({ type: 'badge', text: badgeText(totalMs) });
  }

  // ---- lifecycle -----------------------------------------------------------

  function start(cfg) {
    disarm();
    config = cfg;
    fired = false;
    if (!cfg || !cfg.enabled) {
      sendBg({ type: 'badge', text: '' });
      return;
    }
    const ms = Math.max(MIN_INTERVAL_SEC, cfg.intervalSec | 0) * 1000;
    deadline = Date.now() + ms;
    armTimer(ms);
    scheduleBadge(ms);
    console.debug(`[evirgen] armed: ${ms / 1000}s, bypassCache=${!!cfg.bypassCache}`);
  }

  function fire() {
    if (fired) return; // worker and watchdog can race — first one wins
    fired = true;
    console.debug('[evirgen] firing reload');
    if (config && config.bypassCache) {
      sendBg({ type: 'hard-reload' }); // tabs.reload({bypassCache:true}) from SW
    } else {
      location.reload();
    }
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === 'config-changed') {
      start(msg.config);
      sendResponse({ ok: true });
    } else if (msg?.type === 'get-state') {
      sendResponse({ deadline, config });
    }
    return false;
  });

  // On (re)load, ask the SW whether this tab has an active config.
  // This single round-trip is what makes the cycle self-sustaining.
  sendBg({ type: 'get-config' }).then((cfg) => {
    if (cfg && cfg.enabled) start(cfg);
  });
})();
