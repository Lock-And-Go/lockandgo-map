#!/usr/bin/env python3
"""Extract the SPOTS array from /app.html and write data/spots.json.

The SPOTS array is a JS literal with: single-quoted strings, unquoted keys,
trailing commas, /* ... */ comments, null/true/false, and a constant reference
to STANDARD_PRICE (5.90). We convert that JS literal into strict JSON in pure
Python 3 (stdlib only).
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_HTML = os.path.join(ROOT, "app.html")
OUT_JSON = os.path.join(ROOT, "data", "spots.json")

STANDARD_PRICE = 5.90


def read_app_html() -> str:
    with open(APP_HTML, "r", encoding="utf-8") as f:
        return f.read()


def find_spots_literal(html: str) -> str:
    """Return the JS array literal (including outer brackets) for `const SPOTS = [...]`."""
    m = re.search(r"const\s+SPOTS\s*=\s*\[", html)
    if not m:
        raise RuntimeError("Could not find `const SPOTS = [` in app.html")
    start = m.end() - 1  # position of the opening `[`
    depth = 0
    i = start
    n = len(html)
    in_str: str | None = None  # active quote char if inside a string
    in_block_comment = False
    in_line_comment = False
    while i < n:
        c = html[i]
        nxt = html[i + 1] if i + 1 < n else ""
        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if c == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_str is not None:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        # not in str / comment
        if c == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if c == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if c in ("'", '"', "`"):
            in_str = c
            i += 1
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return html[start : i + 1]
        i += 1
    raise RuntimeError("Unterminated SPOTS array")


def strip_comments(src: str) -> str:
    """Remove /* block */ and // line comments outside of strings."""
    out: List[str] = []
    i = 0
    n = len(src)
    in_str: str | None = None
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if in_str is not None:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(nxt)
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            if j == -1:
                raise RuntimeError("Unterminated block comment")
            i = j + 2
            continue
        if c == "/" and nxt == "/":
            j = src.find("\n", i + 2)
            i = j + 1 if j != -1 else n
            continue
        if c in ("'", '"', "`"):
            in_str = c
        out.append(c)
        i += 1
    return "".join(out)


def tokenize_value(src: str, i: int) -> Tuple[Any, int]:
    """Parse a JS value starting at src[i]. Returns (value, next_index)."""
    n = len(src)
    # skip whitespace
    while i < n and src[i] in " \t\r\n":
        i += 1
    if i >= n:
        raise RuntimeError("Unexpected EOF parsing value")
    c = src[i]
    if c == "{":
        return parse_object(src, i)
    if c == "[":
        return parse_array(src, i)
    if c in ("'", '"', "`"):
        return parse_string(src, i)
    # number, identifier, or keyword
    return parse_literal(src, i)


def parse_string(src: str, i: int) -> Tuple[str, int]:
    quote = src[i]
    i += 1
    out: List[str] = []
    n = len(src)
    while i < n:
        c = src[i]
        if c == "\\":
            nxt = src[i + 1] if i + 1 < n else ""
            esc_map = {
                "n": "\n",
                "t": "\t",
                "r": "\r",
                "\\": "\\",
                "'": "'",
                '"': '"',
                "`": "`",
                "/": "/",
                "b": "\b",
                "f": "\f",
            }
            if nxt in esc_map:
                out.append(esc_map[nxt])
                i += 2
                continue
            if nxt == "u" and i + 5 < n:
                hexs = src[i + 2 : i + 6]
                out.append(chr(int(hexs, 16)))
                i += 6
                continue
            if nxt == "x" and i + 3 < n:
                hexs = src[i + 2 : i + 4]
                out.append(chr(int(hexs, 16)))
                i += 4
                continue
            # generic: drop backslash, keep next
            out.append(nxt)
            i += 2
            continue
        if c == quote:
            return "".join(out), i + 1
        out.append(c)
        i += 1
    raise RuntimeError("Unterminated string")


def parse_literal(src: str, i: int) -> Tuple[Any, int]:
    n = len(src)
    j = i
    # Read until we hit a terminator outside of nested structures.
    while j < n and src[j] not in ",}]\n":
        # also stop on closing braces/brackets
        if src[j] in " \t\r":
            # trim trailing whitespace later
            j += 1
            continue
        j += 1
    raw = src[i:j].strip()
    # Trim trailing whitespace tokens
    raw = raw.rstrip()
    if raw == "":
        raise RuntimeError(f"Empty literal at index {i}")
    if raw == "null":
        return None, j
    if raw == "true":
        return True, j
    if raw == "false":
        return False, j
    if raw == "undefined":
        return None, j
    if raw == "STANDARD_PRICE":
        return STANDARD_PRICE, j
    # number? (int or float; allow leading +/-)
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", raw):
        if "." in raw or "e" in raw or "E" in raw:
            return float(raw), j
        return int(raw), j
    raise RuntimeError(f"Unrecognised literal: {raw!r}")


def parse_key(src: str, i: int) -> Tuple[str, int]:
    n = len(src)
    while i < n and src[i] in " \t\r\n":
        i += 1
    if i >= n:
        raise RuntimeError("Unexpected EOF parsing key")
    if src[i] in ("'", '"', "`"):
        return parse_string(src, i)
    j = i
    while j < n and (src[j].isalnum() or src[j] in "_$"):
        j += 1
    if j == i:
        raise RuntimeError(f"Expected identifier at index {i}: {src[i:i+20]!r}")
    return src[i:j], j


def parse_object(src: str, i: int) -> Tuple[dict, int]:
    assert src[i] == "{"
    i += 1
    n = len(src)
    out: dict = {}
    while True:
        while i < n and src[i] in " \t\r\n,":
            i += 1
        if i >= n:
            raise RuntimeError("Unterminated object")
        if src[i] == "}":
            return out, i + 1
        key, i = parse_key(src, i)
        while i < n and src[i] in " \t\r\n":
            i += 1
        if i >= n or src[i] != ":":
            raise RuntimeError(f"Expected ':' after key {key!r} at index {i}")
        i += 1
        value, i = tokenize_value(src, i)
        out[key] = value


def parse_array(src: str, i: int) -> Tuple[list, int]:
    assert src[i] == "["
    i += 1
    n = len(src)
    out: list = []
    while True:
        while i < n and src[i] in " \t\r\n,":
            i += 1
        if i >= n:
            raise RuntimeError("Unterminated array")
        if src[i] == "]":
            return out, i + 1
        value, i = tokenize_value(src, i)
        out.append(value)


def parse_js_array(src: str) -> list:
    src = strip_comments(src)
    value, i = parse_array(src, 0)
    # ensure only whitespace after
    rest = src[i:].strip()
    if rest:
        raise RuntimeError(f"Trailing content after array: {rest[:60]!r}")
    return value


def main() -> int:
    html = read_app_html()
    literal = find_spots_literal(html)
    spots = parse_js_array(literal)
    if not isinstance(spots, list):
        raise RuntimeError("SPOTS literal did not parse to a list")

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(spots)} spots → {OUT_JSON}")
    if spots:
        sample = spots[0]
        print("Sample spot[0]:")
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        last = spots[-1]
        print(f"Sample spot[-1] id={last.get('id')!r} name={last.get('name')!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
