# Reddit posty — LockAndGo

**Princíp:** Reddit pozná spam na míle. Nikdy nepoužívaj marketingový tón. Vždy show-and-tell („pozrite, čo som spravil") + úprimnosť (16 rokov, samouk, učím sa, žiaden venture capital). To na Reddite **funguje** — milujú underdog stories.

**Karma tip:** Pred postnutím sa uisti, že tvoj Reddit účet má aspoň 10-20 karma a je 1+ týždeň starý. Inak sa post môže automaticky filtrovať. Ak máš nový účet, najprv niečo komentuj pár dní (autentické komenty na r/Bratislava, r/Slovakia, r/SK).

**Najlepší čas:** Utorok-štvrtok, 19:00-21:00 SK času. Vtedy je Reddit najaktívnejší.

---

## Post 1 — r/Bratislava (SK)

**Title (skopíruj presne):**

```
Postavil som mapu všetkých úschovní batožiny v Bratislave (mám 16 rokov, urobil som to za víkend)
```

**Body:**

```
Ahojte,

Volám sa Šimon, mám 16 a chodím na lyceum. Vlani som videl turistov ako sa ťahajú s kuframi po Hlavnej stanici a hľadajú kde si ich odložia — niečo na google sa síce dá nájsť, ale je to fragmentované. Bounce má svoje stránky, ZSSK má vlastné skrinky, na Nivách sú lockery od inej firmy.

Tak som spravil jednu mapu pre všetkých — **lockandgo.sk**

Čo tam je:
- 16 spotov v BA (Hlavná stanica, Nivy, Staré Mesto, Petržalka, Štúrova...)
- Filtre podľa otváracích hodín (24/7 boxy, „otvorené teraz")
- Ceny od 5,90 €/deň pri Bounce, 2€/deň na klasickej úschovni stanice
- Mix obchodov/kaviarní s personálom + samoobslužné automaty
- Plus EN verzia pre turistov (/en)

Bez registrácie, bez prirážky. Pri Bounce spotoch zarábam affiliate províziu od nich (turistovi cena rovnaká), pri stanici/Nivách len ukazujem dostupnosť.

Spravil som to za víkend cez Claude Code (vibe coding). Žiadne dependencies, je to čistý HTML + Leaflet mapa. Hostujem na Verceli zadarmo.

Idem ďalej — pridať Petržalku, Karlovku, asi aj automaty pri Auparku. Ak má niekto tip na ďalší spot (alebo poznáte prevádzku kde sa to dá, ale nikde to nie je inzerované), dajte vedieť.

Spätná väzba vítaná — UX, dizajn, čokoľvek. Mapa funguje aj na mobile (90% návštevníkov bude mobil).

vďaka
```

**Tipy ako odpovedať komentárom:**
- Ak sa pýtajú „prečo nie aj Košice/Trnava" → „BA bolo prvé, lebo tu žijem; ak to bude fungovať, rád pridám"
- Ak sa pýtajú „aký máš biznis model" → odpovedaj úprimne: „Bounce affiliate, ale je to side project, učím sa"
- Ak niekto trolluje („to je iba copy Bounce") → „Bounce ti ukáže len ich spoty, ja ukazujem aj ZSSK skrinky a Nivy automaty čo Bounce nemá"
- Ak niekto pýta GitHub → môžeš poslať `github.com/Lock-And-Go/lockandgo-map`

---

## Post 2 — r/Slovakia (SK alebo EN podľa nálady postu)

**Title:**

```
Built a map of luggage storage in Bratislava — feedback from locals welcome
```

**Body:**

```
Hi all — 16-year-old from Slovakia here. Spent a weekend building lockandgo.sk — interactive map of all 16 luggage storage spots in Bratislava (Hlavná stanica, Nivy, Old Town, Petržalka, etc.).

Why I built it: tourists arrive in BA and there's no single place to see all storage options. Bounce, ZSSK self-service lockers at the station, Nivy automated boxes — all in different places. I aggregated them.

Features:
- Interactive map (Leaflet + OpenStreetMap)
- Filters by hours (24/7 boxes, "open now")
- Prices and ratings per spot
- Both SK + EN landing pages

Tech: vanilla HTML + Leaflet, no build step, hosted free on Vercel. Code is open on GitHub.

If you live in BA and know a spot I missed (or a hidden gem where they accept luggage), drop it below. Also keen for UX/design feedback.

Cheers
```

---

## Post 3 — r/solotravel (EN, target: tourists)

**Title:**

```
Bratislava day trip from Vienna? Here's a map of every luggage storage spot (built it for my own family)
```

**Body:**

```
Hey — building stuff for fun and figured this might help some of you.

If you're doing the classic Vienna→Bratislava day trip (or arriving from Budapest, Prague, etc.) and don't want to drag bags around the Old Town, I made **lockandgo.sk/en** — interactive map of every legit luggage storage option in Bratislava.

Coverage:
- **Main Train Station (Hlavná stanica)** — staffed left-luggage (~€2/day) AND 24/7 self-service lockers
- **OC Nivy** (coach station / shopping mall) — 24/7 automated boxes, €4 for 3h up to €8/day
- **Old Town** — 8 spots in cafés, hotels, shops (staffed, €5.90/day average)
- **Petržalka** for Eurolines bus arrivals

16 spots total, prices from €2/day, English booking flows where available.

Why I'm posting: I'm 16, from Slovakia, this is a side project — would love feedback from actual travelers on whether the info is what you'd want before arriving. If something's missing/confusing, tell me.

Not selling anything. Bounce partners pay me a small commission for bookings (price stays the same for you) — other spots are linked free.
```

---

## Post 4 — r/Bratislava (varianta s personal story)

Použiť za týždeň-dva po prvom poste, iný uhol:

**Title:**

```
Update: za tri dni mi cez LockAndGo prešlo X návštevníkov a niekto mi navrhol pridať Karlovku
```

(Toto napíšeš keď budeš mať aspoň pár dní dát. Ľudia milujú update posty.)

---

## Iné subreddity kde môžeš postnúť (pomalý drip, nie všetky naraz)

| Subreddit | Tón | Kedy |
|---|---|---|
| r/Bratislava | SK, casual | Hneď (najlepšie ROI) |
| r/Slovakia | mix SK/EN | Týždeň po prvom |
| r/solotravel | EN, traveler-focused | 2 týždne po prvom |
| r/europetravel | EN | Mesiac po prvom |
| r/digitalnomad | EN, ak máš víc 24/7 boxov | 2-3 týždne |
| r/learnprogramming | SK alebo EN, „built my first site at 16" angle | Posledný — narobíš si tým follow-up komentárov a karma |
| r/InternetIsBeautiful | EN, podmienka: funguje aj bez kontextu | Kedykoľvek (low effort post) |

**Anti-paterny ktorých sa vyhnúť:**
- ❌ NEPÍŠ „Check out my site lockandgo.sk!" v title — moderátori to mažú
- ❌ NEDÁVAJ link v title — vždy v tele postu
- ❌ NEPOSTNI ten istý text do viacerých subov v rovnaký deň — Reddit to označí ako spam
- ❌ NEHACUJ s upvotami (nepýtaj kamošov o upvote) — Reddit to detekuje a shadowbanne
