# Evirgen — Privacy Policy

*Last updated: July 3, 2026*

Evirgen is a browser extension that automatically reloads browser tabs at user-defined intervals. This policy describes what data the extension handles.

## Data collection

**Evirgen does not collect, transmit, sell, or share any data. There is no server, no account, no analytics, no telemetry, and no advertising.**

## What is stored, and where

All data stays on your device, inside the browser's extension storage:

- **Per-tab refresh settings** (interval, enabled state, hard-reload option) are kept in *session storage*. They are deleted automatically when the tab is closed or the browser restarts.
- **Your language preference** (e.g. English or Turkish) is kept in *local storage* so the popup opens in your chosen language.

Nothing else is stored. No browsing history, no page content, no personal information.

## Permissions explained

- **storage** — used only for the two items listed above.
- **tabs** — used to show the titles of tabs with active timers in the popup, to reload a tab with cache bypass, and to clean up settings when a tab closes.
- **Access to websites (content script)** — the refresh timer runs inside the page being refreshed, so the extension must be able to run on any page you choose to auto-refresh. It performs no action unless you explicitly enable a timer for that tab, and it does not read page content.

## Third parties

No data is shared with third parties, because no data is collected in the first place.

## Changes

If this policy ever changes, the update will be published at this address and reflected in the "last updated" date above.

## Contact

Questions: open an issue at [github.com/yfthcn/Evirgen](https://github.com/yfthcn/Evirgen) or visit [kaktusdev.net](https://kaktusdev.net).
