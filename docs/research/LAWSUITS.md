# LAWSUITS -- recent (2020-2026) police-misconduct payout sources
Researched 2026-10-13. Current source (CPDP API, cases ~2011-2019): docs/DATA.md "Lawsuits".

## Ranked candidates
| # | Source | Coverage | Cadence | Officer-level | Access (tested) | Effort |
|---|--------|----------|---------|---------------|-----------------|--------|
| 1 | City DOL "CPD Annual Litigation Reports" (consent decree par. 548). https://www.chicago.gov/city/en/depts/dol/supp_info/CPDAnnLitReports.html | Reports for 2019-2025. Settled + litigated cases by year of settlement/judgment. Parsed OK: 2022-2025 (594 records; 2022-2025 settled $79.7M / $55.6M / $82.8M / $215.0M). 2019-2021: rotated/other layout, NOT parsed | Annual; 2025 report posted 30 Jun 2026; amended 2021 + 2024 reports re-issued Jul/Nov 2025 | YES: named individual CPD defendants, case no., amount, date, category, COPA/CR no.; badge numbers in some years (2022-2023 ~111 records) | Index HTML -> PDF links -> `pdfplumber.extract_tables()`. Built: `src/qcic/sources/lawsuits_recent.py` -> data/raw/lawsuits_recent.json | Done for 2022-25; 2019-21 = 1 custom parser |
| 2 | Chicago Data Portal Payments s4vu-giwb | 1996-now, daily | daily | NO: fields only voucher_number, amount, check_date, department_name, contract_number, vendor_name; no case no.; plaintiff/law-firm names as vendors | `curl https://data.cityofchicago.org/resource/s4vu-giwb.json?$limit=2` -> `{"voucher_number":"PVRF212205404","amount":"19038","check_date":"03/02/2022","contract_number":"DV","vendor_name":"TABATHA PURDIS"}` | Not linkable; skip |
| 3 | CourtListener API v4 (N.D. Ill. civil-rights dockets) https://www.courtlistener.com/api/rest/v4/search/ | 2020-now | live | Defendant parties on docket; no payouts | Anonymous call hit 429 (125/day throttle); needs free token for real use | High: pay absent, officer-party parsing, fuzzy names. Use only to cross-check case_no from #1 |
| 4 | CPDP API api.cpdp.co | cases ~2011-2019 (current) | stale | yes | `/officers/<id>/summary/` works (200); `/lawsuit/<case_no>/` returned "Not found" for 2018 C 02341 | none new data |
| 5 | WTTW analyses (repeat-defendant officers; $295M 2019-2024, 272 officers) https://news.wttw.com/2025/09/22/repeated-police-misconduct-272-officers-cost-chicago-taxpayers-295m-2019-analysis | 2019-2024 | annual (Aug/Sep) | yes, aggregated; built from city data | articles only; no dataset found | Context/validation only |
| 6 | Chicago OIG "Public Safety Complaint Network" dashboard (Jan 2026) | closed complaints | ? | co-accusal network | no export found | complaints, not lawsuits |
| 7 | City Council / Finance Committee settlement agenda items (chicityclerkelms.chicago.gov) | per meeting | monthly | partial (case name, amount; officers in text) | NOT tested (time) | high scrape; superseded by #1 |
| 8 | Chicago Reporter / Invisible Institute / Injustice Watch / BGA / Lucy Parsons / MacArthur | -- | -- | -- | no post-2019 bulk settlement dataset found in search; /home/user/invinst has only CPDB/chicago-police-data mirrors (not re-checked for lawsuits) | -- |

## Recommendation
- Use #1. Free, official, named defendants, 2022-2025 parsed now; add 2019-2021 later.
- Run: `python3 -m src.qcic.sources.lawsuits_recent` (downloads ~10 PDFs to data/raw/dol_pdfs/, writes data/raw/lawsuits_recent.json).
- Dependency: `pdfplumber` (+pypdf), already installed in this env (`pdfplumber 0.11.10`); NOT stdlib; no pip run. Import is lazy. Decide: allow as optional dep, or pre-commit the JSON.
- Record fields: case_no, year (settlement/judgment date), payout, officers[], badges[], defendants_raw, source_url, kind (settled|litigated), case_name, category, incident_date, disposition.
- Join: name rules in METHOD.md; use badges (when present) + unit as tie-break. Unmatched = leave unmatched (AGENTS.md P0.6).

## Caveats
- Multi-officer cases: payout is per case, not per officer. Do not credit the full amount to each officer without labelling (current CPDP total already does this; keep consistent or divide).
- Settlement != admission of liability. Many settled cases list "none"/"Defendants dismissed"/City only (payout with no officer). Show as "named in settled suit".
- Litigated rows (Appendix B) include dismissals with $0; filter payout > 0 for dollar totals.
- Year = settlement/judgment year, not incident year. Reports exclude cases settled but not dismissed by 31 Dec (roll into next year); amended reports re-issued: dedupe key case_no+kind+year (later file wins).
- Name quality: cells are free text (middle initials, "(Ret.)", ranks, "Star no."); 1,648 distinct strings after cleanup contain residual noise (e.g. "Lawrence J", "Bond" split in 2023 uppercase cells). `defendants_raw` kept for re-parse. 2025 report lists names without badges.
- Table extraction: 2022-2025 depend on the PDF having ruled tables; 2019-2021 rotated; 2025 main report PDF has no table (appendices are separate PDFs).
- Overlap: 2019 cases may overlap CPDP data; dedupe on case_no when merging.
- Terms: public record of City of Chicago; no license stated. Cite DOL.
