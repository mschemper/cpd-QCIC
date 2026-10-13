"""data/raw/ -> site/data.json. Contract: docs/SCHEMA.md. Method: docs/METHOD.md."""
from __future__ import annotations

import csv
import json
import math
import re
import sys
import tomllib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "site" / "data.json"
METRICS = ["total", "ot", "cmp", "law", "frc"]
LABELS = {"frc": "Use-of-force reports (3 yr)", "total": "Total pay", "ot": "Overtime pay", "cmp": "Complaints (5 yr)",
          "law": "Lawsuit payouts (City-paid, cases naming officer)"}
SUFFIXES = {"JR", "SR", "II", "III", "IV", "V"}
SOURCES = [
    {"name": "Employee Payroll Data (FMPS Payroll Costing)",
     "url": "https://data.cityofchicago.org/d/dawh-m56b",
     "note": "Actual pay by pay element; department D57."},
    {"name": "Current Employee Names, Salaries",
     "url": "https://data.cityofchicago.org/d/xzkq-xp2w",
     "note": "Current roster (parent of Current Employees - CPD, r5jy-3eix)."},
    {"name": "COPA Cases - Summary", "url": "https://data.cityofchicago.org/d/mft5-nfa8",
     "note": "No officer names; counted by district."},
    {"name": "BIA Cases - By Involved Officer", "url": "https://data.cityofchicago.org/d/t7km-zpxd",
     "note": "No officer names; counted by district."},
    {"name": "CPD roster Nov 2023 (FOIA p891976, Invisible Institute)",
     "url": "https://github.com/invinst/chicago-police-data/tree/master/individual/roster_1985-2023_2023-11_p891976",
     "note": "Unit assignment per active member; primary location source."},
    {"name": "Invisible Institute, Citizens Police Data Project (unified data)",
     "url": "https://github.com/invinst/chicago-police-data",
     "note": "Named complaints, unit history, officer profiles."},
    {"name": "CPDP officer summaries (lawsuit payouts, Chicago Reporter + Invisible Institute)",
     "url": "https://cpdp.co", "note": "Settlements and judgments linked to named officers."},
    {"name": "City of Chicago Dept. of Law, CPD Annual Litigation Reports (consent decree para. 548)",
     "url": "https://www.chicago.gov/city/en/depts/dol/supp_info/CPDAnnLitReports.html",
     "note": "Settled/litigated cases 2022-2025 with named officer defendants and payouts."},
    {"name": "City of Chicago Dept. of Law, Judgment and Settlement Payment Requests",
     "url": "https://www.chicago.gov/city/en/depts/dol/supp_info/judgment-and-settlement-payments-requests.html",
     "note": "Monthly payments by case, POLICE department rows; plaintiff names not shown."},
    {"name": "Chicago City Clerk eLMS (City Council)", "url": "https://chicityclerkelms.chicago.gov",
     "note": "Council approvals of police lawsuit settlements 2024 onward."},
    {"name": "Boundaries - Police Districts (current)",
     "url": "https://data.cityofchicago.org/d/24zt-jpfn", "note": "District map."},
]


# ---------- names ----------
def norm(s: str | None) -> str:
    return re.sub(r"[^A-Z ]", "", (s or "").upper().replace("-", " ")).strip()


def split_payroll_name(name: str) -> tuple[str, str, str]:
    """'LAST,  FIRST M' -> (last, first, mi)."""
    last, _, rest = name.partition(",")
    last_toks = [t for t in norm(last).split() if t not in SUFFIXES]
    toks = [t for t in norm(rest).split() if t not in SUFFIXES]
    first = toks[0] if toks else ""
    mi = toks[1][0] if len(toks) > 1 else ""
    return "".join(last_toks), first, mi


def profile_key(p: dict) -> tuple[str, str, str]:
    last = "".join(t for t in norm(p["last_name"]).split() if t not in SUFFIXES)
    return last, norm(p["first_name"]).split(" ")[0] if norm(p["first_name"]) else "", norm(p["middle_initial"])[:1]


def match(people: dict[str, tuple], profiles: list[dict]) -> dict[str, dict]:
    """Payroll id -> CPDP profile. Unique-on-both-sides only; see METHOD.md 'Matching'."""
    by3, by2 = defaultdict(list), defaultdict(list)
    for p in profiles:
        k = profile_key(p)
        by3[k].append(p)
        by2[k[:2]].append(p)
    pay3, pay2 = Counter(people.values()), Counter(k[:2] for k in people.values())
    out = {}
    for pid, k in people.items():
        if not k[0] or not k[1]:
            continue
        c3 = by3.get(k, [])
        if len(c3) == 1 and pay3[k] == 1:
            out[pid] = {**c3[0], "_mp": 3}
            continue
        c2 = by2.get(k[:2], [])
        if len(c2) == 1 and pay2[k[:2]] == 1:
            pmi = profile_key(c2[0])[2]
            if not pmi or not k[2] or pmi == k[2]:
                out[pid] = {**c2[0], "_mp": 2}
    return out


# ---------- stats ----------
def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return 0.0 if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def quantile(s: list[float], q: float) -> float:
    if not s:
        return 0.0
    i = q * (len(s) - 1)
    lo = math.floor(i)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def robust_scale(xs: list[float]) -> tuple[float, float]:
    """(median, scale) for z = (x - med) / scale. MAD, else mean-abs-dev fallback (Iglewicz-Hoaglin)."""
    med = median(xs)
    mad = median([abs(x - med) for x in xs])
    if mad > 0:
        return med, mad / 0.6745
    meanad = sum(abs(x - med) for x in xs) / len(xs) if xs else 0
    return med, (1.253314 * meanad) if meanad > 0 else 0.0


def pct_rank(sorted_xs: list[float], x: float) -> float:
    import bisect
    return round(100.0 * bisect.bisect_right(sorted_xs, x) / len(sorted_xs), 1) if sorted_xs else 0.0


# ---------- loaders ----------
def load_json(name: str):
    return json.loads((RAW / name).read_text())


def read_csv(name: str):
    with (RAW / "cpdp" / name).open(newline="") as f:
        yield from csv.DictReader(f)


def strip_code(s: str) -> str:
    return s.split(" - ", 1)[1].strip() if " - " in s else s.strip()


def build_pay(cfg: dict) -> dict[str, dict]:
    pe = cfg["pay_elements"]
    cat_of = {**{e: "base" for e in pe["base"]}, **{e: "ot" for e in pe["overtime"]},
              **{e: "det" for e in pe.get("details", [])}, **{e: "bb" for e in pe.get("buybacks", [])}}
    emp: dict[str, dict] = {}
    title_base: dict[str, Counter] = defaultdict(Counter)
    for r in load_json(f"payroll_{cfg['payroll_year']}.json"):
        pid = r["employee_dataset_id"]
        e = emp.setdefault(pid, {"id": pid, "name": strip_code(r["employee"]),
                                 "base": 0.0, "ot": 0.0, "det": 0.0, "bb": 0.0, "other": 0.0})
        amt = float(r.get("amount") or 0)
        el = r["pay_element"]
        cat = cat_of.get(el, "other")
        e[cat] += amt
        title_base[pid][strip_code(r["title"])] += amt if cat == "base" else amt * 1e-6
    for pid, e in emp.items():
        e["title"] = title_base[pid].most_common(1)[0][0]
        e["multi_title"] = len(title_base[pid]) > 1
        e["total"] = e["base"] + e["ot"] + e["det"] + e["bb"] + e["other"]
        e["otr"] = round(e["ot"] / e["base"], 3) if e["base"] > 0 else None
        for k in ("base", "ot", "det", "bb", "other", "total"):
            e[k] = round(e[k], 2)
    return emp


def build_complaints(window: int) -> tuple[dict, dict, dict, str]:
    dates = {r["cr_id"]: r["complaint_date"][:10] for r in read_csv("complaints-complaints.csv")}
    last_year = max(int(d[:4]) for d in dates.values() if d[:4].isdigit())
    start = last_year - window + 1
    all_, win, sus = defaultdict(set), defaultdict(set), Counter()
    for r in read_csv("complaints-accused.csv"):
        uid, cr = r["UID"], r["cr_id"]
        if cr in all_[uid]:
            continue
        all_[uid].add(cr)
        y = dates.get(cr, "")[:4]
        if y.isdigit() and int(y) >= start:
            win[uid].add(cr)
        if (r.get("final_finding") or "").strip().upper() == "SU":
            sus[uid] += 1
    first_year = min(int(d[:4]) for d in dates.values() if d[:4].isdigit() and int(d[:4]) >= 1990)
    return ({u: len(v) for u, v in all_.items()}, {u: len(v) for u, v in win.items()}, sus,
            f"{start}-{last_year} window (data {first_year}-{last_year})")


def build_force(window: int) -> tuple[dict, dict, dict, dict, str]:
    """Per UID: distinct TRRs in window, career, firearm and taser TRRs in window. Dates m/d/yy."""
    path = RAW / "cpdp" / "trr_main.csv"
    if not path.exists():
        return {}, {}, {}, {}, ""
    rows = []
    for r in read_csv("trr_main.csv"):
        parts = (r.get("trr_date") or "").split("/")
        uid = (r["UID"] or "").split(".")[0]          # TRR file writes UIDs as floats ("129702.0")
        if uid and len(parts) == 3 and parts[2][:2].isdigit():
            yy = int(parts[2][:2])
            rows.append((uid, r["trr_id"], 2000 + yy if yy < 50 else 1900 + yy,
                         r.get("firearm_used") == "1", r.get("taser") == "1"))
    last = max(y for _, _, y, _, _ in rows)
    start = last - window + 1
    win, all_, gun, taser = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set)
    for uid, tid, y, g, t in rows:
        all_[uid].add(tid)
        if y >= start:
            win[uid].add(tid)
            if g:
                gun[uid].add(tid)
            if t:
                taser[uid].add(tid)
    n = lambda d: {k: len(v) for k, v in d.items()}
    return n(win), n(all_), n(gun), n(taser), f"{start}-{last} window (data {min(y for _, _, y, _, _ in rows)}-{last}, to Sep {last})"


def build_ot_trend() -> tuple[dict, dict]:
    """meta.ot_trend + per-employee YTD core OT through the latest complete period of the newest year."""
    path = RAW / "payroll_periods.json"
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text())
    years = sorted(data)
    newest = years[-1]
    through = max((int(p) for e in data[newest].values() for p in e), default=0)
    trend, ytd = {"through_period": through, "years": {}}, defaultdict(dict)
    for y in years:
        tot = [0.0] * 24
        for eid, per in data[y].items():
            s_ = 0.0
            for p, v in per.items():
                tot[int(p) - 1] += v
                if int(p) <= through:
                    s_ += v
            ytd[eid][y] = round(s_, 2)
        n = through if y == newest else 24
        trend["years"][y] = [round(v, 2) for v in tot[:n]]
    return trend, ytd


def build_payments(case_officers: dict[str, int], verify_over: float = 1e8) -> tuple[dict, dict]:
    """meta.payments summary + {case key: [paid rows]}. No payee names leave this function."""
    path = RAW / "payments_dol.json"
    if not path.exists():
        return {}, {}
    from .sources.casekey import case_key
    raw = json.loads(path.read_text())
    rows = [r for r in raw["rows"] if r.get("date")]          # undated rows = separate personnel table
    unverified = [r for r in rows if float(r.get("amount") or 0) + float(r.get("fees") or 0) > verify_over]
    rows = [r for r in rows if r not in unverified]
    by_year, by_month, by_cause, paid = defaultdict(lambda: {"n": 0, "amount": 0.0, "fees": 0.0}), Counter(), {}, defaultdict(list)
    for r in rows:
        key = r.get("key") or case_key(r.get("case_no"))
        amt, fees = float(r.get("amount") or 0), float(r.get("fees") or 0)
        y = str(r.get("year") or (r.get("date") or "")[:4])
        by_year[y]["n"] += 1
        by_year[y]["amount"] += amt
        by_year[y]["fees"] += fees
        by_month[(r.get("date") or "")[:7]] += amt + fees
        c = (r.get("cause") or "UNKNOWN").strip().upper()
        n_, a_ = by_cause.get(c, (0, 0.0))
        by_cause[c] = (n_ + 1, a_ + amt + fees)
        if key:
            paid[key].append({"date": r.get("date"), "amount": round(amt, 2), "fees": round(fees, 2)})
    top = sorted(rows, key=lambda r: -(float(r.get("amount") or 0) + float(r.get("fees") or 0)))[:40]
    summary = {
        "asof": raw.get("asof"),
        "unverified": [{"case_no": r.get("case_no"), "key": r.get("key"), "date": r.get("date"),
                        "amount": round(float(r.get("amount") or 0), 2), "cause": r.get("cause"),
                        "note": f"single row over ${verify_over:,.0f}; excluded from totals pending verification"}
                       for r in unverified],
        "by_year": {y: {"n": v["n"], "amount": round(v["amount"], 2), "fees": round(v["fees"], 2)}
                    for y, v in sorted(by_year.items()) if y},
        "by_month": [[m, round(v, 2)] for m, v in sorted(by_month.items()) if m],
        "by_cause": [[c, n_, round(a_, 2)] for c, (n_, a_) in sorted(by_cause.items(), key=lambda kv: -kv[1][1])],
        "top": [{"case_no": r.get("case_no"), "key": r.get("key"), "date": r.get("date"),
                 "amount": round(float(r.get("amount") or 0), 2), "fees": round(float(r.get("fees") or 0), 2),
                 "cause": r.get("cause"), "disposition": r.get("disposition"),
                 "officers_linked": case_officers.get(r.get("key"), 0)} for r in top],
    }
    return summary, paid


def build_council(case_officers: dict[str, int], police_keys: set[str], pay_by_key: dict) -> tuple[list, dict]:
    """Council-approved settlements: police if title signals police OR case key appears in DOL police records."""
    path = RAW / "council_settlements.json"
    if not path.exists():
        return [], {}
    out, by_key = [], {}
    for m in json.loads(path.read_text()).get("matters", []):
        keys = m.get("case_keys") or []
        if not (m.get("police_signal") or any(k in police_keys for k in keys)):
            continue
        paid = sum(x["amount"] + x["fees"] for k in keys for x in pay_by_key.get(k, []))
        item = {"date": m.get("date"), "date_kind": m.get("date_kind"), "key": keys[0] if keys else None,
                "case_no": keys[0] if keys else None, "amount": m.get("amount"),
                "paid": round(paid, 2) if paid else None, "url": m.get("url"),
                "officers_linked": max((case_officers.get(k, 0) for k in keys), default=0)}
        out.append(item)
        for k in keys:
            by_key.setdefault(k, {"date": m.get("date"), "url": m.get("url")})
    out.sort(key=lambda x: x["date"] or "", reverse=True)
    return out, by_key


def build_units() -> tuple[dict, dict, str]:
    ref = {}
    for r in read_csv("unit_reference.csv"):
        ref[str(int(float(r["current_unit"])))] = (r.get("current_unit_description (April 2017 roster)") or "").strip()
    latest: dict[str, tuple] = {}
    last_end = ""
    for r in read_csv("unit-history.csv"):
        if not r["unit"]:
            continue
        key = (r["unit_start_date"] or "", r["unit_end_date"] or "9999")
        last_end = max(last_end, r["unit_end_date"] or "")
        if r["UID"] not in latest or key > latest[r["UID"]][0]:
            latest[r["UID"]] = (key, str(int(float(r["unit"]))))
    return {u: v[1] for u, v in latest.items()}, ref, last_end[:7]


def district_of(unit: str | None) -> str | None:
    if unit and unit.isdigit() and 1 <= int(unit) <= 25 and int(unit) not in (13, 21, 23):
        return str(int(unit))
    return None


def badge_of(p: dict | None, sm: dict | None) -> str | None:
    for b in ((sm or {}).get("badge"), (p or {}).get("current_star")):
        b = str(b or "").split(".")[0].strip()
        if b.isdigit() and int(b) > 0:
            return b
    return None


def ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def build_districts(officers: list[dict]) -> list[dict]:
    gj = load_json("districts.geojson")
    polys = {}
    for f in gj["features"]:
        num = str(int(f["properties"]["dist_num"]))
        g = f["geometry"]
        rings = [p[0] for p in g["coordinates"]] if g["type"] == "MultiPolygon" else [g["coordinates"][0]]
        polys[num] = rings
    pts = [pt for rs in polys.values() for r in rs for pt in r]
    lon0, lon1 = min(p[0] for p in pts), max(p[0] for p in pts)
    lat0, lat1 = min(p[1] for p in pts), max(p[1] for p in pts)
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    s = min(580 / ((lon1 - lon0) * kx), 780 / (lat1 - lat0))

    def xy(p):
        return (10 + (p[0] - lon0) * kx * s, 10 + (lat1 - p[1]) * s)

    copa, bia = defaultdict(Counter), defaultdict(Counter)
    for name, tgt in (("copa_by_beat.json", copa), ("bia_by_beat.json", bia)):
        for r in load_json(name):
            b = (r.get("beat") or "").strip()
            if b.isdigit() and r.get("year"):
                tgt[str(int(b) // 100)][int(r["year"])] += int(r["n"])
    years = sorted({y for c in list(copa.values()) + list(bia.values()) for y in c})[-8:]
    members, flagged = Counter(), Counter()
    for o in officers:
        if o["dist"]:
            members[o["dist"]] += 1
            if o["fs"] or o["ff"]:
                flagged[o["dist"]] += 1
    out = []
    for num in sorted(polys, key=int):
        d, big = [], max(polys[num], key=len)
        for ring in polys[num]:
            last = None
            seg = []
            for p in ring:
                q = xy(p)
                if last is None or abs(q[0] - last[0]) + abs(q[1] - last[1]) >= 1.0:
                    seg.append(q)
                    last = q
            if len(seg) >= 3:
                d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in seg) + "Z")
        bx = [xy(p) for p in big]
        out.append({"num": num, "label": ordinal(int(num)), "path": "".join(d),
                    "lx": round(sum(p[0] for p in bx) / len(bx), 1),
                    "ly": round(sum(p[1] for p in bx) / len(bx), 1),
                    "members": members[num], "flagged": flagged[num],
                    "copa": [[y, copa[num][y]] for y in years],
                    "bia": [[y, bia[num][y]] for y in years]})
    return out


# ---------- recent lawsuits (City DOL CPD litigation reports) ----------
RANKS = {"OFFICER", "PO", "P", "SGT", "SERGEANT", "LT", "LIEUTENANT", "DET", "DETECTIVE", "CPT", "CAPT",
         "CAPTAIN", "CMDR", "COMMANDER", "DEFENDANT", "INDIVIDUALLY", "FORMER", "CHICAGO", "POLICE"}


def defendant_key(name: str) -> tuple[str, str] | None:
    """'Sgt. Clifford J. Martin #18859 (Defendant)' -> ('MARTIN', 'CLIFFORD'); None if unusable."""
    name = re.sub(r"\(.*?\)|#\s*\d+", " ", name)
    toks = [t for t in norm(name).split() if t not in RANKS and t not in SUFFIXES]
    toks = [t for t in toks if len(t) > 1]  # drop middle initials
    if len(toks) < 2:
        return None
    return toks[-1], toks[0]


def link_recent_lawsuits(officers: list[dict]) -> dict[str, list[dict]]:
    from .sources.casekey import case_key
    """Payroll id -> cases. Badge (paired with a matching last name) first, else unique (last, first). Never guess."""
    path = RAW / "lawsuits_recent.json"
    if not path.exists():
        return {}
    by_badge = defaultdict(list)
    by_name = defaultdict(list)
    for o in officers:
        if not o["sworn"]:
            continue
        last, first, _ = split_payroll_name(o["name"])
        by_name[(last, first)].append(o)
        if o["badge"]:
            by_badge[o["badge"]].append(o)
    out: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    for c in json.loads(path.read_text()):
        pay = float(c.get("payout") or 0)
        if pay <= 0 or (c["case_no"], c.get("kind")) in seen:
            continue
        seen.add((c["case_no"], c.get("kind")))
        offs, badges = c.get("officers") or [], c.get("badges") or []
        paired = len(badges) == len(offs)
        for i, nm in enumerate(offs):
            k = defendant_key(nm)
            hit = None
            if paired and len(by_badge.get(badges[i], [])) == 1:
                cand = by_badge[badges[i]][0]
                if k and split_payroll_name(cand["name"])[0] == k[0]:
                    hit = cand
            if hit is None and k and len(by_name.get(k, [])) == 1:
                hit = by_name[k][0]
            if hit and all(x["case_no"] != c["case_no"] for x in out[hit["id"]]):
                out[hit["id"]].append({"case_no": c["case_no"], "key": case_key(c["case_no"]), "year": c.get("year"),
                                       "payout": round(pay, 2), "category": c.get("category"),
                                       "kind": c.get("kind"), "url": c.get("source_url")})
    return out


from .sources.casekey import case_key  # noqa: E402

# ---------- main ----------
def is_sworn(title: str, cfg: dict) -> bool:
    return any(t in title.upper() for t in cfg["sworn"]["titles"])


def main() -> None:
    cfg = tomllib.loads((ROOT / "config" / "qcic.toml").read_text())
    st, fx = cfg["stat"], cfg["fixed"]
    emp = build_pay(cfg)
    roster = {norm(r["name"]) for r in load_json("roster.json")}
    profiles = [r for r in read_csv("final-profiles.csv") if r["current_status"] == "1"]
    cmp_all, cmp_win, sus, cmp_vintage = build_complaints(st["complaint_window_years"])
    frc_win, frc_all, frc_gun, frc_taser, frc_vintage = build_force(st.get("trr_window_years", 3))
    ot_trend, ot_ytd = build_ot_trend()
    units, unit_ref, units_to = build_units()
    summ_path = RAW / "cpdp_summaries.json"
    summaries = json.loads(summ_path.read_text()) if summ_path.exists() else {}

    sworn = {pid for pid, e in emp.items() if is_sworn(e["title"], cfg)}
    matches = match({pid: split_payroll_name(emp[pid]["name"]) for pid in sworn}, profiles)

    rp = RAW / "units_recent.json"
    recent = json.loads(rp.read_text()) if rp.exists() else {}
    officers = []
    for pid, e in emp.items():
        p = matches.get(pid)
        uid = p["UID"] if p else None
        cid = int(p["officer_id"]) if p and p["officer_id"] else None
        sm = summaries.get(str(cid)) if cid else None
        law = None
        if sm and "error" not in sm:
            law = round(float(sm.get("total_lawsuit_settlements") or 0), 2)
        badge = badge_of(p, sm)
        ru = (recent.get(str(cid)) if cid else None) or (recent.get(f"star:{badge}") if p and badge else None)
        if ru and ru.get("unit") is not None:
            unit, udesc, uasof = str(ru["unit"]), ru.get("unit_desc"), ru.get("as_of")
        else:
            unit = units.get(uid) if uid else None
            udesc, uasof = unit_ref.get(unit) if unit else None, units_to if unit else None
        o = {**e, "sworn": pid in sworn, "roster": norm(e["name"]) in roster,
             "cpdp": cid, "mp": p["_mp"] if p else None,
             "cmp": cmp_win.get(uid, 0) if p else None,
             "cmp_all": cmp_all.get(uid, 0) if p else None,
             "sus": sus.get(uid, 0) if p else None, "law": law, "law_n": None,
             "unit": unit.zfill(3) if unit else None,
             "unit_desc": udesc or (f"Unit {unit}" if unit else None), "unit_asof": uasof,
             "dist": district_of(unit), "badge": badge,
             "frc": frc_win.get(uid, 0) if p and frc_all else None,
             "frc_all": frc_all.get(uid, 0) if p and frc_all else None,
             "frc_gun": frc_gun.get(uid, 0) if p and frc_all else None,
             "frc_taser": frc_taser.get(uid, 0) if p and frc_all else None,
             "ot_ytd": ot_ytd.get(pid, {})}
        officers.append(o)

    recent_cases = link_recent_lawsuits(officers)
    for o in officers:
        cases = recent_cases.get(o["id"], [])
        rec = round(sum(x["payout"] for x in cases), 2)
        o["law_cpdp"] = o["law"]
        o["law_dol"] = rec if recent_cases else None
        if recent_cases and o["sworn"]:
            o["law"] = round((o["law"] or 0) + rec, 2)
        o["law_n"] = len(cases) if recent_cases else None
        o["law_cases"] = sorted(cases, key=lambda x: -x["payout"])[:12]

    case_officers = Counter(c["key"] for v in recent_cases.values() for c in v if c.get("key"))
    payments, paid_by_key = build_payments(case_officers, cfg.get("payments", {}).get("verify_over", 1e8))
    police_keys = set(paid_by_key) | set(case_officers) | {
        case_key(c.get("case_no")) for c in (json.loads((RAW / "lawsuits_recent.json").read_text())
                                             if (RAW / "lawsuits_recent.json").exists() else [])}
    council, council_by_key = build_council(case_officers, police_keys, paid_by_key)
    for o in officers:
        for c in o["law_cases"]:
            c["paid"] = paid_by_key.get(c.get("key"), [])
            c["council"] = council_by_key.get(c.get("key"))

    # full-year guard: pay metrics scored only for members with a substantial base salary
    tb = defaultdict(list)
    for o in officers:
        if o["base"] > 0:
            tb[o["title"]].append(o["base"])
    tmed = {t: median(v) for t, v in tb.items()}
    for o in officers:
        o["fy"] = o["base"] > 0 and o["base"] >= st["full_year_base_share"] * tmed.get(o["title"], 0)
    pay_metrics = {"total", "ot"}
    pos_only = set(st.get("positive_only", []))
    logm = set(st.get("log_metrics", []))

    def tf(m, x):
        return math.log1p(max(x, 0.0)) if m in logm else x

    def scored(o, m):
        return o[m] is not None and (m not in pay_metrics or o["fy"])

    # peer groups
    title_n = Counter(o["title"] for o in officers if o["fy"])
    for o in officers:
        o["peer"] = o["title"] if title_n[o["title"]] >= st["min_peer_group"] else (
            "ALL SWORN" if o["sworn"] else "ALL CIVILIAN")
    groups = defaultdict(list)
    for o in officers:
        groups[o["peer"]].append(o)
    peers = {}
    for g, members in groups.items():
        stats = {"n": len(members), "median": [], "p90": [], "p99": []}
        scales, sorteds = [], []
        for m in METRICS:
            xs = sorted(float(x[m]) for x in members if scored(x, m))
            med, sc = robust_scale([tf(m, x) for x in xs if x > 0 or m not in pos_only])
            scales.append((med, sc))
            sorteds.append(xs)
            stats["median"].append(round(median(xs), 2))
            stats["p90"].append(round(quantile(xs, 0.9), 2))
            stats["p99"].append(round(quantile(xs, 0.99), 2))
        peers[g] = stats
        for o in members:
            o["z"], o["pct"], o["fs"] = [], [], []
            for i, m in enumerate(METRICS):
                v = o[m]
                med, sc = scales[i]
                if not scored(o, m) or not sorteds[i] or (m in pos_only and v <= 0):
                    o["z"].append(None)
                    o["pct"].append(pct_rank(sorteds[i], v) if scored(o, m) and sorteds[i] else None)
                    continue
                z = round((tf(m, v) - med) / sc, 2) if sc > 0 else 0.0
                o["z"].append(z)
                o["pct"].append(pct_rank(sorteds[i], v))
                if z >= st["z_flag"]:
                    o["fs"].append(m)
            ff = []
            if o["fy"] and o["total"] >= fx["total_pay"]:
                ff.append("total")
            if o["fy"] and o["ot"] >= fx["overtime_pay"]:
                ff.append("ot")
            if o["fy"] and o["otr"] is not None and o["otr"] >= fx["overtime_ratio"]:
                ff.append("otr")
            if o["cmp"] is not None and o["cmp"] >= fx["complaints_window"]:
                ff.append("cmp")
            if o["sus"] is not None and o["sus"] >= fx["sustained_total"]:
                ff.append("sus")
            if o["law"] is not None and o["law"] >= fx["lawsuit_total"]:
                ff.append("law")
            if o["frc"] is not None and o["frc"] >= fx.get("force_window", 10**9):
                ff.append("frc")
            o["ff"] = ff

    districts = build_districts(officers)
    officers.sort(key=lambda o: o["name"])
    data = {
        "meta": {
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "payroll_year": cfg["payroll_year"],
            "vintage": {"payroll": str(cfg["payroll_year"]), "complaints": cmp_vintage,
                        "units": "roster 2023-11 (FOIA p891976), else unit history to " + units_to,
                        "lawsuits": "CPDP cases ~2011-2019 + City DOL CPD litigation reports 2022-2025 (2020-2021 not yet parsed)",
                        "copa_bia": "live City feeds", "frc": frc_vintage,
                        "payments": f"Law Dept. payment requests through {payments.get('asof')}" if payments else None},
            "counts": {"employees": len(officers), "sworn": len(sworn), "matched": len(matches),
                       "with_lawsuit_data": sum(1 for o in officers if o["law"] is not None),
                       "dol_cases_linked": len({c["case_no"] for v in recent_cases.values() for c in v}),
                       "dol_officers_linked": len(recent_cases),
                       "flagged_stat": sum(1 for o in officers if o["fs"]),
                       "flagged_fixed": sum(1 for o in officers if o["ff"]),
                       "pay_total": round(sum(o["total"] for o in officers), 2),
                       "ot_total": round(sum(o["ot"] for o in officers), 2),
                       "det_total": round(sum(o["det"] for o in officers), 2),
                       "bb_total": round(sum(o["bb"] for o in officers), 2),
                       "part_year": sum(1 for o in officers if not o["fy"])},
            "thresholds": {**st, "fixed": fx},
            "sources": SOURCES,
            "ot_trend": ot_trend, "payments": payments, "council": council,
        },
        "metrics": METRICS, "metric_labels": LABELS, "peers": peers,
        "officers": officers, "districts": districts,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    c = data["meta"]["counts"]
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB): {c}", file=sys.stderr)


if __name__ == "__main__":
    main()
