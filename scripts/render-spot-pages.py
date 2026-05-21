#!/usr/bin/env python3
"""Generate /spot/{id}-{slug}.html pages from data/spots.json and rewrite sitemap.xml.

Each page:
  - title (≤60 chars), meta description (≤155 chars), canonical, hreflang
  - H1 + breadcrumb (Domov → Mapa spotov → name)
  - Sections: Lokácia, Cena, Otváracie hodiny, Ako rezervovať,
    Bezpečnosť & poznámky, FAQ
  - JSON-LD: LocalBusiness (typed: SelfStorage / Store / LodgingBusiness),
    BreadcrumbList, WebPage
  - Brand styling: Instrument Serif + Manrope, palette #F1F1EC / #1F1F1D / #B89A45
  - Footer attributing Šimon Kališ
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
OUT_DIR = os.path.join(ROOT, "spot")
SITEMAP = os.path.join(ROOT, "sitemap.xml")
LLMS = os.path.join(ROOT, "llms.txt")
BASE_URL = "https://lockandgo.sk"
TODAY = datetime.date.today().isoformat()

DAY_NAMES_SK = ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"]
# schedule arrays are indexed [Sun..Sat] per app.html source; reorder to Mon..Sun.
DAY_ORDER_SK_FROM_RAW = [1, 2, 3, 4, 5, 6, 0]
SCHEMA_DAYS = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "spot"


def html_escape(s: str) -> str:
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


def fmt_schedule_human(schedule: List[Optional[List[float]]]) -> List[Tuple[str, str]]:
    """Return list of (day_label, hours_text) rows in Po..Ne order."""
    out: List[Tuple[str, str]] = []
    for i, raw_idx in enumerate(DAY_ORDER_SK_FROM_RAW):
        slot = schedule[raw_idx] if raw_idx < len(schedule) else None
        label = DAY_NAMES_SK[i]
        if not slot:
            out.append((label, "zatvorené"))
            continue
        o, c = slot
        if o == 0 and c == 24:
            out.append((label, "24/7"))
        else:
            out.append((label, f"{fmt_hour(o)} – {fmt_hour(c)}"))
    return out


def schema_opening_hours(schedule: List[Optional[List[float]]]) -> List[Dict[str, Any]]:
    """Generate openingHoursSpecification entries (one per active day)."""
    out: List[Dict[str, Any]] = []
    for i, slot in enumerate(schedule):
        if not slot:
            continue
        o, c = slot
        opens = "00:00" if (o == 0 and c == 24) else fmt_hour(o)
        closes = "23:59" if (o == 0 and c == 24) else fmt_hour(c)
        out.append(
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": f"https://schema.org/{SCHEMA_DAYS[i]}",
                "opens": opens,
                "closes": closes,
            }
        )
    return out


def infer_business_type(spot: Dict[str, Any]) -> str:
    provider = (spot.get("providerLabel") or "").lower()
    notes = (spot.get("notes") or "").lower()
    name = (spot.get("name") or "").lower()
    if any(w in provider for w in ("hotel", "safestay")) or "recepc" in notes:
        return "LodgingBusiness"
    locker_signals = (
        "locker",
        "skrink",
        "samoobsluž",
        "luglocker",
        "luggage locker",
        "boxy",
        "automatick",
    )
    if any(w in provider + " " + notes + " " + name for w in locker_signals):
        return "SelfStorage"
    return "Store"


def price_range(spot: Dict[str, Any]) -> Optional[str]:
    if spot.get("price") is not None:
        try:
            return f"€{float(spot['price']):.2f}"
        except Exception:
            return None
    return None


def is_affiliate(spot: Dict[str, Any]) -> bool:
    """Bounce links (ids 01..12) and Bounce-pattern URLs are affiliate."""
    url = spot.get("bookingUrl") or ""
    return "bounce.com" in url


def has_online_booking(spot: Dict[str, Any]) -> bool:
    return spot.get("bookingType") != "walkin" and bool(spot.get("bookingUrl"))


# ── Context blurbs by area / type ────────────────────────────────


def area_context(area: str) -> str:
    a = (area or "").lower()
    if "hlavná stanica" in a or "hlavna stanica" in a:
        return (
            "Lokalita pri Hlavnej stanici je strategická pre cestujúcich s vlakom — "
            "RegioJet, ZSSK aj nočné spoje IC Bus stoja minútu chôdze. Hodí sa to aj "
            "pred odletom z Letiska M. R. Štefánika cez bus 61 (nástup priamo pri stanici)."
        )
    if "nivy" in a or "mlynsk" in a or "bottov" in a:
        return (
            "Nivy / Mlynské nivy je hub medzinárodnej autobusovej dopravy — FlixBus, "
            "RegioJet, Eurolines. Pohodlne odložíš batožinu medzi check-out a "
            "odchodom buse, alebo si necháš veci pred prehliadkou centra (15 min "
            "pešo do Starého Mesta)."
        )
    if "petržalk" in a or "petrzalk" in a or "aupark" in a:
        return (
            "Petržalka je dôležitá pre cestujúcich z/do Viedne — REX-1, RegioJet a "
            "Slovak Lines stoja v ŽST Petržalka. Pohodlné aj pre návštevníkov "
            "Auparku a Sad Janka Kráľa."
        )
    if "staré mesto" in a or "stare mesto" in a or "michalsk" in a or "obchodn" in a or "poštov" in a or "postov" in a or "námestie" in a or "namestie" in a:
        return (
            "Staré Mesto je centrum prehliadky — Bratislavský hrad, Michalská brána, "
            "Hlavné námestie a UFO veža sú do 20 minút pešo. Bez batožiny si "
            "ich užiješ omnoho viac."
        )
    if "ružinov" in a or "ruzinov" in a:
        return (
            "Ružinov susedí s biznis distriktom a centrálnymi električkami. Ideálne, "
            "ak máš meeting alebo bývaš v ubytovaní v zóne Miletička / Dulovo námestie."
        )
    if "nové mesto" in a or "nove mesto" in a or "vinohrad" in a or "vajnorsk" in a:
        return (
            "Nové Mesto je dobrá voľba, ak prichádzaš z Viedne diaľnicou alebo "
            "navštevuješ OC Vivo!, Polus a Bratislavské Vinohrady."
        )
    if "medick" in a:
        return (
            "Medická záhrada je pokojná zelená zóna na pomedzí Starého Mesta a "
            "biznis distriktu — kúsok od Univerzity Komenského a Národnej rady."
        )
    return (
        "Bratislava má kompaktné centrum — z väčšiny spotov je do Starého Mesta "
        "najviac 15–20 minút MHD alebo pešo."
    )


def fit_blurb(spot: Dict[str, Any]) -> str:
    biz = infer_business_type(spot)
    is247 = bool((spot.get("hours") or {}).get("is247"))
    if biz == "SelfStorage" and is247:
        return (
            "Tento spot je samoobslužný locker s prístupom 24/7. Hodí sa, ak prichádzaš "
            "nočným vlakom, busom alebo skoro ráno pred otvorením obchodov. "
            "Odomkýna sa typicky QR kódom alebo PIN-om, takže nepotrebuješ personál."
        )
    if biz == "SelfStorage":
        return (
            "Samoobslužné skrinky bez personálu — rýchle a anonymné. Skontroluj "
            "rozmer skrinky vopred, aby sa tam tvoj kufor zmestil."
        )
    if biz == "LodgingBusiness":
        return (
            "Hotel s úschovňou pre non-guests (za poplatok). Personál na recepcii ti "
            "vystaví doklad. Pred príchodom radšej zavolaj a potvrď non-guest "
            "policy — v sezóne býva plno."
        )
    return (
        "Obchod / kaviareň s personálom — odovzdáš batožinu, dostaneš lístok alebo "
        "QR kód a pri vyzdvihnutí ju jednoducho prevezmeš. Vhodné pre väčšiu "
        "batožinu aj nadrozmerné kusy."
    )


def build_title(name: str) -> str:
    """Title ≤60 chars: '{name} · Úschovňa batožiny v Bratislave | LockAndGo'."""
    suffix = " · Úschovňa batožiny v Bratislave | LockAndGo"
    max_name = 60 - len(suffix)
    if max_name < 10:
        # safety: degrade suffix
        return truncate(name, 60)
    short = truncate(name, max_name)
    return short + suffix


def build_description(spot: Dict[str, Any]) -> str:
    name = spot["name"]
    area = spot.get("area", "")
    price = spot.get("price")
    is247 = bool((spot.get("hours") or {}).get("is247"))
    parts: List[str] = []
    parts.append(f"{name} ({area}) — úschovňa batožiny v Bratislave.")
    if price is not None:
        parts.append(f"Od {price:.2f} €/deň.")
    else:
        parts.append("Ceny podľa prevádzkovateľa.")
    parts.append("Otvorené 24/7." if is247 else "Otváracie hodiny v detaile.")
    parts.append("Rezerváciu spravíš za 2 min.")
    desc = " ".join(parts)
    return truncate(desc, 155)


# ── Anonymous Bounce spot detection + landmark inference ─────────
#
# 12 Bounce partner spots (ids 01–12) have anonymized English names from
# the upstream provider (e.g. "Near Bratislava Station Storage Spot").
# Those names hurt long-tail SK SEO. We translate them into landmark-led
# Slovak headlines while keeping transparency that it's a Bounce partner.
# URLs/slugs stay the same — only visible content + schema name changes.

# "Near {X} Storage Spot" landmark translations (English → Slovak landmark)
LANDMARK_EN_TO_SK = {
    "Bratislava Station": "Hlavnej stanici",
    "Faculty of Medicine": "Lekárskej fakulte UK",
    "Slovak Pub": "Slovak Pub",
    "Michael's Gate": "Michalskej bráne",
    "Michael’s Gate": "Michalskej bráne",
    "Michaels Gate": "Michalskej bráne",
    "Gallery Multium": "Galérii Multium",
    "Poštová Tram Stop": "zastávke Poštová",
    "Postova Tram Stop": "zastávke Poštová",
}

# Anonymous-name pattern detection
ANON_PATTERNS = [
    re.compile(r"^Near (.+?) Storage Spot$", re.IGNORECASE),
    re.compile(r"^Across (.+?) Storage Spot$", re.IGNORECASE),
    re.compile(r"^(Stare Mesto Area|Staré Mesto Area) Storage Spot$", re.IGNORECASE),
    re.compile(r"^Bratislava (Stare Mesto|Staré Mesto) Storage Spot$", re.IGNORECASE),
    re.compile(r"^(Petržalka|Petrzalka|Staré Mesto|Stare Mesto) Storage Spot$", re.IGNORECASE),
    re.compile(r"^(Masala Darbar) Storage Spot$", re.IGNORECASE),  # venue-named anon
]


def is_anonymous_bounce(spot: Dict[str, Any]) -> bool:
    """True if this spot uses Bounce's anonymized naming pattern."""
    name = spot.get("name") or ""
    if not is_affiliate(spot):
        return False
    for pat in ANON_PATTERNS:
        if pat.match(name):
            return True
    # Catch-all: any Bounce spot whose name ends with "Storage Spot"
    return bool(re.search(r"Storage Spot$", name))


def _translate_landmark(en_landmark: str) -> str:
    """Translate an English landmark phrase to Slovak (locative case)."""
    en_landmark = en_landmark.strip()
    # Try exact match first
    if en_landmark in LANDMARK_EN_TO_SK:
        return LANDMARK_EN_TO_SK[en_landmark]
    # Try case-insensitive
    for key, val in LANDMARK_EN_TO_SK.items():
        if key.lower() == en_landmark.lower():
            return val
    # Fall back to the original
    return en_landmark


def landmark_for(spot: Dict[str, Any]) -> Dict[str, str]:
    """Return SEO display fields for a spot.

    Returns a dict with keys: headline, seo_title, seo_description, breadcrumb_name.
    For anonymous Bounce spots, builds a landmark-led Slovak headline.
    For non-anonymous spots, uses the original name as-is.
    """
    name = spot["name"]
    area = spot.get("area", "")
    address = spot.get("address") or ""
    price = spot.get("price")
    hours_display = (spot.get("hours") or {}).get("display", "")
    is247 = bool((spot.get("hours") or {}).get("is247"))

    if not is_anonymous_bounce(spot):
        # Non-anonymous spot — keep existing behavior. The name is already specific
        # (e.g. "Hlavná stanica · samoobslužné skrinky", "Radical Storage · Miletičová").
        return {
            "headline": name,
            "seo_title": build_title(name),
            "seo_description": build_description(spot),
            "breadcrumb_name": name,
            "og_name": name,
        }

    # ── Anonymous Bounce spot: infer landmark from name (in priority order). ──
    landmark = None
    preposition = None  # SK preposition that fits the landmark's locative case

    # Rule 1: "Near {X} Storage Spot" → "pri/v {translated X}"
    m = re.match(r"^Near (.+?) Storage Spot$", name, re.IGNORECASE)
    if m:
        en = m.group(1).strip()
        landmark = _translate_landmark(en)
        # Pick preposition: "pri" for buildings/gates/stations, "v" for galleries
        if "galéri" in landmark.lower() or "galér" in landmark.lower():
            preposition = "v"
        else:
            preposition = "pri"

    # Rule 2: "Across {X} Storage Spot" → "pri/oproti {translated X}"
    if landmark is None:
        m = re.match(r"^Across (.+?) Storage Spot$", name, re.IGNORECASE)
        if m:
            en = m.group(1).strip()
            landmark = _translate_landmark(en)
            preposition = "oproti"

    # Rule 3: "{Venue} Storage Spot" where venue is a real proper noun (e.g. Masala Darbar)
    if landmark is None:
        m = re.match(r"^(Masala Darbar) Storage Spot$", name, re.IGNORECASE)
        if m:
            landmark = m.group(1)
            preposition = "pri"

    # Rule 4: area-based fallback for "{Area} Storage Spot" or "Bratislava {Area} Storage Spot"
    if landmark is None:
        if area:
            # area may contain " · " segments (e.g. "Staré Mesto · galérie"); take the head
            landmark = area.split(" · ")[0].strip()
            # Pick a sensible locative preposition based on area name.
            low = landmark.lower()
            if low in ("petržalka", "petrzalka"):
                preposition = "v"
            elif low.startswith("staré mesto") or low.startswith("stare mesto"):
                preposition = "v"
            elif low.startswith("námestie") or low.startswith("namestie"):
                preposition = "na"
            else:
                preposition = "v"
            # Apply locative case for common areas
            locative_map = {
                "Staré Mesto": "Starom Meste",
                "Stare Mesto": "Starom Meste",
                "Petržalka": "Petržalke",
                "Petrzalka": "Petržalke",
                "Námestie SNP": "Námestí SNP",
                "Obchodná": "Obchodnej",
                "Štúrova": "Štúrovej",
                "Hlavná stanica": "Hlavnej stanici",
            }
            if landmark in locative_map:
                landmark = locative_map[landmark]
                if landmark == "Hlavnej stanici":
                    preposition = "pri"

    if landmark is None:
        landmark = area or "Bratislave"
        preposition = "v"

    # ── Build headline (for H1, breadcrumb, JSON-LD name). ──
    headline = f"Úschovňa batožiny {preposition} {landmark} (Bounce partner)"

    # ── Build SEO title (≤60 chars). ──
    # Prefer: "Úschovňa {landmark} · Bratislava | LockAndGo"
    title_attempts = [
        f"Úschovňa {preposition} {landmark} · Bratislava | LockAndGo",
        f"Úschovňa batožiny {preposition} {landmark} | LockAndGo",
        f"Úschovňa {landmark} | LockAndGo",
    ]
    seo_title = next((t for t in title_attempts if len(t) <= 60), truncate(title_attempts[0], 60))

    # ── Build SEO description (≤155 chars). ──
    # Template: "Úschovňa batožiny [pri/v/oproti {landmark}] v Bratislave. {price}. Otváracie hodiny {hours}. Bounce partner — rezervácia online."
    price_str = f"Od {price:.2f} €/deň" if price is not None else "Cena podľa prevádzkovateľa"
    hours_str = "Otvorené 24/7" if is247 else f"Otváracie hodiny {hours_display}"
    desc = (
        f"Úschovňa batožiny {preposition} {landmark} v Bratislave. "
        f"{price_str}. {hours_str}. Bounce partner — rezervácia online."
    )
    # If too long, shorten the hours portion progressively
    if len(desc) > 155:
        desc = (
            f"Úschovňa batožiny {preposition} {landmark} v Bratislave. "
            f"{price_str}. Bounce partner — rezervácia online."
        )
    if len(desc) > 155:
        desc = truncate(desc, 155)

    return {
        "headline": headline,
        "seo_title": seo_title,
        "seo_description": desc,
        "breadcrumb_name": headline,
        "og_name": headline,
    }


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
.wrap{max-width:780px;margin:0 auto;padding:24px 20px 80px}
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
h1{font-family:var(--display);font-weight:400;font-size:clamp(34px,5vw,46px);line-height:1.1;margin:0 0 8px;letter-spacing:-0.01em}
.lede{font-size:17px;color:var(--ink-2);margin:0 0 28px;max-width:60ch}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 24px}
.badge{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border:1px solid var(--line-2);border-radius:999px;font-size:13px;color:var(--ink-2);background:var(--paper)}
.badge.accent{background:var(--accent-50);border-color:var(--accent);color:var(--accent-2)}
section.block{background:var(--paper);border:1px solid var(--line);border-radius:var(--r-lg);padding:22px 22px 18px;margin:0 0 18px}
section.block h2{font-family:var(--display);font-weight:400;font-size:24px;margin:0 0 12px;letter-spacing:-0.005em}
section.block p{margin:0 0 10px;color:var(--ink-2)}
section.block p:last-child{margin-bottom:0}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:0;font-size:15px}
.kv dt{color:var(--ink-3);font-size:13px;letter-spacing:0.02em;text-transform:uppercase;padding-top:2px}
.kv dd{margin:0;color:var(--ink)}
.hours-table{width:100%;border-collapse:collapse;font-size:15px}
.hours-table td{padding:6px 0;border-bottom:1px solid var(--line)}
.hours-table tr:last-child td{border-bottom:none}
.hours-table td:first-child{font-weight:500;width:60px;color:var(--ink-2)}
.hours-table td:last-child{text-align:right;color:var(--ink)}
.cta{display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:var(--bg);padding:13px 22px;border-radius:14px;font-weight:600;text-decoration:none;border:1px solid var(--accent-2);box-shadow:0 10px 24px -8px rgba(184,154,69,0.32)}
.cta:hover{background:var(--accent-2);text-decoration:none}
.cta-sec{display:inline-flex;align-items:center;gap:8px;padding:11px 18px;border:1px solid var(--line-2);border-radius:14px;color:var(--ink);text-decoration:none;background:var(--bg);margin-left:8px}
.cta-sec:hover{border-color:var(--accent);color:var(--accent-2)}
.faq details{border-top:1px solid var(--line);padding:14px 0}
.faq details:first-of-type{border-top:none;padding-top:4px}
.faq summary{font-weight:600;cursor:pointer;list-style:none;font-size:16px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:'+';float:right;color:var(--accent-2);font-weight:400;font-size:22px;line-height:1}
.faq details[open] summary::after{content:'−'}
.faq p{margin:8px 0 0;color:var(--ink-2)}
footer.bot{margin-top:36px;padding-top:20px;border-top:1px solid var(--line);font-size:13px;color:var(--ink-3);display:flex;flex-wrap:wrap;gap:8px;justify-content:space-between}
footer.bot a{color:var(--ink-2);text-decoration:none}
footer.bot a:hover{color:var(--accent-2)}
@media (max-width:560px){
  .wrap{padding:18px 16px 64px}
  .kv{grid-template-columns:1fr}
  .kv dt{padding-top:8px}
  .cta-sec{margin-left:0;margin-top:8px}
  h1{font-size:34px}
}
""".strip()


def render_spot_page(spot: Dict[str, Any]) -> str:
    name = spot["name"]
    area = spot.get("area", "")
    address = spot.get("address") or area
    lat = spot.get("lat")
    lng = spot.get("lng")
    provider = spot.get("providerLabel", "")
    booking_url = spot.get("bookingUrl")
    notes = spot.get("notes")
    rating = spot.get("rating")
    reviews = spot.get("reviews") or 0
    price = spot.get("price")
    price_details = spot.get("priceDetails")
    hours = spot.get("hours") or {}
    is247 = bool(hours.get("is247"))
    hours_display = hours.get("display", "")
    schedule = hours.get("schedule") or []
    spot_id = spot["id"]
    slug = slugify(name)
    canonical = f"{BASE_URL}/spot/{spot_id}-{slug}"

    # SEO display fields (handles anonymous Bounce spots → landmark-led headlines).
    seo = landmark_for(spot)
    headline = seo["headline"]
    title = seo["seo_title"]
    description = seo["seo_description"]
    breadcrumb_name = seo["breadcrumb_name"]
    og_name = seo["og_name"]
    biz_type = infer_business_type(spot)

    gmaps_link = (
        f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        if lat is not None and lng is not None
        else None
    )

    # ── JSON-LD graph ─────────────────────────────────────────────
    local_business: Dict[str, Any] = {
        "@type": biz_type,
        "@id": f"{canonical}#business",
        "name": headline,
        "url": canonical,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": address,
            "addressLocality": "Bratislava",
            "addressRegion": "Bratislavský kraj",
            "addressCountry": "SK",
        },
    }
    if lat is not None and lng is not None:
        local_business["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": lat,
            "longitude": lng,
        }
    oh = schema_opening_hours(schedule)
    if oh:
        local_business["openingHoursSpecification"] = oh
    pr = price_range(spot)
    if pr:
        local_business["priceRange"] = pr
    if rating is not None and reviews:
        local_business["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating,
            "reviewCount": reviews,
            "bestRating": 5,
            "worstRating": 1,
        }
    local_business["paymentAccepted"] = "Cash, Credit Card"
    local_business["areaServed"] = {"@type": "City", "name": "Bratislava"}

    breadcrumb = {
        "@type": "BreadcrumbList",
        "@id": f"{canonical}#breadcrumb",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Domov",
                "item": f"{BASE_URL}/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Mapa spotov",
                "item": f"{BASE_URL}/app",
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": breadcrumb_name,
                "item": canonical,
            },
        ],
    }
    webpage = {
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
    # Note: @context only required at top-level in JSON-LD, but some validators
    # check every node — add it everywhere for maximum compatibility.
    for node in (webpage, breadcrumb, local_business):
        node["@context"] = "https://schema.org"
    graph = {"@context": "https://schema.org", "@graph": [webpage, breadcrumb, local_business]}
    jsonld_str = json.dumps(graph, ensure_ascii=False, indent=2)

    # ── Hours table ───────────────────────────────────────────────
    rows = fmt_schedule_human(schedule) if schedule else []
    if rows:
        hours_rows_html = "\n".join(
            f"      <tr><td>{day}</td><td>{html_escape(text)}</td></tr>"
            for day, text in rows
        )
        hours_table_html = (
            f"    <table class=\"hours-table\" aria-label=\"Otváracie hodiny po dňoch\">\n"
            f"{hours_rows_html}\n"
            f"    </table>"
        )
    else:
        hours_table_html = f"    <p>{html_escape(hours_display) or 'Otváracie hodiny nie sú k dispozícii.'}</p>"

    # ── Price block ───────────────────────────────────────────────
    if price_details:
        price_lines = [html_escape(line) for line in price_details.split("\n") if line.strip()]
        price_html = "<br>\n      ".join(price_lines)
        price_block = f"    <p>{price_html}</p>"
    elif price is not None:
        price_block = (
            f"    <p>Cena <strong>{price:.2f} €</strong> za kus batožiny a deň. "
            f"LockAndGo si neúčtuje žiadnu prirážku — platíš priamo prevádzkovateľovi.</p>"
        )
    else:
        price_block = (
            "    <p>Cena podľa prevádzkovateľa — final pricing uvidíš pred zaplatením "
            "na ich stránke.</p>"
        )

    # ── Booking CTA ───────────────────────────────────────────────
    if has_online_booking(spot):
        rel = "sponsored noopener" if is_affiliate(spot) else "noopener"
        target_extra = " target=\"_blank\""
        booking_label = "Rezervovať teraz"
        booking_explain = (
            "Klikni na Rezervovať a presmerujeme ťa na booking stránku prevádzkovateľa. "
            "Platba prebehne priamo u nich, dostaneš potvrdenie alebo PIN kód."
        )
        if is_affiliate(spot):
            booking_explain += (
                " LockAndGo je pri tomto spote affiliate partnerom — provízia je už "
                "započítaná v cene prevádzkovateľa, pre teba sa nič nemení."
            )
        cta_html = (
            f'    <p><a class="cta" href="{html_escape(booking_url)}" '
            f'rel="{rel}"{target_extra}>{booking_label} →</a>'
        )
        if gmaps_link:
            cta_html += (
                f' <a class="cta-sec" href="{gmaps_link}" '
                f'rel="noopener" target="_blank">Navigovať</a>'
            )
        cta_html += "</p>"
    else:
        booking_explain = (
            "Toto je walk-in spot bez online rezervácie — choď priamo na miesto v "
            "otváracích hodinách. Zaplatíš na mieste, zvyčajne hotovosťou alebo kartou."
        )
        cta_html = ""
        if booking_url:
            cta_html += (
                f'    <p><a class="cta-sec" href="{html_escape(booking_url)}" '
                f'rel="noopener" target="_blank">Info prevádzkovateľa</a>'
            )
        if gmaps_link:
            if not cta_html:
                cta_html = '    <p>'
            else:
                cta_html += " "
            cta_html += (
                f'<a class="cta" href="{gmaps_link}" rel="noopener" '
                f'target="_blank">Navigovať na miesto →</a>'
            )
        if cta_html:
            cta_html += "</p>"

    # ── Notes / safety ────────────────────────────────────────────
    if notes:
        safety_html = f"    <p>{html_escape(notes)}</p>"
    else:
        safety_html = (
            "    <p>Spot je reálna prevádzka — obchod, stanica alebo hotel s personálom, "
            "prípadne zabezpečené samoobslužné skrinky. Pred uložením skontroluj, "
            "že krehké veci máš dobre zabalené.</p>"
        )

    # ── FAQ ───────────────────────────────────────────────────────
    faq_where = (
        f"{html_escape(headline)} sa nachádza v lokalite <strong>{html_escape(area)}</strong>"
    )
    if address and address != area:
        faq_where += f" — adresa: {html_escape(address)}"
    faq_where += "."
    if price_details:
        first_line = price_details.split("\n", 1)[0]
        faq_price = html_escape(first_line)
    elif price is not None:
        faq_price = f"Cena je {price:.2f} € za kus batožiny a deň."
    else:
        faq_price = "Cena závisí od prevádzkovateľa — final cenu uvidíš pred platbou."
    faq_247 = (
        "Áno, tento spot je dostupný 24/7."
        if is247
        else f"Nie, otváracie hodiny: {html_escape(hours_display)}."
    )

    # ── Extra FAQ items (practical) ───────────────────────────────
    if has_online_booking(spot):
        faq_payment = (
            "Platba prebieha online u prevádzkovateľa pri rezervácii — karta, Apple Pay alebo Google Pay. "
            "Po platbe dostaneš potvrdenie na email s adresou a inštrukciami."
        )
    else:
        faq_payment = (
            "Walk-in spot — platíš na mieste. Väčšina prevádzok berie kartu, "
            "samoobslužné lockery niekedy iba mince (skontroluj pred príchodom)."
        )
    if is247:
        faq_arrival = (
            "Prísť môžeš kedykoľvek vrátane noci a víkendu. Pri samoobslužných "
            "lockeroch odporúčame mať pri sebe svetlo telefónu — niektoré priestory "
            "majú slabšie osvetlenie."
        )
    else:
        faq_arrival = (
            f"Prísť môžeš v rámci otváracích hodín ({html_escape(hours_display)}). "
            "Pri rezervácii s časom príchodu sa drž rezervovaného okna — "
            "neskorý príchod môže znamenať, že obchod bude zatvorený."
        )

    faq_html = f"""
    <details>
      <summary>Kde presne je {html_escape(headline)}?</summary>
      <p>{faq_where}</p>
    </details>
    <details>
      <summary>Koľko stojí úschovňa?</summary>
      <p>{faq_price}</p>
    </details>
    <details>
      <summary>Je tento spot otvorený 24/7?</summary>
      <p>{faq_247}</p>
    </details>
    <details>
      <summary>Ako sa platí?</summary>
      <p>{faq_payment}</p>
    </details>
    <details>
      <summary>Kedy môžem prísť?</summary>
      <p>{faq_arrival}</p>
    </details>
"""

    # ── Location section ──────────────────────────────────────────
    geo_lines = [f"<dt>Lokalita</dt><dd>{html_escape(area)}</dd>"]
    if address and address != area:
        geo_lines.append(f"<dt>Adresa</dt><dd>{html_escape(address)}</dd>")
    if lat is not None and lng is not None:
        geo_lines.append(
            f"<dt>Súradnice</dt><dd>{lat:.4f}, {lng:.4f} "
            f'(<a href="{gmaps_link}" rel="noopener" target="_blank">Google Maps</a>)</dd>'
        )
    if provider:
        geo_lines.append(f"<dt>Prevádzkovateľ</dt><dd>{html_escape(provider)}</dd>")
    if rating is not None and reviews:
        geo_lines.append(
            f"<dt>Hodnotenie</dt><dd>{rating:.1f} / 5 z {reviews} recenzií</dd>"
        )
    geo_html = "\n      ".join(geo_lines)

    # ── Badges ────────────────────────────────────────────────────
    badges: List[str] = []
    badges.append(f'<span class="badge">{html_escape(area)}</span>')
    if is247:
        badges.append('<span class="badge accent">24/7</span>')
    if price is not None:
        badges.append(f'<span class="badge">od {price:.2f} €/deň</span>')
    if provider:
        badges.append(f'<span class="badge">{html_escape(provider)}</span>')
    badges_html = "\n      ".join(badges)

    # ── Lede ──────────────────────────────────────────────────────
    if is247:
        availability_phrase = "Dostupné 24 hodín, 7 dní v týždni."
    else:
        availability_phrase = f"Otvorené: {html_escape(hours_display)}."
    if price is not None:
        price_phrase = f"Cena od {price:.2f} € za kus batožiny a deň."
    else:
        price_phrase = "Cena podľa prevádzkovateľa."
    lede = (
        f"{html_escape(headline)} je úschovňa batožiny v lokalite {html_escape(area)}. "
        f"{availability_phrase} {price_phrase} "
        f"Rezerváciu spravíš za pár minút, LockAndGo si neúčtuje žiadnu prirážku."
    )

    area_ctx = area_context(area)
    fit_ctx = fit_blurb(spot)

    # ── Final assembly ────────────────────────────────────────────
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
{f'<meta name="geo.position" content="{lat};{lng}" />' if lat is not None and lng is not None else ''}
{f'<meta name="ICBM" content="{lat}, {lng}" />' if lat is not None and lng is not None else ''}

<link rel="canonical" href="{canonical}" />
<link rel="alternate" hreflang="sk" href="{canonical}" />
<link rel="alternate" hreflang="x-default" href="{canonical}" />

<meta property="og:type" content="article" />
<meta property="og:locale" content="sk_SK" />
<meta property="og:site_name" content="LockAndGo" />
<meta property="og:title" content="{html_escape(truncate(og_name + ' · LockAndGo', 90))}" />
<meta property="og:description" content="{html_escape(description)}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:image" content="{BASE_URL}/api/og" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html_escape(truncate(og_name + ' · LockAndGo', 90))}" />
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
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="icon" type="image/x-icon" href="/favicon.ico" sizes="any" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
</head>
<body>
<a class="skip" href="#main" style="position:absolute;left:-9999px">Preskočiť na obsah</a>
<div class="wrap">

<header class="top">
  <a class="brand" href="/">Lock<em>&amp;</em>Go</a>
  <nav aria-label="Hlavná navigácia">
    <a href="/">Domov</a>
    <a href="/app">Mapa</a>
  </nav>
</header>

<nav class="crumbs" aria-label="Drobky">
  <a href="/">Domov</a>
  <span aria-hidden="true">›</span>
  <a href="/app">Mapa spotov</a>
  <span aria-hidden="true">›</span>
  <span aria-current="page">{html_escape(breadcrumb_name)}</span>
</nav>

<main id="main">

  <h1>{html_escape(headline)}</h1>
  <p class="lede">{lede}</p>

  <div class="badges">
      {badges_html}
  </div>

  <section class="block" id="lokacia" aria-labelledby="h-lokacia">
    <h2 id="h-lokacia">Lokácia</h2>
    <dl class="kv">
      {geo_html}
    </dl>
  </section>

  <section class="block" id="cena" aria-labelledby="h-cena">
    <h2 id="h-cena">Cena</h2>
{price_block}
  </section>

  <section class="block" id="hodiny" aria-labelledby="h-hodiny">
    <h2 id="h-hodiny">Otváracie hodiny</h2>
    <p>Súhrn: <strong>{html_escape(hours_display)}</strong></p>
{hours_table_html}
  </section>

  <section class="block" id="rezervacia" aria-labelledby="h-rezervacia">
    <h2 id="h-rezervacia">Ako rezervovať</h2>
    <p>{booking_explain}</p>
{cta_html}
  </section>

  <section class="block" id="pre-koho" aria-labelledby="h-pre-koho">
    <h2 id="h-pre-koho">Pre koho je tento spot vhodný</h2>
    <p>{fit_ctx}</p>
    <p>{area_ctx}</p>
  </section>

  <section class="block" id="bezpecnost" aria-labelledby="h-bezp">
    <h2 id="h-bezp">Bezpečnosť &amp; poznámky</h2>
{safety_html}
    <p>Spoty v zozname LockAndGo sú reálne prevádzky alebo zabezpečené lockery — overujeme ich pred zaradením. Pri cenných veciach (laptop, doklady) odporúčame nosiť ich pri sebe alebo využiť spot s personálom a poistením batožiny.</p>
  </section>

  <section class="block" id="tipy" aria-labelledby="h-tipy">
    <h2 id="h-tipy">Praktické tipy pred uložením</h2>
    <p>Aby si si batožinu prevzal bez stresu: skontroluj, či máš pri sebe doklady, nabíjačku a peňaženku — tieto veci do úschovne nikdy nedávaj. Krehké predmety (sklenené suveníry, elektroniku) obal mäkkou vrstvou — väčšina spotov ručí za poškodenie iba do určitej sumy podľa svojich podmienok.</p>
    <p>Ak si vyzdvihuješ batožinu skoro ráno alebo neskoro večer, počítaj s otváracími hodinami spotu — pri walk-in prevádzkach (obchody, kaviarne) sa drž ich času, pri samoobslužných lockeroch je prístup nonstop. Pri batožine s rezerváciou si ulož potvrdzovací email alebo screenshot — neraz sa hodí, ak by sa systém zasekol.</p>
  </section>

  <section class="block faq" id="faq" aria-labelledby="h-faq">
    <h2 id="h-faq">Časté otázky</h2>
{faq_html}
  </section>

</main>

<footer class="bot">
  <span><a href="/" rel="author">LockAndGo</a> · Šimon Kališ</span>
  <span><a href="/app">Späť na mapu spotov</a></span>
</footer>

</div>
</body>
</html>
"""


# ── Sitemap + llms.txt rewriting ─────────────────────────────────


SPOT_BLOCK_TEMPLATE = (
    "  <url>\n"
    "    <loc>{loc}</loc>\n"
    "    <lastmod>{lastmod}</lastmod>\n"
    "    <changefreq>monthly</changefreq>\n"
    "    <priority>0.7</priority>\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"sk\" href=\"{loc}\" />\n"
    "    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{loc}\" />\n"
    "  </url>\n"
)


def rewrite_sitemap(spots: List[Dict[str, Any]]) -> int:
    with open(SITEMAP, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip any prior spot entries (those that have /spot/ in loc).
    pattern = re.compile(
        r"\s*<url>\s*<loc>https://lockandgo\.sk/spot/[^<]+</loc>.*?</url>\s*",
        re.DOTALL,
    )
    content = pattern.sub("\n", content)

    blocks = []
    for spot in spots:
        slug = slugify(spot["name"])
        loc = f"{BASE_URL}/spot/{spot['id']}-{slug}"
        blocks.append(SPOT_BLOCK_TEMPLATE.format(loc=loc, lastmod=TODAY))
    insert = "\n" + "\n".join(blocks)

    # Insert just before </urlset>.
    if "</urlset>" not in content:
        raise RuntimeError("Missing </urlset> in sitemap.xml")
    new_content = content.replace("</urlset>", insert + "\n</urlset>", 1)

    # Normalize multiple blank lines.
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)

    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Count <url> entries
    return new_content.count("<url>")


LLMS_MARK_START = "<!-- spot-pages:start -->"
LLMS_MARK_END = "<!-- spot-pages:end -->"


def rewrite_llms(spots: List[Dict[str, Any]]) -> None:
    with open(LLMS, "r", encoding="utf-8") as f:
        content = f.read()

    # Build the spot-pages section.
    lines = ["", LLMS_MARK_START, "## Spot pages", ""]
    for spot in spots:
        slug = slugify(spot["name"])
        url = f"{BASE_URL}/spot/{spot['id']}-{slug}"
        area = spot.get("area", "")
        hours_display = (spot.get("hours") or {}).get("display", "")
        price = spot.get("price")
        if price is not None:
            price_str = f"od {price:.2f} €/deň"
        else:
            price_str = "cena podľa prevádzkovateľa"
        # Use the landmark-led headline for anonymous Bounce spots so LLM-readable
        # lists show the SK landmark name instead of the upstream English alias.
        display_name = landmark_for(spot)["headline"]
        lines.append(f"- [{display_name}]({url}) — {area}, {price_str}, {hours_display}")
    lines.append("")
    lines.append(LLMS_MARK_END)
    new_section = "\n".join(lines)

    # Remove any existing section between markers.
    pattern = re.compile(
        re.escape(LLMS_MARK_START) + r".*?" + re.escape(LLMS_MARK_END) + r"\s*",
        re.DOTALL,
    )
    content_stripped = pattern.sub("", content).rstrip()

    # Insert after the existing "## Pages" block. Prefer inserting BEFORE the
    # area-pages marker (if present) so the spot-pages block stays a sibling,
    # not nested inside area-pages. Otherwise fall back to the next "## " heading.
    idx_pages = content_stripped.find("## Pages")
    if idx_pages != -1:
        idx_area_start = content_stripped.find("<!-- area-pages:start -->", idx_pages)
        m_next_h2 = re.search(r"\n## ", content_stripped[idx_pages + 1 :])
        candidates: List[int] = []
        if idx_area_start != -1:
            candidates.append(idx_area_start)
        if m_next_h2:
            candidates.append(idx_pages + 1 + m_next_h2.start())
        if candidates:
            insert_at = min(candidates)
            new_content = (
                content_stripped[:insert_at]
                + "\n"
                + new_section
                + "\n"
                + content_stripped[insert_at:]
            )
        else:
            new_content = content_stripped + "\n" + new_section + "\n"
    else:
        new_content = content_stripped + "\n" + new_section + "\n"

    new_content = re.sub(r"\n{3,}", "\n\n", new_content)
    if not new_content.endswith("\n"):
        new_content += "\n"

    with open(LLMS, "w", encoding="utf-8") as f:
        f.write(new_content)


def main() -> int:
    with open(SPOTS_JSON, "r", encoding="utf-8") as f:
        spots = json.load(f)
    if not spots:
        raise RuntimeError("spots.json is empty")

    os.makedirs(OUT_DIR, exist_ok=True)
    written: List[str] = []
    for spot in spots:
        slug = slugify(spot["name"])
        out_path = os.path.join(OUT_DIR, f"{spot['id']}-{slug}.html")
        html = render_spot_page(spot)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append(out_path)

    url_count = rewrite_sitemap(spots)
    rewrite_llms(spots)

    print(f"wrote {len(written)} spot pages → {OUT_DIR}/")
    print(f"sitemap.xml: {url_count} <url> entries")
    print(f"llms.txt updated with {len(spots)} spot URLs")
    print(f"sample: {written[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
