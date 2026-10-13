#!/usr/bin/env python3
"""Page QA for site/index.html (stdlib). Usage: python3 tools/qa_page.py [path]. Exit 1 on failure.

Fails on: colour literals outside the token blocks, gradient, box-shadow,
border-radius other than 50% (0 allowed: resets browser default on controls),
<script src=>, any font-size below 12px.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMED = ("white black red green blue grey gray silver maroon yellow orange purple "
         "pink brown cyan magenta navy teal olive lime aqua fuchsia gold ivory beige "
         "cream tan crimson coral salmon").split()
TOKEN_OPEN = re.compile(r":root(?:\:not\(\[data-theme=light\]\)|\[data-theme=dark\])?\s*\{")


def strip_token_blocks(text):
    """Remove :root{..}, :root[data-theme=dark]{..} and the dark @media block (balanced braces)."""
    out, i, n = [], 0, len(text)
    pat = re.compile(r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{|:root(?:\[data-theme=dark\])?\s*\{")
    while i < n:
        m = pat.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        depth, j = 1, m.end()
        while j < n and depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        i = j
    return "".join(out)


def lineno(text, pos):
    return text.count("\n", 0, pos) + 1


def check(path):
    raw = Path(path).read_text(encoding="utf-8")
    errs = []
    if not re.search(r":root\s*\{", raw):
        errs.append("no :root token block")
    if not re.search(r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*:root:not\(\[data-theme=light\]\)", raw):
        errs.append("missing guarded dark @media block")
    if not re.search(r":root\[data-theme=dark\]\s*\{", raw):
        errs.append("missing :root[data-theme=dark] block")
    if not re.search(r"body\s*\{[^}]*background\s*:", raw):
        errs.append("body has no explicit background")
    body = strip_token_blocks(raw)
    # note: positions refer to `body`; report snippet instead of line numbers
    for m in re.finditer(r"(?<![&\w])#[0-9a-fA-F]{3,8}\b", body):
        errs.append("colour literal outside tokens: " + m.group(0))
    for m in re.finditer(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklch|oklab)\s*\(", body):
        errs.append("colour function outside tokens: " + m.group(0))
    nm = "|".join(NAMED)
    for m in re.finditer(r"(?:color|background|fill|stroke|border[a-z-]*)\s*[:=]\s*[\"']?\s*(?:[0-9.]+px\s+solid\s+)?(%s)\b" % nm, body, re.I):
        errs.append("named colour outside tokens: " + m.group(0))
    if re.search(r"gradient", raw, re.I):
        errs.append("'gradient' present")
    if re.search(r"box-shadow|text-shadow|drop-shadow", raw, re.I):
        errs.append("shadow present")
    for m in re.finditer(r"border(?:-[a-z]+)*-radius\s*:\s*([^;}]+)", raw, re.I):
        v = m.group(1).strip()
        if v not in ("50%", "0", "0px"):
            errs.append("border-radius not 50%%: %s" % v)
    for m in re.finditer(r"<script\b[^>]*\bsrc\s*=", raw, re.I):
        errs.append("external <script src>")
    for m in re.finditer(r"\bimport\s*\(|\bimportScripts\s*\(", raw):
        errs.append("dynamic script import")
    for m in re.finditer(r"font-size\s*:\s*([0-9.]+)\s*px", raw, re.I):
        if float(m.group(1)) < 12:
            errs.append("font-size %spx < 12" % m.group(1))
    for m in re.finditer(r"font-size\s*=\s*[\"']([0-9.]+)", raw, re.I):
        if float(m.group(1)) < 12:
            errs.append("font-size attr %s < 12" % m.group(1))
    return errs


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "site" / "index.html"
    if not path.exists():
        print("qa_page: %s not found" % path)
        return 1
    errs = check(path)
    for e in errs:
        print("FAIL", e)
    print("qa_page: %s" % ("OK" if not errs else "%d problem(s)" % len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
