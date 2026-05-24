#!/usr/bin/env python3
"""Generate brand-aligned QR codes for the printable posters.

Outputs:
- qr/lockandgo-sk.svg → encodes https://lockandgo.sk
- qr/lockandgo-en.svg → encodes https://lockandgo.sk/en

SVG is preferred over PNG: vector, prints at any size, ~1 KB, no CSP issue
(served from self origin), no external CDN dependency.

Re-run any time the URLs change.
"""
import re
from pathlib import Path

import qrcode
import qrcode.image.svg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "qr"
OUT.mkdir(exist_ok=True)

# High error correction (H = ~30%) lets the QR survive a small brand mark
# overlay in the centre. We don't add an overlay here, but this future-proofs
# the choice.
TARGETS = [
    ("lockandgo-sk.svg", "https://lockandgo.sk"),
    ("lockandgo-en.svg", "https://lockandgo.sk/en"),
]


def build_svg(url: str, fg: str = "#1F1F1D", bg: str = "transparent") -> str:
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=0,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(image_factory=factory)

    svg_bytes = img.to_string(encoding="unicode")

    # Patch the SVG so:
    # 1. it has viewBox + width/height 100% (responsive),
    # 2. brand ink colour replaces default black,
    # 3. transparent background by default.
    svg_bytes = re.sub(
        r'<svg[^>]*?>',
        lambda m: (
            m.group(0)
            .replace('width="', 'data-original-width="')
            .replace('height="', 'data-original-height="')
            .replace('<svg', '<svg width="100%" height="100%" preserveAspectRatio="xMidYMid meet"', 1)
        ),
        svg_bytes,
        count=1,
    )
    svg_bytes = svg_bytes.replace('fill="#000000"', f'fill="{fg}"')
    svg_bytes = svg_bytes.replace('fill="black"', f'fill="{fg}"')
    return svg_bytes


for fname, url in TARGETS:
    svg = build_svg(url)
    (OUT / fname).write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT / fname}  ({len(svg):,} bytes, encodes {url!r})")
