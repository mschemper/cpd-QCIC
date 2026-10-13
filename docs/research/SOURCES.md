# SOURCES.md -- newer / additional data sources (survey 2026-10-13). T = access tested, R = read about only.

## Usable now (ranked)
| # | Source | Latest | Officer-level / key | Effort | Adds |
|---|---|---|---|---|---|
| 1 | DOL Judgment & Settlement Payment Requests xlsx (chicago.gov/city/en/depts/dol/supp_info/judgment-and-settlement-payments-requests.html) T | 2026-08-31, monthly | Case-level; key CASE # (= DOL litigation report case_no -> officers) | S | 2024-2026 YTD police payouts ($242M 2026 YTD, 377 reversed-conviction rows); officers via case_no join |
| 2 | Use of force in data already downloaded: unified_data.zip TRR/trr_main.csv (+actions, weapon discharges); CPDP summary trr_count, percentile_trr T | 2023-09 | Yes; UID / officer_id | S | New metric: use-of-force reports, firearm/taser counts |
| 3 | DOL CPD Litigation Report 2023 xlsx + amended 2021/2024 PDFs + 2025 Appendix C (Watts) T | 2026-06-30 | Yes; names + star | S | Cleaner 2023 parse; 2021 amended; Watts cases |
| 4 | FMPS payroll 2026 partial (dawh-m56b, periods 1-6) T | 2026-05-18 refresh, irregular | Yes; employee_dataset_id | S | 2026 YTD OT trend vs same periods 2024-25 (OT posts in even periods) |
| 5 | City Clerk eLMS API (api.chicityclerkelms.chicago.gov/matter?search=settlement) T | live | Case-level; titles carry case no. + sometimes officer names | M | Council approvals/dates for large settlements; cross-check #1 |
| 6 | COPA ufxy-tgry police_shooting flag T | 2026-10-07, weekly | Beat only | S | District count of shooting cases |

## Promising, blocked from cloud (test from PC or request)
- OIG Complaints & Notifications Lookup + CPD Complaint Network (igchicago.org/information-portal/data-dashboards/...): named/star complaints since 2000, closed cases, current. Self-hosted Tableau (views OfficerCMSComplaints_NEW/CPDMemberComplaintNotifications, ComplaintNetwork/ComplaintNetwork); not on Tableau Public; server unreachable from cloud proxy. Try CSV export from PC; else ask OIG for data; else FOIA CPD CRs 2024+ with star. Highest value (complaints past 2023).
- CPD Use of Force Dashboard "Download TRR Data 2025" (chicagopolice.org, 403 from cloud): check from PC whether star/unit columns exist. Only route to use-of-force after 2023.
- ILETSB decertification lookup (ptb.illinois.gov/resources/decertification/): named, rare, strong flag; no bulk file found; request one.
- IDOT Traffic & Pedestrian Stop Study: row-level has officer name/badge (R); not public; request via DOT.ITPSS@Illinois.gov.
- Chicago Justice Project FOIA response P610144 (2026): unit of assignment + payroll items (R); PDF unreadable here.

## Dead ends
- COPA/BIA portal feeds: no names (confirmed again; live to 2026-10).
- COPA case portal: names only inside per-case PDFs; no API.
- Arrests dpt3-jri9: no officer/beat. Pursuits, ISR stops, BWC, warrants: no public dataset.
- Payments s4vu-giwb: no case/officer. Overtime & Supplemental Earnings: stops 2022.
- CourtListener: token required (free); parties, no payouts. MuckRock API 403.
- Police Board, CPD discipline pages, IMT monitor sites: unreachable or PDF aggregates.
- PABF / Comptroller / OpenTheBooks / BGA: no officer-level disability or 2025-26 data found.
- No 2024-2026 officer-level unit source anywhere: needs new FOIA.
