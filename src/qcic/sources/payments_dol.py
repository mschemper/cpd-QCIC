"""City DOL Judgment & Settlement Payment Requests (Finance Cmte xlsx), 2024-latest, POLICE rows only.
Stdlib only (xlsx parsed via zipfile + ElementTree) -> data/raw/payments_dol.json.
Run: python3 -m src.qcic.sources.payments_dol
"""
from __future__ import annotations

import datetime as dt
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from .casekey import case_key
except ImportError:  # run as a script
    from casekey import case_key  # type: ignore

INDEX = "https://www.chicago.gov/city/en/depts/dol/supp_info/judgment-and-settlement-payments-requests.html"
BASE = "https://www.chicago.gov"
YEARS = (2024, 2025, 2026)
OUT = Path(__file__).resolve().parents[3] / "data" / "raw" / "payments_dol.json"
UA = {"User-Agent": "Mozilla/5.0 (cpd-qcic/1 public-records research)"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _get(url: str, tries: int = 5) -> bytes:
    err = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = e
            time.sleep(2 ** i)
    raise RuntimeError(f"GET failed {url}: {err}")


# ---------- links ----------
def _name_date(name: str):
    """Sortable (month, day) of 'through 8.31.26' style names; (0,0) if none."""
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", name)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def pick_links(html: str, years=YEARS) -> list[str]:
    """Latest xlsx URL per year. Year from the 'YYYY JS' in the name, else the directory."""
    best: dict[int, tuple] = {}
    for h in re.findall(r'href="([^"]*\.xlsx[^"]*)"', html, re.I):
        path = urllib.parse.unquote(h)
        base = path.rsplit("/", 1)[-1]
        m = re.search(r"(20\d\d)\s*JS", base) or re.search(r"(20\d\d)", base) or re.search(r"/(20\d\d)/", path)
        if not m or int(m.group(1)) not in years:
            continue
        y = int(m.group(1))
        url = BASE + urllib.parse.quote(path) if h.startswith("/") else h
        key = (_name_date(base), html.find(h))
        if y not in best or key[0] > best[y][0][0]:
            best[y] = (key, url)
    return [best[y][1] for y in sorted(best)]


# ---------- xlsx ----------
def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def _text(el) -> str:
    return "".join(t.text or "" for t in el.iter(M + "t"))


def read_sheet(data: bytes, sheet: str = "A") -> list[list]:
    """Rows (lists; None = empty) of the named sheet (case-insensitive), else the first sheet."""
    z = zipfile.ZipFile(io.BytesIO(data))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    sheets = [(s.get("name"), rels[s.get(RNS + "id")]) for s in wb.find("m:sheets", NS)]
    target = next((t for n, t in sheets if n.strip().upper() == sheet.upper()), sheets[0][1])
    target = target.lstrip("/")
    path = target if target.startswith("xl/") else "xl/" + target
    rows = []
    for r in ET.fromstring(z.read(path)).iter(M + "row"):
        cells: dict[int, object] = {}
        for c in r.findall("m:c", NS):
            t, v = c.get("t"), c.find("m:v", NS)
            if t == "inlineStr":
                val = _text(c.find("m:is", NS))
            elif v is None or v.text is None:
                continue
            elif t == "s":
                val = shared[int(v.text)]
            elif t in ("str", "e", "b"):
                val = v.text
            else:
                try:
                    f = float(v.text)
                    val = int(f) if f == int(f) and "." not in v.text and "E" not in v.text.upper() else f
                except ValueError:
                    val = v.text
            cells[_col(c.get("r"))] = val
        if cells:
            row = [None] * (max(cells) + 1)
            for k, val in cells.items():
                row[k] = val
            rows.append(row)
    return rows


# ---------- field parsing ----------
def money(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = re.sub(r"[^\d.]", "", s)
    try:
        x = float(s)
    except ValueError:
        return None
    return -x if neg else x


def to_date(v) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        if not 20000 < v < 80000:
            return None
        return (dt.date(1899, 12, 30) + dt.timedelta(days=int(v))).isoformat()
    s = str(v).strip()
    if re.fullmatch(r"\d{5}(\.\d+)?", s):
        return to_date(float(s))
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _norm(h) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(h or "").upper()).strip()


FIELDS = {  # field -> predicate on normalised header
    "case_no": lambda h: h.startswith("CASE"),
    "payee": lambda h: h.startswith("PAYEE"),
    "amount": lambda h: h.startswith("PAYMENT") or h in ("AMOUNT", "PAYMENT AMOUNT"),
    "fees": lambda h: h.startswith("FEES"),
    "cause": lambda h: "CAUSE" in h,
    "dept": lambda h: "DEPARTMENT" in h or h == "DEPT",
    "disposition": lambda h: h.startswith("DISPOSITION"),
    "date": lambda h: "COMPTROLLER" in h or h == "DATE",
}


def parse_rows(grid: list[list]) -> list[dict]:
    """POLICE rows from a sheet grid; header row located by content."""
    hi, cols = None, {}
    for i, row in enumerate(grid):
        found = {}
        for j, cell in enumerate(row):
            h = _norm(cell)
            for f, pred in FIELDS.items():
                if f not in found and h and pred(h):
                    found[f] = j
        if {"case_no", "dept", "amount"} <= set(found):
            hi, cols = i, found
            break
    if hi is None:
        return []
    out = []
    for row in grid[hi + 1:]:
        def g(f):
            j = cols.get(f)
            return row[j] if j is not None and j < len(row) else None
        if str(g("dept") or "").strip().upper() != "POLICE":
            continue
        case_no = re.sub(r"\s+", " ", str(g("case_no") or "")).strip()
        d = to_date(g("date"))
        out.append({
            "case_no": case_no,
            "key": case_key(case_no),
            "payee": re.sub(r"\s+", " ", str(g("payee") or "")).strip(),
            "amount": money(g("amount")),
            "fees": money(g("fees")),
            "cause": str(g("cause") or "").strip(),
            "disposition": str(g("disposition") or "").strip(),
            "date": d,
            "year": int(d[:4]) if d else None,
        })
    return out


def parse_xlsx(data: bytes) -> list[dict]:
    return parse_rows(read_sheet(data, "A"))


def dedupe(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        k = (r["case_no"], r["date"], r["amount"], r["fees"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def fetch(out: Path = OUT) -> dict:
    html = _get(INDEX).decode("utf8", "replace")
    links = pick_links(html)
    if not links:
        raise RuntimeError("no xlsx links found on DOL payments page")
    rows = []
    for u in links:
        rows += parse_xlsx(_get(u))
    rows = dedupe(rows)
    dates = [r["date"] for r in rows if r["date"]]
    res = {"asof": max(dates) if dates else None, "files": links, "rows": rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    return res


def main() -> int:
    res = fetch()
    by: dict = {}
    for r in res["rows"]:
        n, a, f = by.get(r["year"], (0, 0.0, 0.0))
        by[r["year"]] = (n + 1, a + (r["amount"] or 0), f + (r["fees"] or 0))
    print("asof", res["asof"], "files", len(res["files"]), "rows", len(res["rows"]),
          "key None", sum(1 for r in res["rows"] if r["key"] is None))
    for y in sorted(by, key=lambda k: (k is None, k)):
        n, a, f = by[y]
        print(f"{y}: n={n} amount=${a:,.2f} fees=${f:,.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
