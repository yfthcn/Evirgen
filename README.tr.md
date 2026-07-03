# Evirgen — Auto Refresh

Sekme başına otomatik sayfa yenileme. Hazır aralıklar (5/10/15/20 dk), özel aralık (sn/dk), sekme başına aç/kapat, geri sayım rozeti ve tek tuşla "tümünü durdur".

Bir [kaktusdev.net](https://kaktusdev.net) projesi. Sıfır bağımlılık, saf vanilla JS.

## Mimari — neden tarayıcıyı yormaz

- **Zamanlayıcı content script'te yaşar, service worker'da değil.** SW yalnızca ayar değişikliklerinde ve seyrek rozet güncellemelerinde uyanır; geri kalan zamanda tamamen uykudadır.
- **Web Worker tabanlı sayaç.** Chrome, arka plan sekmelerinde `setTimeout`'u dakikada bir uyanmaya kısıtlar (intensive throttling). Worker zamanlayıcıları bu kısıtlamadan muaftır — arka planda bırakılan dashboard sekmeleri tam zamanında yenilenir. Sayfa CSP'si blob worker'ı engellerse `Date.now()` ile kendini düzelten parçalı `setTimeout`'a düşer (bu durumda arka plan sekmelerinde ±1 dk sapma olabilir).
- **Rozet güncellemeleri seyrektir:** kademeli işaretler: saat sınırları → son 90 dk'da 5 dk → son 10 dk'da dakika → 30/10 sn (24 saatlik aralık bile ~50 uyandırma). Saniye saniye SW uyandırma yoktur. Popup'taki canlı geri sayım ise deadline'dan lokal hesaplanır — popup açıkken bile mesajlaşma olmaz.
- **Ayarlar `storage.session`'da** tutulur: sekme kapanınca veya tarayıcı yeniden başlayınca kendiliğinden temizlenir, sızıntı olmaz. Sekme kapanışında ayrıca `tabs.onRemoved` ile çöp toplanır.
- Yenileme döngüsü kendi kendini besler: reload sonrası content script yeniden enjekte olur, SW'den ayarını sorar, sayacı yeniden kurar.

## Kurulum (geliştirici modu)

```
python3 build.py
```

- **Chrome / Edge:** `chrome://extensions` → Developer mode → *Load unpacked* → `dist/chrome/`
- **Firefox:** `about:debugging#/runtime/this-firefox` → *Load Temporary Add-on* → `dist/firefox/manifest.json`

Mağaza paketleri `dist/evirgen-<sürüm>-{chrome,firefox}.zip` olarak üretilir.

## Dil ekleme

1. `src/locales/` altına yeni bir JSON dosyası koy (ör. `de.json`) — anahtarlar için `en.json`'u şablon al.
2. `src/locales/index.json` içindeki `languages` listesine ekle:
   ```json
   { "code": "de", "name": "Deutsch" }
   ```
3. `python3 build.py` ile yeniden paketle.

Varsayılan dil sistem dilinden algılanır (`navigator.language`); kullanıcı popup'taki seçiciden değiştirebilir, tercih `storage.local`'da saklanır.

## Notlar

- Minimum aralık **5 saniye** (kod tarafında zorlanır).
- "Sert yenileme" işaretliyken önbellek atlanır (`tabs.reload({bypassCache: true})`) — monitoring sayfaları için.
- Tarayıcı iç sayfalarında (`chrome://`, `about:`, eklenti sayfaları) content script çalışamayacağı için otomatik yenileme desteklenmez; popup bunu belirtir.
