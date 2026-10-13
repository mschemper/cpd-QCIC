"""Download every source into data/raw/ (cached; --refresh re-downloads).

Sources and their caveats: docs/DATA.md.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
SOCRATA = "https://data.cityofchicago.org/resource/{id}.json"
UA = {"User-Agent": "cpd-qcic/1 (public-records research)"}

PAYROLL = "dawh-m56b"   # Employee Payroll Data (FMPS Payroll Costing)
ROSTER = "xzkq-xp2w"    # Current Employee Names, Salaries (parent of r5jy-3eix)
COPA = "mft5-nfa8"      # COPA Cases - Summary (no officer names)
BIA = "t7km-zpxd"       # BIA Cases - By Involved Officer (no officer names)
DISTRICTS = "24zt-jpfn"  # Boundaries - Police Districts (current), GeoJSON
CPDP_ZIP = ("https://media.githubusercontent.com/media/invinst/"
            "chicago-police-data/master/data/unified_data.zip")
CPDP_API = "https://api.cpdp.co/api/v2/officers/{id}/summary/"
UNIFIED_MEMBERS = (
    "unified_data/officers/final-profiles.csv",
    "unified_data/unit-history/unit-history.csv",
    "unified_data/unit-history/unit_reference.csv",
    "unified_data/complaints/complaints-accused.csv",
    "unified_data/complaints/complaints-complaints.csv",
)


def get(url: str, params: dict | None = None, timeout: int = 180) -> bytes:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network: retry with backoff
            if attempt == 4 or getattr(e, "code", 0) in (400, 403, 404):
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def soql(dataset: str, query: str, page: int = 1000) -> list[dict]:
    rows: list[dict] = []
    while True:
        q = f"{query} LIMIT {page} OFFSET {len(rows)}"
        batch = json.loads(get(SOCRATA.format(id=dataset), {"$query": q}))
        rows += batch
        print(f"    {dataset}: {len(rows)} rows", file=sys.stderr)
        if len(batch) < page:
            return rows


def write_json(name: str, obj) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / name).write_text(json.dumps(obj))
    print(f"  {name}: {len(obj) if hasattr(obj, '__len__') else ''}", file=sys.stderr)


def fetch_payroll(year: int, page: int = 100000) -> None:
    """Raw CSV rows (fast; server GROUP BY is ~1k rows/min), summed locally per employee/title/element."""
    agg: dict[tuple, float] = {}
    n = 0
    while True:
        blob = get(SOCRATA.format(id=PAYROLL).replace(".json", ".csv"), {
            "$select": "employee_dataset_id,employee,title,pay_element,amount",
            "$where": f"department_code='D57' AND payroll_year='{year}'",
            "$order": ":id", "$limit": page, "$offset": n}, timeout=600)
        rows = list(csv.DictReader(io.StringIO(blob.decode("utf-8"))))
        for r in rows:
            k = (r["employee_dataset_id"], r["employee"], r["title"], r["pay_element"])
            agg[k] = agg.get(k, 0.0) + float(r["amount"] or 0)
        n += len(rows)
        print(f"    {PAYROLL}: {n} raw rows", file=sys.stderr)
        if len(rows) < page:
            break
    write_json(f"payroll_{year}.json", [
        {"employee_dataset_id": k[0], "employee": k[1], "title": k[2], "pay_element": k[3],
         "amount": round(v, 2)} for k, v in sorted(agg.items())])


def fetch_roster() -> None:
    write_json("roster.json", soql(ROSTER, (
        "SELECT name, job_titles, full_or_part_time, salary_or_hourly, annual_salary, "
        "typical_hours, hourly_rate WHERE department='CHICAGO POLICE DEPARTMENT' ORDER BY name")))


def fetch_oversight() -> None:
    # Officer-anonymous city feeds: counts by district (beat -> first 2 digits) and year.
    for name, ds in (("copa", COPA), ("bia", BIA)):
        write_json(f"{name}_by_beat.json", soql(ds, (
            "SELECT beat, date_extract_y(complaint_date) AS year, count(*) AS n "
            "GROUP BY beat, year ORDER BY beat, year")))


def fetch_districts() -> None:
    write_json("districts.geojson", json.loads(get(
        f"https://data.cityofchicago.org/resource/{DISTRICTS}.geojson")))


def unified_via_git() -> bytes:
    """Fallback when raw GitHub URLs are blocked: sparse shallow clone of data/ only."""
    import subprocess
    dst = RAW / "_invinst"
    if not (dst / ".git").exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse",
                        "https://github.com/invinst/chicago-police-data", str(dst)],
                       check=True, env={**__import__("os").environ, "GIT_LFS_SKIP_SMUDGE": "1"})
        subprocess.run(["git", "-C", str(dst), "sparse-checkout", "set", "--no-cone",
                        "/data/unified_data.zip"], check=True)
    return (dst / "data" / "unified_data.zip").read_bytes()


def fetch_unified() -> None:
    try:
        blob = get(CPDP_ZIP, timeout=600)
    except Exception:
        blob = unified_via_git()
    z = zipfile.ZipFile(io.BytesIO(blob))
    out = RAW / "cpdp"
    out.mkdir(parents=True, exist_ok=True)
    for m in UNIFIED_MEMBERS:
        (out / Path(m).name).write_bytes(z.read(m))
        print(f"  cpdp/{Path(m).name}", file=sys.stderr)


def fetch_lawsuits(workers: int = 4) -> None:
    """CPDP officer summaries (lawsuit payout totals) for active officers. Resumable."""
    profiles = RAW / "cpdp" / "final-profiles.csv"
    ids = [r["officer_id"] for r in csv.DictReader(profiles.open())
           if r["current_status"] == "1" and r["officer_id"]]
    path = RAW / "cpdp_summaries.json"
    done: dict = json.loads(path.read_text()) if path.exists() else {}
    todo = [i for i in ids if i not in done or "error" in done[i]]
    print(f"  cpdp summaries: {len(done)} cached, {len(todo)} to fetch", file=sys.stderr)

    def one(i: str):
        try:
            s = json.loads(get(CPDP_API.format(id=i), timeout=60))
        except Exception as e:
            return i, {"error": str(e)[:80]}
        keep = ("total_lawsuit_settlements", "allegation_count", "sustained_count",
                "discipline_count", "trr_count", "unit", "rank", "badge", "full_name")
        return i, {k: s.get(k) for k in keep}

    with ThreadPoolExecutor(workers) as pool:
        for n, (i, s) in enumerate(pool.map(one, todo), 1):
            done[i] = s
            if n % 500 == 0:
                path.write_text(json.dumps(done))
                print(f"    {n}/{len(todo)}", file=sys.stderr)
    path.write_text(json.dumps(done))


OUTPUTS = {"payroll": "payroll_{year}.json", "roster": "roster.json",
           "oversight": "bia_by_beat.json", "districts": "districts.geojson",
           "unified": "cpdp/complaints-complaints.csv", "units": "units_recent.json",
           "lawsuits_recent": "lawsuits_recent.json"}

def fetch_units_recent() -> None:
    from .sources import units_recent
    units_recent.fetch()


def fetch_lawsuits_recent() -> None:
    from .sources import lawsuits_recent
    lawsuits_recent.fetch()


STEPS = {"payroll": None, "roster": fetch_roster, "oversight": fetch_oversight,
         "districts": fetch_districts, "unified": fetch_unified, "units": fetch_units_recent,
         "lawsuits_recent": fetch_lawsuits_recent, "lawsuits": fetch_lawsuits}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("steps", nargs="*", default=list(STEPS))
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--only-missing", action="store_true", help="skip steps whose output exists")
    a = ap.parse_args(argv)
    for s in a.steps:
        out = OUTPUTS.get(s, "").format(year=a.year)
        if a.only_missing and out and (RAW / out).exists():
            print(f"fetch {s}: cached", file=sys.stderr)
            continue
        t = time.time()
        print(f"fetch {s}", file=sys.stderr)
        fetch_payroll(a.year) if s == "payroll" else STEPS[s]()
        print(f"fetch {s}: {time.time() - t:.0f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
