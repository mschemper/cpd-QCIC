# SCHEMA.md -- site/data.json contract (build.py writes, index.html reads). Change both + tests together.

```
{
 "meta": {
   "generated": "2026-10-13T12:00:00Z",
   "payroll_year": 2025,
   "vintage": {"payroll": "2025", "complaints": "2000-2023", "units": "to 2024-07", "lawsuits": "CPDP, 2011-2019 cases", "copa_bia": "live to 2026-10"},
   "counts": {"employees": 13000, "sworn": 11800, "matched": 10500, "with_lawsuit_data": 10400, "dol_cases_linked": 213, "dol_officers_linked": 486,
              "flagged_stat": 400, "flagged_fixed": 900, "pay_total": 1.86e9, "ot_total": 2.6e8,
              "det_total": 3.3e7, "bb_total": 4.8e7, "part_year": 1890},
   "thresholds": {<config [stat] keys verbatim>, "fixed": {<config [fixed] verbatim>}},   # config/qcic.toml verbatim
   "sources": [{"name": "...", "url": "...", "note": "..."}],
   "ot_trend": {"through_period": 6, "years": {"2024": [p1..p24 core OT $, dept], "2025": [...], "2026": [p1..p6]}},
   "payments": {                    # DOL Judgment & Settlement Payment Requests, CITY DEPARTMENT = POLICE
     "asof": "2026-08-31",
     "unverified": [{"case_no", "key", "date", "amount", "cause", "note"}],   # rows > config payments.verify_over; not in totals
     "by_year": {"2024": {"n": 600, "amount": 1.2e8, "fees": 1.5e7}, "2025": {...}, "2026": {...}},
     "by_month": [["2024-01", 9.1e6], ...],          # amount + fees per month, all years
     "by_cause": [["REVERSED CONVICTION", 377, 1.9e8], ...],   # 2024-2026, desc by amount
     "top": [{"case_no": "18 CV 1028", "key": "18-1028", "date": "2026-03-31", "amount": 1.4e7, "fees": 0,
              "cause": "REVERSED CONVICTION", "disposition": "SETTLEMENT", "officers_linked": 2}]   # top 40; no plaintiff names
   },
   "council": [{"date": "2026-05-22", "date_kind": "final_action|introduced", "key": "18-1028", "case_no": "18-1028",
                "amount": null (titles carry none), "paid": 1.4e7 | null (DOL payments, same key),
                "url": "<eLMS matter URL>", "officers_linked": 2}]   # Council-approved police settlements 2024-2026; no plaintiff names
 },
 "metrics": ["total", "ot", "cmp", "law", "frc"],   # order used in z/pct/flag arrays
 "metric_labels": {"total": "Total pay", "ot": "Overtime pay", "cmp": "Complaints (5 yr)", "law": "Lawsuit payouts",
                   "frc": "Use-of-force reports (3 yr)"},
 "peers": {"POLICE OFFICER": {"n": 8000, "median": [110000, 18000, 1, 0], "p90": [...], "p99": [...]}},
 "officers": [
   {"id": "C1081EDB5EEAE1",          # payroll employee_dataset_id
    "name": "DOE, JOHN Q", "title": "POLICE OFFICER", "sworn": true, "roster": true, "peer": "POLICE OFFICER",
    "base": 101234.5, "ot": 45000.0, "det": 3000.0, "bb": 2000.0, "other": 4000.0, "total": 155234.5, "otr": 0.44,
                                     # ot = core overtime; det = outside-agency details; bb = comp-time buybacks
    "fy": true,                      # full-year guard passed; false -> z/pct null for total, ot; no pay fixed flags
    "multi_title": false,            # held >1 title in payroll year
    "mp": 3 | 2 | null,              # CPDP match path (3-key, 2-key fallback)
    "cpdp": 13788 | null,            # CPDP officer id -> https://cpdp.co/officer/<id>/
    "cmp": 3, "cmp_all": 12, "sus": 1,
    "law": 700000.0,                 # law_cpdp + law_dol (sworn); null only if neither source covers the member
    "law_cpdp": 600000.0 | null,     # CPDP career total, cases ~2011-2019 (matched only)
    "law_dol": 100000.0 | null,      # City DOL litigation reports 2022-2025, cases linked to this member
    "law_n": 1,                      # number of linked DOL cases
    "law_cases": [{"case_no": "22C5270", "key": "22-5270", "year": 2023, "payout": 26500.0, "category": "False Arrest",
                   "kind": "settled", "url": "<DOL report PDF>",
                   "paid": [{"date": "2024-02-29", "amount": 26500.0, "fees": 0.0}],   # DOL payment rows, same case key ([] if none)
                   "council": {"date": "2024-01-17", "url": "..."} | null}],          # Council approval, same case key
                                     # top 12 by payout
    "frc": 4 | null,                 # use-of-force reports (distinct TRR) in last trr_window_years of data; null if unmatched
    "frc_all": 11 | null, "frc_gun": 0 | null, "frc_taser": 1 | null,   # career; firearm / taser TRRs in window
    "ot_ytd": {"2024": 9100.0, "2025": 8800.0, "2026": 12000.0},   # core OT periods 1..meta.ot_trend.through_period; key absent = not on payroll that year
    "unit": "004", "unit_desc": "4TH DISTRICT - SOUTH CHICAGO", "unit_asof": "2023-11", "dist": "4" | null,
    "badge": "17432" | null,         # star number from CPDP (latest known); null if unmatched
    "z":   [1.2, 4.1, 0.3, null, 0.8],    # robust z per metric; null = not available (unmatched)
    "pct": [77.1, 99.2, 60.0, null, 70.0], # percentile within peer group
    "fs":  ["ot"],                   # statistical flags (metric keys)
    "ff":  ["ot", "law"]             # fixed-limit flags: total, ot, otr, cmp, sus, law, frc
   }
 ],
 "districts": [
   {"num": "4", "label": "4th", "path": "M...Z", "lx": 512.0, "ly": 840.0,   # SVG path in 600x800 viewBox; label point
    "members": 420, "flagged": 37, "copa": [[2021, 310], [2022, 290], ...], "bia": [[2021, 120], ...]}
 ]
}
```
- Money in USD, floats rounded to 2 dp. Counts ints.
- `officers` holds every payroll member (all needed for strip plots); page filters to flagged by default.
- Unmatched to CPDP -> cmp/cmp_all/sus/law/cpdp/unit/dist = null; z/pct entries null for cmp/law.
- Plaintiff / payee names never written to data.json (private individuals).
