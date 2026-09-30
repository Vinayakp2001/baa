# VR16+17 — Source Coverage & Freshness + Cross-Source Overlap

Generated: `2026-09-26T10:59:20Z`
Script: `scripts/probe_vr16_17_source_coverage_overlap.py`
JSON: `reports/validation_rounds/VR16_17_SOURCE_COVERAGE_OVERLAP.json`

---

## PART A — Source Freshness & Coverage

### Summary Table

| Province | City/Source | Status | Access | Date Signal | Rows Sampled | Employee | Phone/Email |
|---|---|---|---|---|---|---|---|
| ON | Hamilton — hamilton_food_shops | HTTP 400 | unknown | ? | ? | none | phone:none email:none |
| ON | Hamilton — hamilton_trade_cont | HTTP 404 | dead | ? | ? | none | phone:none email:none |
| ON | Ottawa — ottawa_business | HTTP 400 | unknown | ? | ? | none | phone:none email:none |
| ON | Brampton — brampton_business | HTTP 0 | unknown | ? | ? | none | phone:none email:none |
| ON | Mississauga — mississauga_current | HTTP 400 | unknown | ? | ? | none | phone:none email:none |
| BC | BC (provincial) — bc_indigenous | HTTP 200 | direct_csv | 2021-12-11 | 500 | Number of Employees | phone:Phone email:Email,Mailing Address |
| BC | BC (provincial) — bc_establishments_ckan | HTTP 200 | ckan_metadata | ? | ? | none | phone:none email:none |
| BC | BC (provincial) — bc_wineries_ckan | HTTP 200 | ckan_metadata | ? | ? | none | phone:none email:none |
| BC | Surrey — surrey_arcgis | HTTP 404 | dead | ? | ? | none | phone:none email:none |
| BC | Burnaby — burnaby_business | HTTP 200 | portal_page_only | ? | ? | none | phone:none email:none |
| BC | New Westminster — new_west_all | HTTP 404 | dead | ? | ? | none | phone:none email:none |
| BC | New Westminster — new_west_new_this_year | HTTP 404 | dead | ? | ? | none | phone:none email:none |
| BC | Kelowna — kelowna_business | HTTP 200 | portal_page_only | ? | ? | none | phone:none email:none |
| BC | Port Moody — port_moody | HTTP 404 | dead | ? | ? | none | phone:none email:none |
| AB | Chestermere — chestermere | HTTP 0 | unknown | ? | ? | none | phone:none email:none |
| NB | Moncton — moncton_grocery | HTTP 0 | unknown | ? | ? | none | phone:none email:none |
| NB | Saint John — saintjohn_grocery | HTTP 404 | dead | ? | ? | none | phone:none email:none |
| SK | Saskatoon — saskatoon_portal | HTTP 200 | html_only | ? | ? | none | phone:none email:none |
| SK | Regina — regina_business | HTTP 403 | blocked | ? | ? | none | phone:none email:none |
| NS | Halifax — halifax_business | HTTP 404 | dead | ? | ? | none | phone:none email:none |
| NB | Fredericton — fredericton_business | HTTP 200 | portal_page_only | ? | ? | none | phone:none email:none |

### Detailed Findings

#### ON — Hamilton (hamilton_food_shops)
- URL: `https://open.hamilton.ca/datasets/1be5ece7f68c4e01855ada16c5f0a8e0_0.csv`
- Notes: Hamilton food shop licences — 1 of 13 Hamilton specialized datasets
- HTTP status: 400
- Access method: unknown
- Observation: HTTP 400

#### ON — Hamilton (hamilton_trade_cont)
- URL: `https://opendata.hamilton.ca/datasets/fdb8d2e7de9e4879bcf9b7faac8abb0e_0.csv`
- Notes: Hamilton trade contractors
- HTTP status: 404
- Access method: dead
- Observation: HTTP 404 — URL dead or rotated.

#### ON — Ottawa (ottawa_business)
- URL: `https://open.ottawa.ca/datasets/6dd1e4b7db2f48d48af04c3adb71e9c9_0.csv`
- Notes: Ottawa business licences — major ON city
- HTTP status: 400
- Access method: unknown
- Observation: HTTP 400

#### ON — Brampton (brampton_business)
- URL: `https://opendata.brampton.ca/datasets/brampton::business-directory/explore`
- Notes: Brampton business directory portal
- HTTP status: 0
- Access method: unknown
- Observation: Connection error: <urlopen error [Errno 11001] getaddrinfo failed>

#### ON — Mississauga (mississauga_current)
- URL: `https://opendata.arcgis.com/datasets/68b12f84eb0b4b9484a9781b4ccf6c0e_0.csv`
- Notes: Mississauga current business directory (not the 2019 403 one)
- HTTP status: 400
- Access method: unknown
- Observation: HTTP 400

#### BC — BC (provincial) (bc_indigenous)
- URL: `https://catalogue.data.gov.bc.ca/dataset/bdc81d33-1ab5-4882-9764-8701e8971bb7/resource/f805f66e-8294-4f8d-bdd9-2400eb3938d0/download/bcindigenousbusinesslistings.csv`
- Notes: BC Indigenous Business Listings — direct CSV confirmed VR14.2
- HTTP status: 200
- Access method: direct_csv
- Observation: CSV downloaded. Sample=500 rows. Fields: 24. Date field: When Updated. Max date in sample: 2021-12-11. Employee field: Number of Employees. Phone: ['Phone']. Email: ['Email', 'Mailing Address'].
- Fields (24): ['Business Name', 'Description', 'Address', 'Postal Code', 'Email', 'Phone', 'Fax', 'Web Site', 'City', 'Latitude', 'Longitude', 'Keywords', 'Mailing Address', 'Indigenous Ownership', 'Region', 'Type', 'Industry Sector', 'Year Formed', 'Number of Employees', 'Primary Contact', 'Contact Title', 'Twitter', 'Facebook', 'When Updated']
- Fill rates (top 8): {'Business Name': 100.0, 'City': 100.0, 'Latitude': 100.0, 'Longitude': 100.0, 'Keywords': 100.0, 'Region': 100.0, 'When Updated': 100.0, 'Indigenous Ownership': 99.8}

#### BC — BC (provincial) (bc_establishments_ckan)
- URL: `https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=2b71813e-fb00-4a8a-a60e-a67a46c81d2d`
- Notes: BC Licensed Establishments — CKAN metadata to find current download URL
- HTTP status: 200
- Access method: ckan_metadata
- Observation: CKAN package found. Resources: 1. [HTML] https://www2.gov.bc.ca/gov/content?id=6D2A8A0AC8C64BECB9B1C2AD7FB33006 | 

#### BC — BC (provincial) (bc_wineries_ckan)
- URL: `https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=1d21922b-ec4f-42e5-8f6b-bf320a286157`
- Notes: BC Winery Locations — CKAN metadata to find current download URL
- HTTP status: 200
- Access method: ckan_metadata
- Observation: CKAN package found. Resources: 1. [HTML] https://www2.gov.bc.ca/gov/content?id=6D2A8A0AC8C64BECB9B1C2AD7FB33006 | 

#### BC — Surrey (surrey_arcgis)
- URL: `https://opendata-surrey.hub.arcgis.com/datasets/surrey::active-business-licences/about`
- Notes: Surrey active business licences — migrated to ArcGIS Hub
- HTTP status: 404
- Access method: dead
- Observation: HTTP 404 — URL dead or rotated.

#### BC — Burnaby (burnaby_business)
- URL: `https://data.burnaby.ca/datasets/burnaby::business-licences/explore`
- Notes: Burnaby business licences
- HTTP status: 200
- Access method: portal_page_only
- Observation: Portal page: HTTP 200, 51951 bytes. 22licen. Date signal: 2025-03-17.

#### BC — New Westminster (new_west_all)
- URL: `https://opendata.newwestcity.ca/datasets/NewWest::business-licences-current-year/explore`
- Notes: New Westminster all current year
- HTTP status: 404
- Access method: dead
- Observation: HTTP 404 — URL dead or rotated.

#### BC — New Westminster (new_west_new_this_year)
- URL: `https://opendata.newwestcity.ca/datasets/NewWest::business-licences-new-this-year/explore`
- Notes: New Westminster new-this-year — highest-priority new-biz signal
- HTTP status: 404
- Access method: dead
- Observation: HTTP 404 — URL dead or rotated.

#### BC — Kelowna (kelowna_business)
- URL: `https://opendata.kelowna.ca/datasets/kelowna::business-licences/about`
- Notes: Kelowna business licences — portal confirmed live VR14.3
- HTTP status: 200
- Access method: portal_page_only
- Observation: Portal page: HTTP 200, 48791 bytes. 22licen. Date signal: 2025-12-24.

#### BC — Port Moody (port_moody)
- URL: `https://data.portmoody.ca/datasets/portmoody::business-licences/explore`
- Notes: Port Moody business licences
- HTTP status: 404
- Access method: dead
- Observation: HTTP 404 — URL dead or rotated.

#### AB — Chestermere (chestermere)
- URL: `https://data.chestermere.ca/datasets/chestermere::business-licences/explore`
- Notes: Chestermere — small AB city
- HTTP status: 0
- Access method: unknown
- Observation: Connection error: <urlopen error [Errno 11001] getaddrinfo failed>

#### NB — Moncton (moncton_grocery)
- URL: `https://opendata.moncton.ca/datasets/moncton::grocery-stores/explore`
- Notes: Moncton grocery stores — sector-specific
- HTTP status: 0
- Access method: unknown
- Observation: Connection error: <urlopen error timed out>

#### NB — Saint John (saintjohn_grocery)
- URL: `https://catalogue-saintjohn.opendata.arcgis.com/datasets/saintjohn::grocery-stores/explore`
- Notes: Saint John grocery stores — sector-specific
- HTTP status: 404
- Access method: dead
- Observation: HTTP 404 — URL dead or rotated.

#### SK — Saskatoon (saskatoon_portal)
- URL: `https://opendata-saskatoon.opendata.arcgis.com/`
- Notes: Saskatoon open data portal — check for other business datasets beyond already-downloaded XLSX
- HTTP status: 200
- Access method: html_only
- Observation: HTML/unknown: HTTP 200, 5580 bytes. Date signal: no 2020s date found.

#### SK — Regina (regina_business)
- URL: `https://openregina.ca/datasets/regina::business-licences/explore`
- Notes: Regina business licences — second SK city, not in ODBus
- HTTP status: 403
- Access method: blocked
- Observation: HTTP 403 — blocked/WAF. Not a prohibition if open data portal.

#### NS — Halifax (halifax_business)
- URL: `https://catalogue-hrm.opendata.arcgis.com/datasets/hrm::business-licences/explore`
- Notes: Halifax Regional Municipality — NS gap coverage, not in ODBus
- HTTP status: 404
- Access method: dead
- Observation: HTTP 404 — URL dead or rotated.

#### NB — Fredericton (fredericton_business)
- URL: `https://data.fredericton.ca/datasets/fredericton::business-licences/explore`
- Notes: Fredericton — NB city not in ODBus
- HTTP status: 200
- Access method: portal_page_only
- Observation: Portal page: HTTP 200, 38643 bytes. 22licen. Date signal: 2025-03-13.

---

## PART A — Key Findings Summary

### BC Indigenous Business Listings — CONFIRMED LIVE, RICHEST CONTACT FIELD SET FOUND

| Field | Fill Rate (500-row sample) |
|---|---|
| Business Name | 100% |
| Phone | 93.4% |
| Email | 89.4% |
| Postal Code | 93.4% |
| Mailing Address | 98.6% |
| Primary Contact | 87.8% |
| Contact Title | 76.2% |
| Industry Sector | 97.0% |
| Number of Employees | 52.6% |
| Web Site | 52.4% |
| Year Formed | 56.8% |
| Indigenous Ownership | 99.8% |
| When Updated (max in sample) | 2021-12-11 |

Full schema (24 fields): Business Name, Description, Address, Postal Code, Email, Phone, Fax, Web Site, City, Latitude, Longitude, Keywords, Mailing Address, Indigenous Ownership, Region, Type, Industry Sector, Year Formed, Number of Employees, Primary Contact, Contact Title, Twitter, Facebook, When Updated

**GPT correction applied (2026-09-26):** The 2021-12-11 dates in the sample are RECORD-LEVEL `When Updated` values, not dataset-level freshness. The official BC Open Government Portal confirms the CSV resource was last updated **January 28, 2026**. Dataset is current. The sampled records may not have been individually updated since 2021 but the dataset itself has a 2026 refresh. Licence = OGL-BC. Status: RECLASSIFIED as current candidate source.

### BC Establishments + BC Wineries — CKAN resource is HTML page, not CSV

Both CKAN packages return 1 resource each, but the resource URL resolves to a BC government HTML content page (`gov.bc.ca/gov/content?id=6D2A8A0AC8C64BECB9B1C2AD7FB33006`), not a downloadable CSV. The actual download mechanism is not an open data API — requires manual inspection of the BC government content page to find the current data file.

### ArcGIS Hub URLs — Widespread 404 (URL rotation pattern)

The following ArcGIS Hub `/datasets/{org}::{dataset-slug}/explore` URLs all returned HTTP 404:
- Surrey active-business-licences
- New Westminster business-licences-current-year
- New Westminster business-licences-new-this-year
- Port Moody business-licences
- Halifax HRM business-licences
- Saint John grocery-stores

Pattern: ArcGIS Hub dataset slugs rotate when datasets are updated or republished. The portal organization pages themselves may still be live — the specific dataset slug paths have changed. GPT needs to find current dataset URLs by browsing the portal organization pages directly.

### Ontario sources (Hamilton, Ottawa, Mississauga) — HTTP 400

All three ON ArcGIS-style direct CSV URLs returned HTTP 400. These are likely stale direct-download resource IDs that have rotated. The open data portals for these cities are expected to still exist — new dataset resource IDs needed.

### Connection failures (Brampton, Chestermere, Moncton) — DNS/timeout

DNS resolution failed for `opendata.brampton.ca` and `data.chestermere.ca`. Moncton timed out. These are transient network failures or subdomain changes — not confirmed dead.

### Portal pages with date signals (Burnaby, Kelowna, Fredericton)

Three portals returned HTTP 200 portal pages with date signals in HTML:
- Burnaby: date signal 2025-03-17 (page content)
- Kelowna: date signal 2025-12-24 (page content)
- Fredericton: date signal 2025-03-13 (page content)

All show "22licen" pattern in HTML — consistent with licence count display. Actual dataset download URLs not extracted from portal JS-rendered pages.

### Regina (SK) — HTTP 403

Regina open data portal returned HTTP 403. This is a WAF/bot-protection response, consistent with the ArcGIS Hub portal pattern seen elsewhere. Not a content prohibition. Regina has an open data programme — browser inspection needed for current dataset URL.

### Saskatoon portal — HTTP 200, no date signal extracted

Saskatoon ArcGIS Hub root page returned 200 (5,580 bytes) but no 2020s date found in static HTML — JS-rendered content. Portal is alive but business licence dataset URL not extractable without JS rendering.

---

## PART B — Cross-Source Overlap & Entity Resolution

### Sources Compared

- **Ontario Select Licence (VR06)**: 344 unique names
- **Saskatoon All Businesses (VR07)**: 7141 unique names

### Exact Name Overlap Matrix

- **ontario_select_licence** vs **saskatoon_businesses**: 0 exact matches (0.0% of A=344, 0.0% of B=7141)

### Entity Resolution Patterns

#### Winnipeg (VR14.4) — multi_licence_per_entity
- 13,757 rows but only 275 unique trade_name values — ~50 licence rows per business on average. Grain is licence-event, not entity.
- Implication: Group by trade_name + address to approximate entity count; expect significant loss from 13,757 → ~275

#### Vancouver (VR14.4.1) — multi_licence_employee_variance
- 17.7% of unique business names have multiple different employee values across rows. Extreme example: Pacific National Exhibition = [0, 30, 200, 3000, 4000].
- Implication: Employee count must be resolved at entity layer (e.g. most-recent licence row), not averaged

#### Saskatoon (VR07) — schema_grain_mismatch
- all-businesses file (7,472 rows, Bus_Lic_Acct_Id) and new-businesses file (51 rows, Business_License_Id) use different ID schemas — 5.9% name match across files.
- Implication: Two Saskatoon files cannot be joined on ID. Name-based fuzzy match required with high false-positive risk.

#### Saskatoon intra-city (VR07) — intra_city_schema_mismatch
- New-biz file vs all-biz file exact name match rate.
- Implication: Low match rate confirms different populations or different naming conventions, not simply a subset.

---

## VR16+17 — CLOSED WITH FOLLOW-UP ITEMS

GPT conclusions applied 2026-09-26:

- ODBus 69 underlying sources have substantial link rot, portal migration, and stale resource URLs — expected for a 2022 aggregation. ODBus remains a source-discovery/reference layer only. Do not attempt to repair all 69 URLs.
- Individual underlying datasets should be promoted only after independent validation (as was done for Calgary, Edmonton, Vancouver, Winnipeg in VR14.4).
- BC Indigenous Business Listings reclassified: dataset last updated January 28, 2026 (OGL-BC). Record-level `When Updated` dates (2021) are per-record, not dataset-level. Sector/population-specific (Indigenous-owned BC businesses) — cannot serve as general BC business master but is a high-value enrichment layer for that population.
- ArcGIS Hub 404s are stale resource slugs, not confirmed dataset deletions. Do not classify as dead without browser verification of the portal org pages.
- Cross-source testing confirms that entity-grain varies per source (business vs licence vs location vs event). Name matching alone cannot be used for deduplication. Source IDs and source-grain metadata must be preserved throughout the pipeline.
- Next: VR18 — New Business Detection + Employee-Size Consistency + Source Complementarity (combines original VR18 + VR19 scope).

## Next: VR18 brief

Validate the three remaining questions needed before architecture/data-model:
1. Which confirmed sources produce reliable new-business/change event signals, and what is the event lag?
2. How consistent are employee-size classifications across sources that provide them (Vancouver, NNI, BC Indigenous), and do they agree for the same business?
3. What additional business coverage does each source layer provide that others do not (complementarity)?

Use only the strongest confirmed-current sources: Corporations Canada CBCA CSV, Calgary, Edmonton, Vancouver, Winnipeg, Saskatoon, Ontario Select Licence, NNI, BC Indigenous, BC OrgBook API.
Do not chase new unvalidated sources in this round.
