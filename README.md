# Evirgen — Auto Refresh

Per-tab auto page refresh with presets (5/10/15/20 min), custom intervals, a live countdown, per-tab on/off and a one-button stop-all.

Zero dependencies, plain vanilla JavaScript. A [kaktusdev.net](https://kaktusdev.net) project.

*Evirgen* means "the one who turns" in Turkic mythology — a fitting name for a refresher.

[Türkçe README](README.tr.md) · [Privacy policy](PRIVACY.md)

## Why it's light

- **The timer lives in the content script, not the service worker.** The SW wakes only for settings changes and a handful of sparse badge updates per cycle; the rest of the time it sleeps.
- **Worker-based countdown.** Chrome throttles window timers in background tabs (intensive throttling = one wakeup per minute), which would wreck exactly the tabs people auto-refresh. Worker timers are exempt. If the page CSP blocks blob workers, a self-correcting chunked `setTimeout` watchdog takes over — the reload is guaranteed either way (the two layers race; first one wins).
- **Sparse badge marks:** hour boundaries → 5-minute marks in the last 90 min → minute marks in the last 10 min → 30/10 s. Even a 24-hour interval costs only ~50 SW wakeups.
- **Session-only settings** in `storage.session`: closing a tab (or the browser) cleans everything up automatically. `tabs.onRemoved` garbage-collects as well.
- The refresh cycle is self-sustaining: after each reload the content script re-injects, asks the SW for its config, and re-arms.

## Install (developer mode)

```
python3 build.py
```

- **Chrome / Edge:** `chrome://extensions` → Developer mode → *Load unpacked* → `dist/chrome/`
- **Firefox:** `about:debugging#/runtime/this-firefox` → *Load Temporary Add-on* → `dist/firefox/manifest.json`

Store-ready packages are produced as `dist/evirgen-<version>-{chrome,firefox}.zip`.

## Adding a language

1. Drop a JSON file into `src/locales/` (e.g. `de.json`) — use `en.json` as the key template.
2. Add it to the `languages` list in `src/locales/index.json`:
   ```json
   { "code": "de", "name": "Deutsch" }
   ```
3. Rebuild with `python3 build.py`.

The default language is detected from the system (`navigator.language`); users can switch in the popup, and the preference is kept in `storage.local`.

## Notes

- Minimum interval is **5 seconds** (enforced in code).
- The "hard reload" option bypasses the cache (`tabs.reload({bypassCache: true})`) — useful for monitoring pages.
- Browser-internal pages (`chrome://`, `about:`, extension pages) can't run content scripts, so they can't be auto-refreshed; the popup says so.
- `test/test.html` is a standalone page that counts reloads and logs timestamps + deltas — handy for verifying timing behavior.

## License

MIT — see [LICENSE](LICENSE).
