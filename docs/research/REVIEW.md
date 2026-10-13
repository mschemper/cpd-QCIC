# REVIEW.md -- adversarial review of CPD-QCIC (13 Oct 2026). Read-only; no code changed.
Basis: build.py, fetch.py, audit.py, config/qcic.toml, docs; site/data.json (law=null); data/raw/payroll_2025.json; cpdp_summaries.json (3-5k of ~11.7k, still filling; ordered by officer_id = older officers first, so biased high).
Severity: H = can wrongly name/flag a person; M = misleading flag/number; L = polish.

## Ranked findings

### 1. [H] Retiree/stub records are flagged as "overtime outliers"; stubs poison peer pools
- 1,023 sworn (7.7%) have base < $5k; 969 have base = 0. They are payouts after separation (comp-time buy-back, OT paid late) or promotion-stub rows.
- 63 of them carry a flag (22 'ot', 31 'otr', 14 'sus', 13 'cmp'; 23 statistical). Examples: DOHERTY JR, JOHN A (CAPTAIN) base 0, ot $175,109 -> ff 'ot'; PRESNELL, PAUL (forensic inv.) base 0, ot $170,194 -> fs+ff 'ot'; HOWARD, RICHARD J / SODINI, PETER E (SERGEANT) base 0, ot $146k/$141k. A person who retired is shown as an overtime outlier for a lump payout.
- 'otr' = ot/base: 103 of 200 otr flags have base < $50k; meaningless ratio.
- Pool contamination: CAPTAIN group n=80 has 45 base<$5k; median total = $45,268 (real captains ~$250k), MAD scale $66,993 -> 7/80 (8.8%) of captains stat-flagged on total only because the median is dragged down. SERGEANT 363/1,725 stubs, LIEUTENANT 146/423.
- Fix (build.py main/build_pay): add `min_base_frac = 0.8` and `min_base_abs = 20000` to [stat]; compute `full_year = base >= min_base_frac * median(base of peer members with base>=5000)`. Peer medians/MAD/pct from full_year members only; stat flags for total/ot only for full_year members; `otr` only when base >= min_base_abs. Fixed-limit 'otr' same guard. Show non-full-year members as "part-year / separated: not scored" instead of a blank. Simulation (PO, base>=80% of median): stat total flags 176 -> 284 (cleaner pool, higher median), stat ot 517 -> 361, 34 current ot flags are part-year and drop.

### 2. [H/M] "Overtime" includes items that are not the member's overtime work
Pay elements by $ (2025, 47 elements, total $1.8556B; category = current config):
```
 1,408.9M base  REGULAR SALARY            137.4M OT OT 1_0              98.4M OT OT FLSA
   41.7M other  DUTY AVAILABILITY          28.9M OT COMP TIME SWN BB    22.7M other UNIFORM ALLOWANCE
   20.9M OT SPCL EMP CTA                   18.2M OT COMP TIME 200 HR BB 14.3M OT SUPERVISORS QUARTERLY OT
    8.4M other LEMART                       7.8M OT COURT NO PEN         7.4M other BABY FURLOUGH BUY BACK
    6.9M OT SPCL EMP CHA                    6.9M other HOLIDAY PREMIUM   5.6M other PERSONAL DAY BUY BACK
    5.6M OT PARKS                           4.6M other VAC SWN HR PAYOUT 3.1M other BIKE
    2.4M other ML DEPLOY COMBAT             1.9M other CIT               1.1M other CPD FITNESS PAY
    1.0M other ML NON COMBAT  ... (rest < 0.8M each; DOCK -0.73M, SUSPENSION -0.81M)
```
- DUTY AVAILABILITY ($3,800 flat/yr, 12.8k people), HOLIDAY PREMIUM, UNIFORM/LEMART/BIKE/CIT/FITNESS: correctly 'other' (allowances, not extra hours). Keep.
- SPCL EMP CTA/CHA, PARKS ($33.5M, 3.3k people): paid by CTA/CHA/Park District under detail agreements, reimbursed to the City. Labelled "overtime" = overstates City cost and implies abuse. 231 of 570 stat-ot flags would not flag on core OT alone (core = OT 1_0, OT FLSA, DEC OT FLSA, SUPERVISORS QUARTERLY OT, CANINE OVERTIME); 152 of 303 fixed 'ot'>=$100k flags need BB/SPCL to reach the limit. Examples verified live: ALLEN, KEVIN C ot $99,894 of which $48,072 is CTA+CHA+PARKS.
- COMP TIME *BB (cash-out of banked comp time, $48.6M): earned in prior years, paid in 2025; same hours may already be in earlier-year OT. Also the main driver of stubs (finding 1).
- COURT NO PEN: legitimate OT (court appearances). Keep as OT.
- Cash-outs in 'other' that inflate *total* (not ot): BABY FURLOUGH BUY BACK, PERSONAL DAY BUY BACK, VAC SWN HR PAYOUT, CBA LUMP SUM ($650k), COURT SETTLEMENT / PR YR CRT STTLMNT (back pay, 3 rows). Total-pay flags for retirees partly reflect leave payouts.
- Fix (config/qcic.toml + build_pay): split categories: `overtime` (OT 1_0, OT FLSA, DEC OT FLSA, SUPERVISORS QUARTERLY OT, CANINE OVERTIME, COURT NO PEN), `detail` (SPCL EMP CTA, SPCL EMP CHA, PARKS: outside-funded), `buyback` (COMP TIME*, DEC COMP*), `payout` (VAC*, BABY FURLOUGH*, PERSONAL DAY*, DEC PERS DAY BB, CBA LUMP SUM, COURT SETTLEMENT, PR YR CRT STTLMNT). Flag `ot` on overtime only; show detail/buyback as separate columns; total-pay stat flag on `total - payout`. Rename label to "Overtime (City-funded)". DOCK/SUSPENSION: keep in total (documented), fine.
- Primary title: build_pay picks max REGULAR/base-category $ per title. 479 sworn have >1 title (promotions, FTO, detective assignment); 253 split >25%. Stat flag rate for them 12.5% (60/479) vs 7.1% sworn overall -> promotees inflate totals (two jobs' pay in one peer). Examples: ALMARU/GROSS (PO -> FTO), CUEVAS (FTO -> SERGEANT, base 43.9k + 80.2k). Fix: for multi-title members score only if one title holds >= 80% of base, else mark "changed title in year: not scored"; or annualise (finding 3).

### 3. [M] Statistics
a) law (once filled), MAD = 0 fallback. From 4,982 fetched summaries: 1,067 (21.4%) have a payout > 0, median payee $59.5k, max $10.3M. Median 0 and MAD 0 -> scale = 1.2533 * mean|x| = $66.6k, cut = $233k (drifted from $176k at n=2,988; will move again at n=11.7k). Result: 169 flagged = 15.8% of payees (3.4% of all) -- NOT every payee, but the cut rides on the mean, which three $9.5M multi-officer settlements dominate. Not reproducible/defensible.
   Fix (build.py robust_scale callers): for zero-inflated metrics (law, cmp where median 0) compute z among members with x > 0 only; flag if x > 0 and z >= z_flag. Simulation payee-only: median $59.5k, scale $60.0k, cut $269.7k, 79 flags of 2,988 (2.6%) ~ same as the fixed $250k limit. Simpler and explainable: `law` stat flag = payee AND >= p90 of payees ($433k, 107 of 4,982) or drop the stat flag for law and keep only the fixed limit. Show "named in k settlements" rather than $ per officer.
b) law double-counts: identical payouts repeat across officers (9,499,999 x3, 1,170,646 x3, 724,999 x4, 650,000 x4, 500,000 x4) = multi-officer cases credited in full to each (DATA.md admits). A $250k fixed limit therefore flags anyone named in one big case. Fix: fetch case ids (or approximate: divide by count of officers sharing identical amount in the cached set) and show "named in a $X settlement (N officers)"; do not rank officers by it.
c) Skew: z on right-skewed OT. PO group stat-ot flags 383/8,815 = 4.3% (cut $66.5k) vs 0.02% under normality: "outlier" label is loose. After finding-1 pool fix PO ot cut = $74.6k, 259 flags (3.5% of full-year POs); p99 = $98.5k. Recommend flag ot at z>=3.5 AND >= p98 of peer; do not use log1p (zeros: cut $1.5M, 0 flags).
d) cmp: PO cut 6 complaints / 5 yr (326 flagged, 4.6% of matched POs); group median 0, scale 1.7. Counts every allegation outcome (NS 107k, UN 58k, NAF 38k, SU 24k, EX 19k, blank 14k rows). A member with 6 CRs and 0 sustained is stat-flagged (COGLIANESE, CRAIG M: 6 CRs 2019-23, 0 sustained, also pay-flagged). Exposure unadjusted: appointed after 2019 => fewer years; patrol vs desk assignments differ -> district/unit context. Last CPDP years are thin (2022: 3,389; 2023: 1,984 CRs vs 6,765 in 2020: reporting lag), so window 2019-2023 under-counts the newest years. Fix: label as "complaints filed against, any outcome"; add `cmp_sus` (sustained in window) next to `cmp`; add `appointed` year to officers and compute rate per year-at-risk (min(5, 2023 - appointed + 1)); require >= 3 years at risk.
e) Part-year: 1,721 sworn have base < 50% of peer median; 2,068 < 80%. Only 35 of the part-year are currently flagged (so deflation is the bigger error: part-year members pull medians down and cannot reach the flag). Fix = finding 1; do not annualise OT (seasonal, lump payouts); annualise only for display ("annualised base-equivalent"), exclude from scoring.
f) Peer fallback ALL SWORN for titles < 30 members mixes ranks (e.g. COMMANDER, DEPUTY CHIEF compared with all sworn -> pay flags). Fix: fall back to rank band (command staff) or skip scoring when n < 30.

### 4. [M] Matching (build.py match) -- false-positive risk is LOW, and measured
Evidence:
- Matches 10,580 of 13,216 sworn (80.1%): 8,957 by 3-key, 1,623 by 2-key (all have a blank middle initial on exactly one side).
- Placebo test: remove the true profile of 5% / 10% of matched members (simulates new hires / profile absent) and re-run: wrongly matched 1/529 (0.2%) and 0/1,058. Estimated false-match rate < 0.5% (< ~50 people) -- upper bound, concentrated in the 2-key blank-MI bucket.
- Rank check vs CPDP profile (cleaned_rank): 470 differ by title class; most are payroll SERGEANT/LIEUTENANT vs CPDP lower rank (plausible post-snapshot promotion) or "assigned as detective" (not individually verified). Only 17 have CPDP rank higher than payroll title and all are exempt ranks (COMMANDER vs LIEUTENANT/CAPTAIN: payroll career-service title) -- same person. 12 with payroll rank >= 2 levels above CPDP, all command staff. No implausible pair found. 0 matched with appointed date > 2024.
- 4,126 matched members cross-checked vs CPDP summary API cache (full_name, rank, badge): 0 surname mismatches; 0 badge conflicts profile vs summary. (Weak: both keyed by officer_id, so this tests normalisation, not identity.)
- 30 random matches (seed 7) vs final-profiles: all rank/appointment/star plausible (hired 1991-2023; 4 with 2021-23 appointment have no star yet).
- Edge cases: hyphens -> space on both sides (consistent); apostrophe stripped (O'BRIEN -> OBRIEN) vs profile "O BRIEN" -> unmatched (safe); "DE LA CRUZ" vs "DELACRUZ" / "MC LAUGHLIN" vs "MCLAUGHLIN" -> unmatched (safe, 59 recoverable by squashing spaces, 418 active profiles have multiword last names); nicknames (JOE/JOSEPH) -> unmatched (safe). SR/JR collision (father/son) -> both collapse to one key -> pay3 = 2 -> neither matched (safe).
- Real gaps (all safe-side except one): (i) suffix tokens are removed from the *first-name side too*, so a middle initial "V" is dropped (JOHN V -> mi blank) and then compatible with anything; harmless but widens 2-key. (ii) status=='1' filter works: 964 unmatched sworn have an inactive same-name profile -- without the filter these would be cross-linked. But status is as of snapshot; a profile active at snapshot whose officer left after it (not in 2025 payroll) can absorb a same-name new hire. This is the only residual path to a wrong link and is what the placebo measures (<=0.2%).
- Fix (cheap guard, build.py match): after candidate chosen, reject if (a) rank_level(payroll title) - rank_level(profile cleaned_rank) >= 2 or payroll rank LOWER than profile rank except exempt ranks; (b) profile appointed_date year > payroll year; (c) 2-key blank-MI match AND (profile resignation/org_hire inconsistent). Also store `match: "3"|"2"` in officers and, optionally, drop the cmp/sus/law columns for 2-key matches that are flagged only by conduct metrics (show "possible match" with a CPDP link for the reader to verify). Add `name_ambiguous` count (314 ambiguous, 34 MI conflicts, 2,288 no active profile) to meta.counts.
- Under-match: 20% of sworn have no conduct data (mostly 2024-25 hires: no active profile). Conduct flags therefore under-represent recent hires; say so on the page.

### 5. [M] Live end-to-end spot check (3 flagged members) -- all MATCH
Payroll: SoQL dawh-m56b, employee_dataset_id + payroll_year 2025, sum by pay_element -> to the cent.
| member | live payroll total | ours | CPDP live (officer id) | ours |
|---|---|---|---|---|
| ALLEN, KEVIN C (9F5F554C5EE386) | $237,209.81 (base 123,444.00) | 237,209.81 / ot 99,894.06 | 385: 39 allegations, 5 sustained, badge 12788, unit 022 | cmp_all 39, sus 5, badge 12788, unit 022 |
| COGLIANESE, CRAIG M (24AD11D831805A) | $220,209.86 | 220,209.86 / ot 88,616.29 | 4927: 55 alleg., 0 sust., badge 19028, unit 022 | 55 / 0 / 19028 / 022 |
| ALDERDEN, JACOB M (5904E5ACAFF7DF) | $299,061.22 | 299,061.22 / ot 106,826.13 | 295: 15 alleg., 1 sust., badge 62, unit 001, Captain | 15 / 1 / 62 / 001 |
- CRs per officer in complaints-accused.csv: one row per (UID, cr_id), 39/55/15 distinct CRs, SU 5/0/1, 2019+ CRs 2/6/3 (cmp column). CPDP `allegation_count` = our `cmp_all`. Sustained counting has no double-count bug (checked all 263,315 officer-CR pairs: first-row SU == any-row SU).
- Observation: ALLEN is flagged `total`+`ot` and `sus` but his ot includes $48,072 CTA/CHA/Parks details (finding 2), and 3 of his 5 sustained findings are not force-related (Operational Violation, Miscellaneous, Slow/No Response; 2 are excessive force). A reader sees "5 sustained" without category.
- Payroll fetch is sound (SUM per element equals live). Risk: department_code='D57' only; a member paid partly from another department is under-counted (not seen in sample).

### 6. [M] Wording / ethics
- Strong: README/AGENTS/METHOD all say "outlier for review", "complaint = allegation".
- Risks:
  1. The page/data show a named person with red-flag-style `fs/ff` arrays. Flags 'sus' >= 3 (337 members) and 'cmp' and 'law' are conduct signals attached to a real name, some via 2-key matches. Fix: for every conduct flag expose (a) match basis (3-key / 2-key), (b) link to cpdp.co/officer/<id> so the reader can verify, (c) disclaimer line adjacent to the number, not only on the About block.
  2. `lawsuit_total` label "CPDP lawsuit payouts linked to officer" implies officer liability. Reality: City paid the settlement; officer usually named only; multi-officer cases counted in full. Rename: "named in settled suits (total of case payouts)". Never rank by it.
  3. `meta.vintage.lawsuits` says cases ~2011-2019; add "not updated since 2019".
  4. Retiree/stub OT flags (finding 1) name people for a payout rather than behaviour.
  5. 56 civilians (detention aides, clerks) carry flags; no conduct data; pay-only. Recommend scope = sworn only or at least mark civilian with no flag display.
  6. `roster` field = name-only join against roster.json: same-name collisions make it True for the wrong person; cosmetic (do not use as identity).
  7. SOURCES note for the CPDP summaries says "Settlements and judgments linked to named officers": ok; add "no admission of liability".

### 7. [L] Pipeline bugs
- fetch_lawsuits: `todo = [i for i in ids if i not in done]` -> API errors stored as {"error":...} are never retried (12 of 3,000 so far). Fix: `todo = [i for i in ids if i not in done or "error" in done[i]]`.
- build: `with_lawsuit_data` counts only matched with a summary; unmatched can have data; fine. meta.counts has no breakdown of 3-key / 2-key / ambiguous (add).
- build: dead loop `if o["peer"] != o["title"]: pass`.
- build_pay: title chosen by base-category sums only; ties (all-zero base) choose via 1e-6*amt of non-base -> arbitrary for stubs.
- unit-history ends 2024-07; `unit` for members promoted/transferred since is stale (units from CPDP summary API are newer for fetched members: cached `unit` in summaries could override). Cross-check ALLEN/COGLIANESE/ALDERDEN agree.
- audit.py duplicates badge check: 4 badges shared by 2 members ('12327','20168','15607','12395') -> possible bad match or reissued stars; inspect before launch (not done: needs data/raw lookup of those pairs).
- Config comment "~top 2% of sworn" for total_pay/overtime_pay: audit shows 287 (2.0% of 14k) and 303 (2.2%): OK.

## Do-first order
1. Stub/part-year/title-change guard (finding 1) -- removes wrongly named retirees and fixes peer pools.
2. Split pay categories (finding 2).
3. law rule: payee-only or fixed-only; flag multi-officer duplication (3a/3b).
4. Match guard + match basis in output + 4 duplicate-badge pairs review (4).
5. Wording changes (6); error retry (7).
