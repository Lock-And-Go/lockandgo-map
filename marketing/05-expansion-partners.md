# LockAndGo — expansion / partner research

**STATUS (2026-05-20):** Všetky tieto spoty boli pridané do `app.html` ako id 17–32. Mapa teraz zobrazuje **32 spotov** (predtým 16). Affiliate registrácie zatiaľ NEsú dokončené — booking URL-ky idú priamo na operátorov.

Zoznam ďalších úschovní v Bratislave, ktoré pôvodne **neboli** na LockAndGo. Použitie:
- spoty s ✅ affiliate môžu ísť rovno do `app.html` SPOTS array (po overení) a generujú províziu
- spoty s 🚶 walk-in pridať len ako mapový spot bez `bookingUrl` (typ `walkin`)
- spoty s ⚠️ pred publikovaním overiť telefonicky

Legenda affiliate stĺpca:
- ✅ **má verejný affiliate program** (možné sa prihlásiť cez sieť alebo priamo)
- 🤝 **vyžaduje priamy partnership outreach** (žiadny verejný affiliate, len B2B kontakt)
- 🚶 **walk-in / žiadne online booking** — affiliate sa nedá nasadiť na úschovňu samu, max. cez Booking.com (hotely)

---

## 1. Self-service 24/7 skrinky (slovenské / lokálne)

### uschovabatoziny.sk / bratislava.center
- **Typ:** automatické skrinky 24/7
- **Adresa:** Obchodná 9, Bratislava (vedľa zastávky Poštová)
- **Cena:** 2 € / 2h · 4 € / 4h · 6 € / 24h
- **Platba:** iba karta · **Bezpečnosť:** CCTV 24/7
- **Booking:** https://uschovabatoziny.sk/en/ (alt: https://bratislava.center/)
- **Affiliate:** 🤝 žiadny verejný program — outreach priamo prevádzkovateľovi
- **⚠️ Konflikt:** Obchodná 9 je už v `app.html` ako id:16 (`Obchodná 9 · automatické skrinky`). Overiť či to je ten istý operátor — ak áno, len doplniť `bookingUrl` po dohode.

### Luggage Lockers Bratislava (Pod mostom SNP)
- **Typ:** self-service lockery 24/7
- **Adresa:** Pod mostom SNP (strana Petržalky, vstup k Mostu SNP) — INÉ miesto ako Hviezdoslavovo nám.
- **Bezpečnosť:** CCTV 24/7, WhatsApp support
- **Kontakt:** +421 905 599 053
- **Booking:** https://www.luggagelockersbratislava.com/
- **Affiliate:** 🤝 priamy outreach (vlastný booking systém, malý prevádzkovateľ)
- **Status:** Unikátna lokalita, žiadne prekrytie s Lock&Go.

### LugLockers (nová sieť, 2026)
- **Typ:** lockery, 3 lokality
- **Lokality:**
  - Hlavná stanica: Námestie Franza Liszta, 811 04 — https://www.luglockers.com/branches/hlavna-stanica-central-railway-station
  - AS Mlynské Nivy: Mlynské nivy 31, 811 09
  - ŽST Bratislava-Petržalka: Kopčianska, 851 01
- **Hub:** https://www.luglockers.com/cities/bratislava
- **Affiliate:** 🤝 nová sieť — outreach priamo, dobrá šanca na partnership lebo potrebujú traffic
- **⚠️ STATUS:** Web funguje, ale booking na Hlavnej ukazuje „0 EUR / is not bookable" — pred publikovaním overiť telefonicky.

---

## 2. Globálne platformy — nové zóny mimo Lock&Go

### Radical Storage — Ružinov spoty (mimo Starého Mesta)
- **Hub:** https://radicalstorage.com/luggage-storage/bratislava
- **Cena:** 5 €/deň/kus, poistenie 3000 €
- **Nové lokality (NIE sú v Lock&Go zónach):**
  - Miletičová — reštaurácia pri trhu, 10:00–21:00 (Ružinov)
  - Pri Dulovom námestí — shop, 9:00–18:00 (Ružinov)
  - Nivy area — reštaurácia, 6:00–23:00 — https://radicalstorage.com/luggage-storage/bratislava/bratislava-old-town/luggage-storage-nivy
  - Medická záhrada — reštaurácia, 11:00–21:00 — https://radicalstorage.com/luggage-storage/bratislava/city-center/luggage-storage-medicka-zahrada
- **Affiliate:** ✅ **MÁ verejný affiliate program** — Radical Storage Partners (Impact Radius). Komisia per booking. Prihláška: https://radicalstorage.com/affiliate-program/
- **TODO:** zaregistrovať sa, získať deep linky na 4 spoty, pridať do `app.html` ako Bounce-style entries s `providerLabel:'Radical Storage'`.

### LuggageHero — Petržalka + Nové Mesto
- **Cena:** 1.49 €/hod ALEBO 4.90 €/deň, poistenie 500 €
- **Nové lokality (mimo Lock&Go zón):**
  - Bratislava-N.Mesto / Vinohrady: https://luggagehero.com/bratislava/bratislava-n-mesto/
  - ŽST Bratislava-Petržalka: https://luggagehero.com/bratislava/zeleznicna-stanica-bratislava-petrzalka/
- **Affiliate:** ✅ **MÁ partner program** — cez Awin / Impact siete + vlastný "LuggageHero Partner" program. Komisia per booking + permanent cookie.
- **TODO:** zaregistrovať cez https://luggagehero.com/business/ alebo Awin, pridať deep linky.

### Stasher
- **Cena:** 3.49–4.75 €/deň/kus, poistenie 1100 €
- **Hub:** https://stasher.com/luggage-storage/slovakia/bratislava
- **Affiliate:** ✅ **MÁ affiliate program** — cez Awin (search "Stasher" v Awin advertiser directory). Komisia per booking.
- **Status:** Iba 2 spoty (Hlavná, Safestay) — väčšina duplicitná s Lock&Go. Nízka priorita.

---

## 3. Shopping centrá (cloakroom / customer service)

### OC Vivo! (býv. Polus City Center) — NOVÁ ZÓNA
- **Adresa:** Vajnorská 100, Bratislava-Nové Mesto
- **Typ:** vyhradený priestor so skrinkami pri infodesku
- **Citácia:** „U nás môžete prísť aj s batožinou, máme vyhradený priestor so skrinkami…"
- **Info:** https://vivo-shopping.com/en/bratislava/services
- **Booking:** walk-in, info na infodesku
- **Affiliate:** 🚶 walk-in, žiadne online booking
- **Status:** Úplne NOVÁ geografická zóna (Vajnorská smer) — neprekrýva sa s Lock&Go.

### OC Aupark — cloakroom (separátne od Bounce)
- **Adresa:** pri konci travelátora dole do garáže, blízko TERNO supermarketu
- **Typ:** klasická cloakroom (slúži aj ako Packeta výdajné miesto)
- **Otváracia doba:** podľa OC: https://aupark-bratislava.sk/en/opening-hours
- **Affiliate:** 🚶 walk-in, žiadny online booking
- **Status:** Aupark je v Lock&Go zónach, ale Bounce tam ide cez iný partner — cloakroom je ODLIŠNÝ produkt.

---

## 4. Dopravné uzly (oficiálne)

### Náhradná AS Bottova / Chalupkova
- **Adresa:** Chalupkova / Bottova (oproti Alza, krátkodobá zóna z 2017)
- **Typ:** úschovňa
- **Info:** https://www.autobusovastanica.sk/nova-stanica-nivy
- **Affiliate:** 🚶 walk-in
- **Status:** INÉ ako „OC Nivy" v Lock&Go — minoritná stanica.

### ZSSK Petržalka (manual + lockers)
- **Adresa:** ŽST Petržalka, Kopčianska
- **Typ:** ZSSK manuálna úschovňa + lockery
- **Cena (manual):** <15 kg 2 €/deň, >15 kg 2.50 €/deň, kočík 1.50 €, bicykel 2.50 €, 2. deň 1.50 €
- **Lockery:** 2 € štart, max 72h, iba mince 1 €/2 €
- **Info:** https://www.zssk.sk/sluzby/sluzby-na-stanici/uschova-batozin/
- **Affiliate:** 🚶 verejná služba — žiadny affiliate
- **Status:** Petržalka je v Lock&Go zónach iba cez Aupark — toto je iný typ.

### ⛔ Letisko M. R. Štefánika BTS — VYRADENÉ
- **Status:** Oficiálne potvrdené že letisko **nemá** úschovňu ani lockery. Iba luggage wrapping a váženie.
- **Zdroj:** https://www.bts.aero/en/services/baggage/

---

## 5. Hostely / hotely s non-guest storage

### Safestay Bratislava (Presidential Palace) — DÔLEŽITÝ
- **Adresa:** Leskova 9A
- **Typ:** luggage room **explicitne pre non-guests** (za poplatok, info na recepcii)
- **Booking:** https://www.safestay.com/venue/safestay-bratislava-presidential-palace/
- **Affiliate:**
  - 🚶 samotná úschovňa = walk-in (nedá sa booknúť online)
  - ✅ ubytovanie cez **Booking.com / Hostelworld affiliate** áno — len ak chceš generovať províziu z ubytovania
- **Status:** Najistejší non-guest hostel v BA — väčšina iných je len pre svojich hostí.

### Hotel Loft Bratislava (4★)
- **Adresa:** biznis distrikt, blízko Prezidentského paláca
- **Typ:** 24h recepcia + luggage storage
- **Info:** https://loft.hotelbratislava.net/en/
- **Affiliate:**
  - 🚶 luggage storage walk-in
  - ✅ ubytovanie cez Booking.com affiliate
- **Status:** Non-guest policy treba potvrdiť telefonicky.

---

## TL;DR — kde sa DÁ získať affiliate link pre booking online

| Služba | Affiliate? | Sieť / kontakt |
|---|---|---|
| **Radical Storage** (4 nové spoty v Ružinove/Nivy/Medická) | ✅ ÁNO | radicalstorage.com/affiliate-program/ (Impact Radius) |
| **LuggageHero** (Nové Mesto, ŽST Petržalka) | ✅ ÁNO | luggagehero.com/business/ alebo Awin |
| **Stasher** (Hlavná, Safestay — duplicitné s Lock&Go) | ✅ ÁNO | Awin advertiser directory |
| **Safestay / Hotel Loft** (len ubytovanie, nie úschovňa) | ✅ áno na hotel | Booking.com affiliate / Hostelworld |
| uschovabatoziny.sk · Obchodná 9 | 🤝 priamy outreach | partner@... priamy email |
| Luggage Lockers Bratislava (Most SNP) | 🤝 priamy outreach | +421 905 599 053 |
| LugLockers (3 lokality) | 🤝 priamy outreach | nová sieť, dobré timing pre partnership |
| OC Vivo! · OC Aupark cloakroom | 🚶 walk-in | žiadny online booking |
| AS Bottova · ZSSK Petržalka | 🚶 walk-in | verejná služba |
| Letisko BTS | ⛔ N/A | nemá úschovňu |

**Priorita pre rýchle pridanie províznych spotov:**
1. **Radical Storage** — 4 nové geografické zóny (Ružinov, Nivy area, Medická záhrada) → najväčší ROI
2. **LuggageHero** — Nové Mesto/Vinohrady + Petržalka (mimo Bounce pokrytia)
3. **Stasher** — odložiť, väčšina duplicitná
