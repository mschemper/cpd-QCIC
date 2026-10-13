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
   "sources": [{"name": "...", "url": "...", "note": "..."}]
 },
 "metrics": ["total", "ot", "cmp", "law"],          # order used in z/pct/flag arrays
 "metric_labels": {"total": "Total pay", "ot": "Overtime pay", "cmp": "Complaints (5 yr)", "law": "Lawsuit payouts"},
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
    "law_cases": [{"case_no": "22C5270", "year": 2023, "payout": 26500.0, "category": "False Arrest",
                   "kind": "settled", "url": "<DOL report PDF>"}],   # top 12 by payout
    "unit": "004", "unit_desc": "4TH DISTRICT - SOUTH CHICAGO", "unit_asof": "2023-11", "dist": "4" | null,
    "badge": "17432" | null,         # star number from CPDP (latest known); null if unmatched
    "z":   [1.2, 4.1, 0.3, null],    # robust z per metric; null = not available (unmatched)
    "pct": [77.1, 99.2, 60.0, null], # percentile within peer group
    "fs":  ["ot"],                   # statistical flags (metric keys)
    "ff":  ["ot", "law"]             # fixed-limit flags: total, ot, otr, cmp, sus, law
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
