# Evirgen — Chrome Web Store Listing Kiti

## Kategori
**Primary: Workflow & Planning** (Productivity grubu altında)
Alternatif: Tools. Rakiplerin çoğu bu ikisinden birinde; Workflow & Planning monitoring/verimlilik aramalarında daha iyi eşleşiyor.

Default language: **English**

---

## Short description (max 132 karakter — 118 karakter)

Per-tab auto refresh with presets, custom intervals and a live countdown. Lightweight, private, zero background load.

---

## Detailed description (EN — store'a bunu yapıştır)

Evirgen reloads any tab automatically — each tab with its own interval, its own countdown, its own on/off switch.

FEATURES

• Per-tab timers: every tab is configured independently
• One-tap presets: 5 / 10 / 15 / 20 minutes
• Custom intervals: anything from 5 seconds upward, in seconds or minutes
• Live countdown: on the toolbar badge and in the popup
• Hard reload option: bypass the cache for monitoring pages that must be fresh
• Active timers list: see every refreshing tab in one place, switch any of them off
• Stop all: one button kills every timer at once
• English and Turkish included — more languages can be added with a single JSON file

LIGHT BY DESIGN

Evirgen was built around one rule: the browser must never feel it running.

• The background worker stays asleep. It wakes only for settings changes and a handful of badge updates per refresh cycle — never once per second.
• Timers are worker-based, so they stay accurate even in throttled background tabs. Dashboards left in the background refresh on time.
• Timers live inside each tab. Close the tab and the timer is gone — nothing lingers, nothing leaks.

PRIVATE BY DEFAULT

• No account, no sign-up, no tracking, no telemetry, no ads
• Settings are kept in session storage and vanish when the tab closes
• Nothing is ever sent anywhere — there is no server

Great for dashboards (Grafana, Kibana, status pages), ticket queues, live scores, auctions, stock/price monitoring and any page you are tired of refreshing by hand.

Zero dependencies. Plain vanilla JavaScript. A kaktusdev.net project — source and build pipeline at github.com/yfthcn.

---

## Detailed description (TR — Türkçe listing eklersen)

Evirgen sekmeleri otomatik yeniler — her sekmenin kendi aralığı, kendi geri sayımı, kendi aç/kapat düğmesi vardır.

ÖZELLİKLER

• Sekme başına zamanlayıcı: her sekme bağımsız ayarlanır
• Tek dokunuş preset'ler: 5 / 10 / 15 / 20 dakika
• Özel aralık: 5 saniyeden başlayarak saniye veya dakika cinsinden
• Canlı geri sayım: araç çubuğu rozetinde ve popup'ta
• Sert yenileme: önbelleği atlayarak her zaman taze içerik
• Aktif zamanlayıcı listesi: yenilenen tüm sekmeler tek yerde, istediğini kapat
• Tümünü durdur: tek tuşla bütün zamanlayıcılar durur
• İngilizce ve Türkçe hazır — tek JSON dosyasıyla yeni dil eklenebilir

TASARIM GEREĞİ HAFİF

• Arka plan işçisi uyur; yalnızca ayar değişiminde ve döngü başına birkaç rozet güncellemesinde uyanır
• Worker tabanlı sayaçlar kısıtlanmış arka plan sekmelerinde bile dakiktir
• Zamanlayıcı sekmenin içinde yaşar: sekme kapanınca zamanlayıcı da yok olur

VARSAYILAN OLARAK ÖZEL

• Hesap yok, kayıt yok, takip yok, telemetri yok, reklam yok
• Ayarlar oturum belleğinde tutulur, sekme kapanınca silinir
• Hiçbir veri hiçbir yere gönderilmez — sunucu yoktur

Bir kaktusdev.net projesidir — github.com/yfthcn

---

## Privacy sekmesi cevapları (reviewer bunları soruyor)

**Single purpose description:**
Automatically reloads browser tabs at user-defined intervals, with a per-tab countdown and controls.

**Permission justifications:**

- `storage` — Stores per-tab refresh intervals in session storage (cleared automatically when tabs close) and the user's language preference in local storage. No browsing data is stored.
- `tabs` — Required to display the titles of tabs with active timers in the popup list, to reload a tab with cache bypass (tabs.reload with bypassCache), and to clean up timer settings when a tab is closed.
- Host permission `<all_urls>` (content script) — The refresh timer runs inside the page being refreshed. The content script must be able to run on any page the user chooses to auto-refresh; it performs no action unless the user explicitly enables a timer for that tab, and it reads no page content.

**Remote code:** No, all code is packaged.
**Data usage:** Does not collect or transmit any user data. (Tüm "data collected" kutularını boş bırak.)

---

## Yükleme sırası notları

1. Package: `dist/evirgen-1.1.1-chrome.zip`
2. Screenshots (1280×800, sırayla): hero → intervals → control → light
3. Small promo tile: `small-promo-440x280.png`
4. Marquee promo tile: `marquee-promo-1400x560.png`
5. Global promo video: boş bırak
6. Homepage URL: https://kaktusdev.net — Support URL: https://github.com/yfthcn
7. TypeLess'te olduğu gibi privacy policy istenirse kaktusdev.net altına bir `evirgen/privacy.html` koy; metni "no data collected, settings stored locally in session storage, nothing transmitted" çerçevesinde tut. İstersen hazırlarım.
