# CPD-QCIC

Quis custodiet ipsos custodes? Who will guard the guardians?

Static dashboard flagging Chicago Police Department members as statistical outliers for review on total pay, overtime, misconduct complaints and lawsuit payouts, with each flagged member's unit or district.

## Caveats
- Flags are statistical outliers for review. They are not findings of wrongdoing.
- Complaints are allegations. A not-sustained finding is not an exoneration; a sustained finding is not a criminal finding.
- Lawsuit payouts are settlements or judgments, usually without admission of liability. A multi-officer case counts in full for each named officer.
- Payroll is unaudited and point-in-time. Payroll periods do not equal earning periods.
- Matching is by name rules; ambiguous matches are left unmatched.

## Quickstart
```
python3 -m src.qcic.fetch
python3 -m src.qcic.build
bash tools/checks.sh
python3 -m http.server -d site
```
Then open http://localhost:8000.

## Sources
- Employee Payroll Data: https://data.cityofchicago.org/d/dawh-m56b
- Current Employee Names, Salaries: https://data.cityofchicago.org/d/xzkq-xp2w
- COPA complaints: https://data.cityofchicago.org/d/mft5-nfa8
- BIA complaints: https://data.cityofchicago.org/d/t7km-zpxd
- Police District boundaries: https://data.cityofchicago.org/d/24zt-jpfn
- CPDP unified data (Invisible Institute): https://github.com/invinst/chicago-police-data
- CPDP API: https://api.cpdp.co/api/v2/ and https://cpdp.co
- Lawsuit context: Chicago Reporter "Settling for Misconduct"

## Docs
- docs/DATA.md, docs/METHOD.md, docs/SCHEMA.md, docs/DESIGN.md, docs/STATE.md, docs/BACKLOG.md, docs/CODEMAP.md.

## License
Code: TBD by owner.
