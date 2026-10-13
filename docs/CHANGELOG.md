# CHANGELOG.md

## v1.1 (unreleased)
- Use-of-force metric (frc): TRRs per officer, 2021-2023 window, from unified_data TRR/trr_main.csv; firearm/taser counts; scored among officers with >= 1 report; fixed limit 10.
- 2026 YTD core overtime trend (payroll periods 1-6 vs same periods 2024, 2025); per-officer ot_ytd.
- Law Dept. Judgment & Settlement payment requests 2024-2026 (POLICE rows): by year, month, cause, largest; linked to officers' DOL cases by case key. Rows > $100M held out as unverified (22 L 3091, $750M; press reports $7.5M).
- City Council (eLMS) police settlement approvals 2024-2026, linked by case key.
- Plaintiff names never written to data.json.

## v1 (unreleased)
- Payroll 2025 pull (dawh-m56b), aggregated by employee_dataset_id.
- Roster, COPA/BIA district counts, CPDP unified data (complaints, units).
- CPDP lawsuit summaries (fetch in progress).
- Matching payroll to CPDP (sworn titles).
- Robust z flags by job title; fixed-limit flags shown separately.
- site/data.json build; page in progress.
