# LOCATION.md -- up-to-date unit/district research (13 Oct 2026)

## Verdict
- No 2024-2026 officer-level unit feed is public. Best fetchable: Nov-2023 FOIA roster (Invisible Institute repo), newer + fuller than unit-history.csv.
- Use as primary location (fills ~1,670 no-unit officers; fixes stale unit for ~4,600 of 11,272 matched); keep unit-history as fallback.
- ~2,600 post-snapshot hires: no source. Leave unit blank.

## Ranked sources (all tested 13 Oct 2026)
| # | Source | Recency | Officer-level | Join key | Tested | Effort |
|---|---|---|---|---|---|---|
| 1 | invinst/chicago-police-data `individual/roster_1985-2023_2023-11_p891976/export/output/*.csv.gz` | snapshot Nov 2023 (max appointed 2023-10-10) | yes: 11,721 active, all with unit + unit_description + star1..7 | star1; or first+last+birth_year (11,272 unique matches to final-profiles active) | curl raw.githubusercontent.com 200, 405 KB; parsed | done: src/qcic/sources/units_recent.py |
| 2 | CPDP API /api/v2/officers/<id>/summary/ `unit`,`historic_units` | NOT newer: of 30 sampled active, API unit = latest unit-history row in ~22; 3 had none | yes | officer_id | 30 calls | cached already in data/raw/cpdp_summaries.json (3,500) |
| 3 | invinst `roster-inactive_2015-2024_2024-05_p944287` | May 2024 | inactive officers only | name | listed, not parsed | skip |
| 4 | invinst `unit-history_2014-2020_2020-10_p596580` | Oct 2020 | yes | name/star | listed | older than current |
| 5 | CPDP /api/v2/units/ | -- | -- | -- | 301 then 404 | no endpoint; unit table only via summaries |
| 6 | Data Portal COPA ufxy-tgry (By Involved Officer) | live (2026-10-07) | NO names/IDs: beat, race, sex, age, years_on_force | none | SODA 200 | district counts only (already used) |
| 7 | Data Portal z8bn-74gv Police Stations | current | 23 rows: district HQ address + lat/lon | district | SODA 200 | optional map pins |
| 8 | FMPS payroll dawh-m56b fund / appropriation / department_function | 2023-present | yes but no unit: fund = F0100 Corporate, department_function = Public Safety, appropriation = pay type (A0005 salary, A0020 OT, A0022 duty availability...) | -- | SoQL group-by, department_code='D57' | no unit signal |
| 9 | Data Portal catalog search (police unit assignment / roster / beat / watch) | -- | none found | -- | catalog API | none |
| 10 | Web: Lucy Parsons Labs, Sun-Times/WBEZ, National Police Index, CPDP 2024-25 | -- | no 2025 roster release found | -- | WebSearch | only FOIA request pages (Chicago Justice Project, MuckRock); file a FOIA for current roster+unit if wanted |
| 11 | invinst GitHub commits | last commit 1 Sep 2025 (LFS re-enable); data newest = complaints 2023-09, roster 2023-11, inactive roster 2024-05 | -- | -- | git sparse clone | -- |

## Notes
- Roster descriptions are 2023 names (e.g. 610 = Detectives - Area 1; CPDP 2017 table says Detective Area - Central). Districts 13, 21, 23 absent (merged); 25 = Grand Central.
- Roster is a snapshot, not history: officers moved after Oct 2023 are stale; payroll gives no correction.
- Join caveat: unique name+birth_year only (AGENTS P0.6); ambiguous -> unmatched. star key can be reassigned over time.
- Raw github.com/.../raw/ URL returns 403; raw.githubusercontent.com returns 200.
- Not covered: CPD directives site, 2024 reorganisation page (no officer-level data; unit names only).

## Current unit -> description (roster Nov 2023, 125 units)
```csv
unit,description
1,1ST DISTRICT - CENTRAL
2,2ND DISTRICT - WENTWORTH
3,3RD DISTRICT - GRAND CROSSING
4,4TH DISTRICT - SOUTH CHICAGO
5,5TH DISTRICT - CALUMET
6,6TH DISTRICT - GRESHAM
7,7TH DISTRICT - ENGLEWOOD
8,8TH DISTRICT - CHICAGO LAWN
9,9TH DISTRICT - DEERING
10,10TH DISTRICT - OGDEN
11,11TH DISTRICT - HARRISON
12,12TH DISTRICT - NEAR WEST
14,14TH DISTRICT - SHAKESPEARE
15,15TH DISTRICT - AUSTIN
16,16TH DISTRICT - JEFFERSON PARK
17,17TH DISTRICT - ALBANY PARK
18,18TH DISTRICT - NEAR NORTH
19,19TH DISTRICT - TOWN HALL
20,20TH DISTRICT - LINCOLN
22,22ND DISTRICT - MORGAN PARK
24,24TH DISTRICT - ROGERS PARK
25,25TH DISTRICT - GRAND CENTRAL
44,RECRUIT TRAINING SECTION (RTS)
45,DISTRICT REINSTATEMENT SECTION (DRS)
50,AIRPORT OPERATIONS (AO) - NORTH
51,AIRPORT OPERATIONS (AO) - SOUTH
55,MOUNTED UNIT (MU)
57,DETAIL SECTION (DS)
59,MARINE OPERATIONS UNIT (MOU)
60,HELICOPTER OPERATIONS UNIT (HOU)
79,SPECIAL INVESTIGATIONS UNIT (SIU)
102,COMMUNICATIONS DIVISION (CD)
111,OFFICE OF THE SUPERINTENDENT (OTS)
114,LEGAL AFFAIRS DIVISION (LAD)
115,COMPSTAT UNIT (CU)
116,CPIC / DEPLOYMENT OPERATIONS CENTER (DOC)
117,RISK MANAGEMENT UNIT (RMU)
120,OFFICE OF CONSTITUTIONAL POLICING AND REFORM (OCPR)
121,BUREAU OF INTERNAL AFFAIRS (BIA)
122,FINANCE DIVISION (FD)
123,HUMAN RESOURCES DIVISION (HRD)
124,TRAINING AND SUPPORT GROUP (TSG)
125,FIELD TECHNOLOGY AND INNOVATION SECTION (FTIS)
126,INSPECTION DIVISION (ID)
127,RESEARCH AND DEVELOPMENT DIVISION (R&D)
128,PROFESSIONAL COUNSELING DIVISION (PCD)
129,LABOR RELATIONS DIVISION (LRD)
131,4TH AMENDMENT STREET STOP REVIEW UNIT (4ASRU)
132,SPECIAL OPERATIONS GROUP (SOG)
133,FIELD TECHNOLOGY UNIT (FTU)
135,OFFICE OF COMMUNITY POLICING (OCP)
136,SPECIAL EVENTS SECTION (SES)
138,STRATEGIC INITIATIVES DIVISION (SID)
140,OFFICE OF THE FIRST DEPUTY SUPERINTENDENT (OFDS)
141,SPECIAL FUNCTIONS DIVISION (SFD)
142,BUREAU OF PATROL (BOP)
143,CRISIS INTERVENTION TEAMS (CIT)
145,TRAFFIC SECTION (TS)
148,TRAFFIC COURT UNIT (TCU)
150,BUREAU OF COUNTERTERRORISM (BCT)
153,SPECIALTY VEHICLES (SV)
161,ADMINISTRATIVE SUPPORT DIVISION (ASD)
162,RECORDS SERVICES SECTION (RSS)
163,RECORDS INQUIRY SECTION (RIS)
166,FIELD SERVICES SECTION (FSS)
167,EVIDENCE AND RECOVERED PROPERTY SECTION (ERPS)
168,AUTO POUNDS SECTION (APS)
169,POLICE DOCUMENTS SECTION (PDS)
171,CENTRAL DETENTION UNIT (CDU)
172,EQUIPMENT AND SUPPLY SECTION (ESS)
177,FORENSIC SERVICES DIVISION (FSD)
180,BUREAU OF  DETECTIVES (BOD)
181,INVESTIGATIVE RESPONSE TEAM (IRT)
184,YOUTH INVESTIGATION DIVISION (YID)
187,CRIMINAL REGISTRATION UNIT (CRU)
188,NARCOTICS AND VICE INVESTIGATIONS GROUP (NVIG)
189,NARCOTICS DIVISION (ND)
191,INTELLIGENCE SECTION (IS)
192,VICE SECTION (VS)
193,GANG INVESTIGATION DIVISION (GID)
195,CONFIDENTIAL ANALYTICS SECTION (CAS)
196,ASSET FORFEITURE SECTION (AFS)
211,DEPUTY CHIEF - AREA 1
212,DEPUTY CHIEF - AREA 2
213,DEPUTY CHIEF - AREA 3
214,DEPUTY CHIEF - AREA 4
215,DEPUTY CHIEF - AREA 5
216,DEPUTY CHIEF - CENTRAL CONTROL GROUP (CCG)
220,PROFESSIONAL STANDARDS AND COMPLIANCE DIVISION (PSCD)
221,RANDOM DRUG SECTION (RDS)
222,TIMEKEEPING UNIT (TU) - HEADQUARTERS
223,OFFICER SUPPORT UNIT (OSU)
224,AWARDS SECTION (AS)
231,MEDICAL SECTION (MS)
240,RECRUITMENT AND RETENTION SECTION (RRS)
241,TROUBLED BUILDING UNIT (TBU)
261,COURT SECTION (CS)
276,DETAIL SECTION (DS) - OEMC
277,CRIME SCENE PROCESSING UNIT (CSU)
341,CANINE UNIT (CU)
353,SPECIAL WEAPONS AND TACTICS (SWAT) UNIT
376,ALTERNATE RESPONSE SECTION (ARS)
441,SPECIAL ACTIVITIES SECTION (SAS)
442,BOMB SQUAD (BS)
484,MISSING PERSONS SECTION (MPS)
541,FOP DETAIL
543,DETACHED SERVICES (DS) - MISCELLANEOUS DETAIL
544,DETACHED SERVICES (DS) - UNIFORMED SUPPORT DIVISION
545,PBPA SERGEANT
549,INSPECTOR GENERAL DETAIL UNIT (IGDU)
602,CENTRAL INVESTIGATIONS DIVISION (CID)
603,ARSON SECTION (AS)
604,FINANCIAL CRIMES SECTION (FCS)
606,INVESTIGATIVE FIELD GROUP (IFG)
608,MAJOR ACCIDENT INVESTIGATION SECTION (MAIS)
610,DETECTIVES - AREA 1
620,DETECTIVES - AREA 2
630,DETECTIVES - AREA 3
640,DETECTIVES - AREA 4
650,DETECTIVES - AREA 5
701,PUBLIC TRANSPORTATION (PT)
704,TRANSIT SECURITY UNIT (TSU)
715,CRITICAL INCIDENT RESPONSE TEAM (CIRT)
716,COMMUNITY SAFETY TEAM (CST)
721,TACTICAL REVIEW AND EVALUATION DIVISION
```
