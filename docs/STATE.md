# STATE.md -- what is true now. Update with every change.

## Status
- v1 built, unreleased (draft PR). Published privately as claude.ai artifact.
- Branch: claude/epic-lovelace-osevpd. Draft PR: https://github.com/mschemper/cpd-QCIC/pull/1
- Published page (private; owner shares via Share menu): https://claude.ai/artifact/W4hncuYMsZQVYchSQreJdU. Republish = Artifact publish site/index.html with url=<that link>, files {data.json: site/data.json}.
- Git: v1 committed on the branch; see PR.

## Data vintage (per column; shown on page)
- Payroll: dawh-m56b, payroll year 2025. Unaudited, point-in-time.
- Roster: xzkq-xp2w, current ("on current roster" mark only).
- Complaints: CPDP unified data, 2000-2023 (window 2019-2023).
- Units: FOIA roster 2023-11 (primary), else CPDP unit history to 2024-07. No 2024+ officer-level unit source exists (docs/research/LOCATION.md).
- Use of force: TRR 2004-2023-09 (window 2021-2023).
- OT trend: payroll periods 2024-2026 (2026 through period 6).
- Payments: DOL J&S payment requests 2024-2026-08-31. Council: eLMS 2024-2026.
- Lawsuits: CPDP API cases ~2011-2019 (11,713 of 11,764 summaries; 51 persistent HTTP 500) + City DOL litigation reports 2022-2025 (594 records). 2020-2021 not parsed (docs/research/LAWSUITS.md).
- COPA/BIA: live city feeds, district counts only.

## Counts (tools/audit.py, 2026-10-13)
- Members 14,072; sworn titles 13,216; roster 12,234; part-year (not scored on pay) 1,890.
- Sworn matched to CPDP 10,670 (80.7%); est. false-match rate < 0.5% (docs/research/REVIEW.md).
- Matched with a district unit 5,819; rest in named non-district units (detective areas, training, airport...).
- Badges 8,969 (4 duplicated).
- Pay $1,855,577,355: core OT $257,928,144; outside-agency details $33,430,114; comp-time buybacks $47,528,095.
- DOL cases linked: 213 paid cases -> 486 current members.

## Flags (v1.1)
- Statistical (robust z >= 3.5 by job title; log scale for money; lawsuits + use of force among those with >= 1): total 77, ot 44, cmp 450, law 26, frc 118.
- Fixed: total >= $250k 286; ot >= $100k 150; ot >= base 44; complaints >= 10 in 5 yr 145; sustained >= 3 343; lawsuits >= $250k 345; use of force >= 10 in 3 yr 52.
- Any flag: 1,415.

## New in v1.1 (2026-10-13)
- Use of force: 10,670 matched officers scored; TRR 2021-2023 (data to 2023-09). Firearm TRR 118 officers, taser 246.
- OT trend: core OT periods 1-6: 2024 $79.2M, 2025 $48.6M, 2026 $47.3M (-2.7% vs 2025). Payroll refresh 2026-05-18.
- DOL payments (POLICE): 2024 $108.3M (265 lines), 2025 $266.1M (280), 2026 to 08-31 $246.5M (528). Reversed convictions 66% of 2024-2026. Held out: 22 L 3091 $750M line (press: $7.5M) -- ask DOL / re-check next file.
- Council approvals: 78 police settlements 2024-2026; 45 officer-linked DOL cases carry a Council date; 240 carry DOL payment rows.

## Standing preferences (Mark)
- ADHD output mode on (docs/skills/i-have-adhd/SKILL.md).
- Parallel subagents on fitted models.
- Tufte for all charts (docs/DESIGN.md).
- Never guess identities; leave ambiguous matches unmatched.
- Wording: "statistical outlier for review".
- Time estimates concrete.

## Fetch quirks
- Socrata GROUP BY server-side ~1k rows/min: payroll pulls raw CSV (~50k rows / 3 s) and aggregates locally.
- Raw GitHub URLs return 403 through the cloud proxy: sparse git clone fallback for unified data.
- CPDP API ~0.3 s/call, 4 workers (~25 min full run); errors retried on re-run.
- raw.githubusercontent.com works; github.com/.../raw/ and media.githubusercontent.com 403.
- DOL PDFs need pdfplumber (optional dependency, lawsuits_recent step only).

## Pending
- See docs/BACKLOG.md.
- Research done: docs/research/LAWSUITS.md, LOCATION.md, REVIEW.md (fixes applied: full-year guard, OT split, log z, positive-only law, name squash, match path, error retry).
