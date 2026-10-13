# HISTORY.md -- rationale behind decisions

- Payroll FMPS, not the 2013 OT feeds: the 2013 overtime datasets (5yfy-npzv, skd4-skdv) cover 2013 only; yearly OT files stop at 2022; payroll covers 2023-present with every pay element.
- COPA/BIA at district level only: city feeds carry no officer names or IDs, so they cannot be attached to a person without guessing.
- CPDP for officer-level complaints and lawsuits: the only source linking named officers to complaints and settlements. Lawsuit data is from ~2011-2019 cases.
- Stdlib-only Python: no install step; runs on a bare machine.
- Static page plus data.json: no server; the page is readable offline and the data is inspectable.
- Robust z (median/MAD) by job title: pay and overtime depend on rank and title, so peers are the same title. Fixed limits added alongside because plain-language thresholds are easier to explain. Mark chose "both, shown separately".
