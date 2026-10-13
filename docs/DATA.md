# DATA.md -- sources, how each is pulled, caveats. Fetch code: src/qcic/fetch.py.

## Payroll (primary pay + overtime)
- dawh-m56b Employee Payroll Data (FMPS Payroll Costing). 2023-present, 24 periods/yr, every pay element. CPD = department_code D57.
- Pulled server-side aggregated: SUM(amount) by employee_dataset_id, employee, title, pay_element for payroll_year.
- Key = employee_dataset_id (same names exist). Primary title = title carrying most base pay.
- Pay elements -> base / overtime / other: config/qcic.toml [pay_elements]. Overtime includes court time, special employment details (CTA, CHA, Parks) and comp-time buybacks (cash for banked overtime).
- Unaudited, point-in-time (dataset disclaimer). Payroll periods != earning periods.

## Roster
- xzkq-xp2w Current Employee Names, Salaries, department = 'CHICAGO POLICE DEPARTMENT'. r5jy-3eix (named in the request) is a filtered view of it; SODA on the view returns []. Used only for the "on current roster" mark.

## Superseded overtime feeds
- 5yfy-npzv "Police Overtime", skd4-skdv "POLICE OT": 2013 only (views of s9zb-nuc6). Yearly "Employee Overtime and Supplemental Earnings" files stop at 2022 (njrn-3hws). Not used; payroll replaces them.

## Misconduct, officer-level
- City COPA (mft5-nfa8) and BIA (t7km-zpxd) feeds carry NO officer names or IDs (race/sex/age/years only). Used only as district counts (beat // 100 = district) by year.
- Named complaints: Invisible Institute unified data (github invinst/chicago-police-data, data/unified_data.zip): complaints-accused.csv (cr_id, UID, final_finding), complaints-complaints.csv (dates). Complaint dates to 2023.
- Officer profiles: final-profiles.csv (UID, officer_id = CPDP id, names, star, current_status). Active = current_status 1.
- Units: unit-history.csv (latest start per UID; open rows end 2024-07) + unit_reference.csv (April 2017 descriptions). Units 1-25 = districts.

## Lawsuits
- No officer-level lawsuit feed on the city portal. DOL CPD Litigation Reports = PDFs with named defendants (2022-2025 parsed, below).
- Used: CPDP API https://api.cpdp.co/api/v2/officers/<id>/summary/ -> total_lawsuit_settlements (Chicago Reporter "Settling for Misconduct" + Invisible Institute, cases ~2011-2019), badge, unit. One call per active officer; 4 workers; cached in data/raw/cpdp_summaries.json; resumable. No bulk lawsuit list endpoint exists (lawsuit/<case_no> only).
- Payout total is per lawsuit naming the officer: a multi-officer case counts its full payout for each named officer.

## Lawsuits 2022-2025 (City DOL)
- CPD Annual Litigation Reports PDFs (Appendix A settled, B litigated): src/qcic/sources/lawsuits_recent.py -> data/raw/lawsuits_recent.json. Needs pdfplumber (optional, non-stdlib; only for this step). 2019-2021 layouts not parsed yet. Research: docs/research/LAWSUITS.md.

## Units 2023-11 (FOIA roster)
- invinst roster_1985-2023_2023-11_p891976 via raw.githubusercontent.com: src/qcic/sources/units_recent.py -> data/raw/units_recent.json. Newest officer-level unit data found; no 2024+ source exists. Research: docs/research/LOCATION.md.

## Use of force (TRR)
- unified_data.zip TRR/trr_main.csv (extracted by `unified`): 98,864 rows, 2004-01 to 2023-09-15. UID written as float ("129702.0") -> strip ".0". One row per officer per incident; count distinct trr_id. Newer TRR (CPD dashboard, 2025) not reachable from cloud: docs/research/SOURCES.md.

## Payroll periods (OT trend)
- dawh-m56b raw CSV filtered to core-OT pay elements, by employee + payroll_period, 2024-2026 (`payroll_periods`, ~1.5 min). OT posts in even periods. 2026 partial (refresh 2026-05-18, through period 6).

## Settlement payments (DOL)
- Judgment & Settlement Payment Requests xlsx, 2024-2026 (`payments`, src/qcic/sources/payments_dol.py, stdlib xlsx parse). CITY DEPARTMENT = POLICE. Monthly. Case-level, no officer names; join on case key (src/qcic/sources/casekey.py) to DOL litigation report cases. Undated rows = separate personnel table: dropped. Single rows > config payments.verify_over held out.

## City Council approvals (eLMS)
- api.chicityclerkelms.chicago.gov /matter?search=&top=100&skip= (filters ignored by API); category LAWSUITS/SETTLEMENTS, 2024+ (`council`, src/qcic/sources/council.py). Titles carry case no., no amounts. Police = title signal OR case key in DOL police records. Raw titles include plaintiff names: data/raw only.

## Map
- 24zt-jpfn Boundaries - Police Districts (current) GeoJSON (fthy-xz3r's .geojson is empty). Projected to 600x800 SVG in build.py.
