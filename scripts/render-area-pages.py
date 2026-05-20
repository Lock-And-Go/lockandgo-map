#!/usr/bin/env python3
"""Generate /area/[slug].html and /en/area/[slug].html area landing pages.

Reads data/spots.json + data/areas.json, builds SK+EN landing pages for each
logical area (grouping fragmented raw area labels into 7 canonical areas),
then re-injects area URLs into sitemap.xml and llms.txt.

Each page contains:
  - <title> ≤60 chars, meta description ≤155 chars
  - canonical + hreflang (sk/en/x-default)
  - H1 + breadcrumb (Domov → Mapa spotov → [Area])
  - Intro paragraph
  - Spoty v tejto oblasti — full article-list of every spot
  - Ako sa sem dostať (transit hint)
  - Časté otázky (3 area-specific Q&A)
  - JSON-LD: Place + ItemList + BreadcrumbList + WebPage + FAQPage

Idempotent: re-running rewrites pages and replaces marked sections in
sitemap.xml / llms.txt rather than duplicating.

Pure stdlib. No external deps.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS_JSON = os.path.join(ROOT, "data", "spots.json")
AREAS_JSON = os.path.join(ROOT, "data", "areas.json")
OUT_SK = os.path.join(ROOT, "area")
OUT_EN = os.path.join(ROOT, "en", "area")
SITEMAP = os.path.join(ROOT, "sitemap.xml")
LLMS = os.path.join(ROOT, "llms.txt")
BASE_URL = "https://lockandgo.sk"
TODAY = datetime.date.today().isoformat()

DAY_NAMES_SK = ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"]
DAY_ORDER_FROM_RAW = [1, 2, 3, 4, 5, 6, 0]  # raw is [Sun..Sat] → Mon..Sun

# Per-area transit + intent metadata. Hand-written copy, real data only.
AREA_META: Dict[str, Dict[str, Any]] = {
    "stare-mesto": {
        "name_sk": "Staré Mesto",
        "name_en": "Old Town",
        "headline_sk": "Staré Mesto",
        "headline_en": "Old Town, Bratislava",
        "intent_sk": (
            "Staré Mesto je dôvod, prečo turisti vôbec chodia do Bratislavy — "
            "Bratislavský hrad, Michalská brána, Hlavné námestie, Modrý kostolík "
            "a UFO veža sú všetko v okruhu 15–20 minút pešo. Ak máš medzi vlakom "
            "a busom pár hodín, tu si chceš odložiť kufor a ísť sa prejsť — všetko "
            "podstatné stihneš bez batožiny. Spoty sa rozprestierajú od Rázusovho "
            "nábrežia pod Mostom SNP cez Hlavné námestie, Michalskú bránu, Obchodnú, "
            "Poštovú až po Prezidentský palác a Štefánikovu."
        ),
        "intent_en": (
            "Old Town is why people come to Bratislava in the first place — "
            "Bratislava Castle, Michael's Gate, Main Square, the Blue Church and "
            "the UFO bridge tower are all within a 15–20 minute walk. If you have "
            "a few hours between trains, this is where you want to drop your bag "
            "and actually see the city. Storage spots here run from the embankment "
            "under SNP Bridge through the Main Square, Michael's Gate, Obchodná, "
            "Poštová and up to the Presidential Palace."
        ),
        "transit_sk": (
            "Električky 1, 4 a 9 (zastávka Námestie SNP alebo Poštová) ťa pustia "
            "do centra z Hlavnej stanice za 5 minút. Pešo z Hlavnej stanice "
            "po Štefánikovej trvá ~15 minút. Z Auparku/Petržalky chyť bus 84 alebo "
            "prejdi peši cez Most SNP (~15 min) — pod mostom je spot "
            "Luggage Lockers Bratislava 24/7."
        ),
        "transit_en": (
            "Trams 1, 4 and 9 (stops Námestie SNP and Poštová) reach the Old Town "
            "from the Main Train Station in 5 minutes. From Hlavná stanica it's "
            "about 15 minutes on foot down Štefánikova. From Aupark / Petržalka, "
            "take bus 84 or walk across SNP Bridge (~15 min) — there's a 24/7 "
            "Luggage Lockers Bratislava spot right under the bridge."
        ),
        "faq_sk": [
            ("Kde si v Starom Meste odložiť kufor cez víkend?",
             "Cez víkend funguje viacero spotov: Luggage Lockers Bratislava pod Mostom SNP a Obchodná 9 sú 24/7, Bounce partneri okolo Hlavného námestia a Michalskej brány majú víkendovú prevádzku do 21–22:00. Skontroluj konkrétny spot v zozname nižšie — pri každom je presný rozpis hodín."),
            ("Aký je najlacnejší spot v centre Bratislavy?",
             "Najlacnejšie sú Bounce partneri (od 5,90 €/deň) a samoobslužné skrinky Obchodná 9 (od 2 €/2 h, 6 €/24 h). Hotely Safestay a Hotel Loft majú walk-in luggage room s cenou podľa recepcie."),
            ("Sú v Starom Meste nonstop lockery?",
             "Áno — Luggage Lockers Bratislava na Rázusovom nábreží pod Mostom SNP a Obchodná 9 fungujú 24/7. Safestay a Hotel Loft majú 24h recepciu (pre non-guests za poplatok)."),
        ],
        "faq_en": [
            ("Where can I store luggage in Old Town on a weekend?",
             "Several spots run weekends: Luggage Lockers Bratislava under SNP Bridge and Obchodná 9 self-service lockers are 24/7. Bounce partners around Main Square and Michael's Gate operate till 21–22:00. Check the spot list below for exact hours."),
            ("What's the cheapest luggage storage in central Bratislava?",
             "Bounce partners are cheapest at €5.90/day. Obchodná 9 lockers start at €2/2h or €6/24h. Safestay and Hotel Loft offer walk-in luggage rooms — ask reception for the non-guest rate."),
            ("Is there 24/7 luggage storage in Bratislava Old Town?",
             "Yes — Luggage Lockers Bratislava (Rázusovo nábrežie, under SNP Bridge) and the Obchodná 9 self-service locker bank are both 24/7. Safestay and Hotel Loft front desks operate 24h for non-guests too."),
        ],
        "ld_name_sk": "Staré Mesto, Bratislava",
        "ld_name_en": "Old Town, Bratislava",
    },
    "hlavna-stanica": {
        "name_sk": "Hlavná stanica",
        "name_en": "Hlavná stanica (Main Train Station)",
        "name_en_short": "Hlavná stanica",
        "headline_sk": "Hlavnej stanici",
        "headline_en": "Hlavná stanica (Main Train Station), Bratislava",
        "intent_sk": (
            "Hlavná stanica je najväčší dopravný uzol v Bratislave — ZSSK vlaky, "
            "RegioJet, nočné IC Bus, ale aj bus 61 priamo na Letisko M. R. Štefánika. "
            "Ak prichádzaš z Viedne, Budapešti alebo Prahy, prvá vec, ktorú "
            "potrebuješ, je odložiť batožinu. LockAndGo má pri stanici niekoľko "
            "možností — od klasickej ZSSK úschovne s personálom (2 €/deň, najlacnejšia v meste) "
            "až po 24/7 samoobslužné skrinky a Bounce partnera priamo pri staničnom vestibule."
        ),
        "intent_en": (
            "Hlavná stanica is the main transport hub in Bratislava — ZSSK trains, "
            "RegioJet, overnight IC Bus, and bus 61 straight to BTS airport. If you "
            "arrive from Vienna, Budapest or Prague, the first thing you need is to "
            "drop the bag. LockAndGo lists a few options right at the station — "
            "from the classic ZSSK manned cloakroom (€2/day, cheapest in town) to "
            "24/7 self-service lockers and a Bounce partner right by the main hall."
        ),
        "transit_sk": (
            "Si na stanici, takže ti netreba transit hint — všetky spoty sú do 3 minút "
            "chôdze od východu z hlavnej haly. Električky 1 a 4 odtiaľto vedú do "
            "Starého Mesta (5 min). Pre Letisko M. R. Štefánika choď autobus 61 "
            "(zastávka priamo pri stanici)."
        ),
        "transit_en": (
            "You're already at the station, so no transit hint needed — every spot "
            "is within a 3-minute walk of the main hall. Trams 1 and 4 reach the "
            "Old Town in 5 minutes. For BTS airport, take bus 61 (the stop is "
            "right outside the station)."
        ),
        "faq_sk": [
            ("Funguje úschovňa na Hlavnej stanici 24/7?",
             "ZSSK samoobslužné skrinky pri nástupišti 1 sú 24/7 (platba iba mincami 1 € a 2 €, max 72 h). Bounce 24/7 partner pri stanici je tiež nonstop. ZSSK manuálna úschovňa s personálom funguje len ~6:15–20:00 s prestávkami."),
            ("Koľko stojí úschovňa na Hlavnej stanici?",
             "Najlacnejšia je ZSSK manuálna úschovňa: 2 €/deň pre batožinu ≤15 kg, 2,50 €/deň nad 15 kg, kočík 1,50 €, bicykel 2,50 €. Samoobslužné skrinky od ~2 €. Bounce partner stojí 5,90 €/deň."),
            ("Kde je úschovňa, ak prichádzam nočným vlakom?",
             "Najjednoduchšie ZSSK samoobslužné skrinky pri nástupišti 1 (24/7, ale potrebuješ 1 € a 2 € mince) alebo Bounce 24/7 spot, ktorý sa odomyká bookingom cez mobil — netreba personál ani hotovosť."),
        ],
        "faq_en": [
            ("Is luggage storage at Bratislava Main Station 24/7?",
             "ZSSK self-service lockers by platform 1 run 24/7 (coins only, €1 and €2, max 72h). The Bounce 24/7 partner near the station is also non-stop. The ZSSK manned cloakroom only operates ~6:15–20:00 with breaks."),
            ("How much does luggage storage at Hlavná stanica cost?",
             "Cheapest is the ZSSK manned cloakroom: €2/day under 15 kg, €2.50 over 15 kg, stroller €1.50, bike €2.50. Self-service lockers start around €2. Bounce partner is €5.90/day."),
            ("Where should I store luggage if I arrive on a night train?",
             "Easiest: ZSSK self-service lockers by platform 1 (24/7 but you need €1 and €2 coins) or the Bounce 24/7 spot, which unlocks via phone booking — no staff or cash needed."),
        ],
        "ld_name_sk": "Bratislava-Hlavná stanica",
        "ld_name_en": "Bratislava-Hlavná stanica (Main Train Station)",
    },
    "nivy": {
        "name_sk": "OC Nivy / Autobusová stanica",
        "name_en": "OC Nivy / Bus Station",
        "headline_sk": "OC Nivy a Autobusovej stanici",
        "headline_en": "OC Nivy / Bus Station, Bratislava",
        "intent_sk": (
            "Stanica Nivy je nová medzinárodná autobusová stanica — FlixBus, "
            "RegioJet, Eurolines a Slovak Lines z/do Viedne, Prahy a Budapešti. "
            "Pod stanicou je obchodné centrum Nivy s reštauráciami a Manufaktúrou. "
            "Ak prichádzaš busom skoro ráno a check-in v hoteli máš až na 15:00, "
            "tu si odložíš veci a prejdeš sa do centra (15 min pešo)."
        ),
        "intent_en": (
            "Stanica Nivy is the new international bus station — FlixBus, RegioJet, "
            "Eurolines and Slovak Lines connecting Vienna, Prague and Budapest. "
            "Under the station sits Nivy shopping centre with food court and "
            "Manufaktúra. If you arrive by bus early and hotel check-in isn't until "
            "15:00, drop bags here and walk to the centre (15 minutes on foot)."
        ),
        "transit_sk": (
            "Si priamo pri busovej stanici, takže väčšina spotov je pod jednou "
            "strechou. Do Starého Mesta dôjdeš električkou 9 (zastávka Nivy → "
            "Námestie SNP, 8 min) alebo pešo cez Dunajskú a Štúrovu (~15 min). "
            "Na Hlavnú stanicu chyť bus 50 alebo trolejbus 210."
        ),
        "transit_en": (
            "You're right at the bus station, so most spots are under one roof. "
            "Get to Old Town by tram 9 (stop Nivy → Námestie SNP, 8 min) or walk "
            "via Dunajská and Štúrova (~15 min). For Main Train Station, take bus "
            "50 or trolleybus 210."
        ),
        "faq_sk": [
            ("Sú v Nivách lockery 24/7?",
             "Áno — samoobslužné boxy Stanica Nivy na -1 podlaží (oproti Alza) fungujú 24/7. Aj LugLockers v AS Mlynské Nivy sú nonstop. Radical Storage Nivy funguje 06:00–23:00."),
            ("Aký je rozdiel medzi Nivy samoobslužnými boxmi a LugLockers?",
             "Stanica Nivy boxy sú na -1 podlaží OC Nivy oproti Alza (Box M od 4 €/3 h, Box L od 5 €/3 h). LugLockers sú v inej budove — priamo v AS Mlynské Nivy. Skontroluj adresu v detaile pred príchodom."),
            ("Mám 4 hodiny medzi busmi v Nivách — kam s batožinou?",
             "Stanica Nivy boxy: Box M 4 €/3 h, 6 €/12 h. Radical Storage v Nivách: 5 €/deň s poistením 3000 €. Pre krátku úschovu (do 4 h) sú boxy najrýchlejšie — odomykáš QR kódom, nepotrebuješ personál."),
        ],
        "faq_en": [
            ("Are there 24/7 lockers at Nivy bus station?",
             "Yes — Stanica Nivy self-service boxes on level -1 (opposite Alza) run 24/7. LugLockers inside AS Mlynské Nivy are non-stop too. Radical Storage Nivy is open 06:00–23:00."),
            ("What's the difference between Stanica Nivy boxes and LugLockers?",
             "Stanica Nivy boxes sit on level -1 of OC Nivy opposite Alza (Box M from €4/3h, Box L from €5/3h). LugLockers are in a different building — inside AS Mlynské Nivy. Double-check the address before you go."),
            ("I have 4 hours between buses at Nivy — where do I put the bag?",
             "Stanica Nivy boxes: Box M €4/3h, €6/12h. Radical Storage Nivy: €5/day with €3000 insurance. For short stops (under 4h), the boxes are fastest — QR code unlock, no staff needed."),
        ],
        "ld_name_sk": "OC Nivy / Autobusová stanica, Bratislava",
        "ld_name_en": "OC Nivy / Bus Station, Bratislava",
    },
    "petrzalka": {
        "name_sk": "Petržalka",
        "name_en": "Petržalka",
        "headline_sk": "Petržalke",
        "headline_en": "Petržalka, Bratislava",
        "intent_sk": (
            "Petržalka je vstupný bod pre cestujúcich z/do Viedne — REX-1, RegioJet "
            "a Slovak Lines stoja v ŽST Bratislava-Petržalka, autobusové linky "
            "104 a 184 spájajú stanicu s centrom. Aupark je dôvod, prečo sem "
            "chodia turisti aj domáci — shopping, kino a Sad Janka Kráľa na "
            "druhej strane Mosta SNP. Pre nás je dôležité, že pri ŽST Petržalka "
            "máš ZSSK lockery 24/7, Aupark má walk-in cloakroom a LugLockers + "
            "LuggageHero stoja pri stanici."
        ),
        "intent_en": (
            "Petržalka is the entry point from Vienna — REX-1, RegioJet and Slovak "
            "Lines stop at ŽST Bratislava-Petržalka, with buses 104 and 184 "
            "linking to the centre. Aupark is the local shopping draw, with Sad "
            "Janka Kráľa park just across SNP Bridge. The key facts for storage: "
            "ŽST Petržalka has 24/7 ZSSK lockers, Aupark has a walk-in cloakroom, "
            "and both LugLockers and LuggageHero operate by the station."
        ),
        "transit_sk": (
            "Z Auparku do centra cez Most SNP pešo ~15 min, alebo bus 84 do "
            "centra. Zo ŽST Petržalka chyť bus 84, 93, 99 alebo nočný N91. "
            "Na Hlavnú stanicu z Petržalky najlepšie cez Most SNP a potom "
            "trolejbus alebo električkou 1/4 (~25 min)."
        ),
        "transit_en": (
            "From Aupark to the centre: ~15 min walk across SNP Bridge, or take "
            "bus 84. From ŽST Petržalka, buses 84, 93, 99 or night N91. To Hlavná "
            "stanica from Petržalka, cross SNP Bridge then take a tram (line 1 or "
            "4) — roughly 25 minutes total."
        ),
        "faq_sk": [
            ("Funguje úschovňa pri Auparku 24/7?",
             "Cloakroom v OC Aupark funguje len v otváracích hodinách centra (typicky 09:00–21:00). Pre 24/7 v Petržalke choď k ŽST Petržalka — ZSSK lockery sú nonstop (mince 1 € a 2 €) a LugLockers tiež 24/7."),
            ("Aká je úschovňa na ŽST Bratislava-Petržalka?",
             "Sú tu tri možnosti: ZSSK manuálna úschovňa (~6:00–20:00, 2 €/deň), ZSSK samoobslužné lockery (24/7, od 2 €, max 72 h, iba mince), a LugLockers + LuggageHero v okolí stanice."),
            ("Mám check-out o 11:00 v Aupark zóne, bus do Viedne ide až o 18:00 — kam s kufrom?",
             "Najpohodlnejšie do cloakroom v Auparku (walk-in, od 09:00) alebo cez Most SNP do centra a využiť Luggage Lockers Bratislava 24/7 na Rázusovom nábreží. ZSSK lockery v ŽST Petržalka sú alternatíva, ak ideš peši smer Viedeň."),
        ],
        "faq_en": [
            ("Is luggage storage at Aupark 24/7?",
             "No — the Aupark cloakroom only operates during mall hours (typically 09:00–21:00). For 24/7 in Petržalka, head to ŽST Petržalka: ZSSK lockers are non-stop (coins €1 and €2) and LugLockers run 24/7 too."),
            ("What luggage storage is available at Bratislava-Petržalka train station?",
             "Three options: ZSSK manned cloakroom (~6:00–20:00, €2/day), ZSSK self-service lockers (24/7, from €2, max 72h, coins only), and LugLockers + LuggageHero in the area."),
            ("I check out at 11:00 near Aupark, but my Vienna bus leaves at 18:00 — where do I leave the bag?",
             "Easiest: Aupark cloakroom (walk-in, from 09:00). Or cross SNP Bridge into town and use Luggage Lockers Bratislava 24/7 under the bridge. ZSSK lockers at ŽST Petržalka are the third option if you're heading on foot toward Vienna."),
        ],
        "ld_name_sk": "Petržalka, Bratislava",
        "ld_name_en": "Petržalka, Bratislava",
    },
    "ruzinov": {
        "name_sk": "Ružinov",
        "name_en": "Ružinov",
        "headline_sk": "Ružinove",
        "headline_en": "Ružinov, Bratislava",
        "intent_sk": (
            "Ružinov je rezidenčná štvrť hneď za Nivami — Miletička s trhom je "
            "obľúbená medzi domácimi (sobota dopoludnia trh) a Dulovo námestie "
            "leží na pomedzí Ružinova a Nív. Pre cestujúcich má Ružinov význam, "
            "ak bývaš v Airbnb v tejto zóne alebo máš biznis meeting v okolí "
            "Mlynských nív. Radical Storage tu má dva spoty — oba 5 €/deň "
            "s poistením 3000 €."
        ),
        "intent_en": (
            "Ružinov is a residential district right behind Nivy — Miletička "
            "(with its weekend farmers' market) is a local favourite, and Dulovo "
            "námestie sits on the Ružinov/Nivy border. Storage here matters if "
            "your Airbnb is in this zone or you have a business meeting around "
            "Mlynské nivy. Radical Storage operates two spots here — both €5/day "
            "with €3000 insurance."
        ),
        "transit_sk": (
            "Z Miletičky do centra električka 9 alebo bus 75 (~12 min). "
            "Z Hlavnej stanice na Miletičku chyť bus 78 alebo trolejbus 210. "
            "K Stanici Nivy je to z oboch ružinovských spotov ~10 min pešo."
        ),
        "transit_en": (
            "From Miletička to the centre: tram 9 or bus 75 (~12 min). From "
            "Hlavná stanica to Miletička: bus 78 or trolleybus 210. Both Ružinov "
            "spots are ~10 min walk from Stanica Nivy."
        ),
        "faq_sk": [
            ("Sú v Ružinove samoobslužné 24/7 lockery?",
             "Nie — oba spoty (Radical Storage Miletičová a Dulovo námestie) sú walk-in s personálom, otvorené 10:00–21:00 (Miletičová) a 09:00–18:00 (Dulovo nám.). Pre 24/7 prejdi 10 min pešo do Stanice Nivy alebo na Hlavnú stanicu."),
            ("Koľko stojí úschovňa v Ružinove?",
             "Obe Radical Storage prevádzky majú jednotnú cenu 5 €/deň/kus a v cene je poistenie 3000 €."),
            ("Mám trh na Miletičke v sobotu ráno, kam s kufrom?",
             "Radical Storage Miletičová je otvorené od 10:00 každý deň — odložíš kufor (5 €/deň), prejdeš sa po trhu, vyzdvihneš do 21:00. Ak chceš začať skôr ako 10:00, využiť ZSSK lockery na Hlavnej stanici (10 min trolejbusom 210)."),
        ],
        "faq_en": [
            ("Are there 24/7 self-service lockers in Ružinov?",
             "No — both spots (Radical Storage Miletičová and Dulovo námestie) are walk-in with staff, open 10:00–21:00 (Miletičová) and 09:00–18:00 (Dulovo). For 24/7, walk 10 minutes to Stanica Nivy or take the trolleybus to Hlavná stanica."),
            ("How much does luggage storage cost in Ružinov?",
             "Both Radical Storage locations charge a flat €5/day per bag, with €3000 insurance included."),
            ("I'm at the Miletička market on Saturday morning — where do I leave the bag?",
             "Radical Storage Miletičová opens at 10:00 daily — drop the bag (€5/day), browse the market, pick up by 21:00. If you want to start before 10:00, use the ZSSK lockers at Hlavná stanica (10 min on trolleybus 210)."),
        ],
        "ld_name_sk": "Ružinov, Bratislava",
        "ld_name_en": "Ružinov, Bratislava",
    },
    "nove-mesto": {
        "name_sk": "Nové Mesto",
        "name_en": "Nové Mesto",
        "headline_sk": "Novom Meste",
        "headline_en": "Nové Mesto, Bratislava",
        "intent_sk": (
            "Nové Mesto je severnejšia časť Bratislavy s vlastnou železničnou "
            "stanicou (Bratislava-Nové Mesto), OC Vivo! na Vajnorskej a začiatkom "
            "Vinohradov. Pre cestujúcich má najmä význam, ak prichádzaš z Viedne "
            "alebo Prahy a vystupuješ skôr ako na Hlavnej stanici, alebo ideš "
            "na shopping do Vivo!. LockAndGo tu má dva spoty — LuggageHero pri "
            "stanici Nové Mesto a OC Vivo! skrinky pri infodesku."
        ),
        "intent_en": (
            "Nové Mesto is north of the centre, with its own train station "
            "(Bratislava-Nové Mesto), OC Vivo! mall on Vajnorská and the start of "
            "the Vinohrady wine district. Storage matters here if you arrive from "
            "Vienna or Prague and disembark earlier than Hlavná stanica, or if "
            "you're heading to Vivo! for shopping. LockAndGo lists two spots — "
            "LuggageHero by Nové Mesto station and OC Vivo! lockers by the "
            "info desk."
        ),
        "transit_sk": (
            "Zo ŽST Bratislava-Nové Mesto do centra električka 2 alebo bus 53 "
            "(15–20 min). Z Hlavnej stanice na Vajnorskú (k OC Vivo!) trolejbus "
            "201 alebo 207. K Stanici Nivy z Nového Mesta bus 50."
        ),
        "transit_en": (
            "From ŽST Bratislava-Nové Mesto to the centre: tram 2 or bus 53 "
            "(15–20 min). From Hlavná stanica to Vajnorská (for OC Vivo!): "
            "trolleybus 201 or 207. To Stanica Nivy from Nové Mesto: bus 50."
        ),
        "faq_sk": [
            ("Funguje úschovňa pri OC Vivo!?",
             "Áno — OC Vivo! má vyhradený priestor so skrinkami pri infodesku, walk-in bez online rezervácie, hodiny podľa OC (typicky 09:00–21:00). Cenu povie infodesk pri odovzdaní."),
            ("Koľko stojí LuggageHero pri ŽST Nové Mesto?",
             "LuggageHero účtuje 1,49 €/hod alebo 4,90 €/deň. V cene je poistenie 500 €. Otvorené podľa konkrétnej prevádzky, typicky 08:00–22:00."),
            ("Hodí sa Nové Mesto, ak prichádzam zo Schwechatu cez Viedeň?",
             "Iba ak vlak zastavuje v Bratislava-Nové Mesto (REX a niektoré R linky áno, EuroCity ide rovno na Hlavnú stanicu). Skontroluj cestovný poriadok ZSSK — ak ti vyhovuje, ušetríš 5 min a hneď máš LuggageHero pri stanici."),
        ],
        "faq_en": [
            ("Is there luggage storage at OC Vivo! shopping mall?",
             "Yes — OC Vivo! has a dedicated locker area by the info desk, walk-in only (no online booking), open during mall hours (typically 09:00–21:00). The info desk quotes the price when you drop off."),
            ("How much does LuggageHero at Bratislava-Nové Mesto station cost?",
             "LuggageHero charges €1.49/hour or €4.90/day. Includes €500 insurance. Hours depend on the host shop, typically 08:00–22:00."),
            ("Should I use Nové Mesto if I'm arriving from Vienna via Schwechat?",
             "Only if your train stops at Bratislava-Nové Mesto (REX and some R lines do; EuroCity goes straight to Hlavná stanica). Check the ZSSK timetable — if it fits, you save 5 minutes and LuggageHero is right at the station."),
        ],
        "ld_name_sk": "Nové Mesto, Bratislava",
        "ld_name_en": "Nové Mesto, Bratislava",
    },
    "medicka-zahrada": {
        "name_sk": "Medická záhrada",
        "name_en": "Medická záhrada",
        "headline_sk": "Medickej záhrade",
        "headline_en": "Medická záhrada, Bratislava",
        "intent_sk": (
            "Medická záhrada je pokojná zelená oáza na pomedzí Starého Mesta a "
            "biznis distriktu — bývalá botanická záhrada Univerzity Komenského. "
            "V okolí je Lekárska fakulta UK (Špitálska), Národná rada SR a "
            "ministerstvá. Pre cestujúcich má zmysel, ak máš stretnutie na ulici "
            "Špitálska/Bezručova/Vajanského nábrežie alebo si sem prišiel na konferenciu. "
            "Oba spoty (Radical Storage a Bounce partner pri LF UK) sú 5 min pešo "
            "od záhrady."
        ),
        "intent_en": (
            "Medická záhrada is a calm green pocket on the edge of the Old Town "
            "— a former Comenius University botanical garden. Around it sit the "
            "Faculty of Medicine (Špitálska), the National Council and several "
            "ministries. Storage here helps if you have a meeting on Špitálska / "
            "Bezručova / Vajanského nábrežie or you're in town for a conference. "
            "Both spots (Radical Storage and the Bounce partner near LF UK) are "
            "a 5-minute walk from the garden."
        ),
        "transit_sk": (
            "Z Hlavnej stanice na Medickú záhradu bus 50 alebo 70 (~10 min) — "
            "vystupuješ na zastávke Americké námestie alebo Krížna. Pešo z centra "
            "(Hlavné námestie) ~10 min cez Bezručovu."
        ),
        "transit_en": (
            "From Hlavná stanica to Medická záhrada: bus 50 or 70 (~10 min) — "
            "get off at Americké námestie or Krížna. On foot from the centre "
            "(Main Square): about 10 minutes via Bezručova."
        ),
        "faq_sk": [
            ("Sú spoty pri Medickej záhrade 24/7?",
             "Nie — oba sú walk-in. Radical Storage Medická záhrada má 11:00–21:00 každý deň (5 €/deň, poistenie 3000 €), Bounce partner pri LF UK má Po-Pi 10:00–17:30, So-Ne 12:00–17:30 (5,90 €/deň). Pre 24/7 choď k Hlavnej stanici."),
            ("Som na konferencii na LF UK, kam s kufrom?",
             "Bounce partner Near Faculty of Medicine je doslova vedľa LF UK (Špitálska), 5,90 €/deň. Otvorené Po-Pi od 10:00 — pohodlné pre celodennú konferenciu."),
            ("Aký je rozdiel medzi spotmi pri Medickej záhrade?",
             "Bounce partner (Near Faculty of Medicine) je obchod s personálom, online rezervácia, 5,90 €/deň. Radical Storage je reštaurácia s personálom, 5 €/deň, poistenie 3000 €. Bounce má lepšie hodnotenie (5,0 / 111 recenzií), Radical je o niečo lacnejší."),
        ],
        "faq_en": [
            ("Are the Medická záhrada storage spots 24/7?",
             "No — both are walk-in. Radical Storage Medická záhrada runs 11:00–21:00 daily (€5/day, €3000 insurance), and the Bounce partner near LF UK is open Mon-Fri 10:00–17:30, Sat-Sun 12:00–17:30 (€5.90/day). For 24/7, head to Hlavná stanica."),
            ("I'm at a conference at the Faculty of Medicine — where do I store my bag?",
             "The Bounce partner Near Faculty of Medicine is literally next to LF UK on Špitálska, €5.90/day. Open Mon-Fri from 10:00 — convenient for a full-day conference."),
            ("What's the difference between the two Medická záhrada spots?",
             "The Bounce partner (Near Faculty of Medicine) is a staffed shop, online booking, €5.90/day. Radical Storage is a staffed restaurant, €5/day, €3000 insurance. Bounce has a stronger rating (5.0 from 111 reviews), Radical is slightly cheaper."),
        ],
        "ld_name_sk": "Medická záhrada, Bratislava",
        "ld_name_en": "Medická záhrada, Bratislava",
    },
}


# ── Slug helper ──────────────────────────────────────────────────


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "spot"


def spot_slug(spot: Dict[str, Any]) -> str:
    return f"{spot['id']}-{slugify(spot['name'])}"


def html_escape(s: str) -> str:
    if s is None:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def fmt_hour(h: float) -> str:
    hr = int(h)
    mn = round((h - hr) * 60)
    if mn == 60:
        hr += 1
        mn = 0
    return f"{hr:02d}:{mn:02d}"


# ── Aggregations ─────────────────────────────────────────────────


def price_range_for_area(spots: List[Dict[str, Any]]) -> str:
    """Compute a human price range string."""
    prices = [s.get("price") for s in spots if s.get("price") is not None]
    if not prices:
        return "ceny podľa prevádzkovateľa"
    lo = min(prices)
    hi = max(prices)
    if abs(hi - lo) < 0.01:
        return f"od {lo:.2f} €/deň"
    return f"{lo:.2f}–{hi:.2f} €/deň"


def price_range_for_area_en(spots: List[Dict[str, Any]]) -> str:
    prices = [s.get("price") for s in spots if s.get("price") is not None]
    if not prices:
        return "prices set by operator"
    lo = min(prices)
    hi = max(prices)
    if abs(hi - lo) < 0.01:
        return f"from €{lo:.2f}/day"
    return f"€{lo:.2f}–€{hi:.2f}/day"


def is247_count(spots: List[Dict[str, Any]]) -> int:
    return sum(1 for s in spots if (s.get("hours") or {}).get("is247"))


def centroid(spots: List[Dict[str, Any]]) -> Tuple[float, float]:
    lats = [s["lat"] for s in spots if s.get("lat") is not None]
    lngs = [s["lng"] for s in spots if s.get("lng") is not None]
    if not lats or not lngs:
        return (48.1486, 17.1077)  # Bratislava city center fallback
    return (round(sum(lats) / len(lats), 6), round(sum(lngs) / len(lngs), 6))


# ── CSS (same as spot pages) ─────────────────────────────────────


CSS = """
:root{
  --bg:#F1F1EC; --paper:#FAFAF6; --ink:#1F1F1D; --ink-2:#555550; --ink-3:#8E8E89;
  --line:rgba(31,31,29,0.10); --line-2:rgba(31,31,29,0.18);
  --accent:#B89A45; --accent-2:#8B6F2A; --accent-50:#F5EFD8;
  --display:'Instrument Serif','Times New Roman',serif;
  --body:'Manrope',system-ui,sans-serif;
  --r-md:14px; --r-lg:22px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:var(--body);font-size:16px;line-height:1.65;color:var(--ink);background:var(--bg);-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:underline;text-decoration-color:var(--line-2);text-underline-offset:3px}
a:hover{text-decoration-color:var(--accent)}
.wrap{max-width:820px;margin:0 auto;padding:24px 20px 80px}
header.top{display:flex;align-items:center;justify-content:space-between;padding:8px 0 24px;border-bottom:1px solid var(--line);margin-bottom:24px}
.brand{font-family:var(--display);font-weight:400;font-size:24px;color:var(--ink);text-decoration:none}
.brand em{font-style:italic;color:var(--accent-2)}
.brand:hover{text-decoration:none}
.top nav a{font-size:14px;color:var(--ink-2);margin-left:18px;text-decoration:none}
.top nav a:hover{color:var(--ink)}
.crumbs{font-size:13px;color:var(--ink-3);margin:0 0 16px;display:flex;flex-wrap:wrap;gap:6px}
.crumbs a{color:var(--ink-2);text-decoration:none}
.crumbs a:hover{color:var(--accent-2)}
.crumbs span[aria-hidden]{color:var(--ink-4,#BFBFB9)}
h1{font-family:var(--display);font-weight:400;font-size:clamp(34px,5vw,48px);line-height:1.08;margin:0 0 8px;letter-spacing:-0.01em}
.lede{font-size:17px;color:var(--ink-2);margin:0 0 24px;max-width:62ch}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 28px}
.badge{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border:1px solid var(--line-2);border-radius:999px;font-size:13px;color:var(--ink-2);background:var(--paper)}
.badge.accent{background:var(--accent-50);border-color:var(--accent);color:var(--accent-2)}
section.block{background:var(--paper);border:1px solid var(--line);border-radius:var(--r-lg);padding:22px 22px 18px;margin:0 0 18px}
section.block h2{font-family:var(--display);font-weight:400;font-size:26px;margin:0 0 12px;letter-spacing:-0.005em}
section.block p{margin:0 0 12px;color:var(--ink-2)}
section.block p:last-child{margin-bottom:0}
.spot-card{border:1px solid var(--line);border-radius:var(--r-md);padding:18px 18px 14px;margin:0 0 12px;background:var(--bg)}
.spot-card:last-child{margin-bottom:0}
.spot-card h3{font-family:var(--display);font-weight:400;font-size:22px;margin:0 0 6px;letter-spacing:-0.005em}
.spot-card h3 a{text-decoration:none;color:var(--ink)}
.spot-card h3 a:hover{color:var(--accent-2)}
.spot-meta{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:var(--ink-3);margin:0 0 8px}
.spot-meta strong{color:var(--ink-2);font-weight:600}
.spot-card p{margin:6px 0 0;color:var(--ink-2);font-size:14.5px}
.spot-card .more{display:inline-block;margin-top:8px;font-size:13.5px;color:var(--accent-2);text-decoration:none;border-bottom:1px solid var(--line-2)}
.spot-card .more:hover{border-bottom-color:var(--accent)}
.faq details{border-top:1px solid var(--line);padding:14px 0}
.faq details:first-of-type{border-top:none;padding-top:4px}
.faq summary{font-weight:600;cursor:pointer;list-style:none;font-size:16px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:'+';float:right;color:var(--accent-2);font-weight:400;font-size:22px;line-height:1}
.faq details[open] summary::after{content:'−'}
.faq p{margin:8px 0 0;color:var(--ink-2)}
.author{display:flex;gap:12px;align-items:center;background:var(--paper);border:1px solid var(--line);border-radius:var(--r-md);padding:14px 16px;font-size:14px;color:var(--ink-2)}
.author .who{flex:1}
.author .who a{color:var(--accent-2);text-decoration:none}
.author .who a:hover{text-decoration:underline}
.cta{display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:var(--bg);padding:11px 18px;border-radius:14px;font-weight:600;text-decoration:none;border:1px solid var(--accent-2);font-size:14.5px}
.cta:hover{background:var(--accent-2);text-decoration:none}
footer.bot{margin-top:36px;padding-top:20px;border-top:1px solid var(--line);font-size:13px;color:var(--ink-3);display:flex;flex-wrap:wrap;gap:8px;justify-content:space-between}
footer.bot a{color:var(--ink-2);text-decoration:none}
footer.bot a:hover{color:var(--accent-2)}
@media (max-width:560px){
  .wrap{padding:18px 16px 64px}
  h1{font-size:34px}
}
""".strip()


# ── Page rendering ───────────────────────────────────────────────


def render_area_page_sk(area_slug: str, spots: List[Dict[str, Any]]) -> str:
    meta = AREA_META[area_slug]
    name = meta["name_sk"]
    headline = meta["headline_sk"]
    spot_count = len(spots)
    price_str = price_range_for_area(spots)
    n247 = is247_count(spots)
    lat, lng = centroid(spots)

    canonical = f"{BASE_URL}/area/{area_slug}"
    canonical_en = f"{BASE_URL}/en/area/{area_slug}"

    # Title ≤60. Try richest version first, then strip elements until it fits.
    candidates = [
        f"Úschovňa batožiny {name} · {spot_count} spotov | LockAndGo",
        f"Úschovňa batožiny {name} | LockAndGo",
        f"Úschovňa batožiny · {name}",
    ]
    title = next((c for c in candidates if len(c) <= 60), truncate(candidates[0], 60))
    desc_parts = [
        f"Úschovňa batožiny v lokalite {name} (Bratislava) — {spot_count} spotov,",
        price_str + ".",
    ]
    if n247:
        desc_parts.append(f"{n247} z nich 24/7.")
    else:
        desc_parts.append("Otváracie hodiny v detaile.")
    description = truncate(" ".join(desc_parts), 155)

    # JSON-LD graph
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{canonical}#webpage",
        "url": canonical,
        "name": title,
        "description": description,
        "inLanguage": "sk-SK",
        "isPartOf": {"@id": f"{BASE_URL}/#website"},
        "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
        "primaryImageOfPage": f"{BASE_URL}/og-image.svg",
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": f"{canonical}#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Domov", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Mapa spotov", "item": f"{BASE_URL}/app"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }
    place = {
        "@context": "https://schema.org",
        "@type": "Place",
        "@id": f"{canonical}#place",
        "name": meta["ld_name_sk"],
        "url": canonical,
        "containedInPlace": {
            "@type": "City",
            "name": "Bratislava",
            "containedInPlace": {"@type": "Country", "name": "Slovakia"},
        },
        "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng},
    }

    item_list_elements = []
    for i, s in enumerate(spots, 1):
        slug = spot_slug(s)
        spot_url = f"{BASE_URL}/spot/{slug}"
        biz = {
            "@type": "LocalBusiness",
            "@id": f"{spot_url}#localbusiness",
            "name": s["name"],
            "url": spot_url,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": s.get("address") or s.get("area", ""),
                "addressLocality": "Bratislava",
                "addressCountry": "SK",
            },
        }
        if s.get("lat") is not None and s.get("lng") is not None:
            biz["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": s["lat"],
                "longitude": s["lng"],
            }
        if s.get("price") is not None:
            biz["priceRange"] = f"€{float(s['price']):.2f}"
        item_list_elements.append(
            {"@type": "ListItem", "position": i, "item": biz}
        )

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{canonical}#itemlist",
        "name": f"Úschovne batožiny v lokalite {name}",
        "numberOfItems": spot_count,
        "itemListElement": item_list_elements,
    }

    faq_qa = meta["faq_sk"]
    faq_page = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": f"{canonical}#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faq_qa
        ],
    }

    graph = {
        "@context": "https://schema.org",
        "@graph": [webpage, breadcrumb, place, item_list, faq_page],
    }
    jsonld_str = json.dumps(graph, ensure_ascii=False, indent=2)

    # Spot list HTML
    spot_cards_html: List[str] = []
    for s in spots:
        slug = spot_slug(s)
        spot_url = f"/spot/{slug}"
        name_s = s["name"]
        area_raw = s.get("area", "")
        address = s.get("address") or area_raw
        hours_display = (s.get("hours") or {}).get("display", "")
        is247 = bool((s.get("hours") or {}).get("is247"))
        price = s.get("price")
        if price is not None:
            price_disp = f"od {price:.2f} €/deň"
        else:
            price_disp = "cena podľa prevádzkovateľa"
        provider = s.get("providerLabel", "")
        notes = s.get("notes")

        meta_bits = []
        meta_bits.append(f"<strong>Adresa:</strong> {html_escape(address)}")
        meta_bits.append(f"<strong>Hodiny:</strong> {html_escape(hours_display)}")
        meta_bits.append(f"<strong>Cena:</strong> {html_escape(price_disp)}")
        if provider:
            meta_bits.append(f"<strong>Prevádzkovateľ:</strong> {html_escape(provider)}")
        meta_html = " · ".join(meta_bits)

        notes_html = ""
        if notes:
            short_notes = notes if len(notes) <= 180 else notes[:178].rstrip() + "…"
            notes_html = f"<p>{html_escape(short_notes)}</p>"

        badge_247 = ' <span class="badge accent">24/7</span>' if is247 else ""
        spot_cards_html.append(
            f"""  <article class="spot-card">
    <h3><a href="{spot_url}">{html_escape(name_s)}</a>{badge_247}</h3>
    <div class="spot-meta">{meta_html}</div>
    {notes_html}
    <a class="more" href="{spot_url}">Detail spotu →</a>
  </article>"""
        )
    spots_block = "\n".join(spot_cards_html)

    # FAQ HTML
    faq_html_items = []
    for q, a in faq_qa:
        faq_html_items.append(
            f"""    <details>
      <summary>{html_escape(q)}</summary>
      <p>{html_escape(a)}</p>
    </details>"""
        )
    faq_html = "\n".join(faq_html_items)

    # Badges
    badges = [f'<span class="badge">{spot_count} spotov</span>']
    badges.append(f'<span class="badge">{html_escape(price_str)}</span>')
    if n247:
        badges.append(f'<span class="badge accent">{n247} × 24/7</span>')
    badges_html = "\n      ".join(badges)

    # Lede
    if n247:
        avail_phrase = f"Z toho {n247} spotov funguje 24/7."
    else:
        avail_phrase = "Otváracie hodiny pri každom spote nižšie."
    lede = (
        f"V lokalite <strong>{html_escape(name)}</strong> LockAndGo eviduje "
        f"{spot_count} úschovní batožiny — {html_escape(price_str)}. "
        f"{avail_phrase} Klikni na ktorýkoľvek spot a otvorí sa detail s adresou, "
        f"hodinami a rezerváciou."
    )

    intent_p = meta["intent_sk"]
    transit_p = meta["transit_sk"]

    return f"""<!DOCTYPE html>
<html lang="sk">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html_escape(title)}</title>
<meta name="description" content="{html_escape(description)}" />
<meta name="theme-color" content="#F1F1EC" />
<meta name="author" content="Šimon Kališ" />
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
<meta name="geo.region" content="SK-BL" />
<meta name="geo.placename" content="Bratislava" />
<meta name="geo.position" content="{lat};{lng}" />
<meta name="ICBM" content="{lat}, {lng}" />

<link rel="canonical" href="{canonical}" />
<link rel="alternate" hreflang="sk" href="{canonical}" />
<link rel="alternate" hreflang="en" href="{canonical_en}" />
<link rel="alternate" hreflang="x-default" href="{canonical}" />

<meta property="og:type" content="article" />
<meta property="og:locale" content="sk_SK" />
<meta property="og:locale:alternate" content="en_US" />
<meta property="og:site_name" content="LockAndGo" />
<meta property="og:title" content="{html_escape(truncate(f'Úschovňa batožiny {name} · LockAndGo', 90))}" />
<meta property="og:description" content="{html_escape(description)}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:image" content="{BASE_URL}/api/og" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html_escape(truncate(f'Úschovňa batožiny {name} · LockAndGo', 90))}" />
<meta name="twitter:description" content="{html_escape(description)}" />
<meta name="twitter:image" content="{BASE_URL}/api/og" />

<script type="application/ld+json">
{jsonld_str}
</script>

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet" />

<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Preskočiť na obsah</a>
<div class="wrap">

<header class="top">
  <a class="brand" href="/">Lock<em>&amp;</em>Go</a>
  <nav aria-label="Hlavná navigácia">
    <a href="/">Domov</a>
    <a href="/app">Mapa</a>
    <a href="{canonical_en}" hreflang="en">EN</a>
  </nav>
</header>

<nav class="crumbs" aria-label="Drobky">
  <a href="/">Domov</a>
  <span aria-hidden="true">›</span>
  <a href="/app">Mapa spotov</a>
  <span aria-hidden="true">›</span>
  <span aria-current="page">{html_escape(name)}</span>
</nav>

<main id="main">

  <h1>Úschovňa batožiny v {html_escape(headline)}</h1>
  <p class="lede">{lede}</p>

  <div class="badges">
      {badges_html}
  </div>

  <section class="block" id="intro" aria-labelledby="h-intro">
    <h2 id="h-intro">Prečo si v {html_escape(headline)} odložiť batožinu</h2>
    <p>{html_escape(intent_p)}</p>
    <p>Všetky spoty nižšie sú reálne overené prevádzky — obchody s personálom, lockery alebo hotelové úschovne. LockAndGo ti spoty len zobrazí; rezerváciu alebo platbu robíš priamo u prevádzkovateľa (Bounce, Radical Storage, LuggageHero, LugLockers, ZSSK, OC) — bez prirážky.</p>
  </section>

  <section class="block" id="spoty" aria-labelledby="h-spoty">
    <h2 id="h-spoty">Spoty v tejto oblasti</h2>
{spots_block}
  </section>

  <section class="block" id="transit" aria-labelledby="h-transit">
    <h2 id="h-transit">Ako sa sem dostať</h2>
    <p>{html_escape(transit_p)}</p>
    <p>Otvor si <a href="/app">interaktívnu mapu</a> a zapni geolokáciu — uvidíš spoty v okolí v reálnom čase.</p>
  </section>

  <section class="block faq" id="faq" aria-labelledby="h-faq">
    <h2 id="h-faq">Časté otázky</h2>
{faq_html}
  </section>

  <section class="block" id="autor" aria-labelledby="h-autor">
    <h2 id="h-autor">O LockAndGo</h2>
    <div class="author">
      <div class="who">LockAndGo je projekt 16-ročného Šimona Kališa zo Slovenska. Cieľom je jednoduchá mapa všetkých úschovní batožiny v Bratislave — bez prirážky, s reálnymi hodinami a cenami. Viac na <a href="/">lockandgo.sk</a>.</div>
    </div>
  </section>

</main>

<footer class="bot">
  <span><a href="/" rel="author">LockAndGo</a> · Šimon Kališ</span>
  <span><a href="/app">Späť na mapu spotov</a> · <a href="{canonical_en}">English version</a></span>
</footer>

</div>
</body>
</html>
"""


def render_area_page_en(area_slug: str, spots: List[Dict[str, Any]]) -> str:
    meta = AREA_META[area_slug]
    name = meta["name_en"]
    headline = meta["headline_en"]
    spot_count = len(spots)
    price_str = price_range_for_area_en(spots)
    n247 = is247_count(spots)
    lat, lng = centroid(spots)

    canonical = f"{BASE_URL}/en/area/{area_slug}"
    canonical_sk = f"{BASE_URL}/area/{area_slug}"

    # Optionally allow areas to provide a shorter alias for tight title slots.
    short_name = meta.get("name_en_short") or name
    candidates = [
        f"Luggage Storage in {name} Bratislava · {spot_count} spots | LockAndGo",
        f"Luggage Storage in {name} Bratislava | LockAndGo",
        f"Luggage Storage · {name} Bratislava | LockAndGo",
        f"Luggage Storage in {short_name} Bratislava | LockAndGo",
        f"Luggage Storage · {short_name}, Bratislava | LockAndGo",
    ]
    title = next((c for c in candidates if len(c) <= 60), truncate(candidates[-1], 60))
    desc_parts = [
        f"Luggage storage in {name}, Bratislava — {spot_count} spots,",
        price_str + ".",
    ]
    if n247:
        desc_parts.append(f"{n247} open 24/7.")
    else:
        desc_parts.append("See full hours per spot.")
    description = truncate(" ".join(desc_parts), 155)

    # JSON-LD
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{canonical}#webpage",
        "url": canonical,
        "name": title,
        "description": description,
        "inLanguage": "en",
        "isPartOf": {"@id": f"{BASE_URL}/#website"},
        "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
        "primaryImageOfPage": f"{BASE_URL}/og-image.svg",
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": f"{canonical}#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/en"},
            {"@type": "ListItem", "position": 2, "name": "Map of spots", "item": f"{BASE_URL}/en/app"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }
    place = {
        "@context": "https://schema.org",
        "@type": "Place",
        "@id": f"{canonical}#place",
        "name": meta["ld_name_en"],
        "url": canonical,
        "containedInPlace": {
            "@type": "City",
            "name": "Bratislava",
            "containedInPlace": {"@type": "Country", "name": "Slovakia"},
        },
        "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng},
    }

    item_list_elements = []
    for i, s in enumerate(spots, 1):
        slug = spot_slug(s)
        spot_url = f"{BASE_URL}/spot/{slug}"
        biz = {
            "@type": "LocalBusiness",
            "@id": f"{spot_url}#localbusiness",
            "name": s["name"],
            "url": spot_url,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": s.get("address") or s.get("area", ""),
                "addressLocality": "Bratislava",
                "addressCountry": "SK",
            },
        }
        if s.get("lat") is not None and s.get("lng") is not None:
            biz["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": s["lat"],
                "longitude": s["lng"],
            }
        if s.get("price") is not None:
            biz["priceRange"] = f"€{float(s['price']):.2f}"
        item_list_elements.append(
            {"@type": "ListItem", "position": i, "item": biz}
        )

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{canonical}#itemlist",
        "name": f"Luggage storage spots in {name}",
        "numberOfItems": spot_count,
        "itemListElement": item_list_elements,
    }

    faq_qa = meta["faq_en"]
    faq_page = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": f"{canonical}#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faq_qa
        ],
    }

    graph = {
        "@context": "https://schema.org",
        "@graph": [webpage, breadcrumb, place, item_list, faq_page],
    }
    jsonld_str = json.dumps(graph, ensure_ascii=False, indent=2)

    # Spot list
    spot_cards_html: List[str] = []
    for s in spots:
        slug = spot_slug(s)
        spot_url = f"/spot/{slug}"
        name_s = s["name"]
        area_raw = s.get("area", "")
        address = s.get("address") or area_raw
        hours_display = (s.get("hours") or {}).get("display", "")
        is247 = bool((s.get("hours") or {}).get("is247"))
        price = s.get("price")
        if price is not None:
            price_disp = f"from €{price:.2f}/day"
        else:
            price_disp = "operator pricing"
        provider = s.get("providerLabel", "")
        notes = s.get("notes")

        meta_bits = []
        meta_bits.append(f"<strong>Address:</strong> {html_escape(address)}")
        meta_bits.append(f"<strong>Hours:</strong> {html_escape(hours_display)}")
        meta_bits.append(f"<strong>Price:</strong> {html_escape(price_disp)}")
        if provider:
            meta_bits.append(f"<strong>Operator:</strong> {html_escape(provider)}")
        meta_html = " · ".join(meta_bits)

        notes_html = ""
        if notes:
            short_notes = notes if len(notes) <= 180 else notes[:178].rstrip() + "…"
            notes_html = f"<p>{html_escape(short_notes)}</p>"

        badge_247 = ' <span class="badge accent">24/7</span>' if is247 else ""
        spot_cards_html.append(
            f"""  <article class="spot-card">
    <h3><a href="{spot_url}">{html_escape(name_s)}</a>{badge_247}</h3>
    <div class="spot-meta">{meta_html}</div>
    {notes_html}
    <a class="more" href="{spot_url}">Spot detail →</a>
  </article>"""
        )
    spots_block = "\n".join(spot_cards_html)

    # FAQ HTML
    faq_html_items = []
    for q, a in faq_qa:
        faq_html_items.append(
            f"""    <details>
      <summary>{html_escape(q)}</summary>
      <p>{html_escape(a)}</p>
    </details>"""
        )
    faq_html = "\n".join(faq_html_items)

    # Badges
    badges = [f'<span class="badge">{spot_count} spots</span>']
    badges.append(f'<span class="badge">{html_escape(price_str)}</span>')
    if n247:
        badges.append(f'<span class="badge accent">{n247} × 24/7</span>')
    badges_html = "\n      ".join(badges)

    if n247:
        avail_phrase = f"{n247} of them run 24/7."
    else:
        avail_phrase = "Hours listed per spot below."
    lede = (
        f"LockAndGo lists {spot_count} luggage storage spots in "
        f"<strong>{html_escape(name)}</strong>, Bratislava — {html_escape(price_str)}. "
        f"{avail_phrase} Click any spot for address, hours and booking."
    )

    intent_p = meta["intent_en"]
    transit_p = meta["transit_en"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html_escape(title)}</title>
<meta name="description" content="{html_escape(description)}" />
<meta name="theme-color" content="#F1F1EC" />
<meta name="author" content="Šimon Kališ" />
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
<meta name="geo.region" content="SK-BL" />
<meta name="geo.placename" content="Bratislava" />
<meta name="geo.position" content="{lat};{lng}" />
<meta name="ICBM" content="{lat}, {lng}" />

<link rel="canonical" href="{canonical}" />
<link rel="alternate" hreflang="sk" href="{canonical_sk}" />
<link rel="alternate" hreflang="en" href="{canonical}" />
<link rel="alternate" hreflang="x-default" href="{canonical_sk}" />

<meta property="og:type" content="article" />
<meta property="og:locale" content="en_US" />
<meta property="og:locale:alternate" content="sk_SK" />
<meta property="og:site_name" content="LockAndGo" />
<meta property="og:title" content="{html_escape(truncate(f'Luggage Storage in {name} Bratislava · LockAndGo', 90))}" />
<meta property="og:description" content="{html_escape(description)}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:image" content="{BASE_URL}/api/og" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html_escape(truncate(f'Luggage Storage in {name} Bratislava · LockAndGo', 90))}" />
<meta name="twitter:description" content="{html_escape(description)}" />
<meta name="twitter:image" content="{BASE_URL}/api/og" />

<script type="application/ld+json">
{jsonld_str}
</script>

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet" />

<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>
<div class="wrap">

<header class="top">
  <a class="brand" href="/en">Lock<em>&amp;</em>Go</a>
  <nav aria-label="Main navigation">
    <a href="/en">Home</a>
    <a href="/en/app">Map</a>
    <a href="{canonical_sk}" hreflang="sk">SK</a>
  </nav>
</header>

<nav class="crumbs" aria-label="Breadcrumbs">
  <a href="/en">Home</a>
  <span aria-hidden="true">›</span>
  <a href="/en/app">Map of spots</a>
  <span aria-hidden="true">›</span>
  <span aria-current="page">{html_escape(name)}</span>
</nav>

<main id="main">

  <h1>Luggage storage in {html_escape(headline)}</h1>
  <p class="lede">{lede}</p>

  <div class="badges">
      {badges_html}
  </div>

  <section class="block" id="intro" aria-labelledby="h-intro">
    <h2 id="h-intro">Why drop your bag in {html_escape(name)}</h2>
    <p>{html_escape(intent_p)}</p>
    <p>Every spot below is a real, verified location — staffed shops, lockers, or hotel storage rooms. LockAndGo just lists them; you book and pay directly with the operator (Bounce, Radical Storage, LuggageHero, LugLockers, ZSSK, OC) — no markup.</p>
  </section>

  <section class="block" id="spots" aria-labelledby="h-spots">
    <h2 id="h-spots">Spots in this area</h2>
{spots_block}
  </section>

  <section class="block" id="transit" aria-labelledby="h-transit">
    <h2 id="h-transit">How to get here</h2>
    <p>{html_escape(transit_p)}</p>
    <p>Open the <a href="/en/app">interactive map</a> and enable geolocation to see real-time distances to every spot.</p>
  </section>

  <section class="block faq" id="faq" aria-labelledby="h-faq">
    <h2 id="h-faq">FAQ</h2>
{faq_html}
  </section>

  <section class="block" id="about" aria-labelledby="h-about">
    <h2 id="h-about">About LockAndGo</h2>
    <div class="author">
      <div class="who">LockAndGo is built by Šimon Kališ, a 16-year-old founder from Slovakia. The goal: one clean map of every luggage storage option in Bratislava — no markup, real opening hours and prices. More at <a href="/en">lockandgo.sk</a>.</div>
    </div>
  </section>

</main>

<footer class="bot">
  <span><a href="/en" rel="author">LockAndGo</a> · Šimon Kališ</span>
  <span><a href="/en/app">Back to map</a> · <a href="{canonical_sk}">Slovenská verzia</a></span>
</footer>

</div>
</body>
</html>
"""


# ── Sitemap rewrite ──────────────────────────────────────────────


AREA_BLOCK_TEMPLATE_SK = (
    "  <url>\n"
    "    <loc>{loc_sk}</loc>\n"
    "    <lastmod>{lastmod}</lastmod>\n"
    "    <changefreq>weekly</changefreq>\n"
    "    <priority>0.85</priority>\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"sk\" href=\"{loc_sk}\" />\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"en\" href=\"{loc_en}\" />\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{loc_sk}\" />\n"
    "  </url>\n"
)
AREA_BLOCK_TEMPLATE_EN = (
    "  <url>\n"
    "    <loc>{loc_en}</loc>\n"
    "    <lastmod>{lastmod}</lastmod>\n"
    "    <changefreq>weekly</changefreq>\n"
    "    <priority>0.85</priority>\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"sk\" href=\"{loc_sk}\" />\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"en\" href=\"{loc_en}\" />\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{loc_sk}\" />\n"
    "  </url>\n"
)

AREA_MARK_START = "  <!-- area-pages:start -->\n"
AREA_MARK_END = "  <!-- area-pages:end -->\n"


def rewrite_sitemap(area_slugs: List[str]) -> int:
    with open(SITEMAP, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip any existing area-pages block (between markers), idempotent.
    pattern = re.compile(
        re.escape(AREA_MARK_START.strip()) + r".*?" + re.escape(AREA_MARK_END.strip()) + r"\s*",
        re.DOTALL,
    )
    content = pattern.sub("", content)

    # Also strip any standalone area URLs that may have been added without markers.
    stray = re.compile(
        r"\s*<url>\s*<loc>https://lockandgo\.sk/(?:en/)?area/[^<]+</loc>.*?</url>\s*",
        re.DOTALL,
    )
    content = stray.sub("\n", content)

    blocks: List[str] = []
    for slug in area_slugs:
        loc_sk = f"{BASE_URL}/area/{slug}"
        loc_en = f"{BASE_URL}/en/area/{slug}"
        blocks.append(
            AREA_BLOCK_TEMPLATE_SK.format(loc_sk=loc_sk, loc_en=loc_en, lastmod=TODAY)
        )
        blocks.append(
            AREA_BLOCK_TEMPLATE_EN.format(loc_sk=loc_sk, loc_en=loc_en, lastmod=TODAY)
        )
    new_section = AREA_MARK_START + "\n".join(blocks) + AREA_MARK_END

    # Insert before </urlset>.
    if "</urlset>" not in content:
        raise RuntimeError("Missing </urlset> in sitemap.xml")
    new_content = content.replace("</urlset>", "\n" + new_section + "\n</urlset>", 1)
    # Normalize triple blank lines.
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)

    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(new_content)

    return new_content.count("<url>")


# ── llms.txt rewrite ─────────────────────────────────────────────


LLMS_AREA_START = "<!-- area-pages:start -->"
LLMS_AREA_END = "<!-- area-pages:end -->"


def rewrite_llms(area_data: List[Tuple[str, List[Dict[str, Any]]]]) -> None:
    with open(LLMS, "r", encoding="utf-8") as f:
        content = f.read()

    lines = ["", LLMS_AREA_START, "## Areas", ""]
    lines.append(
        "Area-level landing pages aggregating luggage-storage spots by Bratislava district. "
        "Each page covers an intent cluster (Old Town, Hlavná stanica, Nivy, Petržalka, "
        "Ružinov, Nové Mesto, Medická záhrada) with the full spot list, transit guidance, "
        "and 3 area-specific FAQs."
    )
    lines.append("")

    for slug, spots in area_data:
        meta = AREA_META[slug]
        name_sk = meta["name_sk"]
        name_en = meta["name_en"]
        n = len(spots)
        n247 = is247_count(spots)
        ps = price_range_for_area(spots)
        n247_str = f", {n247} × 24/7" if n247 else ""
        lines.append(
            f"- [{name_sk} (SK)]({BASE_URL}/area/{slug}) — {n} spotov, {ps}{n247_str}"
        )
        lines.append(
            f"- [{name_en} (EN)]({BASE_URL}/en/area/{slug}) — {n} spots, "
            f"{price_range_for_area_en(spots)}"
            + (f", {n247} × 24/7" if n247 else "")
        )
    lines.append("")
    lines.append(LLMS_AREA_END)
    new_section = "\n".join(lines)

    # Idempotent: remove existing block.
    pattern = re.compile(
        re.escape(LLMS_AREA_START) + r".*?" + re.escape(LLMS_AREA_END) + r"\s*",
        re.DOTALL,
    )
    content_stripped = pattern.sub("", content).rstrip()

    # Insert after the <!-- spot-pages:end --> marker. If not present, append.
    marker = "<!-- spot-pages:end -->"
    idx = content_stripped.find(marker)
    if idx != -1:
        insert_at = idx + len(marker)
        new_content = (
            content_stripped[:insert_at]
            + "\n"
            + new_section
            + "\n"
            + content_stripped[insert_at:]
        )
    else:
        new_content = content_stripped + "\n" + new_section + "\n"

    new_content = re.sub(r"\n{3,}", "\n\n", new_content)
    if not new_content.endswith("\n"):
        new_content += "\n"

    with open(LLMS, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Main ─────────────────────────────────────────────────────────


def main() -> int:
    with open(SPOTS_JSON, "r", encoding="utf-8") as f:
        all_spots = json.load(f)
    with open(AREAS_JSON, "r", encoding="utf-8") as f:
        areas_cfg = json.load(f)

    spots_by_id = {s["id"]: s for s in all_spots}

    os.makedirs(OUT_SK, exist_ok=True)
    os.makedirs(OUT_EN, exist_ok=True)

    written: List[str] = []
    area_data: List[Tuple[str, List[Dict[str, Any]]]] = []
    area_slugs: List[str] = []

    # Sanity: every spot covered exactly once.
    covered: List[str] = []

    for area in areas_cfg["areas"]:
        slug = area["slug"]
        if slug not in AREA_META:
            raise RuntimeError(f"Missing AREA_META for slug: {slug}")
        spot_ids = area["spot_ids"]
        spots = []
        for sid in spot_ids:
            if sid not in spots_by_id:
                raise RuntimeError(f"areas.json references unknown spot id: {sid}")
            spots.append(spots_by_id[sid])
            covered.append(sid)
        # Sort: 24/7 first, then by id
        spots.sort(key=lambda s: (0 if (s.get("hours") or {}).get("is247") else 1, s["id"]))

        sk_html = render_area_page_sk(slug, spots)
        en_html = render_area_page_en(slug, spots)

        sk_path = os.path.join(OUT_SK, f"{slug}.html")
        en_path = os.path.join(OUT_EN, f"{slug}.html")
        with open(sk_path, "w", encoding="utf-8") as f:
            f.write(sk_html)
        with open(en_path, "w", encoding="utf-8") as f:
            f.write(en_html)

        written.extend([sk_path, en_path])
        area_data.append((slug, spots))
        area_slugs.append(slug)

    # Verify coverage.
    all_ids = {s["id"] for s in all_spots}
    covered_set = set(covered)
    uncovered = all_ids - covered_set
    duplicated = [sid for sid in covered if covered.count(sid) > 1]
    if uncovered:
        print(f"WARNING: spots not covered by any area: {sorted(uncovered)}")
    if duplicated:
        print(f"WARNING: spots in multiple areas: {sorted(set(duplicated))}")

    url_count = rewrite_sitemap(area_slugs)
    rewrite_llms(area_data)

    print(f"wrote {len(written)} area pages (SK+EN) into /area/ + /en/area/")
    print(f"areas: {', '.join(area_slugs)}")
    print(f"coverage: {len(covered_set)}/{len(all_ids)} spots")
    print(f"sitemap.xml: {url_count} <url> entries")
    print(f"llms.txt: '## Areas' section inserted after spot-pages block")
    print(f"sample SK: {written[0]}")
    print(f"sample EN: {written[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
