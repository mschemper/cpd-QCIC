"""Normalise court case numbers across DOL reports, DOL payment xlsx, and Council (eLMS) titles.

'2021 C 06001', '21-cv-6001', '21 CV 6001', '21cv06001' -> '21-6001'.  State cases keep a court letter:
'21-L-5264', '2021 L 005264' -> '21-L-5264'. Unparseable -> None (never guess).
"""
from __future__ import annotations

import re

_PAT = re.compile(r"(?<!\d)(\d{4}|\d{2})\s*[-\s]?\s*(CV|C|L|M|D|CH|LA)?\s*[-\s]?\s*0*(\d{1,6})(?!\d)", re.I)


def case_key(s: str | None) -> str | None:
    if not s:
        return None
    m = _PAT.search(s.strip())
    if not m:
        return None
    yy, court, num = m.group(1)[-2:], (m.group(2) or "").upper(), m.group(3)
    if court in ("", "C", "CV"):
        return f"{yy}-{int(num)}"
    return f"{yy}-{court}-{int(num)}"


def case_keys_in(text: str) -> list[str]:
    """All case keys cited in free text, e.g. 'cited as 18 CV 1028'."""
    out = []
    for m in re.finditer(r"(?<!\d)(\d{4}|\d{2})\s*[-\s]?\s*(CV|C|L)\s*[-\s]?\s*0*(\d{1,6})(?!\d)", text or "", re.I):
        k = case_key(m.group(0))
        if k and k not in out:
            out.append(k)
    return out
