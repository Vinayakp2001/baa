# VR06 — Ontario Select Licence and Registration Data

Generated: `2026-09-25T13:20:38.325320+00:00`


## 1. Source Metadata

- Package: `select-licence-and-registration-data`
- Catalogue URL: `https://data.ontario.ca/dataset/select-licence-and-registration-data`
- CKAN API: `https://data.ontario.ca/api/3/action/package_show?id=select-licence-and-registration-data`
- Licence: Open Government Licence – Ontario (OGL Ontario)
- Update frequency: Monthly
- Role: Class A (specialized — 6 licence types) + Class C (contact enrichment)

## 2. Retrieval / Access Validation

- timestamp: `2026-09-25T13:20:38.325320+00:00`
- package_url: `https://data.ontario.ca/dataset/select-licence-and-registration-data`
- ckan_api_url: `https://data.ontario.ca/api/3/action/package_show?id=select-licence-and-registration-data`
- ckan_api_status: `200`
- business_file_size_bytes: `120464`
- business_save_path: `C:\Users\LENOVO\Desktop\baa\data\raw\ontario_select_licence_business_20260925.csv`
- individual_file_size_bytes: `65076`
- individual_save_path: `C:\Users\LENOVO\Desktop\baa\data\raw\ontario_select_licence_individual_20260925.csv`

## 3. Resource Inventory

| Name | Format | URL |
|---|---|---|
| August 2026 Business | CSV | `https://data.ontario.ca/dataset/5f0c3532-6e42-4ed7-a92c-ecde22bfea06/r` |
| August 2026 Business | CSV | `https://data.ontario.ca/dataset/5f0c3532-6e42-4ed7-a92c-ecde22bfea06/r` |
| August 2026 Individual | CSV | `https://data.ontario.ca/dataset/5f0c3532-6e42-4ed7-a92c-ecde22bfea06/r` |
| August 2026 Individual | CSV | `https://data.ontario.ca/dataset/5f0c3532-6e42-4ed7-a92c-ecde22bfea06/r` |

## 4. Business Resource Profile

- Total rows: `674`
- Columns: `14`
- Column names: `Legal Name`, `Operating name`, `Address`, `City`, `Province`, `Postal code`, `Country`, `Telephone`, `Website`, `Email`, `Licence type`, `Licence number`, `Licence status`, `Expiry date`

### Field Classification

| Role | Mapped field |
|---|---|
| legal_name | `Legal Name` |
| operating_name | `Operating name` |
| licence_number | `Licence number` |
| licence_type | `Licence type` |
| status | `Licence status` |
| expiry_date | `Expiry date` |
| issue_date | `None` |
| street | `Address` |
| city | `City` |
| province | `Province` |
| postal | `Postal code` |
| phone | `Telephone` |
| email | `Email` |
| website | `Website` |
| first_name | `None` |
| last_name | `None` |
| employer | `None` |

### Field Completeness

| Field | Non-null % | Distinct | Examples |
|---|---|---|---|
| `Legal Name` | 100.0% | 345 | Lumbermen's Credit Group Ltd. / Family And Credit Counselling  / Sterling Bailiffs Inc. |
| `Operating name` | 100.0% | 139 | N/A / Lumbermen's Credit Bureau / Commercial Recovery Canada |
| `Address` | 100.0% | 664 | 1135-b Markham Road  / 1900 Walkers Line, Unit 5a / 2325 Hurontario Street, Unit 1 |
| `City` | 100.0% | 119 | Wallaceburg / Ajax / Woodstock |
| `Province` | 100.0% | 9 | Florida / Makati / Arizona |
| `Postal code` | 100.0% | 625 | N/A / L3R 5J2 / N3J 3H5 |
| `Country` | 100.0% | 6 | N/A / South Africa 4001 / India |
| `Telephone` | 100.0% | 650 | N/A / 9057942333 / 5195396604 |
| `Website` | 100.0% | 77 | N/A / www.repologix.com / www.goday.ca |
| `Email` | 100.0% | 337 | N/A / paydayloanmart@gmail.com / stop4cash1000@outlook.com |
| `Licence type` | 100.0% | 7 | Consumer Reporting Agency / Bailiff (Owner) / Loan Broker |
| `Licence number` | 100.0% | 369 | 4741473 / 4740788 / 4734453 |
| `Licence status` | 100.0% | 4 | Appointed (Bailiff) / Appointed bailiff / Issued |
| `Expiry date` | 100.0% | 214 | N/A / 2027-04-22 / 2027-08-07 |

### Record Grain

- Duplicate legal names: `329`
- Duplicate operating names: `535`
- Duplicate licence numbers: `305`
- Unique licence numbers: `369`
- Businesses with multiple licence types: `0`

### Licence-Type Distribution

| Licence Type | Records | % |
|---|---|---|
| Payday Lender | 432 | 64.1% |
| Collection Agency | 128 | 19.0% |
| Bailiff (Business) | 76 | 11.3% |
| Consumer Reporting Agency | 34 | 5.0% |
| Bailiff | 2 | 0.3% |
| Loan Broker | 1 | 0.1% |
| Bailiff (Owner) | 1 | 0.1% |

### Status Distribution

| Status | Count | % |
|---|---|---|
| Issued | 600 | 89.0% |
| Appointed (Bailiff) | 64 | 9.5% |
| Appointed Bailiff | 9 | 1.3% |
| Appointed bailiff | 1 | 0.1% |

### Geographic Coverage

- Unique cities: `119`
- Postal code present: `100.0%`
- Postal code valid format: `99.0%`

Province distribution:
| Province | Count |
|---|---|
| Ontario | 662 |
| Quebec | 5 |
| Florida | 1 |
| Makati | 1 |
| Pakistan | 1 |
| British Columbia | 1 |
| Arizona | 1 |
| Mumbai | 1 |
| Durban | 1 |

Top 20 cities:
| City | Count |
|---|---|
| Toronto | 110 |
| Mississauga | 55 |
| Brampton | 34 |
| Ottawa | 33 |
| Scarborough | 29 |
| London | 22 |
| Hamilton | 21 |
| North York | 17 |
| Etobicoke | 16 |
| Barrie | 16 |
| Oshawa | 14 |
| Markham | 12 |
| Windsor | 11 |
| Cambridge | 10 |
| St. Catharines | 10 |
| Sudbury | 9 |
| Vaughan | 9 |
| Burlington | 9 |
| Richmond Hill | 8 |
| Kitchener | 8 |

### Contact Field Quality

| Field | Present % | Valid format % |
|---|---|---|
| Phone | 100.0% | 99.0% |
| Email | 100.0% | 81.2% |
| Website | 100.0% | 10.1% |
| All three | 100.0% | — |

### Address Quality

- Street present: `100.0%`
- City present: `see geography section`
- Postal present: `100.0%`

### Date Range

- Earliest date: `2020-07-05`
- Latest date: `N/A`

## 5. Individual / Person Resource Profile

- Total rows: `329`
- Columns: `15`
- Column names: `First name`, `Last name`, `Legal Name`, `Operating name`, `Address`, `City`, `Province`, `Postal code`, `Country`, `Telephone`, `Website`, `Email`, `Licence type`, `Licence number`, `Expiry date`

### Field Classification

| Role | Mapped field |
|---|---|
| legal_name | `Legal Name` |
| operating_name | `Operating name` |
| licence_number | `Licence number` |
| licence_type | `Licence type` |
| status | `None` |
| expiry_date | `Expiry date` |
| issue_date | `None` |
| street | `Address` |
| city | `City` |
| province | `Province` |
| postal | `Postal code` |
| phone | `Telephone` |
| email | `Email` |
| website | `Website` |
| first_name | `First name` |
| last_name | `Last name` |
| employer | `None` |

### Field Completeness

| Field | Non-null % | Distinct | Examples |
|---|---|---|---|
| `First name` | 100.0% | 316 | Keith E. / Patrick Paul /  Donna Marie |
| `Last name` | 100.0% | 281 | Murray / Warmington / Rostern |
| `Legal Name` | 100.0% | 66 | Big Dog Solutions Limited / 959350 Ontario Inc. / Bailiff Logistics Services Inc |
| `Operating name` | 100.0% | 11 | N/A / Kent County Bailiffs Services / The Recovery Board |
| `Address` | 100.0% | 66 | 3550 Simcoe Street North / 9656 Turk Road Rr # 1 / 10 New Street    |
| `City` | 100.0% | 44 | Sudbury / St. Thomas / Manotick |
| `Province` | 100.0% | 1 | Ontario |
| `Postal code` | 100.0% | 64 | N2J 1Y2 / N0P 1A0 / L2W 1A5 |
| `Country` | 100.0% | 1 | Canada |
| `Telephone` | 100.0% | 64 | N/A / 4162922221 / 8075488133 |
| `Website` | 100.0% | 12 | N/A / www.bailiffsale.com / www.g2cs.ca |
| `Email` | 100.0% | 61 | jmarlow@marlowbailiff.ca / N/A / kingswayrecovery@eastlink.ca |
| `Licence type` | 100.0% | 9 | Bailiff (Assistant - Reg) / Appointment Bailiff / Bailiff (Assistant - Appt) |
| `Licence number` | 100.0% | 329 | 4736802 / 4741388 / 4741404 |
| `Expiry date` | 100.0% | 164 | N/A / 2028-07-06 / 2027-08-14 |

### Record Grain

- Duplicate legal names: `263`
- Duplicate operating names: `318`
- Duplicate licence numbers: `0`
- Unique licence numbers: `329`
- Businesses with multiple licence types: `40`

Multi-type examples:
- `S. Wilson & Co. Bailiffs Limited`: Bailiff (Owner), Bailiff (Assistant - Reg), Bailiff (Employee), Appointed Bailiff
- `Sterling Bailiffs Inc.`: Bailiff (Owner), Bailiff (Assistant - Reg), Bailiff (Assistant - Appt)
- `James Herr & Co. Bailiffs Inc.`: Bailiff (Owner), Bailiff (Assistant - Appt)
- `959350 Ontario Inc.`: Bailiff (Owner), Bailiff (Assistant - Reg)
- `Diligent Bailiff Services Ltd.`: Bailiff (Owner), Bailiff (Assistant - Reg)

### Licence-Type Distribution

| Licence Type | Records | % |
|---|---|---|
| Bailiff (Assistant - Reg) | 209 | 63.5% |
| Bailiff (Owner) | 48 | 14.6% |
| Bailiff (Assistant - Appt) | 26 | 7.9% |
| Personal Information Investigator | 26 | 7.9% |
| Bailiff (Employee) | 10 | 3.0% |
| Appointed Bailiff | 4 | 1.2% |
| Appointment Bailiff | 4 | 1.2% |
| Bailiff (Assistant - Reg)v | 1 | 0.3% |
| Bailiff | 1 | 0.3% |

### Geographic Coverage

- Unique cities: `44`
- Postal code present: `100.0%`
- Postal code valid format: `100.0%`

Province distribution:
| Province | Count |
|---|---|
| Ontario | 329 |

Top 20 cities:
| City | Count |
|---|---|
| Toronto | 56 |
| Newmarket | 24 |
| Oshawa | 19 |
| St. Catharines | 18 |
| Mississauga | 17 |
| Scarborough | 15 |
| Garson | 15 |
| Tecumseh | 13 |
| Brampton | 13 |
| Cambridge | 12 |
| Minesing | 12 |
| Sudbury | 10 |
| Pickering | 8 |
| Hamilton | 8 |
| Innisfil | 8 |
| Stoney Creek | 7 |
| Porcupine | 6 |
| Markham | 6 |
| Halton Hills | 5 |
| Waterloo | 5 |

### Contact Field Quality

| Field | Present % | Valid format % |
|---|---|---|
| Phone | 100.0% | 95.7% |
| Email | 100.0% | 90.3% |
| Website | 100.0% | 31.3% |
| All three | 100.0% | — |

### Address Quality

- Street present: `100.0%`
- City present: `see geography section`
- Postal present: `100.0%`

### Date Range

- Earliest date: `2026-09-30`
- Latest date: `N/A`

## 6. ODBus Overlap Sample

- Skipped: ODBus file not found at data/raw/odbus.csv
- Deferred: ODBus overlap validation requires the ODBus source to be available locally. Not required for VR06 source-role classification. Cross-source overlap analysis to be conducted in the data profiling/overlap phase when multiple validated sources are available.

## 7. New-Business / Change Signal Assessment

- Source contains `licence status` and `expiry date` fields
- Status changes between monthly snapshots = potential change signal
- New record appearing in snapshot diff = new licence, NOT necessarily new business
- A business may have existed for years before obtaining one of these 6 licences
- Appropriate use: regulated-sector business-activity change signal, not general new-business source

## 8. Architecture Role

| Role | Assessment |
|---|---|
| Foundation / discovery | ❌ Only 6 licence types — not Ontario business universe |
| Fresh / change detection | ✅ Monthly snapshots — new/expired/changed licences detectable |
| Contact enrichment | ✅ Phone + email + website directly present |
| Decision-maker enrichment | 🟡 Individual dataset links person to employer (narrow role types) |
| Identity verification | ✅ Legal name + operating name + address + licence number |
| Benchmark | ❌ Not an aggregate count source |

## 9. Strengths

- Phone, email, website directly present — rare in government sources
- Monthly cadence — freshness is good
- OGL Ontario — commercial use permitted
- CKAN API available — clean machine-readable access
- Legal + operating name both present
- Individual dataset explicitly links person to employer

## 10. Limitations

- Only 6 regulated licence types — not Ontario master
- No NAICS / industry classification
- No employee count
- No incorporation date
- New licence ≠ new business
- Individual dataset limited to Bailiff + Personal Information Investigator roles only

## 11. Automation and API

- CKAN Data API: available at `data.ontario.ca/api/3`
- Bulk CSV download: available without authentication
- No pagination required for bulk download (single CSV file)
- Stable resource URLs discoverable via CKAN package API
- No API key required for read access
- Recommended: download full CSV monthly, diff against previous snapshot

## 12. Licence / Terms

- Data licence: Open Government Licence – Ontario
- Commercial use: permitted under OGL Ontario
- Attribution required: yes — credit Government of Ontario
- Automated download: permitted — use official CKAN resource URL, not portal scraping
- robots.txt / portal scraping: use CKAN API endpoint, not HTML portal

## 13. Open Questions

- [ ] Does a second monthly snapshot show record additions/removals (freshness test)?
- [ ] Can the Individual dataset be deterministically linked to the Business dataset via shared `Legal Name` field? (Script mapped employer field as None — actual linkage path is Individual.`Legal Name` → Business.`Legal Name`, normalized.)
- [ ] Are inactive/expired licences retained in the dataset or removed between monthly releases?
- [ ] Licence-type list is not fixed — monitor for new categories appearing in future snapshots.

**Deferred (not VR06 blockers):**
- ODBus overlap sample — requires ODBus locally; defer to data profiling/overlap phase
- Licence-type exhaustiveness — current validated snapshot contains 5 categories; dataset may evolve

## 14. Architecture Conclusion

```
Ontario Select Licence
        │
        ├── Business licence records (674 rows = 369 unique licences, NOT 674 unique businesses)
        │     ├── phone  (99% valid format after treating "N/A" as missing)
        │     ├── email  (81% valid format)
        │     ├── address (100% present)
        │     └── licence / status / expiry
        │
        └── Individual licence records (329 rows = 329 unique person-licences)
              └── person → employer business  (via shared Legal Name field)
```

**Critical distinction — preserve in all downstream logic:**
```
674 licence records  ≠  674 businesses
new/changed licence  ≠  new business
```

**Out-of-province records:** 12/674 records have non-Ontario addresses (Quebec, BC, US states, India, Pakistan, South Africa). Pipeline must NOT hard-filter on province field before retaining source provenance — these may be legitimate businesses holding Ontario licences from registered addresses elsewhere.

**Licence-type finding:** The previously documented list (Collection Agency, Consumer Reporting Agency, Distributor — Ontario-wide, Lender, Loan Broker, Bailiff) was incomplete relative to the validated resource. Current snapshot (August 2026) contains: Payday Lender (64.1%), Collection Agency (19.0%), Bailiff (Business) (11.3%), Consumer Reporting Agency (5.0%), Loan Broker (0.1%). This list is not guaranteed exhaustive — licence types may be added or removed over time.

## 15. Summary Metrics

| Metric | Business resource | Individual resource |
|---|---|---|
| Rows | 674 | 329 |
| Columns | 14 | 15 |
| Unique licence IDs | 369 | 329 |
| Duplicate legal names | 329 | — |
| Phone present % | 100.0% | 100.0% |
| Email present % | 100.0% | 100.0% |
| Website present % | 100.0% | 100.0% |
| Postal valid % | 99.0% | — |
| Unique cities | 119 | — |
| Date range | 2020-07-05 → N/A | — |
| Person→biz linkage | — | None |
| ODBus overlap sample | skipped (ODBus file not found at data/raw/odbus.csv) | — |
| API / download | CKAN CSV — no auth | — |
| Licence | OGL Ontario | — |
| Automation status | ✅ Permitted | — |
| Final status | ✅ VALIDATED | — |