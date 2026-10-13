# AGENTS.md -- CPD-QCIC (Mark). Agent entry point.
Index + hard rules. Detail lives in docs/: point, never copy. Facts that change (data vintage, match rates, published URL, pending work) live ONLY in docs/STATE.md. CLAUDE.md imports this file.

## P0 -- order = precedence; overrides everything below
0. Written for agents, not humans: adherence + minimal tokens; imperative, terse, no rationale (-> docs/HISTORY.md), no duplication. Every edit keeps this form.
1. Ambiguous request -> ask clarifying questions (all in one call) before any work. Never guess-and-rebuild.
2. Fixes: no apology. State what changed: file, behaviour delta, what Mark should check.
3. Subagents: use several, in parallel, whenever work splits into independent parts (fetch vs build vs page vs docs; one per source; one per view). Fit the model: Haiku = search/sweeps/mechanical edits/data probes; Sonnet = routine code/tests/page build; main = design, method, integration, final review. Each subagent gets a standalone prompt: files, contract (data.json schema), done-check.
4. Tool calls: plan; batch independent calls; wait for ALL returns before reading any; dependents in next batch.
5. ADHD output mode always on: read + follow docs/skills/i-have-adhd/SKILL.md at session start (ayghri/i-have-adhd @839872f, MIT). Off only on "stop adhd mode"/"normal mode", that session only. Conflict -> P0 wins (P0.1 allows >1 question).
6. Accuracy over drama: a flag is "statistical outlier for review", never an accusation. Never assert misconduct beyond what the source states. Ambiguous name match -> leave unmatched; never guess an identity.

## What this is
CPD-QCIC ("Quis custodiet ipsos custodes?"): static web dashboard flagging Chicago Police Department members who are cost or conduct outliers -- total pay, overtime, misconduct complaints, lawsuit payouts -- with each flagged member's unit/district on a map. Python pipeline (stdlib only) -> site/data.json -> site/index.html. Interactive (sort, filter, drill-down); not a wall display.

## Session start (in order)
1. docs/STATE.md -- what is true now: data vintage, match rates, published page, standing preferences.
2. docs/BACKLOG.md -- open requests + bugs; plan from here. docs/CODEMAP.md -- files per subject.
3. docs/DATA.md before touching a source; docs/METHOD.md before touching scoring or flags; docs/DESIGN.md before touching the page.
4. docs/CHANGELOG.md -- per-release changes. Old rationale: docs/HISTORY.md.

## Pipeline
- Fetch: `python3 -m src.qcic.fetch [steps] [--year N]` -> data/raw/ (gitignored, cached). Steps: payroll roster oversight districts unified lawsuits. `lawsuits` = ~12k throttled CPDP API calls (~20-30 min): run_in_background, resumable.
- Build: `python3 -m src.qcic.build` -> site/data.json (committed; public-record derived).
- Thresholds + pay-element categories: config/qcic.toml only. Never hard-code a threshold.
- Officer identity: payroll employee_dataset_id is the key; CPDP UID/officer_id joined by name rules in docs/METHOD.md "Matching".
- City COPA/BIA feeds carry no officer names: district-level context only.

## Gates
- `bash tools/checks.sh` before any behaviour-changing commit: unit tests, data.json schema, page QA (tokens-only colours, no chartjunk, text floors, no external JS beyond pinned CDN).
- Text floor 14px body / 12px table on the page.

## Design rules (docs/DESIGN.md)
- Tufte: maximise data-ink; no chartjunk, no gradients, shadows, 3D, rounded rectangles; direct labels over legends; small multiples; sparklines; dot/strip plots over bars; every number with its peer context (median, rank).
- Type: ET Book (Tufte family), cream paper, ink. Colours only via CSS tokens in site/index.html :root. One accent = flag. Light by default; dark via prefers-color-scheme.
- Glanceable: headline counts first, then tables, then drill-down.

## Secrets
- None needed: all sources public. Never commit tokens. If a Socrata app token is added: env SOCRATA_APP_TOKEN only.

## Known pitfalls (detail at the link)
- Payroll has same-name employees: aggregate on employee_dataset_id -- DATA.md "Payroll".
- CPDP unified data ends ~2023 (complaints) / 2024 (units); payroll is 2025 -- show vintage per column -- DATA.md.
- Linked "Police Overtime" datasets (5yfy-npzv, skd4-skdv) are 2013-only -- DATA.md.
- r5jy-3eix is a filtered view; query parent xzkq-xp2w -- DATA.md.

## Git
- Repo mschemper/cpd-QCIC. Work on the assigned branch; PR as draft; never force-push.

## Definition of done
Gates pass; update docs/STATE.md (+ BACKLOG.md if changed) and, for a release, docs/CHANGELOG.md; commit; push.
