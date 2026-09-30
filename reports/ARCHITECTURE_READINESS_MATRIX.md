# Architecture Readiness Matrix
# Canada B2B Business Data Pipeline

**Generated:** 2026-09-27
**Covers:** VR01 – VR19 (all validation rounds)
**Purpose:** Pre-architecture consolidation of all validated source findings, known data-quality issues,
open questions that materially affect schema/architecture decisions, and province/territory coverage gaps.

**Status:** ✅ SOURCE LANDSCAPE FROZEN — VR01–VR20 complete.
VR20 (final province gap round) complete. ON/QC improved with new municipal/specialized sources.
NS and NB confirmed as gaps. No further source discovery.
Next: CANONICAL DATA MODEL → PROVENANCE MODEL → EVENT MODEL → ENTITY RESOLUTION → INGESTION ARCHITECTURE.

**This document does NOT design the DB schema or implement the application.**
It is the factual input to the architecture/data-model discussion.

---

## 1. Validated Source Catalogue

### 1.1 Source Status Legend

- ✅ VALIDATED — confirmed accessible, profiled, licensed, production-candidate
- ⚠️ PARTIALLY VALIDATED — accessible but reuse terms unresolved, or access method incomplete
- 🔶 DEFERRED — technically blocked but NOT prohibited; needs browser/manual resolution
- ❌ NOT SUITABLE — explicitly prohibited, or auth required with no viable path

---

### 1.2 Federal Sources

| Source | Status | Grain | Rows | Access | Licence | New-Biz Signal | Contact | Employee |
|---|---|---|---|---|---|---|---|---|
| Corporations Canada active CBCA CSV | ✅ | corporation | 645,005 | Direct CSV, no auth | OGL-Canada | ❌ not in CSV (use VR03 monthly HTML) | ❌ | ❌ |
| Corporations Canada monthly incorporations HTML (VR03) | ✅ | incorporation-event | ~6,890/snapshot | HTTP 200, no auth | OGL-Canada | ✅ HIGH — monthly new incorporations by jurisdiction | ❌ | ❌ |
| Corporations Canada API (Public Plan) | ✅ | corporation | API per corp number | REST, `user-key` header, 60 req/min | OGL-Canada | ⚠️ activities[] endpoint (path confirmed, data not profiled) | ✅ director name + service address | ❌ |
| Statistics Canada Business Counts Table A (33-10-1174-01) | ✅ | aggregate | 85,793 rows | Bulk CSV ZIP | OGL-Canada | ❌ aggregate only | ❌ | ❌ — aggregate buckets only, 500+ combined |
| Statistics Canada Business Openings/Closures Table B (33-10-0722-01) | ✅ | aggregate | 8.5M rows | Bulk CSV ZIP | OGL-Canada | ✅ `Entrants` = CLASS D benchmark only | ❌ | ❌ — coarser buckets |

**ODBus (ASSET-01):** Reclassified as source-discovery index only. 69 underlying source URLs, data collected 2022. Do NOT ingest ODBus directly. Use as seed for identifying underlying municipal sources. VR14.

---

### 1.3 Provincial Sources

#### British Columbia

| Source | Status | Grain | Rows | Access | Licence | New-Biz Signal | Contact | Employee |
|---|---|---|---|---|---|---|---|---|
| BC OrgBook API v4 | ✅ | entity | API targeted only | REST, no auth, bulk prohibited | BC Gov Terms | ✅ registration date + credential history (status change events) | ❌ legislatively restricted | ❌ |
| Vancouver business licences | ✅ | licence | 206,024 | OpenDataSoft export, no auth, updated daily | OGL-Vancouver | ⚠️ MEDIUM — issueddate = issue or renewal; use min(folderyear) per entity | ❌ | ✅ `numberofemployees` 100% fill, integer, SOURCE-DEFINED |
| BC Indigenous Business Listings | ✅ | business | ~3,000+ est. | Direct CSV, no auth | OGL-BC | ❌ dataset-level Jan 2026, record-level When Updated ambiguous | ✅ phone 93.4%, email 89.4%, website 52.4%, contact 87.8% | ⚠️ 52.6% fill, ALL range strings ("10 to 19"), "500 plus" = combined |

**BC gaps:** Toronto-equivalent large-city municipal source absent (Surrey/New Westminster/Burnaby/Kelowna portal pages alive but dataset URLs unresolved — ArcGIS Hub slug rotation). Not dead — unresolved.

#### Alberta

| Source | Status | Grain | Rows | Access | Licence | New-Biz Signal | Contact | Employee |
|---|---|---|---|---|---|---|---|---|
| Calgary business licences | ✅ | licence | 23,178 | Socrata CSV, no auth | Calgary Open Data | ✅ HIGH — `first_iss_dt` = first-ever licence issuance. 227 new in last 30d, 3,249/year | ❌ | ❌ |
| Edmonton business licences | ✅ | licence | 43,719 | Socrata CSV, no auth | Edmonton Open Data | ✅ HIGH — `originalissuedate` = first ever. 757 new in last 30d, 1,558/year | ❌ | ❌ |

#### Manitoba

| Source | Status | Grain | Rows | Access | Licence | New-Biz Signal | Contact | Employee |
|---|---|---|---|---|---|---|---|---|
| Winnipeg business licences | ✅ | licence-event | 13,757 | Socrata CSV, no auth | Winnipeg Open Data | ❌ LOW — 84.7% of recent rows are "Closed (L)" — confirmed event log not master | ❌ | ❌ |
| Manitoba Companies Office weekly PDF | ✅ | filing-event | ~100–200/week | HTTP 200 direct PDF, no auth | MB Gov (no OGL stated) | ✅ HIGH — `Incorporations` category = new provincial registrations | ⚠️ registered office ~40% | ❌ |

**Winnipeg reclassification:** Reclassify from Class A (discovery master) to Class B (change/event detection — specifically useful for closure event detection via status transitions).

#### Saskatchewan

| Source | Status | Grain | Rows | Access | Licence | New-Biz Signal | Contact | Employee |
|---|---|---|---|---|---|---|---|---|
| Saskatoon all businesses XLSX | ✅ | licence | 7,472 | Direct XLSX, no auth, CKAN retired | Saskatoon Open Data | ❌ no date field in this file | ❌ | ❌ |
| Saskatoon new businesses XLSX | ✅ | licence | 51 (monthly) | Direct XLSX, no auth | Saskatoon Open Data | ✅ HIGH (small volume) — file is explicitly scoped to new licences | ❌ | ❌ |

**SK gap:** Regina — portal returned 403 (WAF, not prohibition). Second SK city unresolved.

#### Ontario

| Source | Status | Grain | Rows | Access | Licence | New-Biz Signal | Contact | Employee |
|---|---|---|---|---|---|---|---|---|
| Ontario Select Licence | ✅ | licence | 674 business / 329 individual | CKAN CSV, no auth, monthly | OGL-Ontario | ❌ no issue date field | ✅ phone 99%, email 81.2%, website 10% | ❌ |

**ON critical gap:** This is 6 regulated licence types only (Payday Lender 64%, Collection Agency 19%, Bailiff 11%). NOT Ontario business universe. Toronto WAF-blocked. Hamilton/Ottawa/Mississauga ArcGIS URLs returned HTTP 400 — likely resource ID rotation, not dead portals. ON discovery layer is the largest unresolved gap for a major province.

**VR20 ON additions — regulated-sector enrichment sources (OGL-Ontario, CSV/CKAN, all current):**

| Source | Status | Grain | Key fields | Licence |
|---|---|---|---|---|
| Community Small Business Investment Funds | ✅ PARTIALLY USABLE | registrant | name, address, contact info, registration date, registration number/status | OGL-Ontario |
| Tobacco Tax Registrant List | ✅ PARTIALLY USABLE | registrant | name, address, modification date | OGL-Ontario |
| Fuel and Gasoline Tax Registrant List | ✅ PARTIALLY USABLE | registrant | name, address, authorization info | OGL-Ontario |
| Dairy Distributors (non-shopkeepers) | ✅ PARTIALLY USABLE | business | name, address, city, postal, phone, licence number | OGL-Ontario |
| Provincially Licensed Dairy Plants | ✅ PARTIALLY USABLE | establishment | name, address, city, postal, phone, licence number | OGL-Ontario |
| Provincially Licensed Meat Plants | ✅ PARTIALLY USABLE | establishment | name, address, city, postal, phone, coordinates | OGL-Ontario |

These are regulated-industry populations only. They do NOT provide general Ontario business discovery.
Role: Ontario enrichment layer — adds phone/postal/contact for regulated businesses not in Select Licence.

#### Quebec

| Source | Status | Grain | Rows | Access | Licence | Key fields | Classification |
|---|---|---|---|---|---|---|---|
| Montréal Commercial Premises (Locaux commerciaux) | ✅ IMPLEMENTABLE | establishment | ~large (10.7MB CSV) | Direct CSV/GeoJSON, no auth | CC-BY 4.0 Québec | name, address, SCIAN (NAICS-equiv), commercial category, occupancy status, coordinates, arrondissement | Discovery + NAICS enrichment |
| Québec City Permits (Permis délivrés) | ⚠️ PARTIALLY USABLE | permit/event | ~large (11MB CSV) | Direct CSV/GeoJSON, no auth | CC-BY 4.0 | permit number, issue date, spatial/property info | Event/change signal only |

**QC note:** REQ (provincial registry) remains blocked — non-commercial restriction. These are municipal sources only.
Montréal dataset is an establishment survey (not a legal registry) — annual collection, some premises may be missed.
This is the first validated QC source with SCIAN codes. Materially improves Montréal coverage.
Province-wide QC gap: unresolved.

---

### 1.4 Territorial Sources

| Source | Status | Grain | Rows | Access | Licence | New-Biz Signal | Contact | Employee |
|---|---|---|---|---|---|---|---|---|
| NNI Nunavut Business Registry | ⚠️ PARTIALLY VALIDATED | registration | 187 active | HTTP 200, no auth, Drupal HTML | ❌ reuse terms unresolved — NNI Regulations PDF not parsed | ⚠️ MEDIUM — effective_date = renewal not founding date; snapshot diff detects new registrations | ✅ phone (conditional), email, contact_name, postal, address | ✅ integer employee count, conditional |
| NWT CROS | 🔶 DEFERRED | targeted verification | — | Browser only — current URL: justice.gov.nt.ca/app/cros-rsel/search | Unknown | — | — | — |
| Yukon Supplier Directory | 🔶 DEFERRED | business | — | 403 (OGL-Yukon confirmed) | OGL-Yukon | — | — | — |

**VR18 vs VR13.1 NNI clarification:** VR18 got HTTP 0 (transient connection failure). VR13.1 confirmed 187 active records, full profile fields, public search, no auth. The correct cumulative status is: NNI technically demonstrated as a high-value source; reuse/automation terms unresolved pending NNI Regulations PDF manual review. HTTP 0 in VR18 is a transient failure — does not supersede VR13.1 findings.

---

### 1.5 Sources Investigated but NOT SUITABLE

| Source | Status | Reason |
|---|---|---|
| NL CADO | ❌ NOT SUITABLE | Disclaimer explicitly prohibits value-added / distribution use without prior written NL government approval |
| PEI OCBR | ❌ NOT SUITABLE | Authentication required; anonymous search not possible; EULA terms restrictive |
| Quebec REQ | ❌ BLOCKED | Non-commercial use restriction — pipeline use not permitted without commercial licence |
| YellowPages.ca / Canada411.ca | ❌ NOT SUITABLE | robots.txt prohibited + HTTP 403 — not suitable for automated pipeline |
| NS RJSC | 🔶 DEFERRED | WAF/bot-protection blocks all HTTP. Not a prohibition — automation permission unknown. Rich field set confirmed from official docs (name, address, directors/officers). Browser DevTools required. |

---

## 2. Province / Territory Coverage Matrix

| Province/Territory | Discovery Layer | New-Biz Signal | Contact/Enrichment | Verification | Gap Level |
|---|---|---|---|---|---|
| Federal | Corps Canada CSV (645k) | CBCA monthly HTML (VR03) | Corps Canada API (directors) | — | ✅ COVERED |
| BC | Vancouver (206k) | Vancouver issueddate (MEDIUM) | BC Indigenous + OrgBook | OrgBook API | ✅ COVERED |
| AB | Calgary (23k) + Edmonton (44k) | Calgary first_iss_dt + Edmonton originalissuedate | ❌ | ❌ | ✅ COVERED |
| MB | Winnipeg (event log) + MB weekly PDF | MB weekly PDF Incorporations | ❌ | ❌ | ⚠️ EVENT-ONLY (no master) |
| SK | Saskatoon (7.5k) | Saskatoon new-biz file (51/month) | ❌ | ❌ | ⚠️ ONE CITY ONLY |
| ON | Ontario Select Licence (674, sector-specific) + 6 VR20 regulated-sector sources | ❌ | Ontario Select Licence + Dairy/Tobacco/Fuel/Meat regulated sources (phone/postal) | ❌ | ⚠️ PARTIAL — regulated sectors only; no general ON master |
| QC | Montréal Commercial Premises (IMPLEMENTABLE, establishment-grain, annual) | Québec City Permits (weekly event signal) | Montréal SCIAN codes | ❌ | ⚠️ PARTIAL — Montréal + QC City municipal only; no provincial master |
| NS | ❌ (RJSC WAF-blocked; no open-data alternative found — VR20 confirmed) | ❌ | ❌ | ❌ | ❌ GAP CONFIRMED |
| NB | ❌ (no municipal open-data source found — VR20 confirmed) | ❌ | ❌ | ❌ | ❌ GAP CONFIRMED |
| PE | ❌ (OCBR auth required) | ❌ | ❌ | ❌ | ❌ NOT SUITABLE |
| NL | ❌ (CADO prohibited) | ❌ | ❌ | ❌ | ❌ NOT SUITABLE |
| YT | ❌ (Supplier Dir 403, OGL confirmed) | ❌ | ❌ | ❌ | 🔶 DEFERRED |
| NT | ❌ (CROS URL confirmed, basic free) | ❌ | ❌ | ❌ | 🔶 DEFERRED (verification only) |
| NU | NNI (187, terms unresolved) | NNI effective_date (MEDIUM) | NNI (phone/email/contact) | ❌ | ⚠️ PARTIAL — terms pending |

**Summary:** BC, AB, Federal = well-covered. MB, SK = partially covered. ON, QC, NS, NB, PE, NL = major gaps for the most commercially important Canadian provinces.

---

## 3. Field Coverage Matrix

| Field | Sources That Provide It | Notes |
|---|---|---|
| Legal name | All sources | |
| Operating/trade name | Vancouver, Manitoba PDF, Corps Canada, Saskatoon | |
| Address (street) | All municipal + Corps Canada CSV | |
| Postal code | Vancouver (53.4%), BC Indigenous (93.4%), NNI, Corps Canada CSV | |
| City | All sources | |
| Province | All sources | |
| Coordinates | Calgary, Edmonton, Vancouver | |
| Phone | Ontario Select Licence (99%), BC Indigenous (93.4%), NNI (conditional) | No municipal source outside these three has phone |
| Email | Ontario Select Licence (81.2%), BC Indigenous (89.4%), NNI (present) | |
| Website | Ontario Select Licence (10%), BC Indigenous (52.4%) | Website discovery via crawl possible when domain known (VR15) |
| Contact name (primary) | NNI (contact_name), BC Indigenous (Primary Contact 87.8%) | |
| Director names | Corporations Canada API only (`_embedded.directors[]`) | Federal CBCA corps only |
| Employee count | Vancouver (100%, integer, licence-grain), NNI (conditional integer), BC Indigenous (52.6%, range strings) | No other confirmed source |
| Employee bucket | Vancouver + NNI → integer → bucket; BC Indigenous → range-string → bucket | "500 plus" / "500 plus employees" = combined bucket in both StatsCan and BC Indigenous |
| NAICS / industry | Saskatoon (NAICS sub-sector), BC Indigenous (Industry Sector), NNI (Sectors/Goods/Services), Montréal Commercial Premises (SCIAN = NAICS-equivalent) | No municipal NAICS for Calgary/Edmonton/Vancouver/Winnipeg. Montréal SCIAN = first validated QC industry classification. |
| Corporation number | Corps Canada CSV (federal) | |
| Business number (BN) | Corps Canada CSV (99.76%) | CRA cross-source matching key |
| Licence number | All municipal sources | Different ID per source — not cross-source compatible |
| Registration date | Corps Canada API activities[], BC OrgBook (credential), NNI (effective_date = renewal not founding) | |
| Status | Vancouver (5 values), Calgary (7 values), Winnipeg (10 values including closed), Corps Canada (Active in active CSV), BC OrgBook (ACT/HIS) | |

---

## 4. Data-Quality Issues to Carry Forward

These must be preserved in the architecture. Do NOT collapse them.

### 4.1 ODBus record-count discrepancy
- CSV row count: 446,575
- Metadata-stated record count: 446,573
- Delta: 2 rows unexplained
- Status: Unresolved. Does not block architecture. Document as known discrepancy.

### 4.2 NNI VR13.1 vs VR18 conflict
- VR13.1 (2026-09-26): 187 active businesses confirmed, full profile fields confirmed, HTTP 200
- VR18 (2026-09-26): HTTP 0 (connection failure)
- Resolution: VR13.1 is the authoritative finding. VR18 HTTP 0 = transient failure. NNI status = PARTIALLY VALIDATED (reuse terms unresolved), NOT "unavailable."

### 4.3 BC Indigenous `When Updated` — record-level vs dataset-level
- Record-level `When Updated` values in 500-row sample: max = 2021-12-11
- Dataset-level resource last updated (BC Open Government Portal): January 28, 2026
- These are different things — record-level update date ≠ dataset refresh date
- Do NOT use `When Updated` field as a proxy for dataset freshness in the pipeline

### 4.4 BC Indigenous employee range strings — two encodings
- Both "50 to 99" and "55 to 99" appear as distinct values in the data
- These are NOT the same — "55 to 99" may reflect a different source or data entry inconsistency
- Must store raw_employee_value separately from normalized_employee_bucket
- Do NOT silently map both to the same bucket without flagging the ambiguity

### 4.5 500+ employee bucket limitation
- StatsCan Table A: `500 plus employees` = combined 500–999 + 1000+ (no split available)
- BC Indigenous: `500 plus` = same combined bucket
- Vancouver: integer values available — CAN distinguish 500–999 from 1000+
- NNI: integer values available (small population) — CAN distinguish
- Architecture must model: `raw_employee_value`, `employee_min`, `employee_max`, `employee_bucket`, `employee_source`, `employee_verified_at`
- System must NOT fabricate the 500–999 / 1000+ split from sources that provide only "500+"

### 4.6 Winnipeg — event log not master
- 84.7% of most-recent 5,000 rows are status "Closed (L)"
- 275 unique trade_name values in 13,757 rows (~50 licence rows per entity)
- Reclassify: Class A → Class B (event detection, specifically closure events)
- Do NOT treat Winnipeg as a current business master — entity resolution from this source requires heavy deduplication and status filtering

### 4.7 Vancouver employee count — licence-grain not entity-grain
- 17.7% of unique business names have multiple different employee values across rows
- Pacific National Exhibition example: [0, 30, 200, 3000, 4000] across different licence records
- `LicenceRSN` is unique per licence row — this is the join key
- Pipeline must preserve licence-grain and resolve to entity at the entity layer using most-recent issued licence

### 4.8 Saskatoon cross-file population mismatch
- `Bus_Lic_Acct_Id` (all-businesses) and `Business_License_Id` (new-businesses) are different ID schemas
- 3 of 51 new-business names (5.9%) found in all-businesses file by exact name match
- Cannot join the two files on ID — name + address match required
- Whether the 94.1% non-match reflects different populations or formatting differences is unresolved

### 4.9 New business ≠ incorporation ≠ licence ≠ employment opening
All of the following are DIFFERENT events that must be modeled separately:
```
federal_incorporation          (CBCA monthly HTML, VR03)
provincial_registration        (Manitoba Companies Office weekly PDF)
municipal_licence_first_issue  (Calgary first_iss_dt, Edmonton originalissuedate)
municipal_licence_renewal      (most_recent_issue_date, issueddate)
licence_status_change          (Vancouver status field — Issued/Pending/Gone Out of Business)
registry_filing                (Manitoba lifecycle events)
payroll_opening / entrant      (StatsCan — benchmark only, no individual records)
nni_registration_renewal       (NNI effective_date — renewal signal)
website_first_seen             (VR15 — not yet validated as a signal)
```
Pipeline must model event_type, event_date, event_source — not a single `created_at` or `new_business_flag`.

### 4.10 Multi-grain sources — do not flatten
Sources operate at different grains. Mapping:
| Grain | Sources |
|---|---|
| corporation (legal entity) | Corps Canada CSV, Corps Canada API, BC OrgBook |
| entity/business (operating) | BC Indigenous, NNI, Saskatoon all-biz |
| location | Some Vancouver records (multi-location businesses have multiple rows) |
| licence | Calgary, Edmonton, Vancouver, Saskatoon, Ontario Select Licence |
| licence-event (historical) | Winnipeg, Manitoba PDF |
| filing-event | Manitoba Companies Office PDF |
| registration | NNI |

Entity resolution layer is required before any cross-source merge. The entity layer must preserve source_id and source_grain from every contributing record.

---

## 5. Source Enrichment Roles

| Pipeline Layer | Sources | Notes |
|---|---|---|
| **Discovery (Class A)** | Corps Canada CBCA CSV, Calgary, Edmonton, Vancouver, Saskatoon all-biz | Build candidate universe |
| **New-business events (Class B)** | CBCA monthly HTML (VR03), Calgary first_iss_dt, Edmonton originalissuedate, Manitoba weekly PDFs Incorporations, Saskatoon new-biz file, NNI snapshot diff | Detect new entries; different event types — do not merge |
| **Enrichment (Class C)** | Corps Canada API (directors), BC OrgBook (BC identity verification), Ontario Select Licence (phone/email), BC Indigenous (phone/email/contact/employee), NNI (phone/email/contact/employee), Vancouver (employee count), website crawl (VR15 — phone opportunistic) | Add fields to known businesses |
| **Benchmark (Class D)** | StatsCan Table A (business counts by province × NAICS × size), StatsCan Table B (Entrants — new employer benchmark) | Validate pipeline coverage — no individual records |

---

## 6. Contact / Decision-Maker Enrichment — Confirmed Findings (updated with VR19)

| Signal | Status | Notes |
|---|---|---|
| Website phone extraction | ⚠️ PARTIAL | Technically viable when domain known. Requires: CA area-code validation filter, franchise/location context preservation, not corporate HQ assumption. ~10% coverage with validation. |
| Website email extraction | ❌ NOT SUITABLE AS CORE ENRICHMENT | 0/30 across VR15+VR19 across 3 methods (visible-text, mailto href, JSON-LD). Demonstrated yield insufficient to justify as core dependency. Keep optional/experimental only. |
| Person/decision-maker from website HTML | ❌ NOT SUITABLE AS CORE ENRICHMENT | 0/30 valid person signals across VR15+VR19. JSON-LD Person 0%, stoplist regex 0%. Fully accessible 9-path site returned zero. Demonstrated yield insufficient for core pipeline use. |
| Director names | ✅ Corps Canada API | Federal CBCA corps only. `_embedded.directors[{firstName, lastName, serviceAddress}]` |
| Contact name | ✅ NNI (conditional), BC Indigenous (87.8%) | Sector/population-specific |
| Director/officer from NS RJSC | 🔶 DEFERRED | Rich public field set confirmed from official docs; WAF-blocked; browser DevTools needed |

**Person data model (confirmed):**
`person_name`, `role`, `role_type`, `source`, `confidence`, `source_url`, `verified_at`

Role types must distinguish: `DIRECTOR` ≠ `OWNER` ≠ `PRESIDENT` ≠ `GENERAL_MANAGER` ≠ `IT` ≠ `PROCUREMENT` ≠ `OTHER`

**Email sources confirmed:**
- Ontario Select Licence (81.2% fill)
- BC Indigenous Business Listings (89.4% fill)
- NNI (present, conditional)
- Website extraction: optional/experimental, NOT a core dependency

---

## 7. Compliance / Automation Constraints

| Source | Constraint |
|---|---|
| StatsCan Business Register | Individual-business data is confidential under Statistics Act — no individual records available |
| BC OrgBook | Bulk enumeration prohibited; 10-page limit enforced; targeted lookup only |
| NL CADO | Value-added product use explicitly prohibited — NOT SUITABLE |
| PEI OCBR | Login required; EULA restrictive — NOT SUITABLE |
| Quebec REQ | Non-commercial restriction — BLOCKED |
| NB corporate registry | Automated copying of search result groups restricted |
| Saskatchewan ISC | Bulk data $200+ minimum — not free |
| Manitoba Companies Office | Weekly listings not an official transcript; annual returns/renewals excluded |
| NS RJSC | WAF blocks all automated HTTP — automation permission unknown |
| NNI | No explicit prohibition; no OGL; NNI Regulations PDF review pending — do not mark commercially cleared |
| Vancouver Open Data | OGL-Vancouver, daily updates, LicenceRSN = unique per licence record |
| Corporations Canada API | Public Plan subscribed; 60 req/min; `user-key` header auth; CBCA corps only |
| BC Indigenous | OGL-BC; commercial use permitted |
| YellowPages / Canada411 | robots.txt prohibited + HTTP 403 — not suitable |
| OSM Overpass | ODbL (commercial use with attribution OK); HTTP 504 timeout was transient — deferred |

---

## 8. Open Questions That Materially Affect Architecture

These must be resolved before or during architecture/schema design:

### Q1 — Entity resolution strategy
How do we merge records from sources operating at different grains (corporation vs licence vs event) into a single canonical business entity?
- Must preserve source_id, source_grain, source_provenance on every record
- Entity ID must be pipeline-generated, not borrowed from any single source
- Corporation number (federal) and BN are the strongest cross-source join keys where available

### Q2 — Event model schema
New-business events must be modeled as separate event types, not a single `created_at` field.
Proposed event table: `(entity_id, event_type, event_date, event_source, raw_value)`
Where `event_type` ∈ {federal_incorporation, provincial_registration, municipal_licence_first_issue, municipal_licence_renewal, licence_status_change, registry_filing, nni_registration_renewal, ...}

### Q3 — Employee field model
Three semantic layers needed:
- `raw_employee_value` — exact value as returned by source ("385.0", "10 to 19", "500 plus", 2)
- `employee_min` / `employee_max` — derived range bounds
- `employee_bucket` — normalized 9-bucket label
- `employee_source` / `employee_verified_at`
Must NOT fabricate 500–999 vs 1000+ split from combined-bucket sources.

Employee data is absent from several major discovery sources including Calgary, Edmonton, Saskatoon, Manitoba weekly PDFs and Corporations Canada CSV, so substantial NULL coverage is expected. The actual combined null rate can only be measured after ingestion and entity resolution — not before.

Rules:
- exact count → direct bucket
- explicit range → bucket
- 500+ → preserve raw value; do not fabricate 500–999 vs 1000+
- inferred/estimated → explicitly labelled
- unavailable → NULL

### Q4 — Ontario + Quebec discovery gap
ON and QC together represent ~60% of Canadian business activity.

**Post-VR20 status:**
- ON: no confirmed general-purpose discovery source. Six new regulated-sector sources add enrichment (phone/postal) for specific populations. General ON gap remains.
- QC: Montréal Commercial Premises (IMPLEMENTABLE) is the first validated QC discovery source. Annual establishment survey with SCIAN codes. Québec City permits = event signal. No provincial master.

Architecture must explicitly flag records as "province not covered by general discovery source" rather than silently under-representing ON/QC. The Montréal dataset materially improves QC coverage at city level but does not resolve province-wide QC. Both provinces remain as known partial gaps in the architecture.

### Q5 — Winnipeg reclassification impact
If Winnipeg is Class B (event log) not Class A (master), MB discovery layer relies entirely on Manitoba Companies Office weekly PDFs for new-business events, with no municipal business master for Winnipeg. Does architecture need a fallback or is this an accepted gap?

### Q6 — NNI reuse terms
NNI Regulations PDF not parsed. Until parsed, NNI cannot be marked as commercially cleared. Architecture must model NNI as conditional — pipeline ingestible pending terms confirmation.

### Q7 — API rate limits and ingestion cadence
Corporations Canada API: 60 req/min. 645,000 active corps would require ~180 hours to enrich one field per corp. This constrains the enrichment layer to event-triggered or sample-based enrichment — not full-population enrichment at launch.

### Q8 — Sales-ready record definition
What fields must be populated for a business record to be considered "sales-ready" for the telecom sales operation?
Suggested minimum: business_name, address, province, status=active, at least one of (phone | email | website | director_name).
This threshold determines how many records are actually usable out of the discovered universe.

---

## 9. Architecture Readiness Summary

| Dimension | Status |
|---|---|
| Source catalogue complete | ✅ |
| Province/territory gaps identified | ✅ |
| Grain/entity-resolution requirements documented | ✅ |
| Event model requirements documented | ✅ |
| Employee field model requirements documented | ✅ |
| Contact enrichment strategy documented | ✅ (updated with VR19) |
| Email enrichment strategy documented | ✅ — website extraction closed as non-core; 3 confirmed sources |
| Decision-maker enrichment strategy documented | ✅ — website extraction closed as non-core; person model defined |
| Compliance constraints documented | ✅ |
| Data-quality issues to preserve documented | ✅ |
| Open architectural questions listed | ✅ |
| ON/QC/NS/NB final province gap round | ✅ COMPLETE — VR20 |
| Source landscape | ✅ FROZEN |
| DB schema designed | ❌ Not yet — this document is the pre-input |
| Application implemented | ❌ Not yet |

**SOURCE LANDSCAPE IS FROZEN. Validation phase: COMPLETE.**

Final province outcomes (VR20):
- ON → PARTIAL (6 regulated-sector enrichment sources; no general master)
- QC → PARTIAL (Montréal Commercial Premises IMPLEMENTABLE; QC City permits event layer; no provincial master)
- NS → GAP CONFIRMED
- NB → GAP CONFIRMED

**Next step: CANONICAL DATA MODEL → PROVENANCE MODEL → EVENT MODEL → ENTITY RESOLUTION/DEDUPLICATION → INGESTION ARCHITECTURE → ENRICHMENT ARCHITECTURE → SCHEDULING/RETRY → API/DASHBOARD → IMPLEMENTATION PLAN.**

Do not begin implementation until full architecture is complete.
