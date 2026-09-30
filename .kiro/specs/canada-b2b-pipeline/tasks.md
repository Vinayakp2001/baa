# Implementation Plan
# Canada B2B Business Data Pipeline

---

- [x] 1. Project scaffold and database foundation






  - Create directory structure: `backend/`, `frontend/`, `n8n/`, `migrations/`, `data/raw/`
  - Create `docker-compose.yml` with services: postgres, api, frontend, n8n, nginx
  - Create `backend/pyproject.toml` with pinned dependencies: fastapi==0.111.0, sqlalchemy==2.0.30, alembic==1.13.1, pydantic==2.7.1, httpx==0.27.0, beautifulsoup4==4.12.3, lxml==5.2.1, pdfplumber==0.11.1, openpyxl==3.1.2, rapidfuzz==3.9.3, structlog==24.2.0, python-dotenv==1.0.1
  - Create `.env.example` with all required environment variables (DATABASE_URL, CORPS_CANADA_API_KEY, etc.)
  - _Requirements: 14.1, 14.7_

- [x] 2. Database schema — core tables





- [x] 2.1 Create Alembic migration for source registry and ingestion tracking tables


  - Write migration creating: `source`, `ingestion_run` tables with all columns per design.md
  - Seed `source` table with all 17 source rows (source_key, adapter_class, province, source_type, source_class, licence, schedule_cron, is_enabled, rate_limit_rpm, base_url, terms_status)
  - NNI row: `terms_status='UNRESOLVED'`, `is_enabled=false`
  - _Requirements: 3.2, 3.7, 10.1_

- [x] 2.2 Create Alembic migration for canonical entity tables


  - Write migration creating: `business`, `business_location`, `business_identifier`, `business_contact`, `person`, `business_employee_data`, `business_industry`
  - Add indexes: `business(province)`, `business(status)`, `business(sales_ready)`, `business_identifier(id_type, id_value)`, `business_contact(entity_id, contact_type)`
  - _Requirements: 1.1, 1.2, 7.1_

- [x] 2.3 Create Alembic migration for provenance tables


  - Write migration creating: `source_record`, `field_observation`
  - `source_record.raw_payload` as JSONB
  - `field_observation` compound index on `(entity_id, field_name, observed_at)`
  - _Requirements: 2.1, 2.2, 2.3, 2.5_


- [x] 2.4 Create Alembic migration for event, quality, and sales layer tables


  - Write migration creating: `business_event`, `business_status_history`, `merge_candidate`, `business_quality_score`, `data_quality_flag`, `province_coverage_gap`, `lead_flag`
  - Seed `province_coverage_gap` with 8 confirmed gap rows (NS, NB, PE, NL confirmed; ON, QC partial; YT, NT deferred)
  - _Requirements: 6.1, 9.4, 9.5, 13.1_

- [ ]* 2.5 Write migration rollback tests
  - Test upgrade + downgrade for each migration file
  - _Requirements: 14.6_

- [x] 3. SQLAlchemy models and base service infrastructure






- [x] 3.1 Write SQLAlchemy ORM models for all 15 tables

  - One model class per table, matching migration schemas exactly
  - Define relationships: `business` → `business_location`, `business_event`, `field_observation`, etc.
  - _Requirements: 1.1, 2.1_


- [x] 3.2 Write database session factory and dependency injection for FastAPI

  - Async session using `asyncpg` driver
  - `get_db()` dependency for route injection
  - _Requirements: 14.1_


- [x] 3.3 Write structured logging setup using structlog

  - JSON-formatted output with `request_id`, `source_key`, `run_id` as bound context
  - _Requirements: 14.2_

- [x] 4. Source adapter interface and ingestion service





- [x] 4.1 Write the `SourceAdapter` abstract base class and data contracts


  - Implement `SourceAdapter` ABC with `fetch()`, `parse()`, `validate()`, `get_metadata()` methods
  - Write `RawArtifact`, `RawRecord`, `SourceMetadata`, `ValidationResult` Pydantic models
  - Write `SourceGrain` enum: CORPORATION, LICENCE, EVENT, REGISTRATION, ESTABLISHMENT
  - _Requirements: 3.1, 3.2_

- [x] 4.2 Write ingestion service FastAPI routes


  - `POST /ingestion/start` → create `ingestion_run` row, return `run_id`
  - `POST /ingestion/fetch` → call adapter `fetch()` + `parse()`, store `source_record` rows, return record count
  - `POST /ingestion/complete` → update run stats and `run_status=COMPLETED`
  - `POST /ingestion/fail` → update `run_status=FAILED`, store `error_message`, increment `retry_count`
  - _Requirements: 2.1, 2.2, 3.3, 3.4_

- [x] 5. Source adapters — Class A discovery sources


- [x] 5.1 Implement `CorporationsCanadaCSVAdapter`


  - Fetch active CBCA CSV (direct URL, no auth), checksum SHA-256, store artifact
  - Parse: `corp_number`, `business_number_bn`, `corporate_name_form_1`, `address_*`, `anniversary_date`, `status`
  - Source grain: CORPORATION
  - _Requirements: 3.8, 10.1_

- [x] 5.2 Implement `CalgaryAdapter`


  - Fetch from Socrata CSV endpoint; support incremental via `first_iss_dt >= last_run` filter
  - Parse: `tradename`, `address`, `jobstatusdesc`, `first_iss_dt`, `exp_dt`, `longitude`, `latitude`, `licencetypes`
  - Source grain: LICENCE
  - _Requirements: 3.8, 10.1, 10.5_


- [x] 5.3 Implement `EdmontonAdapter`

  - Fetch from Socrata CSV endpoint (migrated URL); incremental via `original_issue_date >= last_run`
  - Parse: `business_name`, `address`, `original_issue_date`, `most_recent_issue_date`, `licencetype`, `neighbourhood`
  - Source grain: LICENCE
  - _Requirements: 3.8, 10.1, 10.5_

- [x] 5.4 Implement `VancouverAdapter`


  - Fetch from OpenDataSoft export; incremental via `issueddate >= last_run`
  - Parse: `businessname`, `postalcode`, `status`, `issueddate`, `numberofemployees` (float-string → normalise), `businesstype`, `businesssubtype`, `coordinates`, `LicenceRSN`
  - Source grain: LICENCE. Preserve `LicenceRSN` as `source_record_id`
  - _Requirements: 3.8, 5.9, 10.1, 10.5_

- [x] 5.5 Implement `SaskatoonAllBizAdapter`


  - Fetch XLSX from direct URL; parse with openpyxl
  - Parse: `Bus_Lic_Acct_Id`, `name`, `address` (split fields), `NAICS sub-sector`
  - Source grain: LICENCE
  - _Requirements: 3.8_

- [x] 5.6 Implement `MontrealCommercialPremisesAdapter`


  - Fetch CSV/GeoJSON; parse `name`, `address`, `SCIAN` (map to NAICS), `commercial_category`, `occupancy_status`, `coordinates`, `arrondissement`
  - Source grain: ESTABLISHMENT
  - _Requirements: 3.8_

- [x] 6. Source adapters — Class B new-business event sources



- [x] 6.1 Implement `CorporationsCanadaHTMLAdapter`


  - HTTP GET monthly incorporations HTML page; parse with BeautifulSoup
  - Extract: `company_name`, `jurisdiction`, `incorporation_date` per VR03 structure
  - Source grain: EVENT. Event type: FEDERAL_INCORPORATION
  - _Requirements: 3.8, 6.2_

- [x] 6.2 Implement `ManitobaWeeklyPDFAdapter`


  - HTTP GET current week PDF from listing page; parse with pdfplumber
  - Extract records under `Incorporations` category: `company_name`, `file_no`, `registered_office`
  - De-duplicate against previous run by `file_no` (VR08: zero cross-week overlaps confirmed)
  - Source grain: EVENT. Event type: PROVINCIAL_REGISTRATION
  - _Requirements: 3.8, 6.2_

- [x] 6.3 Implement `SaskatoonNewBizAdapter`


  - Fetch XLSX; parse `Business_License_Id`, `name`, `address`, NAICS
  - Source grain: LICENCE. Event type: MUNICIPAL_LICENCE_FIRST_ISSUE
  - _Requirements: 3.8, 6.2_


- [x] 6.4 Implement `WinnipegAdapter` (Class B — event/closure detection only)

  - Fetch Socrata CSV; filter to non-ACTIVE status rows only for closure detection
  - Parse: `trade_name`, `address`, `status`, `issue_date`, `expiry_date`
  - Source grain: EVENT. Event type: LICENCE_STATUS_CHANGE
  - Adapter MUST NOT submit Winnipeg records as Class A discovery — flag as event-only in metadata
  - _Requirements: 3.8, 5.8, 6.2_

- [x] 6.5 Implement `QuebecCityPermitsAdapter` (event signal only)

  - Fetch the validated weekly CC-BY 4.0 CSV resource; preserve the raw permit row and use `NUMERO_PERMIS` as the source record ID
  - Parse permit number, issue date, work address, domain, impacted lots, permit type, borough, reason, longitude, and latitude
  - Source grain: EVENT; event type: `MUNICIPAL_PERMIT_ISSUED`
  - Do not treat permit number as a business identifier or create a business from a permit-only record; unresolved records remain in the source layer
  - _Requirements: 3.8, 5.10, 6.2, 6.7_

- [x] 7. Normalisation service






- [x] 7.1 Write phone normaliser

  - Strip all formatting → 10-digit string → E.164 → validate NPA against Canadian area code list
  - Return: `normalised_phone`, `phone_valid`, `raw_phone`
  - "N/A" and empty → NULL (not invalid)
  - _Requirements: 4.1_


- [x] 7.2 Write business name normaliser

  - Lowercase → expand abbreviations (LTD→LIMITED, INC→INCORPORATED, CO→COMPANY, CORP→CORPORATION, ST→SAINT) → strip punctuation variants → strip whitespace
  - Preserve both `legal_name` and `trade_name`/`dba` as distinct fields
  - _Requirements: 4.2_


- [x] 7.3 Write address normaliser

  - Standardise street type abbreviations (St→Street, Ave→Avenue, Blvd→Boulevard, Dr→Drive, etc.)
  - Normalise unit/suite formats → uppercase province → format postal as "A1A 1A1"
  - Validate Canadian postal code format (L-D-L D-L-D pattern)
  - Return: `normalised_address`, `raw_address`, `postal_valid`
  - _Requirements: 4.3, 4.4_


- [x] 7.4 Write email, URL, status, date, and NAICS normalisers

  - Email: lowercase domain, validate RFC 5321, "N/A" → NULL
  - URL: extract registered domain, strip www., lowercase, store `raw_url` + `normalised_domain`
  - Status: map source strings to ACTIVE/INACTIVE/SUSPENDED/DISSOLVED/PENDING/UNKNOWN per source key mapping table; preserve `raw_status`
  - Date: multi-format parser → ISO 8601 UTC
  - NAICS: preserve `source_naics`; map to 2-digit `naics_sector` where unambiguous; do not infer
  - _Requirements: 4.5, 4.6, 4.8, 4.9, 4.10_


- [x] 7.5 Write employee value normaliser

  - Handle: exact integer/float-string (Vancouver "385.0"), range string ("10 to 19", "55 to 99"), combined bucket ("500 plus", "500+"), NULL/absent
  - Produce: `raw_employee_value`, `employee_min`, `employee_max`, `employee_bucket`, `employee_exact`
  - "55 to 99" → flag `data_quality_flag` with type EMPLOYEE_RANGE_AMBIGUITY
  - "500 plus" → `employee_min=500`, `employee_max=NULL`, `employee_exact=false`, bucket=`500+`
  - NULL → all derived fields NULL, no estimation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_


- [x] 7.6 Write normalisation service FastAPI route


  - `POST /normalise` → receive `RawRecord[]`, apply all normalisers, return `NormalisedRecord[]`
  - Store `NormalisedRecord` into `source_record.normalised_payload` (JSONB)
  - _Requirements: 4.1_

- [ ]* 7.7 Write normaliser unit tests
  - Phone: "(416) 123-4567", "4161234567", "416-123-4567", "N/A", invalid NPA
  - Employee: "385.0", "10 to 19", "55 to 99", "500 plus", NULL, 42
  - Address: postal formatting, street abbreviations
  - Status: map each source's known status strings
  - _Requirements: 4.1–4.10_

- [x] 8. Entity resolution service






- [x] 8.1 Write exact identifier matcher

  - Query `business_identifier` for: corp_number, BN, source_licence_id (within same source)
  - Return match result with confidence=HIGH and matching identifier
  - _Requirements: 5.1a, 5.1b, 5.1c, 5.2_


- [x] 8.2 Write composite deterministic matcher

  - Match on: normalised_domain + postal_code, normalised_phone + postal_code, normalised_name + normalised_address
  - Query indexed columns in `business` and `business_contact` tables
  - Return match result with confidence=MEDIUM
  - _Requirements: 5.1d, 5.1e, 5.1f, 5.2_


- [x] 8.3 Write fuzzy matcher using RapidFuzz

  - `token_sort_ratio` on `normalised_name + postal_code` against candidate set
  - Default threshold: 88 (configurable via env var FUZZY_MATCH_THRESHOLD)
  - Return match result with confidence=LOW
  - _Requirements: 5.1g, 5.2_


- [x] 8.4 Write merge and entity creation logic

  - HIGH confidence → auto-merge: update `business`, append `field_observation` rows, update `source_record.entity_id`
  - MEDIUM confidence → insert `merge_candidate` row, do NOT auto-merge, set `source_record.resolution_status=CANDIDATE`
  - LOW confidence → create new `business` entity, link as `merge_candidate` with `auto_resolved=false`
  - No match → create new `business` entity, `resolution_status=NEW`
  - Preserve `source_id`, `source_grain`, `source_record_id`, `ingestion_run_id` on every contributing record
  - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7_


- [x] 8.5 Write entity resolution service FastAPI route

  - `POST /resolve` → receive `NormalisedRecord[]`, run resolution pipeline, return `ResolutionResult[]`
  - Write `field_observation` row for every field of every merged record
  - _Requirements: 5.1, 2.5_

- [ ]* 8.6 Write entity resolution integration tests
  - Same corp_number from two sources → single entity, two source_records
  - Same business, different name spelling → fuzzy MEDIUM candidate created
  - Two genuinely distinct businesses with similar names → two entities
  - Vancouver multi-licence conflict: employee resolved to most-recent issued licence
  - _Requirements: 5.3–5.9_


- [ ] 8.7 Write unresolved source-record lifecycle tests
  - Record without a business name or stable identifier → retained with `entity_id=NULL`, `resolution_status=UNRESOLVED`, and no canonical business/event created
  - Later normalized record explicitly references the exact unresolved `{source_key, source_record_id}` → the same source_record is linked, provenance is retained, and its applicable event is created once
  - A mismatched or absent explicit source reference does not link the unresolved row
  - _Requirements: 2.7, 2.8, 5.10, 5.11, 6.7_


- [ ] 8.8 Preserve and reprocess unresolved source records
  - Insufficient identity → retain raw/normalised source record with `entity_id=NULL` and `resolution_status=UNRESOLVED`; do not create a business or business event
  - Sufficient identity with no match → preserve existing behavior and create a new canonical business
  - Reconsider unresolved records only when a later normalized record explicitly references the exact `{source_key, source_record_id}`; preserve the existing row and source/run provenance on success
  - Create field observations and business events only after a canonical entity link exists; event creation is idempotent
  - Expose unresolved outcomes in resolution responses without dropping source records
  - _Requirements: 2.7, 2.8, 5.10, 5.11, 6.7_

- [x] 9. Source adapters — Class C enrichment sources






- [x] 9.1 Implement `CorporationsCanadaAPIAdapter` with rate limiting

  - REST call to `/cc/api/corporations/{corp_number}` with `user-key` header
  - Token bucket rate limiter: max 60 requests/minute using asyncio timestamps
  - Parse `_embedded.directors[{firstName, lastName, serviceAddress}]`
  - Write to `person` table with `role_type=DIRECTOR`
  - Only submit records with valid `corp_number` (federal CBCA corps only)
  - _Requirements: 3.5, 8.3, 8.4_


- [x] 9.2 Implement `BCOrgBookAPIAdapter`

  - Targeted lookup only — no enumeration
  - Query by BC Reg ID or business name; parse `legal_name`, `status`, `registration_date`, `credential_history`
  - Adapter MUST reject any call that attempts to enumerate all entities
  - _Requirements: 3.6, 8.9_


- [x] 9.3 Implement `BCIndigenousAdapter`

  - Fetch direct CSV (OGL-BC); parse `name`, `phone`, `email`, `website`, `Primary Contact`, `employee_range`, `Industry Sector`
  - Employee range → employee normaliser
  - "55 to 99" → flag EMPLOYEE_RANGE_AMBIGUITY
  - "500 plus" → normalise per Req 7.4 rules
  - _Requirements: 3.8_

- [x] 9.4 Implement `OntarioSelectLicenceAdapter`


  - Fetch CKAN CSV; parse `legal_name`, `address`, `phone`, `email`, `website`, `licence_type`
  - "N/A" in phone/email/website → NULL (not invalid)
  - Source grain: LICENCE
  - _Requirements: 3.8_

- [x] 9.5 Implement `NNIAdapter` (conditional — guarded by terms_status check)


  - Adapter MUST check `source.terms_status` before any processing
  - If `terms_status != 'CLEARED'` → log warning, skip, do NOT write to canonical layer
  - When cleared: parse `business_name`, `business_number`, `street_address`, `community`, `postal_code`, `phone`, `email`, `contact_name`, `employee_count` (integer), `sectors[]`, `goods[]`, `services[]`, `effective_date`, `status`
  - _Requirements: 3.7, 8.10_



- [x] 9.6 Implement `OntarioRegulatedSectorAdapters` (×6: Dairy, Meat, Tobacco, Fuel, CSBIF, DairyPlants)

  - One adapter class per source; all extend a shared `OntarioRegulatedBaseAdapter`
  - Each parses: `name`, `address`, `phone`, `licence_number` (fields vary per source)
  - Role: enrichment only — phone/postal for regulated-sector businesses
  - _Requirements: 3.8_

- [x] 10. Events service








- [x] 10.1 Write new-business event detector

  - After entity resolution: if `resolution_status=NEW` → create `BUSINESS_DISCOVERED` event
  - If source_grain=EVENT and event_type is FEDERAL_INCORPORATION/PROVINCIAL_REGISTRATION/MUNICIPAL_LICENCE_FIRST_ISSUE/MUNICIPAL_PERMIT_ISSUED → create typed event record only after the source_record has an entity_id
  - Unresolved source records SHALL NOT produce business_event rows; after later resolution, create the applicable event idempotently
  - _Requirements: 6.1, 6.2_



- [x] 10.2 Write status change and field change detectors

  - Compare new `field_observation` against current `is_current=true` observation for same field
  - If status field changed → create `STATUS_CHANGED` event, write `business_status_history` row, preserve old + new values
  - If name changed → create `NAME_CHANGED` event
  - If location changed → create `LOCATION_CHANGED` event
  - On any change → create `BUSINESS_UPDATED` event
  - _Requirements: 6.4, 6.5_

- [x] 10.3 Write events service FastAPI route


  - `POST /events/detect` → receive entity_id + ingestion_run_id, run all detectors, return events_created count
  - _Requirements: 6.1_

- [x] 11. Enrichment service



- [x] 11.1 Write enrichment service routes for directors and OrgBook

  - `POST /enrich/directors` → receive corp_number list, call CorporationsCanadaAPIAdapter (rate-limited), write person records
  - `POST /enrich/orgbook` → receive entity_id + bc_reg_id, call BCOrgBookAPIAdapter, update entity with BC identity data
  - All enrichment fields stored with `enrichment_source`, `enriched_at`, `enrichment_confidence`, `enrichment_run_id`
  - _Requirements: 8.2, 8.3, 8.9_



- [x] 11.2 Write optional website phone extraction enrichment

  - `POST /enrich/website` → given known domain, crawl /contact and homepage, extract phone with CA NPA validation
  - Store result with `source=website_crawl`, `confidence=low`
  - This route is optional — failure does NOT block entity or pipeline
  - _Requirements: 8.6, 8.7, 8.8_



- [x] 12. Quality scoring service

- [x] 12.1 Write individual confidence score calculators

  - One function per component: identity, address, phone, email, employee, industry, contact, recency, source_reliability
  - Each returns 0–100 integer per documented formula in design.md
  - _Requirements: 9.1_


- [x] 12.2 Write composite `lead_quality_score` calculator and `sales_ready` flag setter

  - Apply weighted formula from design.md: identity×0.25, address×0.20, phone×0.15, email×0.10, contact×0.10, recency×0.10, employee×0.05, industry×0.05
  - Set `sales_ready=true` if: name + address + province + status=ACTIVE + at least one of (phone | email | website | director_name)
  - Upsert `business_quality_score` row; update `business.lead_quality_score` and `business.sales_ready`
  - _Requirements: 9.2, 9.3_




- [ ] 12.3 Write quality service FastAPI route
  - `POST /quality/score` → receive entity_id[], compute all components + composite, persist scores
  - _Requirements: 9.1, 9.2_

- [ ]* 12.4 Write quality score unit tests
  - Known input combinations → expected component scores and composite


  - sales_ready=true threshold cases: minimum required fields
  - _Requirements: 9.2, 9.3_

- [x] 13. Public REST API


- [x] 13.1 Write `GET /businesses` with all filters and pagination

  - Filters: province, city, naics_sector, employee_bucket, status, sales_ready, has_phone, has_email, has_website, has_director, new_since (date), event_type, source_id, dnc
  - Pagination: cursor-based or offset, return total + page_size + next_cursor
  - Response: list of `BusinessSummary` Pydantic models
  - _Requirements: 11.1, 11.2, 11.3_



- [x] 13.2 Write `GET /businesses/{id}` and related detail endpoints

  - `GET /businesses/{id}` → `BusinessDetail` with all sub-objects
  - `GET /businesses/{id}/history` → all `field_observation` records grouped by field, with source attribution
  - `GET /businesses/{id}/sources` → all contributing `source_record` rows

  - _Requirements: 11.1, 11.4_

- [x] 13.3 Write events, sources, stats, and export endpoints

  - `GET /events` → paginated, filterable by event_type, province, date_range
  - `GET /sources` → source registry rows with last `ingestion_run` status per source
  - `GET /stats` → coverage by province, source, field fill rates
  - `GET /export` → CSV or JSON respecting current filter state; DNC excluded by default
  - _Requirements: 11.1, 13.3_


- [x] 13.4 Add OpenAPI documentation and configure CORS


  - FastAPI auto-generates `/docs` (Swagger) and `/openapi.json`
  - Configure CORS to allow Next.js frontend origin
  - _Requirements: 11.5_

- [ ]* 13.5 Write API integration tests
  - `GET /businesses` with each filter combination
  - `GET /businesses/{id}/history` provenance chain correctness
  - `GET /export` CSV output format
  - _Requirements: 11.1–11.5_

- [x] 14. n8n workflow configuration






- [x] 14.1 Create n8n workflow: `ingest-source` (generic, parameterised)

  - Nodes: Cron trigger → read source config (PostgreSQL node) → POST /ingestion/start → POST /ingestion/fetch → POST /normalise → POST /resolve → POST /events/detect → POST /quality/score → POST /ingestion/complete
  - Nodes: Execute Workflow Trigger (receives `source_key`) → read source config (PostgreSQL node) → POST /ingestion/start → POST /ingestion/fetch → POST /normalise → POST /resolve → POST /events/detect → POST /quality/score → POST /ingestion/complete
  - Error branch: POST /ingestion/fail with error detail
  - Retry: exponential backoff 1min → 5min → 30min → 1h
  - _Requirements: 10.1, 10.2, 10.3, 10.6_


- [x] 14.2 Create per-source n8n workflows with correct schedules



  - Calgary: daily cron `0 6 * * *`
  - Edmonton: daily cron `0 6 * * *`
  - Vancouver: daily cron `0 5 * * *`
  - Winnipeg: daily cron `0 7 * * *`
  - Corps Canada CSV: weekly cron `0 4 * * 1`
  - Corps Canada monthly HTML: monthly cron `0 8 1 * *`
  - Manitoba weekly PDF: weekly cron `0 9 * * 5`
  - Saskatoon all-biz + new-biz: weekly cron `0 8 * * 1`
  - Ontario Select Licence + regulated sources: monthly `0 8 1 * *`
  - Montréal: annually `0 8 1 1 *`
  - QC City Permits: weekly `0 9 * * 5`
  - BC Indigenous: monthly `0 8 1 * *`
  - _Requirements: 10.1_



- [-] 14.3 Create n8n workflow: `enrich-directors` (event-triggered)


  - Trigger: new FEDERAL_INCORPORATION event detected (poll `business_event` where event_type=FEDERAL_INCORPORATION and enrichment_attempted=false)
  - POST /enrich/directors with corp_number batch
  - _Requirements: 10.1, 8.3_




- [x] 14.4 Create n8n workflow: `enrich-orgbook` (event-triggered)



  - Trigger: new BC entity detected (poll `business` where province='BC' and orgbook_enriched=false)
  - POST /enrich/orgbook
  - _Requirements: 3.6, 8.9_

- [x] 15. Next.js dashboard

- [x] 15.1 Scaffold Next.js 14 app with Tailwind CSS and shadcn/ui



  - Configure `NEXT_PUBLIC_API_URL` env var
  - Install pinned dependencies: next@14.2.3, tailwindcss@3.4.3, shadcn/ui components
  - _Requirements: 12.1_



- [x] 15.2 Build dashboard home page with KPI summary cards

  - Fetch `GET /stats` on load
  - Display: total businesses, sales-ready count, new last 30 days, province coverage gap flags
  - Province coverage gaps displayed prominently (NS/NB confirmed, ON/QC partial)
  - _Requirements: 12.1, 9.5_

- [x] 15.3 Build business list page with filter panel


  - `FilterPanel` component: province, city, NAICS sector, employee bucket, status, new_since, has_phone, has_email, has_website, has_director, DNC, confidence threshold
  - `BusinessTable` component: paginated, sortable, shows summary fields + quality badge
  - Integrate `GET /businesses` with filter state
  - _Requirements: 12.2_


- [x] 15.4 Build business detail page

  - Tabs: Identity | Contact | Employees | Industry | People | Events | Sources | History
  - `EventTimeline` component: visual timeline of all `business_event` records with event_type badges
  - `ProvenancePanel` component: field_observation history table grouped by field
  - `QualityBadge` component: show component scores breakdown + composite score
  - DNC flag displayed prominently if present
  - _Requirements: 12.3, 12.5_


- [x] 15.5 Build export functionality and sources status page

  - `ExportButton` component: triggers `GET /export` with current filter state, downloads CSV or JSON
  - DNC-flagged records excluded from export by default; opt-in checkbox to include
  - Sources page: `SourceStatusCard` per source showing last run timestamp, record count, status, schedule
  - _Requirements: 12.4, 12.5, 14.3_

- [x] 16. DNC and sales layer



- [x] 16.1 Write DNC API endpoints and sales flag management


  - `POST /businesses/{id}/flags` → set lead_flag (DNC, CONTACTED, QUALIFIED, etc.)
  - `DELETE /businesses/{id}/flags/{flag_type}` → remove flag
  - Flags stored in `lead_flag` table only — no canonical entity fields modified
  - _Requirements: 13.1, 13.2_


- [x] 16.2 Wire DNC flag into export and quality scoring

  - `GET /export` excludes `dnc=true` records by default; `include_dnc=true` param overrides
  - `lead_quality_score` computation: if DNC flag exists → disqualifier applied at composite step only, not stored in quality model
  - _Requirements: 13.3, 13.4_

- [ ] 17. Compliance guards and final integration




- [x] 17.1 Write compliance enforcement guards

  - StatsCan adapters: assert `source_class='D'`, throw if any individual record payload detected
  - BC OrgBook adapter: assert call is targeted lookup, throw if pagination/enumeration attempted
  - NNI adapter: runtime check `source.terms_status == 'CLEARED'` before write — tested guard
  - robots.txt check utility: cache fetched robots.txt per domain, check before any website crawl
  - _Requirements: 15.1, 15.2, 15.3, 15.7, 15.9_


- [x] 17.2 Wire all services together end-to-end and validate full pipeline

  - Run docker-compose up
  - Execute manual ingestion trigger for CorporationsCanadaCSVAdapter (sample 1,000 rows)
  - Verify: ingestion_run created → source_records stored → normalised_payload populated → entity resolved → field_observations written → business_event BUSINESS_DISCOVERED → quality scored → `GET /businesses` returns result with provenance chain
  - _Requirements: 1.1–1.7, 2.1–2.6_
