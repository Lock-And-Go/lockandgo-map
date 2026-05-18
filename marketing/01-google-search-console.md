# Google Search Console — krok po kroku

Cieľ: dostať `lockandgo.sk` do Google indexu **rýchlo** (3-7 dní namiesto 4-6 týždňov).

## A — vytvor property v GSC

1. Choď na **https://search.google.com/search-console**
2. Prihlás sa cez Google účet (môže byť `simon.kalis@lyceum.sk` alebo akýkoľvek iný — odporúčam vytvoriť dedikovaný `info@` alebo používať tvoj hlavný účet)
3. Klikni **+ Add property** vľavo hore
4. Vyber **Domain** (NIE „URL prefix"!) — Domain property pokrýva apex aj www aj všetky subdomény + http/https. Lepšie ako URL prefix.
5. Zadaj: `lockandgo.sk` (bez `https://`, bez `www`)
6. Klikni **Continue**

## B — overenie cez DNS TXT (Websupport)

Google ti ukáže okno s textom typu:

```
google-site-verification=AbCd1234EfGh5678...
```

Skopíruj si tento celý string (počas overenia ho nezatváraj — keď zatvoríš, niekedy Google vygeneruje iný kód).

Otvor **Websupport admin** v ďalšom tabe:

1. Prihlás sa na **admin.websupport.sk**
2. Choď na svoju doménu `lockandgo.sk` → **DNS Records** (Záznamy DNS)
3. Klikni **+ Pridať záznam** (alebo „+ Add record")
4. Vyplň:
   - **Typ**: `TXT`
   - **Názov / Hostname**: nechaj prázdne, alebo daj `@` (znamená koreň domény)
   - **Hodnota / Value**: vlož ten celý reťazec `google-site-verification=AbCd1234...` (vrátane prefixu „google-site-verification=")
   - **TTL**: nechaj predvolené (typicky 600 alebo 3600)
5. Ulož

Návrat do Google Search Console → klikni **Verify**.

Ak hláška „Verification failed":
- Počkaj 5-15 minút (DNS propagácia)
- Skontroluj cez **https://www.nslookup.io/domains/lockandgo.sk/dns-records/txt/** že tam TXT záznam vidno
- Skús **Verify** znovu

Ak hláška „Ownership verified":
- ✅ Hotovo, môžeš pokračovať

## C — submit sitemap

1. V GSC vľavo dole → **Sitemaps**
2. **Add a new sitemap** → vlož: `sitemap.xml` (NIE celú URL, len cestu)
3. **Submit**
4. Status by mal zmeniť z „Couldn't fetch" na **„Success"** do pár minút (môže trvať hodiny pri prvom submite)

## D — request indexing manuálne (kritické!)

Toto je hack ktorý donúti Google nakrúliť tvoje URL hneď, namiesto čakania týždne.

V GSC vľavo hore je **URL Inspection** vyhľadávacie pole. Pre každú z nasledujúcich URL spravi:

1. Vlož URL do poľa, stlač Enter
2. Počkaj 10-30 sekúnd kým Google overí
3. Klikni **Request Indexing** (vpravo, šedé tlačítko)
4. Počkaj na potvrdenie „Indexing requested"
5. Opakuj pre ďalšiu URL

URL ktoré treba pretočiť (5 ks):

```
https://lockandgo.sk/
https://lockandgo.sk/app
https://lockandgo.sk/en
https://lockandgo.sk/sitemap.xml
https://lockandgo.sk/llms.txt
```

## E — čo sa stane potom

- **Do 24 hodín:** Google začne crawlovať
- **3-7 dní:** Tvoja stránka začne ukazovať keď vyhľadáš **„LockAndGo"** alebo **„lockandgo.sk"** v Google
- **2-4 týždne:** Začneš vidieť dáta v **Performance** tabe (impressions, clicks)
- **Po mesiaci:** Vidíš ranking pre keywords ako „úschovňa batožiny Bratislava" — bude pozícia 30-80 spočiatku, postupne sa zlepší ako buduješ backlinky

## F — týždenná kontrola (5 minút, každý pondelok)

1. GSC → **Coverage** → skontroluj či nemáš errory („Excluded", „Error")
2. GSC → **Performance** → ktoré keywordy ti idú najlepšie
3. GSC → **Sitemaps** → status musí byť „Success"

## Bonus: Bing Webmaster Tools

Bing má ~3-5% trhu ale za 10 minút máš ďalšiu indexáciu zadarmo:

1. **https://www.bing.com/webmasters**
2. Pridaj `lockandgo.sk` → **Import from Google Search Console** (Bing to ti dovolí ak si už verifikoval cez GSC)
3. Submit sitemap rovnako: `sitemap.xml`

Hotovo.
