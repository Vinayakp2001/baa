# VR14 — ODBus Underlying/Current-Source Expansion

Generated: `2026-09-26`
Script: `scripts/probe_odbus_vr14_1.py`
JSON: `reports/validation_rounds/VR14_1_ODBUS_SOURCE_INVENTORY.json`

---

## Objective

Use ODBus's 69 underlying providers to answer:
Which original government sources are still live in 2026, have newer data than ODBus,
and can legally/technically become direct production inputs?

ODBus is treated as a source map and historical baseline — not the current Canada-wide
lead database. Its data was collected May–Dec 2022, published Nov 2023. Our system is 2026.

---

## 1. ODBus Source Inventory (Phase 14.1)

### Summary

| Attribute | Value |
|---|---|
| Total sources | 69 |
| Columns in ODBus_Sources.csv | Province/Territory, City, Dataset Name, Link to Dataset, Link to Dataset License, Attribution Statement, License Title, Date last updated as of download |
| File encoding | cp1252 (Windows-1252) — contains © character at position 22218 |

### Province/Territory Distribution

| Province | Sources | Notes |
|---|---|---|
| ON | 32 | Hamilton (13 specialized), New Westminster (6 splits), Toronto, Ottawa, Brampton, Cambridge/Kitchener, Durham, Ajax, Pickering, Guelph, Mississauga, Welland (×2), York Region, Peel Region, Caledon |
| BC | 27 | Vancouver (×2), Victoria (×3), Surrey, Nanaimo, New Westminster (×6 splits), Port Moody (×2), Burnaby, Chilliwack, Delta, Langley (×2), Maple Ridge, Prince George, Squamish, + BC provincial datasets (Indigenous listings, Licensed Establishments, Wineries) |
| AB | 5 | Banff, Calgary, Chestermere, Edmonton, Strathcona County |
| NB | 3 | Moncton (×2: grocery stores + pharmacies), Saint John (grocery stores) |
| MB | 1 | Winnipeg |
| NT | 1 | Yellowknife |
| SK | 0 | Not represented |
| QC | 0 | Not represented |
| NS | 0 | Not represented |
| PE | 0 | Not represented |
| NL | 0 | Not represented |
| YT | 0 | Not represented |
| NU | 0 | Not represented |

**Coverage gap:** 7 of 13 provinces/territories have zero ODBus sources.
SK, QC, NS, PE, NL, YT, NU must be sourced entirely outside ODBus.

### Source Type Breakdown (from dataset names)

| Type | Count | Examples |
|---|---|---|
| Business Licences / Licenses / Permits | ~38 | Calgary, Vancouver, Toronto, Edmonton, Winnipeg |
| Business Directory | ~15 | Brampton, Cambridge, Durham, Ajax, Strathcona, Yellowknife |
| Specialized licence categories | ~13 | Hamilton (food shops, kennels, limos, lodging, mobile food, garages, halls, trade contractors, residential care, salvage yards, second-hand shops, amusement) |
| Specialized sector datasets | 3 | BC Indigenous Businesses, BC Licensed Establishments, BC Wineries |
| Other sector-specific | 3 | Moncton/Saint John grocery stores + pharmacies |

### Notable Sources (pre-triage)

| # | Province | City/Source | Dataset | Notes |
|---|---|---|---|---|
| 19 | BC | New Westminster | Business Licenses (New this Year) | Dedicated new-business file — high value event signal |
| 28 | BC | Vancouver | Business licences (current) | Major city, Socrata portal |
| 29 | BC | Vancouver | Business licences 1997–2012 | Historical only |
| 32 | BC | Victoria | Business Licences – Current Year | Current year file — freshness signal |
| 30 | BC | Victoria | Business Licences – Past 5 Years | Rolling window |
| 66 | ON | Toronto | Business Licences and Permits | Largest Canadian city — top priority |
| 64 | ON | Ontario (provincial) | Select Licence and Registration Data | ✅ Already validated VR06 |
| 60/65 | ON | Ontario (provincial) | Ontario Environment Business Directory | ⚠️ Known stale (2019) — appears twice |
| 4 | AB | Edmonton | Business Licenses | Major AB city |
| 2 | AB | Calgary | Calgary Business Licences | Major AB city |
| 33 | MB | Winnipeg | Business Licenses | Only MB source |

### ODBus Update Date Distribution

From `Date last updated as of date of download` column:
- Many entries show dates in 2018–2021 range
- Calgary shows `..` (unknown/suppressed at time of download)
- All dates are ODBus's download date (2022), not current source update dates
- Current update frequency of each source must be determined independently

---

## 2. Current Endpoint Resolution (Phase 14.2)

Script: `scripts/probe_odbus_vr14_2.py`
Full results: `reports/validation_rounds/VR14_2_ODBUS_ENDPOINT_TRIAGE.json`

### Classification Summary

| Classification | Count |
|---|---|
| CURRENT | 56 |
| DEAD | 7 |
| RESTRICTED | 3 |
| MOVED | 2 |
| UNKNOWN | 1 |
| **Total** | **69** |

**56 of 69 sources (81%) returned HTTP 200 and are reachable.** However, CURRENT
classification means endpoint is alive — it does NOT mean production-usable. Login
detection, WAF signals, stale dataset names, and lack of downloadable data must be
resolved in Phase 14.3.

### DEAD Sources (7)

| # | Prov | City | Dataset | Error |
|---|---|---|---|---|
| 1 | AB | Banff | Business Licences | Timeout |
| 5 | AB | Strathcona County | Business Directory | Timeout |
| 13 | BC | (provincial) | Licensed Establishments in B.C. | 404 — direct CSV URL dead |
| 14 | BC | (provincial) | BC Winery Locations | 404 — direct CSV URL dead |
| 15 | BC | Nanaimo | Business Licenses | 404 |
| 37 | NT | Yellowknife | Business Directory | 404 |
| 44 | ON | Guelph | Business Licenses | SSL handshake failure |

Note: BC Licensed Establishments and BC Winery Locations used hardcoded 2017 CSV
download URLs — the datasets likely still exist on data.gov.bc.ca but under different
resource URLs. Not truly dead, just URL-rotted.

### RESTRICTED Sources (3)

| # | Prov | City | Dataset | Signal |
|---|---|---|---|---|
| 7 | BC | Chilliwack | Business Licenses | HTTP 403 |
| 59 | ON | Mississauga | 2019 Mississauga Business Directory | HTTP 403 |
| 66 | ON | Toronto | Business Licences and Permits | Bot/WAF detected in response body |

Toronto is the most significant restriction — largest Canadian city in the dataset,
open data portal confirmed live and current (2026 date evidence), but WAF blocks
script access. Same pattern as NS RJSC. Not a prohibition — browser/DevTools needed.

### MOVED Sources (2)

| # | Prov | City | Dataset | New URL |
|---|---|---|---|---|
| 8 | BC | Delta | Business Licences | https://www.delta.ca:443/city-hall/municipal-information/open-data-catalogue |
| 26 | BC | Surrey | Business Licenses | https://opendata-surrey.hub.arcgis.com/ |

Surrey migrated from `data.surrey.ca` to ArcGIS Hub. Delta moved within same domain.
Both portals likely still host the data — new download URLs needed.

### UNKNOWN Sources (1)

| # | Prov | City | Dataset | Signal |
|---|---|---|---|---|
| 9 | BC | Kelowna | Business Licence | HTTP 400 — direct GeoJSON URL |

Old direct GeoJSON download URL returns 400. Kelowna likely still has open data
but the resource ID has rotated.

### Notable False Positives in CURRENT Classification

Several sources classified CURRENT need GPT review:
- **[6] Burnaby**: Final URL is the licence page, not the dataset itself — no actual data link observed
- **[25] Squamish**: Name says "Annual 2021" — likely a static historical snapshot, not live
- **[40] Caledon**: "Business Directory 2018" — static snapshot
- **[31] Victoria**: "Past 10 Years (2011-2020)" — historical only
- **[69] York Region**: "2019 Business Directory" — static historical document
- **[29] Vancouver**: "Business licences 1997 to 2012" — historical only
- **Login-flagged sources** (Calgary, Edmonton, Vancouver, Winnipeg): "login_required"
  flag is a false positive from Socrata/open data portal JS that contains login strings
  — these portals are publicly accessible, the flag should be interpreted as
  "login option present" not "login required to access data"

### BC Indigenous Business Listings — Direct CSV Confirmed Live

| # | Detail |
|---|---|
| Source | [12] BC Indigenous Business Listings |
| URL | catalogue.data.gov.bc.ca (direct CSV download) |
| Size | 782,954 bytes (~783KB) |
| Current date evidence | Yes (2024/2025/2026 in content) |
| Licence | OGL-BC |

This is the only source in the triage where a direct CSV download was confirmed alive
with substantial data (783KB). All others returned HTML portal pages.

---

## 3. High-Value Current Sources (Phase 14.3)

*Pending deep validation of confirmed-current sources.*

### Tier A — Municipal Business Licence Datasets (confirmed reachable)

| # | City | Prov | Portal | Current date evidence | Priority |
|---|---|---|---|---|---|
| 2 | Calgary | AB | data.calgary.ca (Socrata) | ✅ | HIGH — major AB city |
| 4 | Edmonton | AB | data.edmonton.ca (Socrata) | ✅ | HIGH — major AB city |
| 28 | Vancouver | BC | opendata.vancouver.ca | ✅ | HIGH — major BC city |
| 33 | Winnipeg | MB | data.winnipeg.ca (Socrata) | ✅ | HIGH — only MB source |
| 18 | New Westminster | BC | opendata.newwestcity.ca | — | HIGH — has "New this Year" split |
| 32 | Victoria | BC | opendata.victoria.ca | — | MED — current year file |
| 66 | Toronto | ON | open.toronto.ca | ✅ | HIGH — largest city; WAF blocked |

### Tier B — New-Business / Change Signal Sources

| # | City | Dataset | Notes |
|---|---|---|---|
| 19 | New Westminster BC | Business Licenses (New this Year) | Dedicated new-business file — highest priority |
| 32 | Victoria BC | Business Licences - Current Year | Annual refresh |

### Tier C — Specialized / Sector Sources

| # | Source | Type | Notes |
|---|---|---|---|
| 12 | BC Indigenous Business Listings | Provincial CSV | 783KB direct download confirmed, OGL-BC, current |
| 45–57 | Hamilton ON (13 datasets) | Sector licences | Food, trade, care, transport — all reachable |
| 34–36 | Moncton/Saint John NB | Grocery/pharmacy | Sector-specific only |
| 61–62 | Ottawa ON | Cultural/food vendors | Small scope |

### Tier D — Stale / Historical (retain for reference only)

- [25] Squamish "Annual 2021"
- [40] Caledon "2018 Directory"
- [31] Victoria "2011–2020"
- [29] Vancouver "1997–2012"
- [69] York Region "2019 Directory"

---

## 4. ODBus vs Current-Source Comparison (Phase 14.4)

Script: `scripts/probe_odbus_vr14_4.py`
Full results: `reports/validation_rounds/VR14_4_ODBUS_VS_CURRENT.json`

### Field Matrix — Current Sources vs ODBus 2022

| City | Prov | Rows (2026) | Name | Address | Postal | Status | Licence ID | New-Biz Date | Employee Count |
|---|---|---|---|---|---|---|---|---|---|
| Calgary | AB | 23,178 | ✅ 100% | ✅ 100% | ❌ | ✅ 7 values | ✅ 100% | ✅ 99.9% (to 2026/09/21) | ❌ |
| Edmonton | AB | 43,719 | ✅ 100% | ✅ 99.9% | ❌ | ❌ not present | ✅ 100% | ✅ 94.2% (to 2025/12/31) | ❌ |
| Vancouver | BC | 206,024 | ✅ 93.4% | ✅ 53.7% | ✅ 53.4% | ✅ 5 values | ✅ 100% | ✅ 86.1% (to 2026/10/01) | ✅ 100% float-strings |
| Winnipeg | MB | 13,757 | ✅ 100% | ⚠️ 20.2% | ❌ | ✅ 10 values | ❌ not present | ✅ 100% (to 2025/12/31) | ❌ |

ODBus comparison: `data/raw/ODBus_Sources.csv` not present in local data/ — direct ODBus row-count comparison not performed. Current source row counts stand as the authoritative measure of production scale.

### Key Findings by Source

#### Calgary ✅
- 23,178 rows, all with name + address + licence ID + status (7 categories) + issue date
- `first_iss_dt` range: 2001/06/01 → 2026/09/21 — includes full history and Sep 2026 records
- No postal code, phone, email, NAICS
- Production-ready: Socrata CSV, no auth

#### Edmonton ✅
- 43,719 rows — largest of the four by row count
- `original_issue_date` range: 2004 → 2025/12/31 — latest date shows Dec 2025, not Sep 2026
- No status field in schema — active/inactive filtering not directly possible from this download
- No postal code, phone, email, NAICS
- Production-ready: Socrata CSV, no auth

#### Vancouver ✅ — BEST FIELD SET
- 206,024 rows, updated 2026-10-01 (most current of all four)
- `issueddate` range: 2023-11-04 → 2026-10-01 — ISO timestamp precision
- Status distribution: Issued=168,509 / Pending=13,440 / Gone Out of Business=11,619 / Inactive=7,019 / Cancelled=5,437
- `street` filled 53.7% (1,289 unique values) — low unique count suggests street name only, not full address
- `postalcode` filled 53.4% (6,070 unique values) — real postal codes
- `numberofemployees`: 100% populated, stored as float-strings ("385.0", "21.0" etc.) — parseable as int after truncation. This is the only municipal source with universal employee count coverage found so far.
- No phone, email, NAICS

#### Winnipeg ⚠️
- 13,757 rows including historical/closed records
- `trade_name` 100% filled but only 275 unique values — suggests many rows per business (licence-grain, not business-grain)
- `address` only 20.2% filled — significant gap
- No postal, no licence number, no NAICS
- Status has 10 values — includes historical lifecycle states
- `issue_date` range: 2011 → 2025/12/31

### Vancouver Employee Count — VR14.4.1 ✅ PROFILED

Full profiling at: `reports/validation_rounds/VR14_4_1_VANCOUVER_EMPLOYEES.json`

- 206,024 rows, all values valid integers (parsed from float-strings), 0 nulls
- Min: 0, Max: 5,876, Median: 1
- Zeros: 73,835 (35.8%) — likely "no employees reported at time of licence application"
- Positives: 132,189 (64.2%)

Bucket distribution across required 9 bands:

| Bucket | Count |
|---|---|
| 1–4 | 82,197 |
| 5–9 | 20,993 |
| 10–19 | 13,451 |
| 20–49 | 8,808 |
| 50–99 | 3,216 |
| 100–199 | 1,868 |
| 200–499 | 1,089 |
| 500–999 | 367 |
| 1000+ | 200 |

Consistency: 11,147 of 62,954 unique business names (17.7%) have different employee values across rows.
Example: Pacific National Exhibition appears with [0, 30, 200, 3000, 4000] — strongly suggests per-licence-event grain, not stable company-level headcount.
Anomaly: "City Vaper Inc" (Retail Dealer) = 5,876 — likely data entry error or company-level total misapplied.

**Semantic status: SOURCE-DEFINED ✅**
City of Vancouver documentation confirms: `NumberofEmployees` = "Number of staff employed with the business". `0` = applicant reported no employees (legitimate — not missing). Dataset updated daily. `LicenceRSN` is unique per licence.

```
employee_count:
  usable = YES
  semantic_definition = "Number of staff employed with the business"
  grain = licence_record
  company_level_semantics = documented
  zero_meaning = applicant_reported_no_employees
  pipeline_instruction = preserve all licence observations; resolve at entity layer
```
Documentation URL: https://opendata.vancouver.ca/explore/dataset/business-licences/information/

### Key confirmed findings from Phase 14.3

#### Calgary — data.calgary.ca (Socrata) ✅ CONFIRMED LIVE + CURRENT
- API: `https://data.calgary.ca/api/views/vdjc-pybd/rows.csv?accessType=DOWNLOAD`
- Columns (18): `tradename`, `address`, `comdistcd`, `comdistnm`, `licencetypes`, `first_iss_dt`, `exp_dt`, `jobstatusdesc`, `point`, `homeoccind`, `getbusid`
- Sample row `FIRST_ISS_DT: 2026/03/26` — confirmed live 2026 data
- Has: name ✅, address ✅, licence type ✅, issue date ✅, expiry date ✅, status ✅, coordinates ✅
- Missing: postal code, phone, email, NAICS
- `first_iss_dt` = new-business signal (first licence issuance date)
- Automation: Socrata CSV download, no auth required

#### Edmonton — data.edmonton.ca (Socrata) ✅ CONFIRMED LIVE + CURRENT
- API: `https://data.edmonton.ca/api/views/qhi4-bdpu/rows.csv?accessType=DOWNLOAD`
- URL migrated: old path `/Sustainable-Development/` → new `/Urban-Planning-Economy/`
- Columns (22): `business_name`, `business_address`, `business_licence_category`, `most_recent_issue_date`, `original_issue_date`, `expiry_date`, `licencetype`, `licenceduration`, `neighbourhood`, `ward`, `latitude`, `longitude`
- Sample row `Most Recent Issue Date: 08/17/2026` — confirmed live 2026 data
- Has: name ✅, address ✅, licence category ✅, issue date ✅, original issue date ✅, neighbourhood ✅
- Missing: postal code, phone, email, NAICS
- `original_issue_date` = new-business signal (first ever licence for this entity)
- Automation: Socrata CSV download, no auth required

#### Vancouver — opendata.vancouver.ca (OpenDataSoft) ✅ CONFIRMED LIVE + CURRENT — BEST FIELD SET
- API: `https://opendata.vancouver.ca/explore/dataset/business-licences/export/?format=csv`
- Row count: **206,024 rows** (updated 2026-09-25 — yesterday)
- Columns (25): `businessname`, `businesstradename`, `status`, `issueddate`, `expireddate`, `businesstype`, `businesssubtype`, `house`, `street`, `city`, `province`, `postalcode`, `localarea`, `numberofemployees`, `feepaid`, `licencenumber`, `licencersn`, `folderyear`, `unit`, `country`, `geom`
- Has: name ✅, trade name ✅, address ✅, postal code ✅, status ✅, issue date ✅, expiry date ✅, business type ✅, **employee count ✅**, **fee paid ✅**, coordinates ✅
- Missing: phone, email, NAICS (has business type/subtype instead)
- `numberofemployees` — employee count field present (only second source after NNI with this field)
- `issueddate` + `folderyear` = new-business signal
- `status` field enables active/inactive filtering
- Automation: OpenDataSoft export API, no auth required

#### Winnipeg — data.winnipeg.ca (Socrata) ✅ CONFIRMED LIVE
- API: `https://data.winnipeg.ca/api/views/d5k3-sfzx/rows.csv?accessType=DOWNLOAD`
- Columns (13): `folder_type`, `folder_description`, `subdescription`, `trade_name`, `address`, `issue_date`, `expiry_date`, `status`, `neighbourhood_name`, `electoral_ward`, `community_characterization_area`, `location`
- Sample row shows `Status: Closed (L)` — dataset includes historical/closed records
- Has: name ✅, address ✅, status ✅, issue date ✅, expiry date ✅, neighbourhood ✅
- Missing: postal code, phone, email, NAICS, licence number
- `issue_date` = new-business signal; `status` enables active filtering
- Automation: Socrata CSV download, no auth required
- Note: `date_last_updated` timestamp = Unix 1788260448 = ~June 2026 — slightly older than Calgary/Edmonton

#### New Westminster "New this Year" — GeoJSON HTTP 403
- Direct GeoJSON download blocked (403). Portal page accessible (HTTP 200).
- Requires browser download or ArcGIS FeatureServer query with correct layer ID.
- Not a content prohibition — open data portal confirmed accessible in VR14.2.
- Defer to browser/manual validation for field profiling.

#### Victoria Current Year + Past 5 Years — GeoJSON HTTP 403
- Same pattern as New Westminster — direct GeoJSON blocked.
- Victoria Past 5 Years returned HTTP 200 but JSON truncated at 64KB fetch limit.
- Defer to browser/manual validation.

#### BC Licensed Establishments + Wineries — CKAN found 1 resource each
- Both datasets confirmed to exist in BC CKAN (1 resource each).
- `current_resource_url` not extracted — CKAN resource objects did not match expected format.
- Actual current download URLs need manual catalogue inspection at:
  - https://catalogue.data.gov.bc.ca/dataset/2b71813e-fb00-4a8a-a60e-a67a46c81d2d
  - https://catalogue.data.gov.bc.ca/dataset/1d21922b-ec4f-42e5-8f6b-bf320a286157

#### Surrey — ArcGIS Hub confirmed, current date evidence
- New portal confirmed at `opendata-surrey.hub.arcgis.com` with 2026 content.
- Business licence dataset URL not yet resolved — needs dataset-specific search on the hub.

#### Kelowna — Open Kelowna portal confirmed, current date evidence
- Portal confirmed at `opendata.kelowna.ca` with 2026 content.
- Business licence dataset URL not yet resolved — needs dataset search.

#### Delta — Portal page confirmed, no dataset links extracted
- Open Data Catalogue page confirmed at new URL.
- No business licence dataset links found in page HTML — may require Javascript rendering.

---

## 5. Coverage Gap Summary

ODBus covers only 6 of 13 provinces/territories. Provinces/territories with zero
ODBus representation that must be covered by other sources:

| Province/Territory | Current best candidate from prior VRs |
|---|---|
| SK | Saskatoon business licences (VR07 ✅) — other SK cities unknown |
| QC | REQ — BLOCKED (non-commercial licence) |
| NS | RJSC — DEFERRED (WAF block) |
| PE | OCBR — CLOSED (auth required) |
| NL | CADO — NOT SUITABLE (disclaimer prohibition) |
| YT | Supplier Directory — DEFERRED (403 block, OGL confirmed) |
| NU | NNI — PARTIALLY VALIDATED (reuse terms pending) |

---

## 6. Next Actions

| Priority | Action |
|---|---|
| 1 | Write endpoint triage script (probe_odbus_vr14_2.py) — HEAD request each of 69 URLs, classify by HTTP status + response content |
| 2 | Deep-validate top Tier A candidates (Toronto, Vancouver, Calgary, Edmonton, Winnipeg) |
| 3 | Profile New Westminster "New this Year" file — dedicated new-business event source |
| 4 | Compare current source vs ODBus 2022 snapshot for confirmed-current sources |
