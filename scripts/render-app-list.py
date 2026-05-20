#!/usr/bin/env python3
"""Inject a crawlable, visually-hidden <section id="spots-prerendered"> into
/app.html and /en/app.html.

The block is rendered in raw HTML so search engines and AI bots can read every
spot without executing JavaScript. It is visually clipped using a screen-reader
pattern (clip-path: inset(50%)) so it doesn't break the existing map UX.

Idempotent: re-running replaces any existing <section id="spots-prerendered">
block instead of duplicating it. Insertion anchor: just before </main>.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS_JSON = os.path.join(ROOT, "data", "spots.json")
TARGETS = [
    (os.path.join(ROOT, "app.html"), "sk"),
    (os.path.join(ROOT, "en", "app.html"), "en"),
]

LABELS = {
    "sk": {
        "heading": "Všetky úschovne batožiny v Bratislave",
        "intro": "Statický zoznam všetkých 32 úschovní pre vyhľadávače a AI asistentov. Interaktívnu mapu nájdeš vyššie.",
        "area": "Lokalita",
        "address": "Adresa",
        "price": "Cena",
        "hours": "Otváracie hodiny",
        "provider": "Prevádzkovateľ",
        "rating": "Hodnotenie",
        "details": "Detail spotu",
        "open_247": "24/7",
        "from": "od",
        "per_day": "/deň",
        "currency": "€",
    },
    "en": {
        "heading": "All luggage storage spots in Bratislava",
        "intro": "Static listing of all 32 spots for search engines and AI assistants. The interactive map is above.",
        "area": "Area",
        "address": "Address",
        "price": "Price",
        "hours": "Opening hours",
        "provider": "Operator",
        "rating": "Rating",
        "details": "Spot details",
        "open_247": "24/7",
        "from": "from",
        "per_day": "/day",
        "currency": "€",
    },
}

HIDDEN_STYLE = (
    "position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;"
    "clip:rect(0 0 0 0);clip-path:inset(50%);white-space:normal;border:0;"
)

MARK_START = "<!-- spots-prerendered:start -->"
MARK_END = "<!-- spots-prerendered:end -->"


def slugify(name: str) -> str:
    """ASCII-safe kebab-case slug for spot names."""
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


def format_price(spot: Dict[str, Any], labels: Dict[str, str]) -> str:
    price = spot.get("price")
    details = spot.get("priceDetails")
    if details:
        first_line = details.split("\n", 1)[0].strip()
        return first_line
    if price is None:
        return "—"
    return f"{labels['from']} {price:.2f} {labels['currency']}{labels['per_day']}"


def render_spot(spot: Dict[str, Any], labels: Dict[str, str]) -> str:
    name = html_escape(spot["name"])
    slug = slugify(spot["name"])
    detail_url = f"/spot/{spot['id']}-{slug}"
    area = html_escape(spot.get("area", ""))
    address = html_escape(spot.get("address", "")) if spot.get("address") else ""
    hours_display = html_escape((spot.get("hours") or {}).get("display", ""))
    provider = html_escape(spot.get("providerLabel", "")) if spot.get("providerLabel") else ""
    price_txt = html_escape(format_price(spot, labels))

    rating = spot.get("rating")
    reviews = spot.get("reviews") or 0
    rating_html = ""
    if rating is not None and reviews:
        rating_html = (
            f"      <dt>{labels['rating']}</dt>"
            f"<dd>{rating:.1f} / 5 ({reviews})</dd>\n"
        )

    address_html = (
        f"      <dt>{labels['address']}</dt><dd>{address}</dd>\n" if address else ""
    )
    provider_html = (
        f"      <dt>{labels['provider']}</dt><dd>{provider}</dd>\n" if provider else ""
    )

    return (
        f'  <article id="prerendered-spot-{spot["id"]}" data-spot-id="{spot["id"]}">\n'
        f"    <h3>{name}</h3>\n"
        f"    <dl>\n"
        f"      <dt>{labels['area']}</dt><dd>{area}</dd>\n"
        f"{address_html}"
        f"      <dt>{labels['price']}</dt><dd>{price_txt}</dd>\n"
        f"      <dt>{labels['hours']}</dt><dd>{hours_display}</dd>\n"
        f"{provider_html}"
        f"{rating_html}"
        f"    </dl>\n"
        f'    <p><a href="{detail_url}">{labels["details"]} →</a></p>\n'
        f"  </article>\n"
    )


def render_block(spots: List[Dict[str, Any]], lang: str) -> str:
    labels = LABELS[lang]
    parts: List[str] = []
    parts.append(MARK_START)
    parts.append(
        f'<section id="spots-prerendered" aria-label="{labels["heading"]}" '
        f'style="{HIDDEN_STYLE}">'
    )
    parts.append(f"  <h2>{labels['heading']}</h2>")
    parts.append(f"  <p>{labels['intro']}</p>")
    for spot in spots:
        parts.append(render_spot(spot, labels))
    parts.append("</section>")
    parts.append(MARK_END)
    return "\n".join(parts) + "\n"


def inject(html: str, block: str) -> str:
    # 1) Remove any prior block between markers (idempotent re-runs).
    pattern = re.compile(
        re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\s*",
        re.DOTALL,
    )
    html = pattern.sub("", html)

    # 2) Also remove any legacy <section id="spots-prerendered"> not wrapped in
    #    our markers, to be safe.
    legacy = re.compile(
        r'<section[^>]*id="spots-prerendered"[^>]*>.*?</section>\s*',
        re.DOTALL | re.IGNORECASE,
    )
    html = legacy.sub("", html)

    # 3) Insert just before </main>.
    if "</main>" not in html:
        raise RuntimeError("Could not find </main> anchor")
    return html.replace("</main>", block + "</main>", 1)


def main() -> int:
    with open(SPOTS_JSON, "r", encoding="utf-8") as f:
        spots = json.load(f)
    if not isinstance(spots, list) or not spots:
        raise RuntimeError("spots.json is empty or invalid")

    for path, lang in TARGETS:
        if not os.path.exists(path):
            print(f"skip (missing): {path}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        block = render_block(spots, lang)
        new_html = inject(html, block)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_html)
        print(f"injected {len(spots)} spots into {path} ({lang})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
