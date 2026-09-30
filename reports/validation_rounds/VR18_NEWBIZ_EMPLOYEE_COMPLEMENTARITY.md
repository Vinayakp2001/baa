# VR18 — New Business Detection + Employee-Size Consistency + Source Complementarity

Generated: `2026-09-26T11:18:38Z`
Script: `scripts/probe_vr18_newbiz_employee_complementarity.py`

---

## PART A — New-Business Event Signals

| Source | Province | Date Field | Event Semantics | Last 30d | Last 90d | Last 365d | Usability |
|---|---|---|---|---|---|---|---|
| Calgary | AB | first_iss_dt | first licence issuance date — new business entering the muni | 227 | 774 | 3249 | HIGH — first_iss_dt directly i |
| Edmonton | AB | originalissuedate + most_recent_issue_date | originalissuedate = first ever licence; most_recent_issue_da | 757 | 1332 | 1558 | HIGH — originalissuedate is th |
| Vancouver | BC | issueddate | issueddate = licence issue/renewal date; folderyear = year o | 100 | 100 | 100 | MEDIUM — issueddate alone does |
| Winnipeg | MB | issue_date | issue_date = licence issuance or renewal date. Dataset inclu | 2 | 81 | 662 | LOW-MEDIUM — issue_date is amb |
| Corporations Canada active CBCA CSV | Federal | ? | ? | ? | ? | ? | ? |
| NNI Nunavut | NU | ? | ? | ? | ? | ? | ? |
| Saskatoon New Businesses XLSX | SK | None | New business licence issuances in Saskatoon — municipal lice | ? | ? | ? | HIGH — this file is explicitly |

### Detailed findings

#### Calgary (AB)
- Date field: first_iss_dt
- Event semantics: first licence issuance date — new business entering the municipal system
- Sample size: 5000
- Date buckets: {'total_with_date': 4970, 'last_30d': 227, 'last_90d': 774, 'last_365d': 3249}
- New-biz usability: HIGH — first_iss_dt directly identifies first-ever licence for this business entity
- Observation: Sample 5000 most-recent rows. Last30d=227, Last90d=774, Last365d=3249.

#### Edmonton (AB)
- Date field: originalissuedate + most_recent_issue_date
- Event semantics: originalissuedate = first ever licence; most_recent_issue_date = latest renewal/amendment
- Sample size: 5000
- Original issue date buckets: {'total_with_date': 4975, 'last_30d': 757, 'last_90d': 1332, 'last_365d': 1558}
- Most recent issue date buckets: {'total_with_date': 4999, 'last_30d': 2906, 'last_90d': 4999, 'last_365d': 4999}
- New-biz usability: HIGH — originalissuedate is the correct new-business signal; most_recent_issue_date tracks activity
- Observation: Sample 5000 most-recent rows. OrigIssue Last365d=1558. MostRecent Last30d=2906.

#### Vancouver (BC)
- Date field: issueddate
- Event semantics: issueddate = licence issue/renewal date; folderyear = year of licence folder (proxy for licence year). Not strictly first-ever issuance — can be renewal.
- Sample size: 100
- Date buckets: {'total_with_date': 100, 'last_30d': 100, 'last_90d': 100, 'last_365d': 100}
- New-biz usability: MEDIUM — issueddate alone doesn't distinguish first licence from renewal; combine with folderyear min to approximate new-business signal
- Observation: Sample 100 most-recent rows. Last30d=100. Statuses: {'Issued': 100}.

#### Winnipeg (MB)
- Date field: issue_date
- Event semantics: issue_date = licence issuance or renewal date. Dataset includes historical/closed records — active filtering on status required.
- Sample size: 5000
- Date buckets: {'total_with_date': 5000, 'last_30d': 2, 'last_90d': 81, 'last_365d': 662}
- New-biz usability: LOW-MEDIUM — issue_date is ambiguous (first vs renewal); only 275 unique business names in 13,757 rows. Grain is licence-event.
- Observation: Sample 5000 most-recent rows. Last30d=2. Statuses sample: {'Issued': 605, 'Approved - New (L)': 1, 'Closed (L)': 4237, 'Ceased Operation': 137, 'Vacant': 3}.
- **KEY FINDING:** 4,237 of 5,000 sampled rows (84.7%) are status "Closed (L)". Dataset is predominantly a historical closure/event log. Only 605 "Issued" + 1 "Approved - New" in the most-recent 5k rows. Not suitable as a current business master — confirmed event log only.

#### Corporations Canada active CBCA CSV (Federal)
- Date field: ?
- Event semantics: ?
- Sample size: ?
- New-biz usability: ?
- Observation: File not found in data/raw/ — skipped. Use CBCA monthly incorporations HTML (VR03) for new-business signal.

#### NNI Nunavut (NU)
- Date field: ?
- Event semantics: ?
- Sample size: ?
- New-biz usability: ?
- Observation: HTTP 0

#### Saskatoon New Businesses XLSX (SK)
- Date field: None
- Event semantics: New business licence issuances in Saskatoon — municipal licence grain
- Sample size: 51
- New-biz usability: HIGH — this file is explicitly scoped to new businesses in the period. Small volume (51 rows) but clean signal.
- Observation: 51 rows. Date fields: []. Buckets: {}.

---

## PART B — Employee-Size Consistency

### Vancouver (BC)
- Employee field: numberofemployees
- Definition: Number of staff employed with the business (source-documented)
- Sample size: 100
- Values parsed: 100
- Bucket distribution: {'0 (no employees)': 3, '1-4': 38, '5-9': 36, '10-19': 17, '20-49': 6, '50-99': 0, '100-199': 0, '200-499': 0, '500-999': 0, '1000+': 0, 'null/unparseable': 0}
- Observation: Sample 100 Issued-status records. 100 employee values parsed.

### BC Indigenous Business Listings (BC)
- Employee field: Number of Employees
- Definition: Not source-documented. Mix of integer counts and range strings observed.
- Sample size: 500
- Values parsed: ?
- Bucket distribution: {'0 (no employees)': 0, '1-4': 0, '5-9': 0, '10-19': 0, '20-49': 0, '50-99': 0, '100-199': 0, '200-499': 0, '500-999': 0, '1000+': 0, 'null/unparseable': 0}
- Range/text values sample: ['55 to 99', '50 to 99', '10 to 19', '1 to 4', '500 plus', '5 to 9', '200 to 499', '100 to 199', '20 to 49']
- Observation: 500-row sample. 0 integer values. 263 range/text values. Sample range values: ['55 to 99', '50 to 99', '10 to 19', '1 to 4', '500 plus'].
- **KEY FINDING:** ALL employee values in this dataset are range strings, not integers (e.g. "10 to 19", "50 to 99", "500 plus"). Zero integer values found. Fill rate = 52.6% (263/500). Direct bucket mapping IS possible via range-string parsing — "10 to 19" maps cleanly to the 10-19 bucket. "500 plus" is a combined bucket (same limitation as StatsCan). Parser must handle range strings not integers.

### NNI (?)
- Employee field: ?
- Definition: ?
- Sample size: ?
- Values parsed: ?
- Observation: HTTP 0

### StatsCan Benchmark note
- Canada-wide employer businesses by size bucket (from VR05). Individual-business data is confidential — these are aggregate counts only.
- Limitation: 500 plus is a combined bucket — cannot split into 500-999 / 1000+ from StatsCan
- Pipeline implication: Pipeline sources (Vancouver, BC Indigenous, NNI) can provide 500-999 vs 1000+ split at the individual-record level

---

## PART C — Source Complementarity

### Province Coverage Matrix

| Province | Confirmed Sources |
|---|---|
| Federal | Corporations Canada active CBCA CSV, Corporations Canada API |
| BC | Corporations Canada API, BC OrgBook API, Vancouver business licences, BC Indigenous Business Listings |
| AB | Calgary business licences, Edmonton business licences |
| MB | Winnipeg business licences, Manitoba Companies Office weekly PDF |
| SK | Saskatoon all businesses, Saskatoon new businesses |
| ON | Ontario Select Licence |
| QC | ❌ NO CONFIRMED SOURCE |
| NS | ❌ NO CONFIRMED SOURCE |
| NB | ❌ NO CONFIRMED SOURCE |
| PE | ❌ NO CONFIRMED SOURCE |
| NL | ❌ NO CONFIRMED SOURCE |
| YT | ❌ NO CONFIRMED SOURCE |
| NT | ❌ NO CONFIRMED SOURCE |
| NU | NNI Nunavut |

### Province Gaps (no confirmed source): ['QC', 'NS', 'NB', 'PE', 'NL', 'YT', 'NT']

### Field Coverage Matrix

- employee_count: Vancouver (100% licence-grain); NNI (integer, conditional); BC Indigenous (52.6%, mixed int/range)
- phone: Ontario Select Licence (99%); NNI (conditional); BC Indigenous (93.4%)
- email: Ontario Select Licence (81.2%); NNI (present); BC Indigenous (89.4%)
- website: Ontario Select Licence (10%); BC Indigenous (52.4%)
- contact_name: NNI (contact_name field); BC Indigenous (Primary Contact 87.8%)
- director_name: Corporations Canada API (_embedded.directors[])
- address: All municipal licence sources; Corporations Canada CSV; BC Indigenous; NNI
- postal_code: Vancouver (53.4%); BC Indigenous (93.4%); NNI (present); Corporations Canada CSV
- naics_industry: Saskatoon (NAICS present); BC Indigenous (Industry Sector 97%); NNI (Sectors/Goods/Services)
- new_business_event: Calgary first_iss_dt; Edmonton originalissuedate; Manitoba weekly PDFs (Incorporations category); CBCA monthly incorporations HTML (VR03); Saskatoon new-businesses file

### Coverage Observations

- QC: No confirmed free source. REQ blocked (non-commercial licence). Largest unresolved gap.
- NS: RJSC WAF-blocked. Halifax HRM ArcGIS URL 404. Remains unresolved.
- PE: OCBR auth required. Not suitable.
- NL: CADO explicitly prohibited for value-added use.
- NT: NWT CROS confirmed (targeted verification only, basic info free). Yellowknife directory 404.
- YT: Supplier directory 403 (OGL confirmed, browser manual download deferred).
- NB: Moncton timed out. Fredericton portal alive (2025-03-13 date signal) — dataset URL unresolved. ODBus had only sector-specific sources (grocery/pharmacy).
- BC: Best-covered province. Vancouver (206k), BC OrgBook (verification), BC Indigenous (enrichment), Calgary/Edmonton cover adjacent AB. Burnaby/Kelowna portals alive but dataset URLs unresolved.
- ON: Ontario Select Licence is sector-specific (regulated businesses). Toronto WAF-blocked. Hamilton/Ottawa/Mississauga ArcGIS URLs returned 400 — likely resource ID rotation, not dead portals.
- Employee count sources: only 3 confirmed — Vancouver (licence-grain), NNI (small Nunavut population), BC Indigenous (sector-specific). No municipal employee count for Calgary/Edmonton/Winnipeg/Saskatoon.

### Confirmed Source Inventory

| Source | Province(s) | Grain | Rows | New-Biz Signal | Contact Fields | Employee |
|---|---|---|---|---|---|---|
| Corporations Canada active CBCA CSV | Federal — all provinces | corporation | 645005 | CBCA monthly incorporations (VR03) | none | no |
| Corporations Canada API | Federal — CBCA corps | corporation | API — query by corp number | activities[] endpoint | director name+address | no |
| BC OrgBook API | BC | entity | API only — bulk prohibited | registration date + credential history | none (legislatively restricted) | no |
| Calgary business licences | AB | licence | 23178 | first_iss_dt (HIGH) | none | no |
| Edmonton business licences | AB | licence | 43719 | originalissuedate (HIGH) | none | no |
| Vancouver business licences | BC | licence | 206024 | issueddate + folderyear (MEDIUM) | none | numberofemployees (100%) |
| Winnipeg business licences | MB | licence-event | 13757 | issue_date — ambiguous (LOW) | none | no |
| Saskatoon all businesses | SK | licence | 7472 | no date field in all-biz file | none | no |
| Saskatoon new businesses | SK | licence | 51 | explicit new-licence file (HIGH — small volume) | none | no |
| Ontario Select Licence | ON | licence | 674 | no event date field | phone(99%) email(81%) website(10%) | no |
| Manitoba Companies Office weekly PDF | MB | filing-event | ~100-200/week | Incorporations category (HIGH) | registered office (~40%) | no |
| NNI Nunavut | NU | registration | 187 | effective_date — renewal signal (MEDIUM) | phone email contact_name address | employee_count (integer, ~conditional) |
| BC Indigenous Business Listings | BC — Indigenous-owned | business | ~783KB CSV, ~est. 3k+ records | When Updated — ambiguous (dataset-level Jan 2026) | phone(93%) email(89%) website(52%) contact(88%) | Number of Employees (52.6%, mixed int/range) |
| StatsCan Business Counts | All provinces | aggregate-only | 85,793 aggregate | Entrants category (CLASS D benchmark only) | none | aggregate size buckets only |