"""City Council (Chicago City Clerk eLMS) approvals of lawsuit settlements/judgments, introduced 2024-01-01 onward.

API: https://api.chicityclerkelms.chicago.gov (anonymous). Working pagination: GET /matter?search=<q>&top=100&skip=N
(response meta = {skip, top, count, pages}; `page`/`pageNumber`/`limit`/`offset` are silently ignored; category
params are ignored too, so we harvest by several search terms and filter matterCategory client-side).
Human page: https://chicityclerkelms.chicago.gov/Matter/?matterId=<id>.
Amounts live only in attached PDFs (not OCR'd): amount is non-null only when a $ figure appears in the title.
Output: data/raw/council_settlements.json (gitignored; titles may hold plaintiff names -> title_redacted too).
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from .casekey import case_keys_in
except ImportError:  # run as a script
    from casekey import case_keys_in

API = "https://api.chicityclerkelms.chicago.gov"
HUMAN = "https://chicityclerkelms.chicago.gov/Matter/?matterId="
SINCE = "2024-01-01"
OUT = Path(__file__).resolve().parents[3] / "data" / "raw" / "council_settlements.json"
QUERIES = ["settlement", "settlement agreement regarding case", "cited as", "et al", "lawsuit", "judgment",
           "v. City of Chicago", "Officer", "Detective", "wrongful conviction", "police misconduct"]
MIN_INTERVAL = 0.3  # s -> <= ~3.3 req/s

_last = [0.0]

_POLICE = re.compile(
    r"\b(chicago police|police department|police officer|police|CPD|officers?|detectives?|sergeants?|lieutenants?|"
    r"patrol(?:man|men)?|deputy superintendent|superintendent)\b", re.I)
_COVER = re.compile(r"judgment and settlement report", re.I)
_AMOUNT = re.compile(r"\$\s*([\d]{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?(?:\s*(million|thousand))?", re.I)
_VS = re.compile(r"\s(?:v\.|vs\.?)\s", re.I)


def police_signal(text: str | None) -> tuple[bool, str | None]:
    """(flag, matched phrase). Title-only heuristic: absence is NOT proof of a non-police case."""
    m = _POLICE.search(text or "")
    return (True, m.group(0)) if m else (False, None)


def is_cover_report(title: str | None, category: str | None = None) -> bool:
    return bool(_COVER.search(title or "")) or "Report of Settlements" in (category or "")


def parse_amount(text: str | None) -> float | None:
    """First $ amount in text (handles 1,234.50, '$2 million'); None if absent."""
    m = _AMOUNT.search(text or "")
    if not m:
        return None
    v = float(m.group(1).replace(",", "") + ("." + m.group(2) if m.group(2) else ""))
    unit = (m.group(3) or "").lower()
    return v * {"million": 1e6, "thousand": 1e3}.get(unit, 1)


def redact_title(title: str | None) -> str:
    """Replace the text before ' v. '/' vs. ' with '[plaintiff]', keeping a leading 'regarding case of' phrase."""
    t = title or ""
    m = _VS.search(t)
    if not m:
        return t
    head = t[:m.start()]
    lead = re.search(r"^(.*?\bcase of\s+)", head, re.I)
    return (lead.group(1) if lead else "") + "[plaintiff]" + t[m.start():]


def _get(path: str, tries: int = 5):
    for i in range(tries):
        wait = MIN_INTERVAL - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(API + path, headers={"User-Agent": "cpd-qcic/1.0"}), timeout=60) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def _harvest(max_pages: int = 10) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for q in QUERIES:
        dry = 0
        for page in range(max_pages):
            d = _get(f"/matter?search={urllib.parse.quote(q)}&top=100&skip={page * 100}")
            rows = d.get("data") or []
            new = 0
            for m in rows:
                if "LAWSUITS/SETTLEMENTS" in (m.get("matterCategory") or "") and m["matterId"] not in found:
                    found[m["matterId"]] = m
                    new += 1
            dry = 0 if new else dry + 1
            if len(rows) < 100 or dry >= 2:
                break
    return found


def _final_date(m: dict) -> tuple[str | None, str | None]:
    for key, kind in (("finalActionDate", "final_action"), ("introductionDate", "introduced")):
        if m.get(key):
            return m[key][:10], kind
    return None, None


def record(m: dict) -> dict:
    title = m.get("title") or ""
    date, kind = _final_date(m)
    flag, phrase = police_signal(title)
    return {
        "matter_id": m["matterId"], "record_number": m.get("recordNumber"),
        "date": date, "date_kind": kind, "introduced": (m.get("introductionDate") or "")[:10] or None,
        "final_action": (m.get("finalActionDate") or "")[:10] or None,
        "status": m.get("status"), "sub_status": m.get("subStatus"), "category": m.get("matterCategory"),
        "title": title, "title_redacted": redact_title(title),
        "case_keys": case_keys_in(title), "amount": parse_amount(title),
        "url": HUMAN + m["matterId"], "police_signal": flag, "police_phrase": phrase,
    }


def fetch(out: Path = OUT) -> dict:
    found = _harvest()
    matters, n_reports = [], 0
    for m in found.values():
        d = (m.get("introductionDate") or "")[:10]
        if not d or d < SINCE:
            continue
        if is_cover_report(m.get("title"), m.get("matterCategory")):
            n_reports += 1
            continue
        matters.append(record(m))
    matters.sort(key=lambda r: (r["date"] or "", r["record_number"] or ""), reverse=True)
    res = {"fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"), "n_reports": n_reports, "matters": matters}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


if __name__ == "__main__":
    r = fetch()
    print(len(r["matters"]), "matters;", r["n_reports"], "cover reports")
