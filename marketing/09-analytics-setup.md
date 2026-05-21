# Analytics setup — pre Šimona

Aktuálne nainštalované:
- ✅ **Vercel Web Analytics** (skripty pridané do 60 HTML súborov) — po deployi treba **enable v dashboarde**: `vercel.com/lockandgo/lockandgo-map/analytics` → kliknúť „Enable Web Analytics" + „Enable Speed Insights"
- ✅ **Google Search Console** (zatiaľ neaktivované) — DNS verify + submit sitemap
- 🟡 **Google Analytics 4** — čaká na tvoj Measurement ID

---

## 1. Vercel Web Analytics (10 sek po deployi)

1. Po deployi otvor https://vercel.com/lockandgo/lockandgo-map
2. V hornom menu kliknúť na **Analytics**
3. Tlačidlo **Enable Web Analytics** → klik
4. Tlačidlo **Enable Speed Insights** → klik
5. Hotovo. Dáta sa začnú zbierať okamžite, prvé reálne čísla uvidíš za 5–30 minút.

**Čo vidíš v dashboarde:**
- Total visitors (unique) + pageviews
- Top pages (ktorá stránka má najviac návštev)
- Top referrers (odkiaľ ľudia prišli — Google, Instagram, priame, atď.)
- Top countries / devices / browsers
- Core Web Vitals (LCP, FID, CLS, INP) — Speed Insights tab
- Real-time live view

Bezplatný plán: **2 500 events/mesiac** stačí pre nový projekt. Keď budeš mať 50+ návštev/deň, ozvi sa, pozrieme upgrade alebo migrácia.

---

## 2. Google Search Console (15 min, **najdôležitejšie pre SEO**)

GSC je iný typ analytics — neukáže ti návštevy, ale **search queries**: čo presne ľudia hľadali pred kliknutím na tvoju stránku v Google.

### Postup:

1. Otvor https://search.google.com/search-console
2. Klikni **Add property** → vyber **Domain** (nie URL prefix — Domain pokryje SK aj EN aj všetky subdomény naraz)
3. Zadaj: `lockandgo.sk`
4. Google ti dá **TXT záznam** typu:
   ```
   google-site-verification=ABC123xyzExampleString
   ```
5. **Kde pridať záznam:** záleží kde máš zaregistrovanú doménu. Pravdepodobne websupport.sk alebo nic.sk. Hľadaj v admin paneli „DNS records" → „Add record" → Type: TXT, Host/Name: `@` (alebo prázdne), Value: ten string z Google.
6. Klikni **Verify** v GSC. Trvá to 5 min až 2 hodiny kým DNS propaguje.
7. Po verifikácii: **Submit sitemap** → URL: `https://lockandgo.sk/sitemap.xml`
8. To isté pre `https://lockandgo.sk/llms-full.txt` (voliteľné, GSC ho neindexuje ale je dobrá prax)

### Čo budeš vidieť (do 7 dní):

- **Performance**: aké queries ti priviedli ľudí, koľko impressions, CTR, priemerná pozícia
- **Pages**: ktoré URL sú indexované (cieľ: všetkých 57 z sitemap)
- **Coverage**: errors, redirecty, soft 404s
- **Mobile usability**: warnings ak niečo nie je mobile-friendly
- **Core Web Vitals**: real-user performance metrics

**Použi to týždenne** — GSC povie či tvoje práce na SEO fungujú alebo nie.

### Ak chceš HTML file verification namiesto DNS:

1. V GSC vyber **URL prefix** namiesto Domain (pokryje len `https://lockandgo.sk/`, nie `lockandgo.sk` ako root domain)
2. Stiahni `googleXXXXXXXX.html` súbor
3. Pošli mi ho cez chat (alebo nahraj do root priečinka `/Users/osobne/lockandgo-v2/`) — ja ho commitnem a deployuje sa
4. Verifikuj cez tlačidlo

DNS verification je odporúčaná lebo verifikuje aj `/en` subpath ako aj prípadné subdomény.

---

## 3. Google Analytics 4 (čaká na tvoju akciu)

### Krok 1 — vytvor property (5 min)

1. Otvor https://analytics.google.com
2. **Admin** (ikona ozubeného kolesa vľavo dole) → **Create** → **Account**
   - Account name: `LockAndGo`
   - Data sharing: vyber čo chceš (môžeš všetko vypnúť, neovplyvní funkčnosť)
3. **Create property**
   - Property name: `lockandgo.sk`
   - Reporting time zone: `Slovakia / Bratislava`
   - Currency: `Euro (EUR)`
4. **Business details** → vyber Small business, Web
5. **Create data stream** → **Web**
   - URL: `https://lockandgo.sk`
   - Stream name: `LockAndGo Web`
   - **Enhanced measurement: ON** (toto automaticky tracker scroll, outbound clicks, file downloads — super pre nás)
6. **Skopíruj Measurement ID** — vyzerá ako `G-XXXXXXXXXX` (10 znakov za G-)

### Krok 2 — pošli mi ID

Pošli mi cez chat presný Measurement ID (`G-XXXXXXXXXX`). Ja ho zapojím do skriptu na všetkých 60 HTML stránkach + nastavím custom event tracking pre kľúčové akcie:

- `book_click` — užívateľ klikol "Rezervovať" na spot pageu
- `map_open` — užívateľ otvoril /app
- `external_link_click` — outbound klik (Bounce, Radical, atď.)
- `area_view` — návšteva area landing page
- `blog_read` — scroll > 75% na blog článku

Po deployi uvidíš v GA4:
- Real-time users (aktuálne na stránke)
- Konverzný funnel: home → mapa → spot → Rezervovať
- Demographics (vek, pohlavie, záujmy — len ak >100 návštev/deň)
- Acquisition: ktorý kanál priniesol najviac konverzií (Reddit vs Instagram vs Google)
- **Linkovanie s GSC** → priame mapovanie query → konverzia (najsilnejší featur)

### Krok 3 — link GSC + GA4 (po oboch)

V GSC → **Settings** → **Associations** → vyhľadaj svoju GA4 property → **Link**. Dôvod: dáta sa krížia, GA4 ti potom vie ukázať aj search queries.

---

## Bonus — vlastný UTM tracking link

Keď postneš na Reddit alebo Instagram, použi UTM parametre:

```
https://lockandgo.sk?utm_source=reddit&utm_medium=social&utm_campaign=launch
https://lockandgo.sk?utm_source=instagram&utm_medium=social&utm_campaign=launch
https://lockandgo.sk?utm_source=tiktok&utm_medium=social&utm_campaign=launch
```

V GA4 potom uvidíš presne, koľko ľudí prišlo z ktorej platformy. Bez UTM by si videl len „social".

---

## Časová investícia (najprv najjednoduchšie)

| Čas | Akcia | ROI |
|---|---|---|
| 30 sek | Vercel: enable Web Analytics + Speed Insights (po deployi) | Vidíš trafiku okamžite |
| 15 min | GSC: DNS verify + submit sitemap | Google ťa zaindexuje za 1-3 dni namiesto 1-3 týždňov |
| 10 min | GA4: create property → pošli mi G-ID | Behavior tracking + konverzie |
| 5 min | Link GSC ↔ GA4 | Query-level konverzia data |

Spolu 30 min tvojho času + 10 min mojej práce → kompletný analytics stack.
