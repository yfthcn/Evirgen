/*
 * Evirgen — background service worker (event page on Firefox)
 *
 * Design: the SW owns NO timers. It is a thin config store + message router.
 * All countdown logic lives in the content script of each tab, so the SW
 * stays asleep except for config changes and sparse badge updates.
 */
'use strict';

const KEY = 'configs'; // storage.session: { [tabId]: { intervalSec, enabled, bypassCache } }

async function getConfigs() {
  const obj = await chrome.storage.session.get(KEY);
  return obj[KEY] || {};
}

async function setConfigs(configs) {
  await chrome.storage.session.set({ [KEY]: configs });
}

function setBadge(tabId, text) {
  chrome.action.setBadgeText({ tabId, text }).catch(() => {});
  if (text) {
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#b45309' }).catch(() => {});
    chrome.action.setBadgeTextColor?.({ tabId, color: '#fffbeb' })?.catch?.(() => {});
  }
}

async function notifyTab(tabId, config) {
  try {
    await chrome.tabs.sendMessage(tabId, { type: 'config-changed', config });
    return true;
  } catch {
    return false; // no content script on this tab (browser-internal page)
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    switch (msg?.type) {
      // ---- from content scripts -------------------------------------
      case 'get-config': {
        if (!sender.tab) return sendResponse(null);
        const configs = await getConfigs();
        sendResponse(configs[sender.tab.id] || null);
        break;
      }
      case 'badge': {
        if (sender.tab) setBadge(sender.tab.id, msg.text || '');
        sendResponse({ ok: true });
        break;
      }
      case 'hard-reload': {
        if (sender.tab) chrome.tabs.reload(sender.tab.id, { bypassCache: true });
        sendResponse({ ok: true });
        break;
      }
      // ---- from popup ------------------------------------------------
      case 'set-config': {
        const configs = await getConfigs();
        if (msg.config) configs[msg.tabId] = msg.config;
        else delete configs[msg.tabId];
        await setConfigs(configs);
        const delivered = await notifyTab(msg.tabId, msg.config || { enabled: false });
        if (!msg.config || !msg.config.enabled) setBadge(msg.tabId, '');
        sendResponse({ ok: delivered });
        break;
      }
      case 'stop-all': {
        const configs = await getConfigs();
        for (const id of Object.keys(configs)) {
          configs[id].enabled = false;
          const tabId = Number(id);
          await notifyTab(tabId, configs[id]);
          setBadge(tabId, '');
        }
        await setConfigs(configs);
        sendResponse({ ok: true });
        break;
      }
      case 'list-active': {
        const configs = await getConfigs();
        const out = [];
        let dirty = false;
        for (const [id, cfg] of Object.entries(configs)) {
          if (!cfg.enabled) continue;
          const tabId = Number(id);
          try {
            const tab = await chrome.tabs.get(tabId);
            out.push({ tabId, title: tab.title || tab.url || '#' + tabId, cfg });
          } catch {
            delete configs[id]; // tab is gone, garbage-collect
            dirty = true;
          }
        }
        if (dirty) await setConfigs(configs);
        sendResponse(out);
        break;
      }
      default:
        sendResponse(null);
    }
  })();
  return true; // keep channel open for async sendResponse
});

// Garbage-collect config when a tab closes.
chrome.tabs.onRemoved.addListener(async (tabId) => {
  const configs = await getConfigs();
  if (configs[tabId]) {
    delete configs[tabId];
    await setConfigs(configs);
  }
});
