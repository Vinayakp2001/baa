# Source Discovery Tracker

> **Purpose:** Living reference for every data source identified during the Canada-wide source discovery pass.
> Never assume — every cell marked `?` must be verified before the source enters the architecture.
> Update this file whenever a meaningful finding is made.
>
> **Last updated:** 2026-09-26 — VR15.1 + VR15.2 complete. VR15 enrichment probe results: Website crawler functional when valid domain known (1/10 full crawl, 2 phones extracted). DDG Lite discovery returned 0 usable domains for no-website records — alternative discovery mechanism needed. Corporations Canada HTML route: 10/10 pages accessible, director names extracted for 2 small corps (Nigel Stokes / MARIO TESTA), large corps returned no director text (likely JS-rendered). API route: 404 on all 10 (unauthenticated access not available — VR04.1 API key still required). Reports: VR15_WEBSITE_ENRICHMENT.md + VR15_CORPORATIONS_CONTACTS.md

---

## Revised Research Phase Plan

```
PHASE 1 — SOURCE DISCOVERY ✅ COMPLETE (all 13 provinces/territories + federal)
       ↓
PHASE 1.5 — CANADA-WIDE GAP ANALYSIS ✅ COMPLETE → reports/CANADA_WIDE_GAP_ANALYSIS.md
       ↓
PHASE 2 — SOURCE VALIDATION  ← IN PROGRESS
       ↓
VR01 ✅ Corporations Canada active CSV — 645,005 rows, 18 cols, validated
VR02 ✅ Province distribution + monthly transactions structure mapped
VR03 ✅ CBCA monthly incorporations HTML profiled — 6,890 records, date range 2026-04-08→2026-10-12, all 13 jurisdictions, 0 duplicates, 0 missing fields
VR04 ⚠️ Corporations Canada API — PARTIALLY VALIDATED: real gateway (api.ic.gc.ca) requires API key; URL paths accepted by ISED host; JSON schemas unvalidated; VR04.1 deferred (subscribe to Public Plan)
VR05 ✅ Statistics Canada Business Counts — Table A (85,793 rows, 8/9 buckets mappable, `500 plus employees` is a combined label covering 500–999 AND 1000+; no current StatsCan table separates these two buckets) + Table B (8.5M rows, Jan 2015–May 2026, coarser buckets, 91% suppressed at CMA level, 8 dynamics categories confirmed: Active/Opening/Continuing/Closing/Reopening/Entrants/Temporary closures/Exits; `Entrants` = best benchmark for genuinely new employer businesses)
VR06 ✅ Ontario Select Licence dataset — 674 business rows (345 unique legal names, 369 unique licence numbers), 329 individual rows. Record grain = 1 row per licence, NOT per business. Payday Lender = 64.1% of records (not listed in original RR02). Phone/email/website fields present but "N/A" used as null placeholder — website valid format only 10.1%, email 81.2%, phone 99%. Individual dataset links person→employer via shared Legal Name. OGL Ontario — commercial use permitted. Report: VR06_ONTARIO_SELECT_LICENCE.md
VR07 ✅ Saskatoon business licence data — All-businesses: 7,472 rows, 10 cols, `Bus_Lic_Acct_Id` (97.5%), NAICS sub-sector (86 codes), structured split address, no postal/phone/email/website/date. New-businesses: 51 rows, 27 cols (17 blank — export template artefact; preserve, do not discard), `Business_License_Id` (different grain/schema from all-biz), NAICS national level, `Business_Desc`. Cross-file name match = 5.9% — unresolved (different IDs + schemas; not evidence of different population). No contact fields in either file. Municipal new-business/licensing signal only — not "newly opened" or "newly incorporated". CKAN portal retired Aug 2024. Report: VR07_SASKATOON_BUSINESS_LICENCES.md
VR08 ✅ Manitoba Companies Office weekly filings — 14 weekly PDFs available (Jun 20–Sep 19 2026), listing page live at companiesoffice.gov.mb.ca/listings.html. Two PDFs downloaded: Sep 19 (55 pages, 89k chars) + Sep 12 (36 pages, 59k chars). Both text-extractable — no OCR needed. Zero file-number overlap between the two weeks — confirmed independent event batches (ideal for incremental ingestion). Filing categories confirmed: Incorporations, Amendments (name change + without), Amalgamations, Revivals, Dissolutions, Restorations, Cancellations, Registration Dissolutions. File No. present 95%+. Registered office ~34–52%. Phone=0, Email=0 — identity/event source only. No NAICS. Report: VR08_MANITOBA_WEEKLY_FILINGS.md
VR09 ✅ BC OrgBook API v4 — All endpoints confirmed. Autocomplete: name/BC Reg ID/CRA BN all return 200. Credential-set endpoint confirmed working — registration_date, entity_status (ACT/HIS), entity_type, jurisdiction, reason_description (filing event type), legal name all present in live credential attributes. Full credential history timeline confirmed (multiple credentials per entity showing status changes). Address/phone/email/directors: absent — legislatively restricted. Bulk enumeration prohibited by BC Terms. Role confirmed: Class C targeted BC identity/status verification + credential-history enrichment. Report: VR09_BC_ORGBOOK_API.md
VR10 ⚠️ DEFERRED Nova Scotia RJSC
VR11 ⚠️ PARTIALLY VALIDATED PEI OCBR — VR11.1 complete. OCBR application confirmed reachable. SPA architecture confirmed. All 3 JS assets fetched. Backend API endpoint confirmed: `/ocbr/search/results?` (`$.ajax GET`, extracted from BasicBusinessSearch.js). Authentication confirmed required: unauthenticated GET to search endpoint returns Login page (not JSON). CSRF token (`X-CSRF-TOKEN`) required. robots.txt: OCBR host has no robots.txt; PEI gov robots.txt is Drupal CMS only — no bot exclusion for OCBR. Anonymous public search: NOT POSSIBLE. Production automation would require registered account session + CSRF handling + unresolved commercial EULA terms. Recommendation: no further investment — PEI OCBR is not suitable for unauthenticated pipeline automation. Proceed to VR12. Report: VR11_PEI_OCBR.md
VR12 ❌ NOT SUITABLE NL CADO — Search page accessible anonymously (HTTP 200, no auth). ASP.NET WebForms confirmed: hidden fields `__VIEWSTATE`/`__VIEWSTATEGENERATOR`/`__EVENTVALIDATION`, search inputs `txtNameKeywords1`/`txtNameKeywords2`/`txtCompanyNumber`. No JSON API. Disclaimer fully retrieved — explicit copyright clause prohibits: copying, distributing, leasing, selling, or using data "as part of a value added product" or making it available to another party without prior written Government of NL approval. No OGL. robots.txt not present. Pipeline is a commercial value-added product — use is directly and unambiguously prohibited by published terms. Script POST gap (field not populated) means search result fields not observed — secondary given licensing outcome. Report: VR12_NL_CADO.md
VR13 ⚠️ DEFERRED (4/6) + PROMISING CANDIDATE (1/6) + DEFERRED/PARTIAL (1/6) — Yukon/NWT/Nunavut combined round. Yukon YCOR: status 0 (host unreachable — low priority). Yukon Supplier Directory: 403 on open.yukon.ca (bot protection — OGL-Yukon confirmed, manual browser download needed; freshness concern: catalogue metadata shows 2022 but government claims annual updates). NWT CROS: host alive, registry URLs 404 (URL migration confirmed — current path: justice.gov.nt.ca/app/cros-rsel/search, basic info free, full profiles paid, role = targeted verification only). NWT BIP Registry: 200 but wrong CMS page (low priority). Nunavut Corporate Registry: 403 Cloudflare (low priority). NNI Registry: PROMISING CANDIDATE — nni.gov.nu.ca returns 200, PUBLIC anonymous search CONFIRMED (no login required), 3 search modes (by community / by name / supplier search), live records with Sep 2026 effective dates, 187 businesses in all-Nunavut community search, supplier classification available. VR13.1 NNI scripted profiling next. Report: VR13_YUKON_NWT_NUNAVUT.md (GPT corrections applied 2026-09-26)
VR13.1 ✅ NNI Business Registry — PARTIALLY VALIDATED HIGH-VALUE CANDIDATE (Class A/B/C hybrid). 187 active NNI-registered Nunavut businesses at /business/list (HTTP 200, no auth, no pagination). List fields: name + effective_date + community. Profile fields confirmed (/business/profile/{id}, plain HTML table, no auth): business_name, business_number, business_type (Incorporations / Sole Proprietor/Partnership), street_address, community, postal_code, territory, phone* (conditional — absent on some records), email, contact_name, employee_count (INTEGER — first individual-level employee count found in this research), status (Active), effective_date (ISO timestamp precision), sectors[], goods[], services[]. Sector classification: 11 sectors + 74 goods + 211 services. Effective date semantics: NNI registration/renewal date — NOT incorporation/opening date (2-year validity, annual renewal). robots.txt: /business/ not restricted. Reuse terms: no prohibition on privacy page; no OGL grant; NNI Regulations PDF (306KB) retrieved but not parsed — manual review for data-use restrictions required before marking commercially cleared. NNI ≠ complete Nunavut business population (qualifying "Nunavut Businesses" only). Report: VR13_1_NNI_PROFILE.md
VR15.1 ⚠️ PARTIAL — Company Website Enrichment — 10 businesses probed. Domain found: 4/10 (all from known website field in VR06 — DDG Lite discovery returned 0 usable domains for the 6 no-website records). Domain reachable: 1/10 (RepologiX). Phones extracted: 1/10 (2 phones from /contact page). Emails: 0/10. Leadership signals: 0/10. Failure modes: DNS resolution failure on 2 VR06 domains (stale government-published fields), HTTP 403 on 1 (WAF), DDG Lite HTML parse yielded no usable results for any no-website record. Crawl logic and extraction confirmed functional on live site. Discovery mechanism is the bottleneck — alternative needed. Report: VR15_WEBSITE_ENRICHMENT.md
VR15.2 ⚠️ PARTIAL — Corporations Canada Director/ISC Enrichment — 10 federal corps tested. HTML route: 10/10 pages HTTP 200, director names extracted for 2 small corps (Mindangler: Nigel Stokes; Airmec: MARIO TESTA), ISC section heading detected for both. Large corps (Canadian Tire, Air Canada, Loblaws, Bombardier, Shoppers, Rogers): HTML 200 but zero director text — likely JS-rendered page or incorrect corp numbers. API route (/cc/api/corporations/XXXXXX): 404 on all 10 — unauthenticated access not available (VR04.1 API key still required). Extraction regex produces noise (boilerplate page text captured alongside real names — filtering needed). Report: VR15_CORPORATIONS_CONTACTS.md
VR14.1 ✅ ODBus Source Catalogue Extracted — 69 sources in ODBus_Sources.csv (cp1252 encoding). Province distribution: ON=32, BC=27, AB=5, NB=3, MB=1, NT=1. Zero coverage for SK, QC, NS, PE, NL, YT, NU — 7 of 13 provinces/territories absent from ODBus entirely. Source types: ~38 municipal business licence datasets, ~15 business directories, 13 Hamilton specialized licence categories, 3 BC provincial datasets. ODBus confirmed as source map for ON/BC/AB only — not Canada-wide backbone. Report: VR14_ODBUS_SOURCE_EXPANSION.md
VR14.2 ✅ ODBus Endpoint Triage — 69 URLs probed (HEAD + GET). Classification: CURRENT=56, DEAD=7, RESTRICTED=3, MOVED=2, UNKNOWN=1. Dead: Banff (timeout), Strathcona County (timeout), BC Licensed Establishments (404 — URL-rotted), BC Wineries (404 — URL-rotted), Nanaimo (404), Yellowknife (404), Guelph (SSL failure). Restricted: Chilliwack (403), Mississauga 2019 directory (403), Toronto (WAF — not a prohibition). Moved: Delta BC (same domain, new path), Surrey BC (migrated to ArcGIS Hub). Key live sources confirmed: Calgary, Edmonton, Vancouver, Winnipeg (all Socrata, current date evidence), New Westminster (has dedicated "New this Year" file), Victoria Current Year, BC Indigenous Business Listings (783KB direct CSV, OGL-BC, current). "Login detected" flag on Socrata portals = false positive — portals are publicly accessible. Full triage: VR14_2_ODBUS_ENDPOINT_TRIAGE.json + VR14_2_ODBUS_ENDPOINT_TRIAGE.md
VR14.4.1 ✅ Vancouver numberofemployees RESOLVED — source documentation confirms "Number of staff employed with the business". 0=applicant reported no employees (legitimate, not missing). 206,024 rows 100% populated. Bucket distribution: 1-4=82197, 5-9=20993, 10-19=13451, 20-49=8808, 50-99=3216, 100-199=1868, 200-499=1089, 500-999=367, 1000+=200. Grain=licence_record, company_level_semantics=documented, usable=YES. 17.7% of business names have multiple employee values — normal for multi-licence businesses, not contradictory. Pipeline must preserve licence-grain and resolve at entity layer. Dataset updated daily. VR14 CLOSED. Report: VR14_4_1_VANCOUVER_EMPLOYEES.json+md — Calgary (23,178 rows, name+address+status+licence_id+first_iss_dt all 100%, date range 2001→2026/09/21, no postal/phone/email/NAICS), Edmonton (43,719 rows, name 100%, address 99.9%, original_issue_date 94.2% to 2025/12/31, no status field, no postal/phone/email/NAICS), Vancouver (206,024 rows updated 2026-10-01, name 93.4%, address/postal both 53.4-53.7%, status 100% with 5 values including Gone Out of Business, licence_id 100%, issueddate 86.1% to 2026-10-01, numberofemployees 100% filled as float-strings e.g. "385.0" — bucket distribution pending, no phone/email/NAICS), Winnipeg (13,757 rows including historical, name 100% but only 275 unique values suggesting licence-grain not business-grain, address 20.2% only, no postal/licence_id/NAICS, status 10 values, date range 2011→2025/12/31). ODBus direct row-count delta not computed (ODBus_Sources.csv not in data/raw). Freshness gain confirmed for all four sources vs ODBus 2022 snapshot. Report: VR14_ODBUS_SOURCE_EXPANSION.md + VR14_4_ODBUS_VS_CURRENT.json — Calgary (Socrata API, 18 cols, 2026 data confirmed — tradename/address/licencetypes/first_iss_dt/exp_dt/jobstatusdesc/coordinates; no postal/phone/email/NAICS). Edmonton (Socrata API, 22 cols, 2026 data confirmed — business_name/address/original_issue_date/most_recent_issue_date/licencetype/neighbourhood; URL migrated to /Urban-Planning-Economy/; no postal/phone/email/NAICS). Vancouver (OpenDataSoft, 206,024 rows updated 2026-09-25, BEST FIELD SET: businessname/postalcode/status/issueddate/numberofemployees/businesstype/businesssubtype/coordinates — employee count field present, only second source after NNI). Winnipeg (Socrata API, 13 cols, includes historical/closed records — trade_name/address/status/issue_date/expiry_date). New Westminster GeoJSON 403 (portal accessible, direct API blocked — browser download needed). Victoria GeoJSON 403 (same). BC Licensed Establishments + Wineries: CKAN datasets confirmed to exist (1 resource each) — current download URLs need manual catalogue check. Surrey/Kelowna portals confirmed live with 2026 content. Report: VR14_ODBUS_SOURCE_EXPANSION.md + VR14_3_ODBUS_HIGH_VALUE_SOURCES.json
       ↓
PHASE 3 — DATA PROFILING
       ↓
PHASE 4 — ARCHITECTURE
       ↓
PHASE 5 — KIRO IMPLEMENTATION
```

---

## Source Class Definitions

### Class A — Master Business Datasets
Large discovery-layer datasets. Used to build the initial business master.

Examples: ODBus, Federal Corporations, provincial registries, municipal business licence datasets.

### Class B — Fresh / Change Datasets
Sources that specifically surface new, changed, or recently active businesses.
Critical for the assignment requirement: "find newly created / newly opened businesses."
If we can identify incremental changes, we avoid re-crawling the entire country daily.

Examples: monthly corporate transactions, new business licence feeds, new permit datasets, status-change feeds.

### Class C — Enrichment Datasets
Sources that add fields to a business we already know about.
Phone, email, website, employee count, address, licences, industry detail.

Examples: business websites, some government licence datasets that include contact info.

### Class D — Validation / Benchmark Datasets
Aggregate data only — no individual business records.
Used to check whether our pipeline is missing large market segments.

Examples: Statistics Canada Business Counts, Statistics Canada provincial/industry counts, Alberta Businesses by Municipality.

---

## Known Assets — Do Not Lose These

These have already been identified and partially researched. Each needs a full validation pass.

---

### ASSET-01 — Statistics Canada ODBus (Open Database of Businesses)

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset |
| URL | https://www150.statcan.gc.ca/n1/pub/71-627-x/71-627-x2018001-eng.htm |
| Coverage | Canada (partial — ON, BC, AB, NT, NU, NB confirmed; other provinces absent from v1) |
| Individual businesses | Yes |
| Record count | 446,575 |
| Freshness | Historical — data collected ~2022, published as v1 |
| API | No |
| Bulk download | Yes — ZIP |
| Employee data | Yes — but messy (exact counts + ranges + `..` + `NOT AVAILABLE`) |
| Address | Yes — full address, postal code, city, province |
| Status | Yes — Active / Pending / Not Active / `..` |
| Registration date | No |
| Website / Phone / Email | No |
| Licence | Open Government Licence — Canada |
| Cost | Free |
| Automation | Bulk download permitted |
| Role | Class A discovery / historical base layer |

**Key findings already measured:**
- 32 columns, utf-8-sig encoding
- Province distribution heavily skewed: ON 205k, BC 163k, AB 76k — several provinces missing
- 393,603 rows involved in duplicate `business_id_no` — record grain unclear (may be licences not unique businesses)
- `total_no_employees` uses inconsistent formats across providers — normalization required
- Status: 284k rows are `..` (unknown)
- No website, phone, or email fields anywhere in the 32 columns
- Source is a harmonization of 69 municipal/regional/provincial open datasets
- Providers are municipal/city governments — the underlying open datasets are a clue for where to find more sources

**Open questions:**
- What exactly does one row represent? (business, licence, establishment?)
- Is `business_id_no` globally unique or only within a provider?
- What is the exact reference period?
- Commercial-use status — confirmed free but commercial use needs verification
- Will a v2 be released?

**Scripts already written:**
- `scripts/inspect_odbus.py` → `reports/ODBUS_INSPECTION_REPORT.md`
- `scripts/inspect_odbus_metadata.py` → `reports/ODBUS_METADATA_INSPECTION.md`

---

### ASSET-02 — Corporations Canada (Federal)

> **VR01 update (2026-09-25):** VALIDATED. Downloaded and profiled active business corporations CSV.
> 645,005 active CBCA records. Dataset URL structure changed — old open.canada.ca ID is dead.
> See: `reports/validation_rounds/VR01_CORPORATIONS_CANADA.md`

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset + B — Fresh/Change Dataset |
| Open data URL | https://open.canada.ca/data/en/dataset/0032ce54-c5dd-4b66-99a0-320a7b5e99f2 |
| Data services page | https://ised-isde.canada.ca/site/corporations-canada/en/data-services |
| Coverage | Federal CBCA corporations only — does NOT include provincial/territorial corps, sole props, or partnerships |
| Individual businesses | Yes |
| Freshness | **Typically updated daily** |
| Dataset splits | 4 CSVs — active CBCA / other active / inactive CBCA / other inactive |
| Bulk download | ✅ YES — direct CSV download, no auth required |
| Employee data | ❌ NOT PRESENT — confirmed by profiling |
| Address | ✅ Street, Street 2, City/town, Province/territory, Country, Postal code |
| Status | ✅ `Active` (single value in active CSV — all 645,005 rows) |
| Status Detail | ✅ Present but 95.73% blank — used for edge cases (e.g. "Active - Dissolution Pending") |
| Corporation Number | ✅ Present — 0% missing — primary stable federal ID |
| Business Number (BN) | ✅ Present — 0.24% missing — CRA cross-source matching key |
| Corporate name form 1 | ✅ Present — 0% missing |
| Corporate name form 2 | ⚠️ 95.58% blank — rarely used |
| Anniversary date | ✅ Present — 0% missing — annual return anniversary |
| Year of last annual filing | ⚠️ 23.88% missing |
| Date of last annual meeting | ⚠️ 34.26% missing |
| Min/max directors | ✅ Present — 0.00% missing |
| Website / Phone / Email | ❌ NOT PRESENT — confirmed |
| NAICS / Industry | ❌ NOT PRESENT — confirmed |
| Directors (names) | ❌ NOT in bulk CSV — available via API only |
| ISC (ownership) | ❌ NOT in bulk CSV — available via API only |
| Licence | Open Government Licence — Canada (commercial use permitted) |
| Cost | Free |
| Automation | Bulk CSV download permitted |
| Role | Class A federal identity layer + Class B change detection |

**Measured dataset sizes (all 4 splits):**

| Dataset | File size | Rows (estimated from size) |
| --- | --- | --- |
| Active business corps (CBCA) | 98.8 MB | **645,005** (confirmed) |
| Other active corps (non-CBCA) | 8.8 MB | ~57k estimated |
| Inactive business corps (CBCA) | 150.1 MB | ~1M+ estimated |
| Other inactive corps (non-CBCA) | 8.1 MB | ~50k estimated |

**Key findings from profiling:**
- Province/territory field present but the profiler did not capture distribution — needs a follow-up run targeting that column specifically
- `Status Detail` is nearly always blank for active corps but encodes edge cases like dissolution-pending
- `Corporate name - form 2` is almost always blank — alternative name rarely used
- Director min/max are integers, not names — actual director names require API calls
- Anniversary date ≠ incorporation date — do not conflate these

**Confirmed gaps (bulk CSV):**
- No employee count
- No NAICS/industry
- No phone, email, website
- No director names (API only)
- No ISC (API only)
- No incorporation date directly — requires API `activities[]` endpoint

**Open questions (post-profiling):**
- [ ] Province/territory distribution — run targeted profiling pass
- [ ] Full inactive corps count — profile the inactive CBCA CSV
- [ ] Monthly transactions dataset — profile transaction types for new-business detection
- [ ] API: confirm ISC is accessible programmatically (not just web UI)
- [ ] Overlap with ODBus — sample-match by name + postal code
- [ ] What % of all Canadian businesses are federal CBCA corps?

**Validation status:** ✅ VALIDATED (active business corporations CSV)
**Partial validation pending:** inactive corps, other active/inactive, API, monthly transactions

---

### ASSET-03 — BC OrgBook

> **RR03 update:** Major correction — bulk download/scraping is explicitly prohibited by ToS.
> Role corrected to: targeted identity verification only.
> Address, directors, ownership also confirmed NOT available.
> See full details: `research_rounds/RR03_BC_ORGBOOK.md`

| Attribute | Value |
| --- | --- |
| Class | C — Targeted Verification / Enrichment (NOT bulk discovery) |
| URL | https://orgbook.gov.bc.ca |
| API URL | https://orgbook.gov.bc.ca/api/v4/ |
| Coverage | British Columbia — all entity types (corps, sole proprietors, etc.) |
| Individual businesses | Yes — active AND historical |
| Freshness | ~30 minutes after BC Registry changes |
| API | Yes — v4, no auth required for read |
| Bulk download | ❌ PROHIBITED — explicitly against ToS |
| Full DB scraping | ❌ PROHIBITED — 10-page limit enforced specifically to prevent it |
| Legal names | ✅ |
| DBA / assumed / translated names | ✅ |
| BC Registries ID | ✅ |
| CRA Business Number | Sometimes |
| Entity type | ✅ (Corp, SP, etc.) |
| Registration status | ✅ |
| Registration date + timeline | ✅ — credential history, effective/revoked dates |
| Selected licences/permits | ✅ — from authorized issuers |
| Address | ❌ — legislatively restricted, cannot be displayed |
| Phone / Email / Website | ❌ |
| Directors | ❌ — deliberately excluded |
| Ownership / beneficial owner | ❌ — deliberately excluded |
| Employee data | ❌ |
| NAICS | ❌ |
| Terms | BC Government Terms / Access Only Data Terms — NOT OGL |
| Cost | Free |
| Role | Class C — targeted verification/enrichment for known BC candidates |

**Correct usage pattern:**
```
Candidate from another source → query OrgBook by name/BN/Registry ID
→ verify legal name, DBA, status, registration timeline, licences
```

**Do NOT use for:** bulk BC business enumeration, contact discovery, director lookup.

**Next actions:**
- [ ] Test API v4 — validate actual response fields
- [ ] Check `/v4/credential-type` — what licence types exist (may eliminate redundant BC source research)
- [ ] Verify commercial pipeline use under BC Government Terms
- [ ] Check whether a change/notification feed exists for production use

**Status (RR03):** Research complete. Previous assumptions corrected. API testing pending.

---

### ASSET-04 — Statistics Canada Business Datasets

> **RR04 update:** Confirmed as Class D validation/benchmark only. Three separate tables identified.
> Critical finding: Statistics Canada "opening" ≠ Corporations Canada "incorporation" — different events.
> CSV download + profiling still needed to confirm exact employment-size label mapping.
> See full details: `research_rounds/RR04_STATSCAN_BUSINESS_COUNTS.md`

#### ASSET-04a — Canadian Business Counts, with employees (Table 33-10-1174-01)

| Attribute | Value |
| --- | --- |
| Class | D — Validation / Benchmark |
| Table | 33-10-1174-01 |
| Current release | June 2026 (released August 14, 2026) |
| Frequency | Semi-annual |
| Geography | Canada + provinces/territories |
| NAICS | Yes — 1,362 unique values |
| Employee-size breakdown | Yes — 8 labels, 7/9 required buckets mappable |
| Employee-size limitation | `500 plus employees` is a combined label — covers 500–999 AND 1000+ together. No current StatsCan Business Counts table separates these. |
| Individual businesses | No — aggregate counts only |
| Licence | OGL – Canada |
| Format | CSV, XML |
| Cost | Free |
| Role | Class D — benchmark pipeline coverage by province × NAICS × employee size |

> **VR05 update (2026-09-25):** VALIDATED. 85,793 rows, 0 suppressed values, all 14 geographies present.
> Employment-size `500 plus employees` confirmed as a combined 500–999+1000+ label.
> No alternative StatsCan table found that separates these two buckets at the Canada/province/NAICS level.
> Pipeline must source the `500–999` / `1000+` split from individual-business enrichment, not StatsCan.
> See: `reports/validation_rounds/VR05_STATSCAN_BUSINESS_COUNTS.md`

#### ASSET-04b — Canadian Business Counts, with employees, CMA/CSD (Table 33-10-1176-01)

| Attribute | Value |
| --- | --- |
| Class | D — Validation / Benchmark |
| Geography | Census Metropolitan Areas + Census Subdivisions (city level) |
| Role | Class D — city/municipality-level coverage validation |

#### ASSET-04c — Canadian Business Counts, without employees (Table 33-10-1175-01)

| Attribute | Value |
| --- | --- |
| Class | D — Validation / Benchmark |
| Purpose | Distinguishes businesses-with-employees vs businesses-without-employees |
| Key finding | Reinforces: missing employee count ≠ zero employees |

#### ASSET-04d — Monthly Business Openings and Closures (Table 33-10-0722-01)

| Attribute | Value |
| --- | --- |
| Class | D — Validation / Benchmark |
| Frequency | Monthly |
| History | January 2015 – May 2026 (137 periods) |
| Geography | Canada / provinces / territories / CMAs (49 geographies) |
| NAICS | 2-digit |
| Employee size | Yes — coarser buckets (1-4, 5-19, 20-99, 100-499, 500+) |
| Business dynamics categories | 8: Active, Opening, Continuing, Closing, Reopening, Entrants, Temporary closures, Exits |
| Best new-business benchmark | `Entrants` — no prior employment activity on record; more precise than `Opening businesses` which includes reactivations |
| Suppression | 91.4% of rows suppressed (`x`) at CMA level; provincial/national level far lower |
| Status | **Experimental estimates** — subject to revision each month |
| Individual businesses | No — aggregate counts only |
| Licence | OGL – Canada |
| Cost | Free |
| Role | Class D — benchmark for new-business/closure patterns |

> **VR05 update (2026-09-25):** VALIDATED. All 8 dynamics categories confirmed from data.
> `Entrants` confirmed as the most precise benchmark for genuinely new employer businesses.
> Employment buckets are coarser than Table A — cannot benchmark all 9 required size buckets.
> See: `reports/validation_rounds/VR05_STATSCAN_BUSINESS_COUNTS.md`

**Key definitions:**
- Opening: employees this month, not last month (includes reactivations)
- Closure: employees last month, not this month
- Reopening: opens again after prior closure — subset of Opening
- Entrant: opening with NO prior activity on record — genuinely new employer business

**CRITICAL DISTINCTION — preserve in architecture:**
```
Corporate registration (Corporations Canada)  ≠  Employment opening (Statistics Canada)
Licence registration (Ontario Select Licence) ≠  Employment opening (Statistics Canada)
```
These are different lifecycle events that can happen months apart for the same business.
The system must distinguish them — do not collapse into a single `new_business = true` flag.

**Next actions:**
- [ ] Download June 2026 Business Counts CSVs → `data/raw/` → profile exact employment-size labels, NAICS levels, geography values, suppression markers
- [ ] Write `scripts/inspect_statscan_business_counts.py`
- [ ] Confirm employment-size label mapping against our 9 required buckets
- [ ] Download Monthly Openings/Closures → inspect dimensions

**Status (RR04):** Research complete. Three lifecycle signal types identified. CSV profiling pending.

---

### ASSET-05 — Alberta Businesses by Municipality

| Attribute | Value |
| --- | --- |
| Class | D — Validation / Benchmark |
| URL | https://open.alberta.ca/opendata/businesses-by-municipality |
| Coverage | Alberta |
| Individual businesses | No — counts by municipality |
| Breakdown | Municipality + year + employee size + industry |
| Formats | CSV, JSON, XLSX, XML |
| Freshness | ? — needs validation |
| Cost | Free |
| Role | Class D validation for Alberta geographic/industry coverage |

**How to use this:**
- Validate Alberta pipeline coverage by municipality and industry
- Cross-check employee-size distribution for AB businesses in our pipeline

**Open questions:**
- What years are covered?
- What industry classification is used? (NAICS?)
- What employee-size bands are used?
- How current is the latest release?

**Status:** NOT YET DOWNLOADED — lower priority (Class D only)

---

### ASSET-06 — Quebec Enterprise Registry (REQ)

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset (QC) |
| URL | https://www.registreentreprises.gouv.qc.ca |
| Coverage | Quebec |
| Individual businesses | Yes |
| Fields | NEQ, enterprise name, registration date, status, legal form, economic activity, employee info, establishments, addresses, other names |
| Freshness | ? |
| Bulk download | Yes — downloadable dataset exists |
| Licence | **Non-commercial use restriction — FLAGGED** |
| Cost | Free for non-commercial |
| Role | Class A — BLOCKED until licence resolved |

**IMPORTANT — Do not ingest until resolved:**
The downloadable dataset has a non-commercial-use restriction.
This is a commercial telecom prospecting system.
Do not make this a production dependency until commercial-use permission is confirmed.

**Open questions:**
- Can commercial use be licensed?
- Is there a commercial API alternative?
- What is the exact restriction wording?
- Are there Quebec municipal open datasets that can be used instead?

**Status:** BLOCKED — licence review required before any use

---

### ASSET-07 — Ontario Open Data Ecosystem

> **RR02 update:** Ontario does NOT have a free general-purpose bulk business registry.
> Ontario strategy is: mine the ecosystem of specialized datasets collectively.
> See full details: `research_rounds/RR02_ONTARIO.md`

#### ASSET-07a — Ontario Select Licence and Registration Data ✅ VALIDATED

| Attribute | Value |
| --- | --- |
| Class | A (specialized — regulated licence types) + C (contact enrichment) |
| URL | https://data.ontario.ca/dataset/select-licence-and-registration-data |
| Coverage | Ontario — regulated licence types only (see validated list below) |
| Individual businesses | Yes — for covered licence types only |
| Record grain | 1 row = 1 licence, NOT 1 business |
| Freshness | Monthly — August 2026 current as of Sep 11 2026 |
| API | Yes — CKAN Data API |
| Bulk download | Yes — CSV, TSV, JSON, XML |
| Legal name | ✅ |
| Operating / DBA name | ✅ |
| Address + postal code | ✅ |
| Phone | ✅ (99% valid format after treating "N/A" as missing) |
| Email | ✅ (81% valid format) |
| Website | ⚠️ (10% valid format — most cells contain "N/A") |
| Licence status + expiry | ✅ |
| Incorporation date | ❌ |
| Employee count | ❌ |
| NAICS | ❌ (licence type only) |
| Licence | OGL – Ontario |
| Cost | Free |
| Automation | Yes — CKAN CSV, no auth |
| Role | Class A specialized + Class C contact enrichment |

**Validated licence-type snapshot (August 2026):**
Current snapshot contains 5 observed categories: Payday Lender (64.1%), Collection Agency (19.0%), Bailiff (Business) (11.3%), Consumer Reporting Agency (5.0%), Loan Broker (0.1%). Previously documented list was incomplete/outdated. List is not exhaustive — categories may change over time.

**Out-of-province records:** 12/674 records have non-Ontario addresses. Do not hard-filter on province before retaining source provenance.

**IMPORTANT:** new licence record ≠ new business. 674 licence records ≠ 674 unique businesses (345 unique legal names). A business may have held a licence for years.

#### ASSET-07b — Ontario Select Licence — Individual Dataset ✅ CONFIRMED USEFUL

Separate dataset linking licensed individuals to their employing business.
Fields: first/last name, employer legal name, employer operating name, workplace address/city/province/postal/phone/email/website, licence type, licence number, expiry date.
Person → Business link is explicitly represented by the government dataset (stronger than website inference).
Limited to: Bailiff (Owner/Employee/Assistant), Personal Information Investigator.

#### ASSET-07c — Ontario Business Registry General Bulk Export ❌ NOT FOUND

No free general-purpose bulk export of all Ontario registered businesses found in current Ontario Data Catalogue.
Ontario Business Registry Partner Portal dataset is NOT the registry — it is a list of authorized intermediary organizations only.

#### ASSET-07d — Ontario Environment Business Directory ⚠️ STALE

Contains 900+ Ontario environmental companies (name, sector, website, contact, location, description).
**Not updated since 2019. Catalogue explicitly marks historical reference only.**
Do not use as a current production source.

#### ASSET-07e — Ontario Specialized Catalogue Datasets (To Be Systematically Mined)

Ontario catalogue contains many other individual-business datasets worth investigating:
- Community Small Business Investment Funds (has name, address, contact, **registration date**)
- Labour Sponsored Investment Funds
- Tobacco tax registrant lists
- Fuel/gasoline tax registrant lists
- Dairy distributors
- Licensed contractors
- Regulated industry directories

**Next action:** Systematically inventory all Ontario catalogue datasets that contain individual business records.

**Status (RR02):** Select Licence confirmed. General registry not found. Ecosystem mining needed.

---

### ASSET-08 — Nova Scotia

> **RR05 update:** RJSC is the primary target — much stronger than open-data catalogue suggested.
> Broad entity coverage (sole props, partnerships, companies, societies, co-ops).
> Key gap: bulk/API access unverified — do not automate until technical inspection done.
> See full details: `research_rounds/RR05_NOVA_SCOTIA.md`

#### ASSET-08a — Nova Scotia Registry of Joint Stock Companies (RJSC) ⭐ STRONG CANDIDATE

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset (NS) + B — Change/Registration signal |
| URL | https://rjsc.novascotia.ca (search) |
| Coverage | Nova Scotia — most registered businesses required by law |
| Entity types | Sole prop, partnership, company, society, co-op, business name |
| Individual businesses | Yes |
| Freshness | Live registry |
| Registry ID | Yes — 7-digit |
| CRA BN | Potentially — linkage documented, not confirmed in public search results |
| Legal name + operating name | Yes |
| Status | Yes |
| Registration date | Yes |
| Address | Yes |
| Directors / officers / partners | Yes — legally filed roles |
| Activity history | Yes — filings, amendments, dissolution events |
| Nature of business | Potentially — coverage/format/NAICS mapping unverified |
| Phone / email / website | ❓ — not documented as standard registry fields |
| Employee count / NAICS | ❌ |
| Bulk download | ❓ UNKNOWN — not found in documentation |
| Public API | ❓ UNKNOWN — not found in documentation |
| Automation permission | ❓ UNVERIFIED |
| Basic public search | Free |
| Document retrieval | Paid ($12.45–$24.95) |
| Role | Strong provincial candidate — targeted lookup confirmed; enumeration not yet approved |

**Status (VR10):** ⚠️ DEFERRED — WAF/bot-protection layer blocks all automated HTTP access before application layer is reached. Official government documentation confirms legal name, operating name, address, registration date, status, entity type, directors/officers/partners and activity history are all publicly available. Machine-readable API and automation permission unvalidated. Browser DevTools inspection required next — do not attempt WAF bypass or bulk enumeration.

#### ASSET-08b — Nova Scotia Open Data Portal (Specialized Datasets)

| Attribute | Value |
| --- | --- |
| Class | A (specialized) |
| URL | https://data.novascotia.ca |
| Coverage | Nova Scotia — specialized/regulated categories only |
| General business bulk export | ❌ Not found |
| Licensed Food Establishments | Exists but currently returning error/private state — not validated |
| Other specialized datasets | Tourism, accommodation, regulated industries |
| Role | Secondary — mine after RJSC is validated |

**Status (RR05):** RJSC identified as primary NS source. Bulk/API access pending technical inspection.

---

### ASSET-09 — Municipal Open Data Portals (ODBus Sources)

ODBus was assembled from 69 contributing datasets across these providers (confirmed in `ODBus_Sources.csv`):

**Alberta:** Banff, Calgary, Chestermere, Edmonton, Strathcona County
**BC:** Burnaby, Chilliwack, Delta, Kelowna, Langley, Maple Ridge, Nanaimo, New Westminster (×6), Port Moody (×2), Prince George, Squamish, Surrey, Township of Langley, Vancouver (×2), Victoria (×3), BC Indigenous Business Listings, Licensed Establishments BC, BC Winery Locations
**Manitoba:** Winnipeg
**NB:** Moncton (Grocery stores, Pharmacies), Saint John (Grocery Stores)
**NT:** Yellowknife
**ON:** Ajax, Brampton, Caledon, Cambridge, Durham Region (×3), Guelph, Hamilton (×12 datasets), Kitchener/Waterloo, Mississauga, Ottawa (×2), Peel (×2), Ontario Environment Business Directory, Select Licence and Registration Data

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset (municipal level) |
| Coverage | Selected municipalities across AB, BC, MB, NB, NT, ON |
| Individual businesses | Yes |
| Freshness | Varies — some have been updated since ODBus compiled them |
| Bulk download | Generally yes via open data portals |
| Cost | Free (Open Government Licence variants) |
| Role | Class A discovery — especially for provinces where provincial registry is inaccessible |

**Important insight:**
ODBus is the compiled result of these sources. But ODBus v1 was compiled in 2022.
The original sources may have been updated since then.
Going directly to the source portals may give us fresher data.

**Open questions:**
- Which municipal portals have been updated since ODBus v1 was compiled?
- Are there additional municipal portals not included in ODBus?
- Do any municipal portals now include phone, email, or website?
- Which portals support API access?

**Status:** Individual portals not yet investigated — use ODBus source list as starting inventory

---

### ASSET-10 — New Brunswick Corporate Registry

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset (NB) — RESTRICTED |
| Coverage | New Brunswick |
| Individual businesses | Yes |
| Automation restriction | **Automated copying of groups of search results is restricted** |
| Cost | ? |
| Role | BLOCKED — do not build bulk scraper |

**Decision:** Do not build a Playwright/Selenium bulk scraper.
Only proceed if an explicitly permitted automated acquisition method is established.

---

### ASSET-11 — Saskatchewan

> **RR06 update:** Provincial registry is paid — not a zero-cost bulk foundation.
> Key free source is Saskatoon municipal business licence open data including a new-businesses list.
> See full details: `research_rounds/RR06_SASKATCHEWAN_MANITOBA.md`

#### ASSET-11a — Saskatchewan Corporate Registry (ISC)

| Attribute | Value |
| --- | --- |
| Class | C — Targeted verification only (paid bulk) |
| Coverage | Saskatchewan — all entity types |
| Individual businesses | Yes |
| Registry fields | Name, status, address, directors potentially |
| Bulk download | ❌ Paid — starts at $200 minimum |
| Profile Report | $10 per company |
| Free bulk | ❌ |
| API | Not found |
| Automation | Paid service — misuse = account suspension |
| Role | Verification only if needed — NOT a zero-cost discovery foundation |

#### ASSET-11b — City of Saskatoon Business Licences ✅ VALIDATED

| Attribute | Value |
| --- | --- |
| Class | A — Municipal discovery + B — New-business/licensing signal |
| Coverage | Saskatoon — Commercial and Home-Based Business Licences only |
| Excludes | Non-Resident Business Licences and other licence types |
| Datasets | All businesses (Dec 31, 2025) + New businesses (Aug 31, 2026) |
| Platform | Direct XLSX from City website — old CKAN portal retired Aug 2024 |
| All-businesses rows | 7,472 |
| All-businesses key field | `Bus_Lic_Acct_Id` (97.5% present) |
| New-businesses rows | 51 |
| New-businesses key field | `Business_License_Id` (different grain/schema) |
| NAICS | ✅ Sub-sector level (all-biz) + National level (new-biz) |
| Address | ✅ Structured split fields — no single address column, no postal code |
| Business description | ✅ `Business_Desc` in new-businesses file |
| Phone / Email / Website | ❌ Not present in either file |
| Postal code | ❌ Not present |
| New-business signal | ✅ Municipal licence-issuance signal — NOT "newly incorporated" or "newly opened" |
| Cross-file linkage | ⚠️ Unresolved — 5.9% name match; different IDs + schemas; not evidence of different population |
| Blank columns | ⚠️ 17/27 columns blank in new-biz file — export template artefact; preserve in raw ingestion |
| Licence | City of Saskatoon Open Data — commercial use permitted |
| Automation | ✅ Direct XLSX download |
| Role | Class A municipal discovery + Class B new-business/licensing signal (no contact enrichment) |

> **VR07 update (2026-09-25):** VALIDATED. See: `reports/validation_rounds/VR07_SASKATOON_BUSINESS_LICENCES.md`

#### ASSET-11c — City of Regina Open Data

| Attribute | Value |
| --- | --- |
| Class | A — Candidate only |
| Coverage | Regina |
| Note | Business licence application mentions name/owner/phone/email/address but publication of records not confirmed |
| Status | Candidate — needs direct validation |

**Status (RR06):** Provincial registry = paid. Saskatoon licences = priority free source. Regina = unverified.

---

### ASSET-12 — Manitoba

> **RR06 update:** Provincial registry has free basic lookup but no bulk/API.
> Key free source is weekly Companies Office filing listings — a live change/new-registration feed through Sep 2026.
> See full details: `research_rounds/RR06_SASKATCHEWAN_MANITOBA.md`

#### ASSET-12a — Manitoba Companies Office

| Attribute | Value |
| --- | --- |
| Class | A — Targeted verification (free basic lookup) |
| Coverage | Manitoba — corps, business names, sole props, partnerships |
| Individual businesses | Yes |
| Registry fields | Name, registry number, reg date, status, officers/directors |
| Free basic lookup | ✅ Free |
| File Summary | $5 per company |
| Bulk download | ❌ Not found |
| API | Not found |
| Role | Class A targeted verification |

#### ASSET-12b — Manitoba Weekly Companies Office Filing Listings ⭐ CHANGE SIGNAL

| Attribute | Value |
| --- | --- |
| Class | B — New-registration / change signal |
| Coverage | Manitoba — weekly filings |
| Current as of | September 19, 2026 |
| Content | Recent Companies Office filings — new registrations + changes |
| Limitation | Not official transcript; excludes annual returns/renewals |
| Fields | To be verified by local inspection |
| API/RSS | Unknown — needs inspection |
| Automation | Unknown — needs inspection |
| Role | Class B change/new-registration discovery signal — NOT a complete registry |
| Status | ⭐ Priority local inspection needed |

**Status (RR06):** Registry = free lookup only, no bulk. Weekly filings = strong change-signal candidate pending inspection.

---

### ASSET-16 — Prince Edward Island (PEI OCBR)

> **RR07:** OCBR functional online registry. Verification source only — no bulk/API found.
> See `research_rounds/RR07_PEI_NL_YUKON.md`

| Attribute | Value |
| --- | --- |
| Class | C — Targeted verification |
| Coverage | PEI — corporations + business names |
| Entity fields | Name, type, status, address, business number |
| ISC/shareholder | Available through filings — not confirmed as bulk public |
| Bulk download | ❌ Not found |
| API | ❌ Not found |
| Free search | ✅ |
| Automation | ⚠️ Unverified |
| Role | Targeted verification — local inspection pending |

**Status (RR07):** Confirmed verification source. Tech inspection needed before any automation.

---

### ASSET-17 — Newfoundland & Labrador (CADO)

> **RR07:** Substantial registry (~50k incorporations, ~26k active). Major gap: NO business-name registry legislation.
> See `research_rounds/RR07_PEI_NL_YUKON.md`

| Attribute | Value |
| --- | --- |
| Class | C — Targeted verification |
| Coverage | NL — incorporated companies only (~26k active) |
| Coverage gap | ❌ NO business-name registry — unincorporated/trade-name businesses not covered |
| Entity fields | Name, status, registered office, directors, filings, annual returns |
| Bulk download | ❌ Not found |
| API | ❌ Not found |
| Free search | ✅ (some paid services) |
| Automation | ⚠️ Unverified |
| Role | Targeted verification for NL corporations only |
| NL Open Data | Specialized/stale datasets only — Mining Companies last modified 2015 |

**Status (RR07):** Verification source. Coverage gap documented. Tech inspection needed.

---

### ASSET-18 — Yukon

> **RR07:** YCOR covers corps/business names/societies. Supplier Directory open licence but freshness unverified.
> See `research_rounds/RR07_PEI_NL_YUKON.md`

#### ASSET-18a — Yukon Corporate Online Registry (YCOR)

| Attribute | Value |
| --- | --- |
| Class | C — Targeted verification |
| Coverage | Yukon — corps, partnerships, business names, societies |
| Entity fields | Name, type, status, address, registry number, directors |
| Bulk download | ❌ Not found |
| API | ❌ Not found |
| Free status search | ✅ |
| Paid entity profile | ✅ |
| Automation | ⚠️ Unverified |
| Role | Targeted verification — tech inspection pending |

#### ASSET-18b — Yukon Government Supplier Directory

| Attribute | Value |
| --- | --- |
| Class | C — Enrichment candidate |
| Coverage | Yukon government-registered suppliers |
| Fields | Business name, description, community, Yukon-business flag |
| Licence | Open Government Licence – Yukon |
| Freshness | Last updated 2022 (metadata) — annual update claimed in 2026 doc — NEEDS VALIDATION |
| Role | Enrichment if freshness confirmed; NOT general Yukon coverage |

#### ASSET-18c — Yukon Business Statistics

| Attribute | Value |
| --- | --- |
| Class | D — Validation/benchmark |
| Coverage | Yukon — aggregate by community |
| Updated | May 20, 2026 |
| Role | Benchmark — not individual leads |

**Status (RR07):** YCOR = verification only. Supplier Directory = freshness unverified. Statistics = benchmark confirmed.

---

### ASSET-19 — Northwest Territories

> **RR08:** CROS is verification-only. BIP Registry is an interesting discovery candidate. 76-dataset open data portal worth mining.
> See `research_rounds/RR08_NWT_NUNAVUT.md`

#### ASSET-19a — NWT Corporate Registries (CROS)

| Attribute | Value |
| --- | --- |
| Class | C — Targeted verification |
| Coverage | NWT — corps, extra-territorial corps, sole props, partnerships, business names, societies, co-ops |
| Key fields | Legal name, status, entity type (free); full profile = paid |
| Bulk / API | ❌ Not found |
| Free basic | ✅ |
| Role | Targeted verification — NOT free bulk foundation |

#### ASSET-19b — NWT BIP Registry ⭐ Discovery Candidate

| Attribute | Value |
| --- | --- |
| Class | A candidate — needs tech inspection |
| Coverage | NWT BIP-eligible businesses (corps + operating names) |
| Fields | Business name, region, community, category |
| Interface | Web search only — no documented bulk API |
| Role | Discovery/enrichment candidate — tech inspection needed |

#### ASSET-19c — NWT Open Data (76 datasets)

| Attribute | Value |
| --- | --- |
| Class | A specialized + D benchmark |
| Coverage | NWT — specialized industry/business datasets |
| Role | Systematic mining needed |

**Status (RR08):** Confirmed. Tech inspections pending.

---

### ASSET-20 — Nunavut

> **RR08:** Corporate registry technically inaccessible. NNI Registry is high-value candidate with strong field coverage. Municipal licensing layer important.
> See `research_rounds/RR08_NWT_NUNAVUT.md`

#### ASSET-20a — Nunavut NNI Business Registry ⭐ HIGH-VALUE CANDIDATE

| Attribute | Value |
| --- | --- |
| Class | A/C candidate — public exposure needs verification |
| Coverage | Nunavut NNI-qualifying businesses |
| Fields collected (application) | Legal name, operating name, manager name, address, phone, email, business type, community |
| Public field exposure | ❓ UNVERIFIED — application form confirms collection, not public exposure |
| Renewal | Every 2 years |
| Cost | Free |
| Role | High-value enrichment candidate if fields are publicly exposed |

#### ASSET-20b — Nunavut Corporate Registry

| Attribute | Value |
| --- | --- |
| Status | Technically inaccessible — no public search API found |
| Role | Not currently usable for automation |

#### ASSET-20c — Nunavut Business Licensing

| Attribute | Value |
| --- | --- |
| Coverage | Nunavut-wide businesses + regulated categories |
| Municipal layer | Separate — businesses in municipalities licence with municipality |
| Annual renewal | ✅ |
| Bulk dataset | ❌ Not found |
| Role | Change-signal candidate if dataset ever published |

**Status (RR08):** NNI Registry = priority verification. Corporate registry = inaccessible. Licensing = no bulk dataset found.

---

### ASSET-13 — Alberta Corporate Registry

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset (AB) |
| Coverage | Alberta |
| Individual businesses | Yes |
| Bulk download | Restricted — involves fees |
| Automation restriction | Registry searches involve fees and restrictions |
| Role | Do NOT treat as zero-cost foundation |

**Decision:** Alberta open datasets (ASSET-05) can provide aggregate/benchmark context.
Alberta Corporate Registry should not be a mandatory dependency in the zero-cost architecture.

---

### ASSET-14 — BC Business Registry API

| Attribute | Value |
| --- | --- |
| Class | A — Master Business Dataset (BC) |
| Coverage | British Columbia |
| Individual businesses | Yes |
| API | Yes — but requires account and involves fees |
| Cost | Paid |
| Role | Not suitable as zero-cost foundation — use BC OrgBook (ASSET-03) instead |

---

### ASSET-15 — Business Websites (Tier 2 Enrichment)

| Attribute | Value |
| --- | --- |
| Class | C — Enrichment |
| Coverage | Any business with a public website |
| Individual businesses | Yes |
| Freshness | Current |
| Fields | Phone, email, address, team/leadership, about, locations |
| Extraction method | Deterministic first (mailto:, tel:, JSON-LD, Schema.org, visible text), LLM fallback |
| Cost | Infrastructure only |
| Automation | Must respect robots.txt, rate limits, terms |
| Role | Class C enrichment — phone, email, decision-makers |

**Pages to target per business:**
- `/` (homepage)
- `/contact`
- `/about`
- `/team`
- `/leadership`
- `/management`
- `/locations`

**Extraction priority:**
1. `mailto:` links
2. `tel:` links
3. JSON-LD structured data
4. Schema.org Organization / LocalBusiness
5. Visible address / telephone / email patterns
6. Social links
7. Meta tags
8. LLM extraction (last resort)

---

## Source Discovery Matrix

Fill this in as each source is validated. `?` = not yet verified.

| # | Source | Coverage | Individual records | Freshness | API | Bulk DL | Employees | Address | Status | Reg. date | Website/Phone/Email | Licence | Cost | Automation | Class | Role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | ODBus | Canada (partial) | ✅ | Old (~2022) | ❌ | ✅ | Partial/messy | ✅ | Partial | ❌ | ❌ | OGL-Canada | Free | ✅ | A | Discovery base |
| 02 | Corporations Canada | Federal only | ✅ | Daily (Apr 2026) | ✅ 60/min | ✅ | ❌ | ✅ | ✅ | ✅ Corp#/BN/dates | ❌ | OGL-Canada | Free | ✅ bulk; API needs terms check | A+B | Discovery + change detection + directors + ISC |
| 03 | BC OrgBook | BC | ✅ | ~30 min | ✅ no auth | ❌ PROHIBITED | ❌ | ❌ legislated | ✅ | ✅ timeline | ❌ | BC Gov Terms (not OGL) | Free | Targeted only; bulk prohibited | C | Targeted verification only |
| 04a | StatsCan Business Counts (w/ employees) | Canada | ❌ aggregate | Semi-annual | ❌ | ✅ CSV | ✅ bands | ❌ | ❌ | ❌ | ❌ | OGL-Canada | Free | ✅ | D | Benchmark: province×NAICS×size |
| 04b | StatsCan Business Counts (CMA/CSD) | Canada | ❌ aggregate | Semi-annual | ❌ | ✅ CSV | ✅ bands | ❌ | ❌ | ❌ | ❌ | OGL-Canada | Free | ✅ | D | City-level benchmark |
| 04c | StatsCan Openings/Closures (monthly) | Canada | ❌ aggregate | Monthly | ❌ | ✅ CSV | ✅ bands | ❌ | ❌ | ❌ | ❌ | OGL-Canada | Free | ✅ | D | New-biz dynamics benchmark |
| 05 | AB Businesses by Municipality | Alberta | ❌ (aggregate) | ? | ? | ✅ | ✅ (bands) | ❌ | ❌ | ❌ | ❌ | ? | Free | ✅ | D | AB validation |
| 06 | Quebec REQ | Quebec | ✅ | ? | ? | ✅ | Partial | ✅ | ✅ | ✅ | ? | Non-commercial | Free | ? | A | BLOCKED |
| 07 | Ontario Select Licence & Registration | Ontario (6 licence types) | ✅ | Monthly (Aug 2026) | ✅ CKAN | ✅ | ❌ | ✅ | ✅ | ✅ phone/email/web | OGL-Ontario | Free | ✅ | A+C | Specialized licence discovery + contact enrichment |
| 08a | Nova Scotia RJSC | NS | ✅ | Live registry | ❓ unknown | ❓ unknown | ❌ | ✅ | ✅ reg date | ❌ phone/email/web ❓ | ? | Free (basic) | ❓ unverified | A+B | Strong candidate — automation pending tech inspection |
| 08b | Nova Scotia Open Data Portal | NS | ✅ vertical only | ? | ? | Some | ? | ? | ? | ? | ? | Free | ? | A | Specialized datasets — secondary to RJSC |
| 09 | Municipal portals (ODBus sources) | Selected cities | ✅ | Varies | Some | ✅ | Some | ✅ | Some | Some | Some | OGL variants | Free | Varies | A | Discovery |
| 10 | NB Corporate Registry | NB | ✅ | ? | ? | ❌ (restricted) | ? | ? | ? | ? | ? | ? | ? | ❌ | A | BLOCKED |
| 11a | SK Corporate Registry (ISC) | SK | ✅ | ? | ❌ | ❌ paid $200+ | ? | ✅ | ✅ | ❌ | ? | Paid | $10/record bulk $200+ | Paid only | C | Verification only — NOT zero-cost discovery |
| 11b | Saskatoon Business Licences | Saskatoon | ✅ | Current (Aug 2026) | ❌ | ✅ | ? | ✅ | ✅ licence date | ❓ | Open Data | Free | ✅ | A+B | Municipal discovery + new-biz signal |
| 11c | Regina Open Data | Regina | ✅ | ? | ? | ? | ? | ? | ? | ❓ | ? | Free | ? | A | Candidate — unverified |
| 12a | MB Companies Office | MB | ✅ | Live | ❌ | ❌ not found | ? | ✅ | ✅ | ❌ | ? | Free basic / $5 detail | Targeted only | A | Targeted verification |
| 12b | MB Weekly Filing Listings | MB | ✅ | Weekly (Sep 2026) | ❓ | ❓ | ❌ | ✅ | ✅ | ❌ | ? | Free | ❓ | B | New-registration / change signal |
| 12a | MB Companies Office | MB | ✅ | Live | ❌ | ❌ not found | ? | ✅ | ✅ | ❌ | ? | Free basic / $5 detail | Targeted only | A | Targeted verification |
| 12b | MB Weekly Filing Listings | MB | ✅ | Weekly (Sep 2026) | ❓ | ❓ | ❌ | ✅ | ✅ | ❌ | ? | Free | ❓ | B | New-registration / change signal |
| 13 | AB Corporate Registry | AB | ✅ | ? | ? | ? | ? | ? | ? | ? | ? | ? | Fees | ❌ | A | BLOCKED (cost) |
| 14 | BC Business Registry API | BC | ✅ | Current | ✅ | ? | ? | ✅ | ✅ | ✅ | ? | ? | Paid | ? | A | Not for zero-cost arch |
| 15 | Business websites | Canada | ✅ | Current | N/A | N/A | Some | ✅ | N/A | N/A | ✅ | Site-specific | Free (infra) | Must respect rules | C | Enrichment |
| 16 | PEI OCBR | PEI | ✅ | Live | ❌ | ❌ | ? | ✅ | ✅ | ❌ | ? | Free search | ⚠️ unverified | C | Targeted verification |
| 17 | NL CADO | NL | ✅ corps only | Live | ❌ | ❌ | ? | ✅ | ✅ | ❌ | ? | Free/some paid | ⚠️ unverified | C | Verification — NO business-name registry |
| 18a | Yukon YCOR | YT | ✅ | Live | ❌ | ❌ | ? | ✅ | ✅ | ❌ | ? | Free search / paid profile | ⚠️ unverified | C | Targeted verification |
| 18b | Yukon Supplier Directory | YT | ✅ | 2022? | ❌ | ✅ | ? | ✅ | ? | ❌ | OGL-Yukon | Free | ✅ | C | Enrichment — freshness unverified |
| 18c | Yukon Business Statistics | YT | ❌ aggregate | 2026 | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ? | Free | ✅ | D | Benchmark |
| 19a | NWT CROS | NT | ✅ | Live | ❌ | ❌ | ? | ✅ | ✅ | ❌ | ? | Free basic / paid profile | ⚠️ unverified | C | Targeted verification |
| 19b | NWT BIP Registry | NT | ✅ | ? | ❓ | ❓ | ❌ | ✅ | ? | ❌ | ? | Free | ⚠️ unverified | A | Discovery candidate — tech inspection needed |
| 19c | NWT Open Data | NT | ✅ specialized | Varies | Some | Some | ? | ? | ? | ❌ | ? | Free | ✅ | A+D | Specialized datasets + benchmark |
| 20a | Nunavut NNI Registry | NU | ✅ | Biennial | ❓ | ❓ | ❌ | ✅ | ? | ❓ phone/email | ? | Free | ⚠️ | A/C | High-value candidate — public exposure unverified |
| 20b | Nunavut Corporate Registry | NU | ✅ | ? | ❌ | ❌ | ? | ? | ? | ❌ | ? | ? | ❌ | — | Inaccessible — no public API found |
| 20c | Nunavut Business Licensing | NU | ✅ | Annual | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ? | Free | ❓ | B | Change-signal candidate — no bulk dataset |

---

## Sources Still to Discover

These categories have not yet been systematically searched. Part of the Phase 1 source discovery pass.

- [x] PEI business registry / open data — **RR07: OCBR confirmed; verification source only; bulk/API not found**
- [x] Newfoundland & Labrador business registry / open data — **RR07: CADO confirmed; no business-name registry; verification source only**
- [x] Yukon business registry / open data — **RR07: YCOR confirmed; Supplier Directory open licence (stale?); verification source only**
- [x] Northwest Territories open data beyond Yellowknife directory — **RR08: CROS + BIP Registry + 76-dataset open data portal**
- [x] Nunavut business data — **RR08: NNI Registry (high-value candidate) + business licensing; corporate registry inaccessible**
- [ ] Canadian municipal open data portals NOT already in ODBus source list
- [ ] Industry Canada / ISED open datasets
- [ ] CRA business number open data (if any)
- [ ] Canada Revenue Agency business datasets (public portions)
- [ ] Canada Post address data (FSA-level open data)
- [ ] Open Street Map Canada POI data — business names + addresses
- [ ] Google Places API (paid — document as optional Tier 4)
- [ ] LinkedIn API (restricted — document as unavailable or optional)
- [ ] Yellow Pages / Canada411 (ToS review required)
- [ ] BBB (Better Business Bureau Canada) — ToS review required
- [ ] Industry-specific regulated profession databases (lawyers, accountants, engineers, etc.)
- [ ] Health authority business/facility databases
- [ ] WSBC / WCB employer registries (workers compensation)
- [ ] Export Development Canada datasets (if any)
- [ ] BDC (Business Development Bank) datasets (if any)
- [ ] Chamber of Commerce member directories — ToS review required

---

## Research Rules (Reminder)

1. Measure the real data — do not assume field content or coverage.
2. Verify commercial-use licence before committing any source to the production system.
3. Prefer bulk download or API over browser automation.
4. Never bypass authentication, CAPTCHA, access controls, or technical restrictions.
5. Preserve source provenance — every value should carry its source, URL, and collection timestamp.
6. Do not overwrite conflicting observations from different sources.
7. Do not fabricate business or contact information.
8. Each source added must satisfy: useful data + permitted automation + acceptable cost.
9. Keep this tracker updated — a finding not recorded is a finding lost.

---

## Next Priority Actions

| Priority | Action | Asset | Status |
| --- | --- | --- | --- |
| A1 | Download Corporations Canada active corps CSV — profile row count, nulls, status, province, BN uniqueness | ASSET-02 | Pending |
| A2 | Inspect ODBus underlying source links — identify which municipal sources are still current | ASSET-09 | Pending |
| A3 | Download StatsCan Business Counts CSVs — profile employee-size labels, NAICS, geography, suppression markers | ASSET-04 | Pending |
| B1 | Download Saskatoon business/new-business files — format, fields, phone/email, ID, licence | ASSET-11b | Pending |
| B2 | Inspect Manitoba weekly Companies Office filings — format, fields, RSS/API, terms | ASSET-12b | Pending |
| B3 | Download Ontario Select Licence Aug 2026 — profile field quality, record count, coverage | ASSET-07a/b | Pending |
| C1 | BC OrgBook API test — `/v4/credential-type`, response fields, commercial terms | ASSET-03 | Pending |
| C2 | NS RJSC technical inspection — 1–2 searches, network capture, JSON endpoint, terms | ASSET-08a | Pending |
| C3 | PEI OCBR technical inspection — same approach as NS | ASSET-16 | Pending |
| C4 | NL CADO technical inspection — same approach as NS | ASSET-17 | Pending |
| C5 | Yukon Supplier Directory — download, check last-modified date, field list | ASSET-18b | Pending |
| C6 | NWT BIP Registry — check interface, machine-readable endpoint? | ASSET-19b | Pending |
| C7 | Nunavut NNI Registry — inspect public directory, confirm which fields are shown | ASSET-20a | Pending |

---

## Research Round Log

| Round | Topic | File | Date | Status |
| --- | --- | --- | --- | --- |
| RR01 | Corporations Canada | `research_rounds/RR01_CORPORATIONS_CANADA.md` | 2026-09-25 | Complete — profiling pending |
| RR02 | Ontario | `research_rounds/RR02_ONTARIO.md` | 2026-09-25 | Complete — download/profiling pending |
| RR03 | BC OrgBook | `research_rounds/RR03_BC_ORGBOOK.md` | 2026-09-25 | Complete — API testing pending; bulk assumption corrected |
| RR04 | Statistics Canada Business Counts + Openings/Closures | `research_rounds/RR04_STATSCAN_BUSINESS_COUNTS.md` | 2026-09-25 | Complete — CSV profiling pending |
| RR05 | Nova Scotia RJSC + Open Data | `research_rounds/RR05_NOVA_SCOTIA.md` | 2026-09-25 | Complete — RJSC strong candidate; bulk/API tech inspection pending |
| RR06 | Saskatchewan + Manitoba | `research_rounds/RR06_SASKATCHEWAN_MANITOBA.md` | 2026-09-25 | Complete — Saskatoon licences + MB weekly filings = key free sources; local inspections pending |
| RR07 | PEI + NL + Yukon | `research_rounds/RR07_PEI_NL_YUKON.md` | 2026-09-25 | Complete — all three = verification sources only; no free bulk found; tech inspections pending |
| RR08 | NWT + Nunavut | `research_rounds/RR08_NWT_NUNAVUT.md` | 2026-09-25 | Complete — **Phase 1 SOURCE DISCOVERY COMPLETE** for all 13 jurisdictions |
| GAP | Canada-wide Gap Analysis | `CANADA_WIDE_GAP_ANALYSIS.md` | 2026-09-25 | Complete — 6 gaps identified, validation queue set, Phase 2 ready |
