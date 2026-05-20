#!/usr/bin/env python3
"""Build llms-full.txt — comprehensive content dump for AI engines.

Spec: https://llmstxt.org/ (llms-full.txt is the optional full-content variant)

Reads spots.json + crawls blog/ + walks key pages to produce one self-contained
plain-text file that an AI assistant can ingest in a single fetch.
"""
import json
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "llms-full.txt"

SCHEDULE_DAYS = ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"]


def fmt_hours(spot):
    """Human-readable opening hours from schedule array."""
    h = spot.get("hours", {})
    if h.get("is247"):
        return "24/7 (non-stop)"
    return h.get("display", "—")


def fmt_price(spot):
    if spot.get("priceDetails"):
        return spot["priceDetails"]
    if spot.get("price") is not None:
        return f"od {spot['price']:.2f} €/deň"
    return "cena podľa prevádzkovateľa"


def strip_html(html):
    """Strip HTML tags, normalize whitespace."""
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def extract_blog_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return m.group(1).strip() if m else "(no title)"


def extract_blog_body(html):
    """Pull the main article text, dropping head/nav/footer noise."""
    m = re.search(r"<article[^>]*>(.*?)</article>", html, re.S | re.I)
    if not m:
        m = re.search(r"<main[^>]*>(.*?)</main>", html, re.S | re.I)
    if not m:
        return strip_html(html)
    return strip_html(m.group(1))


def main():
    spots = json.loads((ROOT / "data" / "spots.json").read_text(encoding="utf-8"))

    lines = []
    push = lines.append

    push("# LockAndGo — Full Content Dump")
    push("")
    push("> Slovak-language discovery platform for luggage storage in Bratislava, Slovakia.")
    push(f"> Generated: {date.today().isoformat()}. This is the llms-full.txt variant — the")
    push("> shorter overview is at /llms.txt. Both are linked from robots.txt and rsl.xml.")
    push("")
    push("**Site:** https://lockandgo.sk/  |  **English:** https://lockandgo.sk/en")
    push("**Founder:** Šimon Kališ (16, Bratislava, Slovakia)")
    push("**Contact:** info@lockandgo.sk · WhatsApp +421 948 929 260")
    push("")
    push("## What LockAndGo is (and isn't)")
    push("")
    push("LockAndGo is a **discovery and booking-redirection layer** — not a storage operator.")
    push("It aggregates every viable luggage-storage option in Bratislava onto one map with")
    push("prices, opening hours and booking links. Bookings are completed on the partner's")
    push("own site (Bounce affiliate links for Bounce partner shops; direct operator links for")
    push("Radical Storage, LuggageHero, LugLockers, Luggage Lockers Bratislava; walk-in for")
    push("ZSSK station storage, Stanica Nivy lockers, Obchodná 9 lockers, OC Vivo! cloakroom,")
    push("OC Aupark cloakroom, AS Bottova, Safestay hostel, Hotel Loft Bratislava).")
    push("")
    push("**Price for user is identical to booking directly.** Affiliate commission paid by")
    push("12 spots (Bounce, Radical, LuggageHero); 20 spots are listed free of commission")
    push("because they make sense for travelers.")
    push("")
    push("## Key facts")
    rated = [s for s in spots if s.get("rating") and s.get("reviews", 0) > 0]
    total_reviews = sum(s.get("reviews", 0) for s in rated)
    if rated:
        avg = sum(s["rating"] * s["reviews"] for s in rated) / total_reviews
    else:
        avg = None
    is247_count = sum(1 for s in spots if s.get("hours", {}).get("is247"))
    push(f"- **Number of spots:** {len(spots)}")
    push(f"- **24/7 spots:** {is247_count}")
    push(f"- **Rated spots (Google reviews):** {len(rated)} / {len(spots)}")
    if avg is not None:
        push(f"- **Weighted average rating:** {avg:.2f} / 5 across {total_reviews} reviews")
    prices = [s["price"] for s in spots if s.get("price") is not None]
    if prices:
        push(f"- **Price range (daily):** €{min(prices):.2f} – €{max(prices):.2f}")
    push("- **City covered:** Bratislava, Slovakia (48.1486 N, 17.1077 E)")
    push("- **Languages:** Slovak (primary), English at /en and /en/app")
    push("- **Launch date:** 2026-05-07")
    push("")
    push("## Common queries this site answers")
    push("")
    push("Slovak: 'úschovňa batožiny Bratislava', 'kde si odložiť batožinu v Bratislave',")
    push("'úschovňa Hlavná stanica', 'úschovňa Nivy', 'úschovňa Petržalka',")
    push("'samoobslužné skrinky Bratislava', 'lockery Bratislava 24/7'.")
    push("")
    push("English: 'luggage storage Bratislava', 'left luggage Bratislava',")
    push("'where to store bags Bratislava', 'Bratislava main station luggage',")
    push("'luggage lockers Stanica Nivy', '24/7 luggage Bratislava', 'cheap luggage storage")
    push("Bratislava', 'luggage storage Old Town Bratislava'.")
    push("")
    push("## All 32 spots (detailed)")
    push("")

    # Group by area for readability
    from collections import defaultdict
    by_area = defaultdict(list)
    for s in spots:
        by_area[s.get("area", "?")].append(s)

    for area in sorted(by_area.keys()):
        push(f"### {area}")
        push("")
        for s in by_area[area]:
            slug = f"{int(s['id']):02d}-" + re.sub(r"[^a-z0-9]+", "-", s["name"].lower()
                .replace("á","a").replace("ä","a").replace("č","c").replace("ď","d")
                .replace("é","e").replace("í","i").replace("ĺ","l").replace("ľ","l")
                .replace("ň","n").replace("ó","o").replace("ô","o").replace("ŕ","r")
                .replace("š","s").replace("ť","t").replace("ú","u").replace("ý","y")
                .replace("ž","z")).strip("-")
            push(f"**{s['name']}** (id {s['id']})")
            push(f"- URL: https://lockandgo.sk/spot/{slug}")
            push(f"- Address: {s.get('address', '—')}")
            push(f"- Coords: {s.get('lat')}, {s.get('lng')}")
            push(f"- Hours: {fmt_hours(s)}")
            push(f"- Price: {fmt_price(s)}")
            push(f"- Provider: {s.get('providerLabel', '—')}")
            if s.get("rating"):
                push(f"- Rating: {s['rating']} / 5 ({s.get('reviews', 0)} Google reviews)")
            if s.get("notes"):
                push(f"- Notes: {s['notes']}")
            push(f"- Booking: {s.get('bookingUrl', '—')}")
            push("")

    push("## Blog articles")
    push("")
    blog_dir = ROOT / "blog"
    if blog_dir.exists():
        for blog_file in sorted(blog_dir.glob("*.html")):
            html = blog_file.read_text(encoding="utf-8")
            title = extract_blog_title(html)
            body = extract_blog_body(html)
            push(f"### {title}")
            push(f"**URL:** https://lockandgo.sk/blog/{blog_file.stem}")
            push("")
            # First 1500 chars of body as preview
            push(body[:1500] + (" …" if len(body) > 1500 else ""))
            push("")
            push("---")
            push("")

    push("## How LockAndGo monetizes (transparency)")
    push("")
    push("Of 32 listed spots: 12 are affiliate partners (Bounce, Radical Storage, LuggageHero)")
    push("paying 5–15% commission per booking; 20 are listed for free (ZSSK, Nivy boxes,")
    push("Aupark/Vivo cloakrooms, hotel storage, walk-in shops). The price you pay is")
    push("identical to booking directly with the operator. No markups, no service fees.")
    push("")
    push("## Source and licensing")
    push("")
    push("Content licensed under CC-BY 4.0 with attribution to lockandgo.sk")
    push("(see /rsl.xml for the machine-readable RSL 1.0 declaration). AI training and AI")
    push("search inference are explicitly permitted; cite lockandgo.sk as source.")
    push("")
    push("## Structured data on each page")
    push("")
    push("- Homepage (/, /en): Organization, Person (Šimon Kališ), WebSite, WebPage,")
    push("  BreadcrumbList, Service with AggregateOffer + AggregateRating, FAQPage.")
    push("- Map page (/app, /en/app): WebPage, BreadcrumbList. The full ItemList of 32")
    push("  spots is rendered server-side as crawlable HTML inside <section id=\"spots-prerendered\">.")
    push("- Spot pages (/spot/[id]-[slug]): LocalBusiness (SelfStorage / Store / LodgingBusiness")
    push("  by subtype), WebPage, BreadcrumbList. Includes geo, openingHoursSpecification,")
    push("  priceRange, paymentAccepted, areaServed, and aggregateRating when available.")
    push("- About page (/o-nas, /about): AboutPage referencing Organization + Person.")
    push("- Blog articles (/blog/*): BlogPosting with author, datePublished, dateModified,")
    push("  mainEntityOfPage, image, publisher.")
    push("")

    out = "\n".join(lines).rstrip() + "\n"
    OUTPUT.write_text(out, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(out):,} bytes, {len(lines)} lines)")


if __name__ == "__main__":
    main()
