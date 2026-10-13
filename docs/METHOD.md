# METHOD.md -- matching, metrics, flags. Code: src/qcic/build.py. Thresholds: config/qcic.toml.

## Metrics (per payroll member, payroll year)
- total = all pay elements (negatives included). ot = overtime elements. otr = ot / base.
- cmp = distinct complaints (CRs) in the last complaint_window_years of CPDP data; cmp_all = career; sus = sustained findings (final_finding SU), career.
- law = law_cpdp (CPDP total_lawsuit_settlements, cases ~2011-2019) + law_dol (DOL CPD litigation reports 2022-2025). Paid by the City; full case payout credited to every named officer. 2020-2021 gap. Unmatched members: law = law_dol only.

## Linking DOL cases -> payroll (sworn)
- Cases with payout > 0; dedupe (case_no, kind).
- Defendant name: strip parentheticals, "#NNNN", ranks, suffixes, middle initials -> (last squashed, first).
- Badge paired by position (only when badge count == defendant count) + same last name -> link. Else (last, first) unique among sworn payroll -> link. Else unlinked. Never guess.
- Defendants no longer on payroll are not shown (not current members).

## Location
- Unit = Nov 2023 FOIA roster (units_recent.json; by CPDP id, else star), else unit-history latest. unit_asof records which. Units 1-25 = districts; others shown by name, not mapped.

## Matching payroll -> CPDP (sworn titles only)
1. Normalise names: upper, letters only, drop JR/SR/II-V.
2. (last, first, middle initial) unique among active CPDP profiles AND unique among payroll -> match.
3. Else (last, first) unique on both sides and middle initials compatible (equal or one blank) -> match.
4. Else unmatched: cmp/sus/law/unit/dist/badge = null. Never guess.
- Multi-token last names squashed ("DE LA CRUZ" = "DELACRUZ"). Match path recorded in `mp` (3 or 2).
- Measured false-match rate < 0.5% (placebo test, docs/research/REVIEW.md).
- Members appointed after the CPDP snapshot are unmatched by design.

## Peer groups
- Peer = job title when >= min_peer_group members, else ALL SWORN / ALL CIVILIAN.

## Scoring population
- Full-year guard: total + ot scored only when base >= full_year_base_share x title median base (fy). Excludes retirees' payouts, new hires, long leave (~1.9k members). fy=false -> z/pct null for total/ot, no pay fixed flags.
- Peer groups sized on fy members.
- Overtime metric = core OT only (OT, FLSA, supervisors' quarterly, canine, court). Outside-agency details (det) and comp-time buybacks (bb) shown and in total, not in ot.

## Statistical flags (fs)
- Robust z = (t(x) - median) / (MAD / 0.6745); t = log(1+x) for log_metrics (total, ot, law), else identity. MAD = 0 -> scale = 1.253314 * mean absolute deviation (Iglewicz-Hoaglin); both 0 -> z = 0.
- positive_only metrics (law): median/scale from members with x > 0; x = 0 -> z null.
- Flag when z >= z_flag (3.5). High side only.
- Percentile = share of scored peers <= x (raw scale).

## Fixed-limit flags (ff)
- total >= total_pay; ot >= overtime_pay; otr >= overtime_ratio; cmp >= complaints_window; sus >= sustained_total; law >= lawsuit_total.

## Wording
- Page and docs say "outlier" / "flagged for review". A complaint is an allegation; not sustained != innocent, sustained != criminal. Lawsuit payouts are settlements/judgments, usually without admission of liability.
