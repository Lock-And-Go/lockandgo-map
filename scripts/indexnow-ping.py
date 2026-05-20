#!/usr/bin/env python3
"""IndexNow ping — notify Bing/Yandex/Seznam of new or updated URLs.

Usage:
  python3 scripts/indexnow-ping.py                # ping all URLs from sitemap.xml
  python3 scripts/indexnow-ping.py URL [URL ...]  # ping specific URLs

Google does not support IndexNow yet (as of mid-2026). For Google, submit
sitemap via Search Console manually.

Spec: https://www.indexnow.org/documentation
"""
import json
import re
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = "8e0f424d53f3b944204762bdc7e87310"
HOST = "lockandgo.sk"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/IndexNow"


def load_urls_from_sitemap():
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.exists():
        print(f"!! sitemap.xml not found at {sitemap}", file=sys.stderr)
        return []
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(sitemap)
    root = tree.getroot()
    return [loc.text.strip() for loc in root.findall("sm:url/sm:loc", ns)]


def ping(urls):
    if not urls:
        print("Nothing to ping.")
        return 0

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "LockAndGo IndexNow Pinger/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.status
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        code = e.code
        text = e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        print(f"!! Network error: {e}", file=sys.stderr)
        return 2

    print(f"HTTP {code} — submitted {len(urls)} URL(s)")
    if text.strip():
        print(text[:300])

    # Per IndexNow spec:
    #   200 = submitted
    #   202 = accepted, will be processed
    #   400 = bad request
    #   403 = key not validated (check keyLocation hosts the key)
    #   422 = some URLs invalid (wrong host)
    #   429 = too many requests (rate limit)
    if code in (200, 202):
        return 0
    return 1


def main():
    urls = sys.argv[1:] or load_urls_from_sitemap()
    # Filter to URLs on our host
    urls = [u for u in urls if HOST in u]
    print(f"→ Pinging IndexNow for {len(urls)} URL(s) on {HOST}")
    for u in urls[:5]:
        print(f"   {u}")
    if len(urls) > 5:
        print(f"   … and {len(urls) - 5} more")
    sys.exit(ping(urls))


if __name__ == "__main__":
    main()
