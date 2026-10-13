"""Generate tests/fixtures/sample.json: synthetic, seeded, schema per docs/SCHEMA.md. stdlib only."""
import json, os, random, statistics

SEED = 20261013
OUT = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "sample.json")
TITLES = [("POLICE OFFICER", 190, 98000, 12000), ("SERGEANT", 55, 128000, 14000),
          ("DETECTIVE", 35, 118000, 14000), ("LIEUTENANT", 12, 150000, 12000), ("CAPTAIN", 8, 168000, 10000)]
FIXED = {"total_pay": 200000, "overtime_pay": 75000, "overtime_ratio": 0.6,
         "complaints_window": 10, "sustained_total": 3, "lawsuit_total": 250000}
METRICS = ["total", "ot", "cmp", "law"]
Z_FLAG = 3.5


def pct_of(sorted_vals, q):
    if not sorted_vals:
        return 0
    i = min(len(sorted_vals) - 1, max(0, int(round(q / 100 * (len(sorted_vals) - 1)))))
    return sorted_vals[i]


def rz(x, vals):
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals])
    if mad == 0:
        return 0.0 if x == med else (None if False else round(0.6745 * (x - med) / 0.5, 2))
    return round(0.6745 * (x - med) / mad, 2)


def main():
    rnd = random.Random(SEED)
    officers = []
    n = 0
    for title, count, base_mu, base_sd in TITLES:
        for _ in range(count):
            n += 1
            base = max(55000, rnd.gauss(base_mu, base_sd))
            ot = max(0.0, rnd.lognormvariate(9.2, 0.9))
            if rnd.random() < 0.05:
                ot *= rnd.uniform(3, 6)
            other = max(0.0, rnd.gauss(7000, 3000))
            matched = rnd.random() < 0.85
            o = {"id": "SAMPLE%04d" % n, "name": "SAMPLE, OFFICER %03d" % n, "title": title,
                 "sworn": True, "roster": rnd.random() < 0.9, "det": round(rnd.random() * 3000, 2), "bb": round(rnd.random() * 2000, 2), "fy": rnd.random() > 0.05, "multi_title": False, "mp": None, "peer": title, "badge": None, "base": round(base, 2), "ot": round(ot, 2),
                 "other": round(other, 2), "total": round(base + ot + other, 2),
                 "otr": round(ot / base, 2), "cpdp": None, "cmp": None, "cmp_all": None,
                 "sus": None, "law": None, "law_n": None, "unit": None, "unit_desc": None, "unit_asof": None, "dist": None}
            if matched:
                d = rnd.randint(1, 25)
                cmp_ = min(40, int(rnd.expovariate(0.9)))
                if rnd.random() < 0.04:
                    cmp_ += rnd.randint(8, 20)
                law = 0.0
                if rnd.random() < 0.08:
                    law = round(rnd.lognormvariate(11, 1.2), 2)
                o.update(mp=rnd.choice([3, 3, 2]), unit_asof="2023-11", badge=str(1000 + n * 7), cpdp=10000 + n, cmp=cmp_, cmp_all=cmp_ + rnd.randint(0, 8),
                         sus=min(cmp_, int(rnd.random() ** 3 * 5)), law=law,
                         law_n=(1 + int(law > 100000)) if law else 0,
                         unit="%03d" % d, unit_desc="District %03d" % d, dist=str(d))
            o["law_cpdp"] = o["law"] if matched else None
            o["law_dol"] = None
            o["law_cases"] = []
            if rnd.random() < 0.12:
                cases = [{"case_no": "2%dC%04d" % (rnd.choice([2, 3, 4, 5]), rnd.randint(1, 9999)),
                          "year": rnd.choice([2022, 2023, 2024, 2025]),
                          "payout": round(rnd.lognormvariate(10.5, 1.0), 2),
                          "category": rnd.choice(["False Arrest", "Excessive Force", "", "Malicious Prosecution"]),
                          "kind": rnd.choice(["settled", "litigated"]),
                          "url": "https://example.org/dol-report.pdf"} for _ in range(rnd.randint(1, 3))]
                cases.sort(key=lambda c: -c["payout"])
                o["law_cases"] = cases
                o["law_dol"] = round(sum(c["payout"] for c in cases), 2)
                o["law_n"] = len(cases)
                o["law"] = round((o["law_cpdp"] or 0) + o["law_dol"], 2)
            elif o["law_n"] is None and matched:
                o["law_n"] = 0
            officers.append(o)
    # a few non-district, unsworn-style gaps are omitted by design
    peers = {}
    for title, *_ in TITLES:
        grp = [o for o in officers if o["peer"] == title]
        peers[title] = {"n": len(grp), "median": [], "p90": [], "p99": []}
        cols = {m: sorted(o[m] for o in grp if o[m] is not None) for m in METRICS}
        for key, q in (("median", 50), ("p90", 90), ("p99", 99)):
            peers[title][key] = [round(float(pct_of(cols[m], q)), 2) for m in METRICS]
    for title, *_ in TITLES:
        grp = [o for o in officers if o["peer"] == title]
        cols = {m: [o[m] for o in grp if o[m] is not None] for m in METRICS}
        for o in grp:
            z, pc, fs = [], [], []
            for m in METRICS:
                v = o[m]
                if v is None:
                    z.append(None); pc.append(None); continue
                zz = rz(v, cols[m])
                z.append(zz)
                pc.append(round(100.0 * sum(1 for x in cols[m] if x <= v) / len(cols[m]), 1))
                if zz is not None and zz >= Z_FLAG:
                    fs.append(m)
            o["z"], o["pct"], o["fs"] = z, pc, fs
            ff = []
            if o["total"] >= FIXED["total_pay"]: ff.append("total")
            if o["ot"] >= FIXED["overtime_pay"]: ff.append("ot")
            if o["otr"] >= FIXED["overtime_ratio"]: ff.append("otr")
            if o["cmp"] is not None and o["cmp"] >= FIXED["complaints_window"]: ff.append("cmp")
            if o["sus"] is not None and o["sus"] >= FIXED["sustained_total"]: ff.append("sus")
            if o["law"] is not None and o["law"] >= FIXED["lawsuit_total"]: ff.append("law")
            o["ff"] = ff
    districts = []
    for i in range(25):
        r, c = divmod(i, 5)
        x, y, w, h = c * 120 + 4, r * 160 + 4, 112, 152
        num = str(i + 1)
        mem = [o for o in officers if o["dist"] == num]
        fl = sum(1 for o in mem if o["fs"] or o["ff"])
        districts.append({
            "num": num, "label": num + ("th" if 11 <= i + 1 <= 13 or (i + 1) % 10 in (0, 4, 5, 6, 7, 8, 9) else {1: "st", 2: "nd", 3: "rd"}[(i + 1) % 10]),
            "path": "M%d %dH%dV%dH%dZ" % (x, y, x + w, y + h, x),
            "lx": x + w / 2, "ly": y + h / 2, "members": len(mem), "flagged": fl,
            "copa": [[yr, rnd.randint(80, 400)] for yr in range(2021, 2026)],
            "bia": [[yr, rnd.randint(30, 160)] for yr in range(2021, 2026)]})
    flagged_stat = sum(1 for o in officers if o["fs"])
    flagged_fixed = sum(1 for o in officers if o["ff"])
    data = {
        "meta": {"generated": "2026-10-13T12:00:00Z", "payroll_year": 2025,
                 "vintage": {"payroll": "2025", "complaints": "2000-2023", "units": "to 2024-07",
                             "lawsuits": "CPDP cases ~2011-2019 + City DOL reports 2022-2025 (2020-2021 not yet parsed)", "copa_bia": "live to 2026-10"},
                 "counts": {"employees": len(officers), "sworn": len(officers),
                            "matched": sum(1 for o in officers if o["cpdp"]),
                            "dol_cases_linked": sum(len(o["law_cases"]) for o in officers), "dol_officers_linked": sum(1 for o in officers if o["law_cases"]), "flagged_stat": flagged_stat, "flagged_fixed": flagged_fixed},
                 "thresholds": {"z_flag": Z_FLAG, "fixed": FIXED},
                 "sources": [{"name": "SAMPLE payroll", "url": "https://example.org/payroll", "note": "synthetic"},
                             {"name": "SAMPLE CPDP", "url": "https://example.org/cpdp", "note": "synthetic"}]},
        "metrics": METRICS,
        "metric_labels": {"total": "Total pay", "ot": "Overtime pay", "cmp": "Complaints (5 yr)", "law": "Lawsuit payouts"},
        "peers": peers, "officers": officers, "districts": districts}
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("wrote", os.path.normpath(OUT), len(officers), "officers;", flagged_stat, "stat,", flagged_fixed, "fixed")


if __name__ == "__main__":
    main()
