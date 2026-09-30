# VR07 — City of Saskatoon Business Licence Data

Generated: `2026-09-25T14:19:08.501288+00:00`


## 1. Source Metadata

- Source: City of Saskatoon — Business Statistics & Publications
- Portal page: `https://www.saskatoon.ca/business-development/economic-profile/business-statistics-publications`
- Open Data portal: `https://opendata.saskatoon.ca/`
- Platform change: Old CKAN portal (opendata-saskatoon.cloudapp.net) retired Aug 26 2024
- Current delivery: Direct XLSX files on City website
- Licence: City of Saskatoon Open Data Licence — free to use, reuse and redistribute
- Scope: Commercial and Home-Based Business Licences only
  - Excludes: Non-Resident Business Licences and other licence types
  - Do NOT describe as 'all Saskatoon businesses'
- Role: Class A (municipal discovery — Saskatoon) + Class B (new-business signal)

## 2. Access Validation

- timestamp: `2026-09-25T14:19:08.501288+00:00`
- portal_page: `https://www.saskatoon.ca/business-development/economic-profile/business-statistics-publications`
- platform_note: `Old CKAN portal retired Aug 26 2024 — files now served as XLSX from City website`
- saskatoon_all_businesses_status: `200`
- saskatoon_all_businesses_url: `https://www.saskatoon.ca/sites/default/files/documents/community-services/planning-development/business-license-mapping-research/business-license/Dec_31_2025_%20All_Commercial_and_Home_Based_Businesses.xlsx`
- saskatoon_all_businesses_bytes: `831244`
- saskatoon_all_businesses_saved: `C:\Users\LENOVO\Desktop\baa\data\raw\saskatoon_all_businesses_20260925.xlsx`
- saskatoon_new_businesses_status: `200`
- saskatoon_new_businesses_url: `https://www.saskatoon.ca/sites/default/files/media/documents/New%20Businesses%20as%20of%20August%2031%2C%202026.xlsx`
- saskatoon_new_businesses_bytes: `128716`
- saskatoon_new_businesses_saved: `C:\Users\LENOVO\Desktop\baa\data\raw\saskatoon_new_businesses_20260925.xlsx`

## 3. File Inventory

| File | Reference date | Format | URL |
|---|---|---|---|
| All Commercial and Home-Based Businesses — Dec 31 2025 | — | XLSX | `https://www.saskatoon.ca/sites/default/files/documents/community-servi` |
| New Businesses — Aug 31 2026 | — | XLSX | `https://www.saskatoon.ca/sites/default/files/media/documents/New%20Bus` |

## 4. Profile — All Commercial and Home-Based Businesses — Dec 31 2025

- Rows: `7,472`
- Columns: `10`
- Column names: `Bus_Lic_Acct_Id`, `Business_Type`, `Business_Name`, `Struc_U_Addr_Unit`, `Struc_U_Addr_St_Num`, `Struc_U_Addr_St_Name`, `Struc_U_Addr_St_Suff`, `Struc_U_Addr_St_Post_Dir`, `NAICS_Sub_Sector_Code`, `NAICS_Sub_Sector`

### Field Mapping

| Role | Identified field |
|---|---|
| business_name | `Business_Name` |
| address | `None` |
| city | `None` |
| postal | `None` |
| phone | `None` |
| email | `None` |
| website | `None` |
| business_type | `Business_Type` |
| status | `None` |
| issue_date | `None` |
| expiry_date | `None` |
| licence_number | `None` |
| owner | `None` |

### Field Completeness

| Field | Non-null % | Distinct | Examples |
|---|---|---|---|
| `Bus_Lic_Acct_Id` | 97.5% | 7,281 | 2394988 / 2466527 / 2435163 |
| `Business_Type` | 100.0% | 1 | COMM |
| `Business_Name` | 100.0% | 7,141 | J&R HALL TRANSPORT INC. / SAFARI MARKET / LIFTED EARTH GARDEN SUPPLY C |
| `Struc_U_Addr_Unit` | 61.6% | 624 | M4 / 414 / T012 |
| `Struc_U_Addr_St_Num` | 100.0% | 1,314 | 3626 / 254 / 2203 |
| `Struc_U_Addr_St_Name` | 100.0% | 361 | 5th / Coy / Langlois |
| `Struc_U_Addr_St_Suff` | 95.1% | 26 | Turn / Pl / Gate |
| `Struc_U_Addr_St_Post_Dir` | 52.1% | 4 | W / E / S |
| `NAICS_Sub_Sector_Code` | 100.0% | 86 | 337 / 414 / 443 |
| `NAICS_Sub_Sector` | 100.0% | 86 | Air Transportation / Nursing and Residential Care / Mining and Quarrying (except |

### Record Grain

- Duplicate business names: `331`
- Unique licence numbers: `0`
- Duplicate licence numbers: `None`

### Business Type / Category Distribution

| Type | Count | % |
|---|---|---|
| COMM | 7,472 | 100.0% |

### Geographic Coverage

- Unique cities: `0`
- Postal present: `0.0%`
- Postal valid format: `0.0%`

### Contact Field Quality

| Field | Present % | Valid format % |
|---|---|---|
| Phone | 0.0% | 0.0% |
| Email | 0.0% | 0.0% |
| Website | 0.0% | 0.0% |

### Date Range

- Earliest: `None`
- Latest: `None`

## 4. Profile — New Businesses — Aug 31 2026

- Rows: `51`
- Columns: `27`
- Column names: `Business_License_Id`, `Business_Name`, `Business_Desc`, `Struc_U_Addr_Unit`, `Struc_U_Addr_St_Num`, `Struc_U_Addr_St_Name`, `Struc_U_Addr_St_Suff`, `Struc_U_Addr_St_Post_Dir`, `NAICS_National`, `NAICS_National_Code`, `col_10`, `col_11`, `col_12`, `col_13`, `col_14`, `col_15`, `col_16`, `col_17`, `col_18`, `col_19`, `col_20`, `col_21`, `col_22`, `col_23`, `col_24`, `col_25`, `col_26`

### Field Mapping

| Role | Identified field |
|---|---|
| business_name | `Business_Name` |
| address | `None` |
| city | `None` |
| postal | `None` |
| phone | `None` |
| email | `None` |
| website | `None` |
| business_type | `None` |
| status | `None` |
| issue_date | `None` |
| expiry_date | `None` |
| licence_number | `None` |
| owner | `None` |

### Field Completeness

| Field | Non-null % | Distinct | Examples |
|---|---|---|---|
| `Business_License_Id` | 100.0% | 51 | 3495183 / 3497894 / 3491752 |
| `Business_Name` | 100.0% | 51 | JAY WALKER, CPA P.C. LTD. / HEARTWOOD COUNSELLING AND TH / COMPASSIONATE CONNECTIONS PS |
| `Business_Desc` | 100.0% | 47 | INDIAN STREET FOOD AND DRINK / MEDITERRANEAN AND MIDDLE EAS / CANNABIS RETAIL STORE |
| `Struc_U_Addr_Unit` | 72.5% | 20 | 6 / 131 / 4 |
| `Struc_U_Addr_St_Num` | 100.0% | 47 | 415 / 139 / 1515 |
| `Struc_U_Addr_St_Name` | 100.0% | 39 | Katz / 45th / Fairlight |
| `Struc_U_Addr_St_Suff` | 98.0% | 10 | Blvd / Cres / Ave |
| `Struc_U_Addr_St_Post_Dir` | 37.3% | 4 | W / E / N |
| `NAICS_National` | 100.0% | 28 | Other Personal Care Services / Other Building Finishing Con / All Other Miscellaneous Stor |
| `NAICS_National_Code` | 100.0% | 28 | 541430 / 332319 / 722512 |
| `col_10` | 0.0% | 0 |  |
| `col_11` | 0.0% | 0 |  |
| `col_12` | 0.0% | 0 |  |
| `col_13` | 0.0% | 0 |  |
| `col_14` | 0.0% | 0 |  |
| `col_15` | 0.0% | 0 |  |
| `col_16` | 0.0% | 0 |  |
| `col_17` | 0.0% | 0 |  |
| `col_18` | 0.0% | 0 |  |
| `col_19` | 0.0% | 0 |  |
| `col_20` | 0.0% | 0 |  |
| `col_21` | 0.0% | 0 |  |
| `col_22` | 0.0% | 0 |  |
| `col_23` | 0.0% | 0 |  |
| `col_24` | 0.0% | 0 |  |
| `col_25` | 0.0% | 0 |  |
| `col_26` | 0.0% | 0 |  |

### Record Grain

- Duplicate business names: `0`
- Unique licence numbers: `0`
- Duplicate licence numbers: `None`

### Geographic Coverage

- Unique cities: `0`
- Postal present: `0.0%`
- Postal valid format: `0.0%`

### Contact Field Quality

| Field | Present % | Valid format % |
|---|---|---|
| Phone | 0.0% | 0.0% |
| Email | 0.0% | 0.0% |
| Website | 0.0% | 0.0% |

### Date Range

- Earliest: `None`
- Latest: `None`

## 5. New-Businesses vs All-Businesses Comparison

- All-businesses unique names: `7,101`
- New-businesses names checked: `51`
- Found in all-businesses: `3` (5.9%)
- Not found in all-businesses: `48` (94.1%)

**Cross-file identity linkage: unresolved.** 94.1% of records in the August 2026 New Businesses file were not matched to the December 2025 All Businesses file using normalized business name alone. Because the two files use different identifier fields (`Bus_Lic_Acct_Id` vs `Business_License_Id`) and substantially different schemas (10 vs 27 columns), this result is insufficient to establish population divergence. The files appear to originate from different internal City extracts/views. Name-only matching should not be used to infer that the New Businesses dataset represents a different licence population. A second matching pass using normalized business name + street address is deferred as a follow-up step.

## 6. New-Business Signal Assessment

- Source explicitly labels one file as 'New Businesses' — direct city-issued municipal licensing signal
- Correct label: **municipal new-business/licensing signal** — not "newly opened" or "newly incorporated"
- New licence appearing in this file = new municipal business-licence activity
- Supported: "appears in New Businesses file → new municipal business-licence activity"
- Not supported: "new municipal licence → recently incorporated" or "new municipal licence → physical business opened on that date"
- A licence may be required when an existing business changes location — licence issuance ≠ business creation
- Closer to actual operating-business start than a corporate registry incorporation date
- Still ≠ StatsCan 'Entrant' (employment-based) — a business can be licensed before hiring employees
- Excludes Non-Resident Business Licences — out-of-city operators not captured

**Architectural note:** This source adds another distinct business lifecycle event type to the pipeline:
```
Corporations Canada  → federal incorporation / corporate events
StatsCan             → employer activity / entrants / openings
Ontario Select Lic.  → regulated licence events
Saskatoon            → municipal business-licence activity
```
These must not be collapsed into a single `business.created_at` field. Each is a separate event with its own provenance and semantics.

## 7. Architecture Role

| Capability | Assessment |
|---|---|
| Business discovery | ✅ Saskatoon commercial/home-based |
| Saskatoon coverage | ✅ |
| Business name | ✅ |
| Structured address | ✅ (split fields — reconstruction needed) |
| NAICS classification | ✅ Sub-sector (all-biz) + national level (new-biz) |
| Local licence ID | ✅ / ⚠️ (`Bus_Lic_Acct_Id` 97.5%; different ID in new-biz file) |
| New-business signal | ✅ Municipal licence-issuance signal |
| Snapshot diffing | ✅ Monthly XLSX releases support diff-based detection |
| Phone | ❌ |
| Email | ❌ |
| Website | ❌ |
| Postal code | ❌ |
| Employee count | ❌ |
| Decision-maker | ❌ |
| Registration date | ❌ |
| Contact enrichment | ❌ |
| Canada-wide coverage | ❌ Municipal only |
| General business registry | ❌ |

## 8. Platform / Access Notes

- Old CKAN portal retired Aug 26 2024 — do not use old URLs
- Current delivery: direct XLSX download from City website
- No CKAN API available for these files
- No authentication required
- Automation: download XLSX monthly, parse with openpyxl, diff against previous snapshot
- URL stability: City website paths may change — monitor Business Statistics page for updates

## 9. Licence / Terms

- Licence: City of Saskatoon Open Data Licence
- Commercial use: permitted — free to use, reuse and redistribute
- Attribution: credit City of Saskatoon

## 10. Open Questions

- [ ] Cross-file identity linkage unresolved — run name+street-address matching between new-biz and all-biz files to determine if low name-match is formatting/extract difference or genuine population divergence
- [ ] 17 blank columns in new-businesses file (`col_10`–`col_26`) — consistent with export/template structure; preserve column names in raw ingestion; monitor future monthly releases to determine if they ever become populated
- [ ] What does 'New Businesses' mean exactly — new licence application, approval, or publication date?
- [ ] What is the exact update/publication frequency for both files?
- [ ] Are licences removed from the all-businesses file when cancelled/expired?

## 11. Summary Metrics

| Metric | All Businesses | New Businesses |
|---|---|---|
| Rows | 7,472 | 51 |
| Columns | 10 | 27 |
| Licence number field | `None` | `None` |
| Unique licence IDs | 0 | 0 |
| Issue date field | `None` | `None` |
| Date range | None → None | None → None |
| Phone present % | 0.0% | 0.0% |
| Email present % | 0.0% | 0.0% |
| Website present % | 0.0% | 0.0% |
| Postal valid % | 0.0% | 0.0% |
| Unique cities | 0 | 0 |
| New biz found in all-biz | — | 5.9% |
| Access | Direct XLSX download | Direct XLSX download |
| Licence | City of Saskatoon Open Data | City of Saskatoon Open Data |
| Automation | ✅ Permitted | ✅ Permitted |
| Final status | ✅ VALIDATED | ✅ VALIDATED |