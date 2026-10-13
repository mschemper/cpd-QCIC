# STATE.md -- what is true now. Update with every change.

## Status
- v1 in progress, unreleased. Not published.
- Branch: claude/epic-lovelace-osevpd. Draft PR to main: pending.
- Published page URL: TBD.
- Git: v1 committed on the branch; see PR.

## Data vintage (per column; shown on page)
- Payroll: dawh-m56b, payroll year 2025. Unaudited, point-in-time.
- Roster: xzkq-xp2w, current ("on current roster" mark only).
- Complaints: CPDP unified data, 2000-2023 (window 2019-2023).
- Units: FOIA roster 2023-11 (primary), else CPDP unit history to 2024-07. No 2024+ officer-level unit source exists (docs/research/LOCATION.md).
- Lawsuits: CPDP API cases ~2011-2019 (11,713 of 11,764 summaries; 51 persistent HTTP 500) + City DOL litigation reports 2022-2025 (594 records). 2020-2021 not parsed (docs/research/LAWSUITS.md).
- COPA/BIA: live city feeds, district counts only.

## Counts (tools/audit.py, 2026-10-13)
- Members 14,072; sworn titles 13,216; roster 12,234; part-year (not scored on pay) 1,890.
- Sworn matched to CPDP 10,670 (80.7%); est. false-match rate < 0.5% (docs/research/REVIEW.md).
- Matched with a district unit 5,819; rest in named non-district units (detective areas, training, airport...).
- Badges 8,969 (4 duplicated).
- Pay $1,855,577,355: core OT $257,928,144; outside-agency details $33,430,114; comp-time buybacks $47,528,095.
- DOL cases linked: 213 paid cases -> 486 current members.

## Flags (v1)
- Statistical (robust z >= 3.5 by job title; log scale for money; lawsuits among payees only): total 77, ot 44, cmp 450, law 26.
- Fixed: total >= $250k 286; ot >= $100k 150; ot >= base 44; complaints >= 10 in 5 yr 145; sustained >= 3 343; lawsuits >= $250k 345.
- Any flag: 1,355.

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
