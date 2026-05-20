# Entity setup — Wikidata + LinkedIn + X/Twitter

Cieľ: vytvoriť overené entity ktoré Google Knowledge Graph + AI engines použijú na potvrdenie identity značky a zakladateľa. Toto je **najdôležitejší zdroj GEO autority** ktorý momentálne LockAndGo nemá.

Sekvencia (od najjednoduchšej po najnáročnejšiu):
1. LinkedIn Company Page (15 min)
2. X / Twitter @lockandgosk (10 min)
3. Wikidata item (45–60 min, vyžaduje 3 zdrojové linky)

Po každom kroku → vrátiť sa do `index.html` + `en/index.html` JSON-LD a pridať nový profile URL do `Organization.sameAs` a `Person.sameAs`. Potom commit + deploy.

---

## 1. LinkedIn Company Page — `linkedin.com/company/lockandgo`

**Type:** Small business · Tourism · 1 employee
**Address:** Bratislava, Slovakia
**Founded:** 2026

**Tagline (120 char max):**
> Mapa 32 úschovní batožiny v Bratislave — Bounce, Radical, ZSSK lockery, walk-in. Po slovensky, zadarmo, bez registrácie.

**About / description (overview field, 2000 char max):**
> LockAndGo je slovenský sprievodca po úschovniach batožiny v Bratislave. Agregujeme 32 spotov v meste na jednej mape — partneri ako Bounce, Radical Storage, LuggageHero, plus ZSSK manuálne úschovne a 24/7 samoobslužné lockery, samoobslužné boxy v OC Nivy, cloakroomy v Auparku a Vivo!, hotelové úschovne (Safestay, Hotel Loft) a walk-in prevádzky. Cena pre užívateľa je rovnaká, ako pri rezervácii priamo u prevádzkovateľa.
>
> Pre koho je to: turisti z Viedne, Budapešti a Prahy, day-trippers, tranzitní cestujúci cez Bratislavu, Slováci pred letiskom BTS, lokáli sťahujúci sa medzi bytmi.
>
> Stránka: https://lockandgo.sk
>
> Zakladateľ Šimon Kališ (16, Bratislava). Verejný štart máj 2026.

**Website:** https://lockandgo.sk
**Phone:** +421 948 929 260
**Industry:** Travel Arrangements
**Specialties:** Luggage storage, Bratislava tourism, Travel logistics, Discovery platforms

**Cover photo:** Použiť OG image z `/api/og` (alebo screenshot mapy z `/app`)
**Logo:** Pošli ako 400×400 PNG — vyrender z `/favicon.svg` (Pillow už nainštalovaný, alebo zväčši cez Figma)

**Po vytvorení:**
1. Skopíruj URL profilu (napr. `https://www.linkedin.com/company/lockandgo`)
2. Pridaj do `index.html` + `en/index.html` v `Organization.sameAs` a `Person.sameAs`
3. Šimonov personálny LinkedIn (ak má) → tiež v `Person.sameAs`

---

## 2. X / Twitter — handle `@lockandgosk`

(Alternatíva ak je `@lockandgo` zabraný: `@lockandgo_sk` alebo `@lockandgomap`. Skontroluj cez `x.com/[handle]`.)

**Display name:** LockAndGo
**Bio (160 char max):**
> Mapa 32 úschovní batožiny v Bratislave 🇸🇰 · Bounce, Radical, ZSSK lockery, walk-in · po slovensky · zadarmo

**Location:** Bratislava, Slovakia
**Website:** https://lockandgo.sk
**Profile photo:** logo (200×200 PNG z `/favicon.svg`)
**Header photo:** OG image z `/api/og` (1500×500 cropped)

**Pinned post (po vytvorení):**
> Mapa všetkých 32 úschovní batožiny v Bratislave na jednom mieste — Bounce, Radical, LuggageHero, ZSSK lockery 24/7, walk-in cloakroomy. Po slovensky, zadarmo. lockandgo.sk

**Po vytvorení:**
1. Add `https://twitter.com/lockandgosk` (alebo finálny handle) do `Organization.sameAs` a `Person.sameAs`
2. Twitter ti dá verifikáciu cez email — to v podstate stačí pre Knowledge Graph signál

---

## 3. Wikidata item — najdôležitejšie

**Toto je high-effort, high-impact. Vyžaduje 3 nezávislé zdrojové URL (preto je krok 1+2 prvý — slúžia ako zdroje).**

Postup:
1. Vytvor účet na https://www.wikidata.org/wiki/Special:CreateAccount (gmail OK)
2. Choď na https://www.wikidata.org/wiki/Special:NewItem
3. **Label (Slovak):** LockAndGo
4. **Label (English):** LockAndGo
5. **Description (Slovak):** slovenský sprievodca po úschovniach batožiny v Bratislave
6. **Description (English):** Slovak discovery platform for luggage storage in Bratislava
7. **Aliases (Slovak):** Lock and Go, lockandgo.sk
8. **Aliases (English):** Lock & Go

### Properties to add (cez „add statement"):

| Property | Value | Source |
|---|---|---|
| `P31` (instance of) | `Q43229` (organization) alebo `Q4830453` (business) | žiadny |
| `P31` (instance of) | `Q4502119` (online business) | žiadny |
| `P17` (country) | `Q214` (Slovakia) | lockandgo.sk |
| `P276` (location) | `Q1780` (Bratislava) | lockandgo.sk |
| `P571` (inception) | 2026-05-07 | lockandgo.sk |
| `P856` (official website) | https://lockandgo.sk | (sama hodnota je zdroj) |
| `P407` (language of work) | `Q9058` (Slovak), `Q1860` (English) | lockandgo.sk |
| `P1296` (image of catalog) | URL OG image / logo | lockandgo.sk |
| `P2002` (Twitter username) | lockandgosk | x.com profil |
| `P4264` (LinkedIn company ID) | lockandgo | linkedin.com profil |
| `P2003` (Instagram username) | lock1and2go | instagram.com profil |
| `P3984` (subreddit) | (none yet) | — |
| `P112` (founder) | (create separate item for Šimon Kališ — see below) | lockandgo.sk |

### Sources required for each non-trivial statement

Wikidata vyžaduje pre tvrdenia minimálne 1 reference. Použiteľné:
- `https://lockandgo.sk/o-nas` — primárny zdroj pre založenie, sídlo, jazyk
- `https://lockandgo.sk/llms-full.txt` — zdroj pre dátum štartu, počet spotov
- Tvoj LinkedIn profile (po vytvorení)
- Tvoj X profile (po vytvorení)
- Akýkoľvek **press article** ak vyjde (Refresher, Startitup, SME) — toto je zlatá referencia

### Šimon Kališ ako samostatná Wikidata Person item (voliteľné)

Šimon by mal byť samostatný Wikidata item LEN ak máš aspoň jeden tlačový článok ktorý ho menuje. Bez press coverage to môže byť označené ako self-promotional a item môže byť deletnutý cez AfD. Počkaj kým vyjde aspoň 1 článok v slovenských médiách.

Keď bude: založ item `Šimon Kališ` s:
- P31: human (Q5)
- P21: male (Q6581097)
- P27: Slovakia (Q214)
- P106 (occupation): software developer (Q5482740) + entrepreneur (Q131524)
- P108 (employer) / P127 (owner): tvoj LockAndGo item ID (Q-niečo)
- P1559 (native name): Šimon Kališ

### Po vytvorení Wikidata itemu

1. Skopíruj Q-identifier (napr. `Q123456789`)
2. Pridaj do `Organization.sameAs` v JSON-LD:
   `"https://www.wikidata.org/wiki/Q123456789"`
3. Tiež do `Person.sameAs` (keď bude Person item)
4. Vyplň `identifier` v `Organization`:
   ```json
   "identifier": [
     { "@type": "PropertyValue", "propertyID": "Wikidata", "value": "Q123456789" }
   ]
   ```
5. Commit + deploy. Knowledge Graph ťa zachytí v priebehu 1–4 týždňov.

---

## Po dokončení všetkých 3

Tieto URL by mali byť v `Organization.sameAs` (`index.html` + `en/index.html`):

```json
"sameAs": [
  "https://lockandgo.sk/",
  "https://www.instagram.com/lock1and2go/",
  "https://www.tiktok.com/@lock_and_go_",
  "https://www.linkedin.com/company/lockandgo",
  "https://twitter.com/lockandgosk",
  "https://www.wikidata.org/wiki/Q<id>"
]
```

A `identifier` pole v Organization:
```json
"identifier": [
  { "@type": "PropertyValue", "propertyID": "Wikidata", "value": "Q<id>" }
]
```

## Časový plán

| Týždeň | Krok |
|---|---|
| 1 | LinkedIn + X účty |
| 1 | Pridať ich URL do JSON-LD, deploy |
| 1–2 | Outreach na 1 médium (Refresher / Startitup) — keď článok vyjde, máš press reference |
| 2–3 | Wikidata item s 3 referenciami (web + LinkedIn + článok) |
| 3 | Pridať Wikidata Q-ID do JSON-LD, deploy |
| 4–8 | Knowledge Graph spracuje entity, AI engines začnú citovať s atribúciou „LockAndGo (lockandgo.sk)" |
