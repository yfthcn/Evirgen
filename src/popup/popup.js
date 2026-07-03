/*
 * Evirgen — popup
 *
 * The countdown ticks LOCALLY from a deadline timestamp fetched once from the
 * content script; no per-second messaging while the popup is open.
 * i18n is JSON-based (locales/*.json) so languages can be added by dropping a
 * file and listing it in locales/index.json — no code change needed.
 */
'use strict';

const $ = (sel) => document.querySelector(sel);

const PRESETS_MIN = [5, 10, 15, 20];
const MIN_INTERVAL_SEC = 5;
const DEFAULT_INTERVAL_SEC = 300;

let T = {};            // active translation table
let currentTab = null; // active tab object
let config = null;     // this tab's config
let deadline = 0;      // epoch ms of next reload for this tab
let ticker = null;

// ---- messaging helpers -----------------------------------------------------

function sendBg(msg) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(msg, (res) => {
      void chrome.runtime.lastError;
      resolve(res);
    });
  });
}

function sendTab(tabId, msg) {
  return new Promise((resolve) => {
    try {
      chrome.tabs.sendMessage(tabId, msg, (res) => {
        if (chrome.runtime.lastError) resolve(null);
        else resolve(res);
      });
    } catch {
      resolve(null);
    }
  });
}

// ---- i18n --------------------------------------------------------------------

async function fetchJson(path) {
  try {
    const res = await fetch(chrome.runtime.getURL(path));
    return await res.json();
  } catch {
    return null;
  }
}

async function initI18n() {
  const index = (await fetchJson('locales/index.json')) || {
    default: 'en',
    languages: [{ code: 'en', name: 'English' }],
  };

  const stored = await chrome.storage.local.get('lang');
  const known = index.languages.map((l) => l.code);
  const sysLang = (navigator.language || 'en').toLowerCase().split('-')[0];
  const lang =
    (stored.lang && known.includes(stored.lang) && stored.lang) ||
    (known.includes(sysLang) && sysLang) ||
    index.default ||
    'en';

  T = (await fetchJson(`locales/${lang}.json`)) || {};

  const select = $('#langSelect');
  select.innerHTML = '';
  for (const l of index.languages) {
    const opt = document.createElement('option');
    opt.value = l.code;
    opt.textContent = l.name;
    if (l.code === lang) opt.selected = true;
    select.appendChild(opt);
  }
  select.addEventListener('change', async () => {
    await chrome.storage.local.set({ lang: select.value });
    T = (await fetchJson(`locales/${select.value}.json`)) || {};
    applyI18n();
    renderPresets();
    refreshActiveList();
  });

  applyI18n();
}

function t(key) {
  return T[key] || key;
}

function applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
}

// ---- formatting ----------------------------------------------------------------

function fmtCountdown(ms) {
  const s = Math.max(0, Math.round(ms / 1000));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n) => String(n).padStart(2, '0');
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`;
}

function fmtInterval(sec) {
  if (sec % 60 === 0) return `${sec / 60} ${t('minShort')}`;
  return `${sec} ${t('secShort')}`;
}

// ---- countdown ticker (local, no messaging) ---------------------------------

function startTicker() {
  stopTicker();
  ticker = setInterval(renderCountdown, 250);
  renderCountdown();
}

function stopTicker() {
  if (ticker) {
    clearInterval(ticker);
    ticker = null;
  }
}

function renderCountdown() {
  const el = $('#countdown');
  const enabled = config && config.enabled && deadline > 0;
  el.classList.toggle('live', !!enabled);
  if (!enabled) {
    el.textContent = '--:--';
    el.classList.remove('imminent');
    return;
  }
  const remaining = deadline - Date.now();
  el.textContent = fmtCountdown(remaining);
  el.classList.toggle('imminent', remaining < 10000);
  // Reload happened while popup is open: re-fetch new deadline from content.
  if (remaining < -1500) syncFromTab();
}

// ---- state sync ------------------------------------------------------------------

let syncInFlight = false;
let lastSyncAt = 0;

async function syncFromTab(force = false) {
  if (syncInFlight || (!force && Date.now() - lastSyncAt < 1000)) return;
  syncInFlight = true;
  lastSyncAt = Date.now();
  try {
    const state = await sendTab(currentTab.id, { type: 'get-state' });
    if (state) {
      if (state.config) config = state.config;
      deadline = state.deadline || 0;
    }
    syncUI();
  } finally {
    syncInFlight = false;
  }
}

function syncUI() {
  $('#enabledToggle').checked = !!(config && config.enabled);
  $('#bypassCache').checked = !!(config && config.bypassCache);

  document.querySelectorAll('.preset').forEach((btn) => {
    btn.classList.toggle(
      'selected',
      !!config && Number(btn.dataset.sec) === config.intervalSec
    );
  });

  if (config && !PRESETS_MIN.includes(config.intervalSec / 60)) {
    if (config.intervalSec % 60 === 0) {
      $('#customValue').value = config.intervalSec / 60;
      $('#customUnit').value = 'm';
    } else {
      $('#customValue').value = config.intervalSec;
      $('#customUnit').value = 's';
    }
  }
  renderCountdown();
}

// ---- actions ----------------------------------------------------------------------

function currentConfigDraft() {
  return {
    intervalSec: config?.intervalSec || DEFAULT_INTERVAL_SEC,
    enabled: config?.enabled || false,
    bypassCache: $('#bypassCache').checked,
  };
}

async function applyConfig(next) {
  config = next;
  const res = await sendBg({ type: 'set-config', tabId: currentTab.id, config: next });
  if (res && res.ok === false && next.enabled) {
    // content script unreachable — page cannot be auto-refreshed
    showUnsupported();
    return;
  }
  await syncFromTab(true);
  await refreshActiveList();
}

function bindEvents() {
  $('#enabledToggle').addEventListener('change', (e) => {
    const draft = currentConfigDraft();
    draft.enabled = e.target.checked;
    applyConfig(draft);
  });

  $('#bypassCache').addEventListener('change', () => {
    const draft = currentConfigDraft();
    applyConfig(draft);
  });

  $('#applyCustom').addEventListener('click', () => {
    const val = Number($('#customValue').value);
    if (!Number.isFinite(val) || val <= 0) return;
    const sec = $('#customUnit').value === 'm' ? val * 60 : val;
    const draft = currentConfigDraft();
    draft.intervalSec = Math.max(MIN_INTERVAL_SEC, Math.round(sec));
    draft.enabled = true;
    applyConfig(draft);
  });

  $('#customValue').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') $('#applyCustom').click();
  });

  $('#stopAll').addEventListener('click', async () => {
    await sendBg({ type: 'stop-all' });
    if (config) config.enabled = false;
    deadline = 0;
    syncUI();
    await refreshActiveList();
  });
}

function renderPresets() {
  const wrap = $('#presets');
  wrap.innerHTML = '';
  for (const min of PRESETS_MIN) {
    const btn = document.createElement('button');
    btn.className = 'preset';
    btn.dataset.sec = String(min * 60);
    btn.textContent = `${min} ${t('minShort')}`;
    btn.addEventListener('click', () => {
      const draft = currentConfigDraft();
      draft.intervalSec = min * 60;
      draft.enabled = true;
      applyConfig(draft);
    });
    wrap.appendChild(btn);
  }
  syncUI();
}

// ---- active timers list ---------------------------------------------------------

async function refreshActiveList() {
  const active = (await sendBg({ type: 'list-active' })) || [];
  const section = $('#activeSection');
  const list = $('#activeList');
  section.classList.toggle('hidden', active.length === 0);
  list.innerHTML = '';

  for (const item of active) {
    const li = document.createElement('li');

    const title = document.createElement('span');
    title.className = 'tab-title';
    if (currentTab && item.tabId === currentTab.id) title.classList.add('current');
    title.textContent = item.title;
    title.title = item.title;

    const interval = document.createElement('span');
    interval.className = 'tab-interval';
    interval.textContent = fmtInterval(item.cfg.intervalSec);

    const off = document.createElement('button');
    off.className = 'tab-off';
    off.textContent = t('off');
    off.addEventListener('click', async () => {
      const next = { ...item.cfg, enabled: false };
      await sendBg({ type: 'set-config', tabId: item.tabId, config: next });
      if (currentTab && item.tabId === currentTab.id) {
        config = next;
        deadline = 0;
        syncUI();
      }
      await refreshActiveList();
    });

    li.append(title, interval, off);
    list.appendChild(li);
  }
}

// ---- boot -------------------------------------------------------------------------

function showUnsupported() {
  $('#unsupported').classList.remove('hidden');
  $('#controls').classList.add('hidden');
  stopTicker();
}

async function init() {
  document.querySelector('#version').textContent =
    'v' + chrome.runtime.getManifest().version;

  await initI18n();
  renderPresets();
  bindEvents();

  [currentTab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const state = currentTab ? await sendTab(currentTab.id, { type: 'get-state' }) : null;

  if (!state) {
    showUnsupported();
  } else {
    config = state.config; // may be null (no timer yet)
    deadline = state.deadline || 0;
    syncUI();
    startTicker();
  }

  await refreshActiveList();
}

init();
