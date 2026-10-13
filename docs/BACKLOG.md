# BACKLOG.md -- open requests and bugs. Plan from here.

## Data
- Newer sources ranked: docs/research/SOURCES.md. Do first: DOL J&S payment xlsx 2024-2026 (join case_no -> officers); use-of-force metric from TRR already in unified_data.zip; 2026 YTD OT trend.
- Needs Mark's PC / requests: OIG complaint dashboards CSV, CPD TRR 2025 download columns, ILETSB bulk list, IDOT stop data, FOIA current roster with unit + CRs 2024+.
- Lawsuits 2019-2021: parse rotated DOL report layouts (src/qcic/sources/lawsuits_recent.py). Ref: docs/research/LAWSUITS.md.
- Units after 2023-11: none public; FOIA a current roster with unit. Ref: docs/research/LOCATION.md.
- Lawsuit count per flagged officer via CPDP timeline endpoint.
- Annualise part-year pay (new hires, leavers).
- 4 duplicate badge numbers (12327, 20168, 15607, 12395): resolve or show.

## Metrics and method
- Complaints z: zero-inflated in small civilian groups (median == p90); consider positive_only or exposure adjustment. Ref: docs/METHOD.md.
- Method review open items: rank/appointment-date match guards; complaints per year of service; sustained category. Ref: docs/research/REVIEW.md.
- 2024 vs 2025 trend.

## Page
- Per-period OT sparklines (24 payroll periods).

## Ops
- Scheduled refresh (cron or Routine).
