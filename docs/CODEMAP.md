# CODEMAP.md -- files per subject

## Fetch (sources -> data/raw/)
- src/qcic/fetch.py: STEPS, get, soql, write_json, fetch_payroll, fetch_roster, fetch_oversight, fetch_districts, unified_via_git, fetch_unified, fetch_lawsuits, main.
- Steps: payroll roster oversight districts unified lawsuits. Entry: python3 -m src.qcic.fetch.

## Build (data/raw/ -> site/data.json)
- src/qcic/build.py: norm, split_payroll_name, match, median, quantile, robust_scale, pct_rank, build_pay, build_complaints, build_units, district_of, badge_of, build_districts, main.
- Entry: python3 -m src.qcic.build.

## Config and rules
- config/qcic.toml: thresholds, pay-element categories, sworn titles. Only place for thresholds.
- docs/METHOD.md: matching, metrics, flags.
- docs/DATA.md: sources and caveats.

## Schema and tests
- docs/SCHEMA.md: site/data.json contract.
- tests/test_schema.py: validate(data); SchemaTests.
- tests/test_build.py: SplitPayrollNameTests, MatchTests, StatsTests, DistrictTests, BadgeTests.
- tests/fixtures/sample.json: fixture.

## Tools
- tools/checks.sh: gate (unit tests; page QA if tools/qa_page.py exists).
- tools/audit.py: current numbers.
- tools/make_sample.py: sample data generator.

## Page (site/)
- site/data.json: build output (committed).
- site/index.html: page (built by another agent; see docs/DESIGN.md).
- Design rules: docs/DESIGN.md.

## Data (gitignored)
- data/raw/: cached fetch output (payroll_2025.json, roster.json, bia_by_beat.json, copa_by_beat.json, districts.geojson, cpdp_summaries.json, cpdp/, _invinst/).
