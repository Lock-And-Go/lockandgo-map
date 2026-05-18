# LockAndGo

Slovenský sprievodca po **Bounce** úschovniach batožiny v Bratislave. 12 ručne vybraných spotov, mapa s filtrami, rezervácia cez Bounce affiliate.

**Live:** https://lockandgo.sk (po deploye)

## Štruktúra

- `index.html` — landing / o nás (statická, žiadny JS)
- `app.html` — interaktívna mapa (Leaflet + geolokácia + filtre)

Žiadny build step, žiadne dependencies — len HTML/CSS/inline JS. CDN pre Leaflet a Google Fonts.

## Lokálny vývoj

```bash
python3 -m http.server 8000
# alebo
npx serve .
```

Otvor `http://localhost:8000/`.

## Deploy

**Vercel:** prepoj repo → auto-deploy. Žiadna konfigurácia nutná. `vercel.json` nastavuje `cleanUrls` (URL bez `.html`).

## Údaje o spotoch

`SPOTS` pole v `app.html` (riadky ~960–1050). Každý spot má:
- `id`, `name`, `area`, `lat`, `lng`
- `hours.schedule` (7-denný rozvrh, index 0=Ne)
- `rating`, `reviews`
- `bookingUrl` (Bounce deep link s affiliate tracking)

Aktualizácia: uprav záznam, commit. Mapa, filtre, sort sa prepočítajú automaticky.

## Affiliate

Bounce affiliate program cez Impact.com. Tracking ref: `LOCKANDGO36164245765`. Pri rezervácii cez deep linky → provízia.
