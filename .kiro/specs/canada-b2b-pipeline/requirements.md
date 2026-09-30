# Requirements Document
# Canada B2B Business Data Pipeline

## Introduction

This system is a production-oriented, Canada-wide B2B business data pipeline for a telecom
sales operation. It ingests, normalises, deduplicates and continuously refreshes Canadian
business records from validated public/open-data sources only — no recurring third-party data
costs.

The source landscape is frozen (VR01–VR20 complete). Every requirement below is derived
directly from findings in those validation rounds. No requirement is speculative.

The pipeline serves two audiences:
- Internal sales operations: filtered, scored, exportable lead lists with phone / email /
  decision-maker where available.
- System operators: full provenance, source history, ingestion status and data-quality
  visibility for every record.

The most important architectural constraint: **no source may silently overwrite another
source**. Every observed value must be traceable to its origin.

---

## Requirements

---

### Requirement 1 — Canonical Business Entity Model

**User Story:** As a data engineer, I want a single canonical representation of a business
that can absorb observations from 10–20 heterogeneous sources without losing source
information, so that the pipeline produces one trustworthy record per real-world business
while preserving full provenance.

#### Acceptance Criteria

1. WHEN a business record is created THEN the system SHALL assign a pipeline-generated
   `entity_id` that is never borrowed from any single source identifier.

2. WHEN the same real-world business is observed in multiple sources THEN the system SHALL
   merge those observations into one canonical entity while preserving each source's raw
   values separately.

3. WHEN two sources report different values for the same field (e.g. address, name) THEN
   the system SHALL preserve both values with their respective source attribution rather
   than silently picking one.

4. WHEN a source provides a value for a field THEN the system SHALL store `source_id`,
   `ingestion_run_id`, `observed_at`, and `raw_value` alongside the canonical value.

5. WHEN no source provides a value for a nullable field (e.g. phone, email, employee count)
   THEN the system SHALL store NULL and SHALL NOT estimate, fabricate or infer a value.

6. WHEN a business record is retrieved THEN the system SHALL be able to answer "which source
   provided this field value and when" for every non-null field.

7. WHEN a province has no confirmed discovery source THEN the system SHALL explicitly flag
   that province as a coverage gap rather than silently under-representing it.

---

### Requirement 2 — Provenance and Raw Data Preservation

**User Story:** As a data engineer, I want every ingested record to carry a complete audit
trail from raw source payload to canonical entity, so that I can debug data quality issues
and answer "why does this business have this value" at any time.

#### Acceptance Criteria

1. WHEN a source is ingested THEN the system SHALL create an `ingestion_run` record
   containing: `source_id`, `run_started_at`, `run_completed_at`, `run_status`,
   `record_count_raw`, `record_count_normalised`, `record_count_new`, `record_count_updated`,
   `source_url`, `retrieval_timestamp`, `source_version_or_date` (where available),
   `checksum_or_hash` (where applicable).

2. WHEN a raw record is received from any source THEN the system SHALL store a `source_record`
   containing the original payload or a stable reference to it, linked to its `ingestion_run`.

3. WHEN a `source_record` is normalised THEN the system SHALL store a `normalised_record`
   that links back to the originating `source_record` and `ingestion_run`.

4. WHEN a `normalised_record` is resolved to a canonical entity THEN the system SHALL
   preserve the link from canonical entity → normalised record → source record → ingestion run.

5. WHEN a source record contributes a field value to a canonical entity THEN that
   contribution SHALL be stored as a `field_observation` with: `entity_id`, `field_name`,
   `raw_value`, `normalised_value`, `source_id`, `ingestion_run_id`, `observed_at`,
   `confidence`.

6. IF a field value was previously observed from the same source and the new value differs
   THEN the system SHALL append a new `field_observation` and SHALL NOT delete the prior one.

7. WHEN a source record cannot yet be safely linked to or represented as a canonical business
   THEN the system SHALL retain its raw and normalised payload in `source_record`, leave
   `entity_id` NULL, and set `resolution_status` to `UNRESOLVED`.

8. WHEN a later normalised record explicitly references an unresolved source record by its
   exact `source_key` and `source_record_id` THEN the system SHALL link that existing
   `source_record` to the canonical entity, preserve its original source and run provenance,
   and SHALL NOT create a duplicate source record. The system SHALL NOT infer this link from
   address or fuzzy similarity alone.

---

### Requirement 3 — Source Adapter Architecture

**User Story:** As a data engineer, I want each source to be implemented as a self-contained
adapter behind a common interface, so that adding or modifying a source does not require
redesigning the pipeline.

#### Acceptance Criteria

1. WHEN a new source is added THEN it SHALL be implemented as an adapter that conforms to a
   defined `SourceAdapter` interface specifying: `fetch()`, `parse()`, `validate()`,
   `get_metadata()`.

2. WHEN a source adapter is registered THEN the system SHALL store its configuration in a
   `source` registry table containing: `source_id`, `source_name`, `source_class`,
   `province`, `source_type` (CSV / JSON / API / HTML / PDF / GeoJSON), `licence`,
   `schedule_expression`, `is_enabled`, `rate_limit_per_minute`, `base_url`, `notes`.

3. WHEN an adapter fetches data THEN it SHALL record the retrieval URL, timestamp and HTTP
   status (or equivalent) in the `ingestion_run`.

4. WHEN an adapter encounters a retrieval failure THEN it SHALL record the failure reason in
   the `ingestion_run` and SHALL NOT silently skip the run.

5. WHEN the Corporations Canada API is called THEN the adapter SHALL respect the 60 req/min
   rate limit enforced by the `user-key` header plan. Enrichment SHALL be event-triggered or
   sample-based — not full-population sweep — given that enriching all 645,005 corps would
   require approximately 180 hours at 60 req/min.

6. WHEN the BC OrgBook API is called THEN the adapter SHALL perform targeted lookups only.
   Bulk enumeration is prohibited by BC Government Terms. No adapter SHALL attempt to
   enumerate all OrgBook entities.

7. WHEN a source is classified as NNI (Nunavut) THEN the adapter SHALL treat that source as
   conditional (reuse terms unresolved) and SHALL NOT process NNI records into the canonical
   layer until the NNI Regulations PDF is reviewed and terms are confirmed.

8. The following sources SHALL each have a dedicated adapter at launch:
   - `CorporationsCanadaCSVAdapter` (federal CBCA CSV, 645,005 rows)
   - `CorporationsCanadaHTMLAdapter` (monthly incorporations HTML, VR03)
   - `CorporationsCanadaAPIAdapter` (directors enrichment, 60 req/min)
   - `CalgaryAdapter` (Socrata CSV, 23,178 rows, `first_iss_dt`)
   - `EdmontonAdapter` (Socrata CSV, 43,719 rows, `originalissuedate`)
   - `VancouverAdapter` (OpenDataSoft, 206,024 rows, daily updates)
   - `WinnipegAdapter` (Socrata CSV, 13,757 rows, Class B event-only)
   - `ManitobaWeeklyPDFAdapter` (weekly PDF, pdfplumber, Incorporations category)
   - `SaskatoonAllBizAdapter` (XLSX, 7,472 rows)
   - `SaskatoonNewBizAdapter` (XLSX, 51 rows, explicit new-licence signal)
   - `OntarioSelectLicenceAdapter` (CKAN CSV, 674 rows, phone/email enrichment)
   - `OntarioRegulatedSectorAdapters` (6 sources: dairy, meat, tobacco, fuel, CSBIF — ON enrichment)
   - `MontrealCommercialPremisesAdapter` (CSV/GeoJSON, annual, SCIAN codes)
   - `QuebecCityPermitsAdapter` (CSV, weekly, event signal only)
   - `BCIndigenousAdapter` (direct CSV, ~3,000+ rows, phone/email/contact/employee)
   - `BCOrgBookAPIAdapter` (targeted verification, bulk prohibited)
   - `NNIAdapter` (conditional — pending terms confirmation)

---

### Requirement 4 — Normalisation

**User Story:** As a data engineer, I want all field values normalised to canonical
representations before entity resolution, so that "416-123-4567" and "(416) 123-4567" are
treated as the same phone number and "ABC LTD." and "ABC Limited" are candidates for the
same business name.

#### Acceptance Criteria

1. WHEN a phone number is normalised THEN the system SHALL produce an E.164 representation,
   validate against Canadian NPA codes, and store `raw_phone`, `normalised_phone`,
   `phone_valid` (boolean), `phone_source`. Phones failing CA NPA validation SHALL be
   flagged as invalid, not silently dropped.

2. WHEN a business name is normalised THEN the system SHALL: lowercase, remove punctuation
   variants, expand common abbreviations (LTD→LIMITED, INC→INCORPORATED, CO→COMPANY,
   CORP→CORPORATION), strip leading/trailing whitespace. Both `legal_name` and
   `trade_name`/`dba` SHALL be preserved as distinct fields.

3. WHEN an address is normalised THEN the system SHALL: standardise street type abbreviations,
   normalise unit/suite formats, uppercase province code, format postal code as `A1A 1A1`.
   The `raw_address` SHALL be preserved alongside the `normalised_address`.

4. WHEN a postal code is normalised THEN the system SHALL validate Canadian postal code
   format (Letter-Digit-Letter Digit-Letter-Digit) and flag invalid formats without dropping
   the record.

5. WHEN an email address is normalised THEN the system SHALL lowercase the domain portion and
   validate RFC 5321 format. Placeholder values such as "N/A" (present in Ontario Select
   Licence) SHALL be treated as NULL.

6. WHEN a URL or domain is normalised THEN the system SHALL extract the registered domain,
   strip `www.` prefix, lowercase, and store `raw_url` and `normalised_domain` separately.

7. WHEN an employee value is normalised THEN the system SHALL apply the rules in
   Requirement 7 (Employee Classification) — normalisation and employee parsing are the
   same step.

8. WHEN a NAICS code is normalised THEN the system SHALL preserve the source-provided value
   in `source_naics` and map it to a 2-digit sector code in `naics_sector` where the mapping
   is unambiguous. The system SHALL NOT infer or fabricate NAICS for records where no source
   provides it.

9. WHEN a status value is normalised THEN the system SHALL map source-specific status strings
   to a canonical status vocabulary: `ACTIVE`, `INACTIVE`, `SUSPENDED`, `DISSOLVED`,
   `PENDING`, `UNKNOWN`. The `raw_status` SHALL be preserved.

10. WHEN a date value is normalised THEN the system SHALL store dates as ISO 8601 with UTC
    timezone where timezone is ambiguous.

---

### Requirement 5 — Entity Resolution and Deduplication

**User Story:** As a data engineer, I want a deterministic, confidence-scored entity
resolution pipeline that merges records from different sources into one canonical business
entity without collapsing genuinely distinct businesses or silently merging ambiguous records.

#### Acceptance Criteria

1. WHEN a normalised record is submitted for entity resolution THEN the system SHALL apply
   matching in priority order:
   a. Exact match on federal corporation number (`corp_number`)
   b. Exact match on Business Number / BN (`business_number_bn`)
   c. Exact match on municipal licence ID within the same source
   d. Exact match on domain + postal code
   e. Exact match on phone + postal code
   f. Exact match on normalised name + normalised address
   g. Fuzzy match on normalised name + postal code (RapidFuzz, threshold configurable)

2. WHEN a match is found THEN the system SHALL assign a confidence level:
   - `HIGH` — matched on corp number, BN, or two strong identifiers
   - `MEDIUM` — matched on domain+postal, phone+postal, or name+address
   - `LOW` — fuzzy name match only

3. WHEN confidence is HIGH THEN the system SHALL automatically merge the record into the
   existing canonical entity.

4. WHEN confidence is MEDIUM THEN the system SHALL create a `merge_candidate` record for
   operator review rather than automatically merging.

5. WHEN confidence is LOW THEN the system SHALL create a separate new canonical entity and
   record the candidate relationship for later review.

6. WHEN entity resolution creates or updates a canonical entity THEN the system SHALL
   preserve the `source_id`, `source_grain` (corporation / licence / event / registration),
   `source_record_id`, and `ingestion_run_id` on every contributing record.

7. WHEN sources operate at different grains THEN the system SHALL NOT flatten them. A
   corporation record and a licence record for the same real-world business SHALL be linked
   at the entity layer while preserving their distinct source grains.

8. WHEN the Winnipeg dataset is ingested THEN the adapter SHALL filter to non-closed statuses
   before entity resolution. Winnipeg is classified as Class B (event detection) — it SHALL
   NOT be used as a primary discovery master. (VR18: 84.7% of rows are "Closed (L)")

9. WHEN the Vancouver dataset is ingested THEN employee values SHALL be preserved at
   licence-grain. Multi-licence businesses with conflicting employee counts (17.7% of
   business names) SHALL be resolved to the most-recent issued licence at the entity layer —
   not by averaging or overwriting.

10. WHEN a record has neither a source-provided business name nor a stable business identifier
   THEN the system SHALL NOT create a canonical business solely to attach that source record;
   it SHALL retain the record as `UNRESOLVED` with `entity_id` NULL.

11. WHEN an unresolved record is reconsidered with later identity evidence THEN the system
   SHALL apply the existing match priority and confidence rules to the new business record.
   An unresolved source record SHALL be linked only when that record is explicitly referenced
   by its exact source key and source record ID; otherwise it SHALL remain `UNRESOLVED`.

12. WHEN a normalized record contains an explicit `source_references` entry THEN each reference
   SHALL identify exactly one prior source row by `source_key` and `source_record_id`. The
   system SHALL treat a successful exact reference as HIGH confidence and SHALL preserve the
   referenced row's original source, ingestion run, and raw payload.

---

### Requirement 6 — Business Events and Change Detection

**User Story:** As a sales analyst, I want to know which businesses are genuinely new in the
last 1 / 7 / 30 days, with the correct event type (incorporation vs. licence vs. registration),
so that I can prioritise outreach to newly-formed businesses before competitors do.

#### Acceptance Criteria

1. WHEN a new-business signal is detected THEN the system SHALL create a `business_event`
   record with: `entity_id`, `event_type`, `event_date`, `event_source`, `raw_value`,
   `ingestion_run_id`, `created_at`.

2. WHEN recording event types THEN the system SHALL use distinct values for each signal type.
   The following event types SHALL be supported and SHALL NOT be collapsed into one another:
   - `FEDERAL_INCORPORATION` — CBCA monthly HTML (VR03)
   - `PROVINCIAL_REGISTRATION` — Manitoba Companies Office weekly PDF (Incorporations category)
   - `MUNICIPAL_LICENCE_FIRST_ISSUE` — Calgary `first_iss_dt`, Edmonton `originalissuedate`,
     Saskatoon new-businesses file
   - `MUNICIPAL_LICENCE_RENEWAL` — most-recent issue date, Vancouver `issueddate` renewal
   - `LICENCE_STATUS_CHANGE` — Vancouver status field, Winnipeg status transitions
   - `REGISTRY_FILING` — Manitoba lifecycle events (amendments, revivals, dissolutions)
   - `NNI_REGISTRATION_RENEWAL` — NNI `effective_date` (2-year renewal cycle)
   - `MUNICIPAL_PERMIT_ISSUED` — Québec City permits, after the source record is linked to a canonical business
   - `BUSINESS_DISCOVERED` — first time a business appears in the pipeline from any source

3. WHEN querying for new businesses THEN the system SHALL support filtering by:
   - `new_today` (event_date = today)
   - `new_last_7_days`
   - `new_last_30_days`
   - `recently_changed` (any event in last 30 days)

4. WHEN an entity already exists and a source provides a new observation THEN the system
   SHALL create a `BUSINESS_UPDATED` event rather than silently updating the record.

5. WHEN a status change is detected (e.g. Active → Gone Out of Business in Vancouver) THEN
   the system SHALL create a `STATUS_CHANGED` event preserving old and new status values.

6. WHEN the incorporation date, business opening date, licence issue date, and registry
   registration date are all available for the same entity THEN the system SHALL preserve all
   four as distinct event records. The system SHALL NOT expose a single `business_created_at`
   field that conflates these events.

7. WHEN a source record has no canonical `entity_id` THEN the system SHALL retain it in the
   source layer without creating a `business_event`. After the same source record is linked
   to a canonical entity, the applicable event SHALL be created idempotently.

---

### Requirement 7 — Employee Classification

**User Story:** As a sales analyst, I want accurate, source-honest employee-size data so that
I can target businesses in specific size buckets without relying on fabricated or
estimated values.

#### Acceptance Criteria

1. WHEN an employee value is ingested THEN the system SHALL store:
   - `raw_employee_value` — exact string/value as returned by source (e.g. "385.0",
     "10 to 19", "500 plus", 2)
   - `employee_min` — lower bound of range, or exact count
   - `employee_max` — upper bound of range, or exact count, or NULL if unbounded (500+)
   - `employee_bucket` — canonical 9-bucket label: `1-4`, `5-9`, `10-19`, `20-49`,
     `50-99`, `100-199`, `200-499`, `500-999`, `1000+`
   - `employee_exact` — boolean: true if source provided a single integer, false if range
   - `employee_source` — source identifier
   - `employee_verified_at` — timestamp

2. WHEN the source provides an exact integer (e.g. Vancouver `numberofemployees = 42.0`)
   THEN the system SHALL derive: `employee_min=42`, `employee_max=42`, `employee_exact=true`,
   `employee_bucket=20-49`.

3. WHEN the source provides an explicit range string (e.g. BC Indigenous "10 to 19") THEN
   the system SHALL parse to: `employee_min=10`, `employee_max=19`, `employee_exact=false`,
   `employee_bucket=10-19`.

4. WHEN the source provides "500 plus" or "500+" THEN the system SHALL store:
   `employee_min=500`, `employee_max=NULL`, `employee_exact=false`,
   `employee_bucket=500+`. The system SHALL NOT fabricate a 500–999 / 1000+ split.

5. WHEN BC Indigenous provides "55 to 99" (distinct from "50 to 99") THEN the system SHALL
   preserve `raw_employee_value="55 to 99"` and derive `employee_min=55`, `employee_max=99`,
   `employee_bucket=50-99`. The ambiguity SHALL be flagged in a `data_quality_flag` rather
   than silently normalised.

6. WHEN no source provides employee data for a record THEN `employee_min`, `employee_max`,
   `employee_bucket` SHALL all be NULL. The system SHALL NOT estimate or infer employee count.

7. WHEN employee data is absent from Calgary, Edmonton, Saskatoon, Manitoba, Corporations
   Canada CSV, and Ontario sources (the majority of the discovery layer) THEN this is
   expected and correct. NULL employee data SHALL NOT be treated as a data error.

---

### Requirement 8 — Enrichment Architecture

**User Story:** As a data engineer, I want enrichment to be a layered, optional process that
adds fields to existing entities without blocking core business creation, so that the
pipeline produces useful records even for entities with no enrichment data.

#### Acceptance Criteria

1. WHEN a canonical entity is created THEN it SHALL be valid and queryable without any
   enrichment having run. Core entity creation SHALL NOT depend on enrichment.

2. WHEN enrichment is applied THEN each enriched field SHALL carry `enrichment_source`,
   `enriched_at`, `enrichment_confidence`, `enrichment_run_id`.

3. WHEN the Corporations Canada API is used for director enrichment THEN only federal CBCA
   corporations SHALL be submitted (corps with a valid `corp_number`). The adapter SHALL
   respect the 60 req/min rate limit. Director data SHALL be stored with role type `DIRECTOR`.

4. WHEN a person record is created from any enrichment source THEN the system SHALL store:
   `person_name`, `role_type`, `role_label_raw`, `source`, `confidence`, `source_url`,
   `verified_at`, `entity_id`.

5. WHEN storing person roles THEN the system SHALL use distinct role types and SHALL NOT
   collapse them: `DIRECTOR`, `OWNER`, `PRESIDENT`, `GENERAL_MANAGER`, `IT_CONTACT`,
   `PROCUREMENT_CONTACT`, `PRIMARY_CONTACT`, `OTHER`.

6. WHEN website phone extraction is used THEN the system SHALL apply CA NPA (North American
   Numbering Plan) area-code validation before storing any phone number. Phone numbers
   failing NPA validation SHALL be discarded or flagged — not stored as valid. Website-derived
   phones SHALL be stored with `source=website_crawl` and `confidence=low`.

7. WHEN website email extraction is attempted THEN the result SHALL be stored as optional
   enrichment only. Website email extraction SHALL NOT be a required pipeline step.
   (VR15+VR19: 0/30 emails found across 3 methods — insufficient yield for core dependency.)

8. WHEN website person/decision-maker extraction is attempted THEN it SHALL be treated as
   optional/experimental enrichment only. It SHALL NOT be a required pipeline step.
   (VR15+VR19: 0/30 valid person signals — insufficient yield for core dependency.)

9. WHEN BC OrgBook is queried for an entity THEN it SHALL be a targeted lookup using known
   BC Reg ID or business name. Bulk enumeration SHALL be rejected at the adapter level.

10. WHEN NNI data is present THEN the system SHALL treat it as conditional enrichment until
    NNI Regulations PDF terms are reviewed and confirmed commercially permissible.

---

### Requirement 9 — Data Quality and Confidence Scoring

**User Story:** As a sales analyst, I want transparent, component-based quality scores for
every business record, so that I can filter for sales-ready leads with confidence and
understand exactly why a record is or is not sales-ready.

#### Acceptance Criteria

1. WHEN a canonical entity is scored THEN the system SHALL compute individual confidence
   components rather than a single opaque score:
   - `identity_confidence` — presence and consistency of name, legal form, corp/BN number
   - `address_confidence` — completeness of address, postal code validity, coordinate presence
   - `phone_confidence` — presence, CA NPA validation, source reliability
   - `email_confidence` — presence, format validity, source reliability
   - `employee_confidence` — presence of employee data, whether exact or range
   - `industry_confidence` — presence of NAICS or mappable industry code
   - `contact_confidence` — presence of any person/director record
   - `recency_confidence` — time since last verified observation
   - `source_reliability` — weighted by source class (A > B > C) and fill rates

2. WHEN all confidence components exist THEN the system SHALL derive a composite
   `lead_quality_score` from the components. The derivation formula SHALL be documented
   and deterministic — not a black box.

3. WHEN a record meets the minimum sales-ready threshold THEN the system SHALL flag it as
   `sales_ready = true`. The minimum threshold is: `business_name` + `address` + `province`
   + `status = ACTIVE` + at least one of (`phone` | `email` | `website` | `director_name`).

4. WHEN a data quality issue is detected (e.g. "55 to 99" vs "50 to 99" anomaly, ODBus
   record-count delta, Vancouver multi-licence employee conflict) THEN the system SHALL store
   a `data_quality_flag` record with: `entity_id`, `flag_type`, `flag_detail`,
   `source_id`, `detected_at`, `resolved` (boolean).

5. WHEN province coverage is absent (NS, NB confirmed gaps; ON/QC partial) THEN the system
   SHALL expose a `province_coverage_gap` flag on affected entities so that reporting can
   distinguish "no source for this province" from "business has no data."

---

### Requirement 10 — Scheduling and Incremental Processing

**User Story:** As a system operator, I want each source to run on its own appropriate
schedule with full retry, failure logging, and idempotency guarantees, so that the pipeline
can run continuously without manual intervention.

#### Acceptance Criteria

1. WHEN a source ingestion job is defined THEN it SHALL have a `schedule_expression` that
   reflects the source's actual update frequency:
   - Calgary → daily (Socrata, confirmed daily updates)
   - Edmonton → daily (Socrata, confirmed daily updates)
   - Vancouver → daily (OpenDataSoft, confirmed daily updates)
   - Winnipeg → daily (Socrata, event-only classification)
   - Corporations Canada CSV → weekly (typically updated daily but refresh weekly is sufficient)
   - Corporations Canada monthly HTML → monthly (VR03 — monthly snapshot)
   - Manitoba weekly PDF → weekly (14 weekly PDFs confirmed available)
   - Saskatoon all-biz → weekly
   - Saskatoon new-biz → weekly
   - Ontario Select Licence → monthly (CKAN, monthly cadence)
   - Ontario regulated-sector sources → monthly
   - Montréal Commercial Premises → annually (dataset updated Dec 2025)
   - Québec City Permits → weekly (confirmed weekly update)
   - BC Indigenous → monthly (dataset-level Jan 2026 refresh)
   - Corporations Canada API director enrichment → event-triggered (on new CBCA corp only)
   - BC OrgBook → event-triggered (on new BC entity only)

2. WHEN a job is executed THEN it SHALL be idempotent — running the same job twice SHALL NOT
   create duplicate records.

3. WHEN a job fails THEN the system SHALL record the failure in `ingestion_run` with
   `run_status = FAILED`, `error_message`, and `retry_count`. The job SHALL be retried
   according to a configurable backoff policy.

4. WHEN a job completes THEN the system SHALL compute and store: records fetched, records
   parsed, records normalised, records matched to existing entity, records creating new
   entity, records flagged for review.

5. WHEN incremental ingestion is supported (Calgary, Edmonton, Vancouver, Winnipeg have
   date fields) THEN the adapter SHALL only fetch records newer than `last_successful_run_at`
   where the source supports date-range filtering.

6. WHEN n8n is used as the orchestration layer THEN Python service endpoints SHALL be called
   via HTTP from n8n workflow nodes. All domain-heavy processing (normalisation, entity
   resolution, confidence scoring) SHALL execute in Python services — not in n8n Code nodes.

7. WHEN a source is temporarily unavailable (e.g. NNI HTTP 0 in VR18 — confirmed transient)
   THEN the failure SHALL be logged and the prior successful ingestion data SHALL remain
   active in the canonical layer. The system SHALL NOT deactivate records on a single
   source failure.

---

### Requirement 11 — API

**User Story:** As a developer or sales analyst, I want a clean REST API that exposes the
canonical business data with filtering, pagination, full history and source transparency, so
that dashboards, exports and integrations can be built on top of it.

#### Acceptance Criteria

1. THE system SHALL expose the following endpoints:
   - `GET /businesses` — paginated, filterable list
   - `GET /businesses/{id}` — full canonical entity with all enrichment
   - `GET /businesses/{id}/history` — all `field_observation` and `business_event` records
   - `GET /businesses/{id}/sources` — all contributing source records
   - `GET /events` — paginated event stream filterable by `event_type`, `province`,
     `date_range`
   - `GET /sources` — source registry with last run status
   - `GET /stats` — pipeline coverage statistics by province, source, field fill rate
   - `GET /export` — CSV/JSON export with applied filters

2. WHEN `GET /businesses` is called THEN it SHALL support filters:
   `province`, `city`, `naics_sector`, `employee_bucket`, `status`, `sales_ready`,
   `has_phone`, `has_email`, `has_website`, `has_director`, `new_since` (date),
   `event_type`, `source_id`, `dnc`.

3. WHEN a response is returned THEN it SHALL include pagination metadata: `total`, `page`,
   `page_size`, `next_cursor`.

4. WHEN `GET /businesses/{id}/history` is called THEN the response SHALL include all
   `field_observation` records grouped by field, showing value changes over time with source
   attribution.

5. WHEN the API is deployed THEN all endpoints SHALL be documented via OpenAPI / Swagger.

---

### Requirement 12 — Dashboard

**User Story:** As a sales manager, I want a web dashboard that lets me search, filter and
export Canadian business leads with full control over quality thresholds and province/industry
filters, so that my team can find decision-ready prospects without needing API access.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN it SHALL display: total businesses, sales-ready count,
   new businesses last 30 days, province coverage gaps.

2. WHEN a user applies filters THEN the dashboard SHALL support: province, city, industry
   (NAICS sector), employee bucket, status, new business (date range), has phone, has email,
   has website, has decision-maker, DNC flag, confidence threshold.

3. WHEN a user views a business detail THEN it SHALL show:
   - Identity (name, legal form, corp number, BN)
   - Contact (phone, email, website)
   - Employees (bucket, exact count if available, source)
   - Industry (NAICS, source industry string)
   - People (directors, contacts with role types)
   - Events (timeline of all business events with event types)
   - Sources (list of contributing sources)
   - History (field-level change history with provenance)

4. WHEN a user exports results THEN the dashboard SHALL produce a CSV or JSON file
   respecting the current filter state.

5. WHEN a DNC flag exists on a record THEN it SHALL be displayed prominently and the record
   SHALL be excluded from exports by default unless explicitly included.

---

### Requirement 13 — DNC and Sales Layer

**User Story:** As a sales manager, I want DNC flags and lead qualification state to be
managed separately from source truth, so that sales-process state never corrupts the
underlying canonical data.

#### Acceptance Criteria

1. WHEN a DNC flag is set on a business THEN it SHALL be stored in a separate `lead_flag`
   table and SHALL NOT modify any field in the canonical `business` entity or any
   `field_observation` record.

2. WHEN lead qualification state changes (e.g. contacted, qualified, disqualified) THEN those
   changes SHALL be stored in the sales layer tables only — not in the canonical entity.

3. WHEN a DNC-flagged business appears in an export THEN it SHALL be excluded by default.
   Inclusion SHALL require an explicit opt-in parameter.

4. WHEN computing `lead_quality_score` THEN the DNC flag SHALL be factored as a disqualifier
   but SHALL NOT be stored in the quality model — it is a sales-layer concern.

---

### Requirement 14 — Deployment and Observability

**User Story:** As a system operator, I want the full pipeline deployable with a single
`docker compose up`, with structured logging, health checks and job-status visibility, so
that I can operate and debug the system without manual infrastructure management.

#### Acceptance Criteria

1. WHEN the system is deployed THEN it SHALL run entirely in Docker Compose with services:
   `api` (FastAPI), `worker` (Python normalisation/entity-resolution services),
   `scheduler` (n8n self-hosted), `db` (PostgreSQL), `frontend` (Next.js).

2. WHEN n8n is used as the orchestration layer THEN it SHALL be self-hosted within the Docker
   Compose stack. No external n8n cloud dependency.

3. WHEN any service produces a log event THEN it SHALL be structured JSON including:
   `timestamp`, `level`, `service`, `run_id`, `source_id`, `entity_id` (where applicable),
   `message`.

4. WHEN a source ingestion job fails THEN the failure SHALL be visible in both the n8n
   workflow UI and the `GET /sources` API endpoint.

5. WHEN `GET /sources` is called THEN each source SHALL show: `last_run_at`,
   `last_run_status`, `last_run_record_count`, `next_scheduled_run`.

6. WHEN the system is started fresh THEN database migrations SHALL run automatically via
   Alembic before the API starts accepting requests.

7. WHEN environment-specific configuration is needed THEN it SHALL be supplied via
   environment variables in a `.env` file. No secrets SHALL be hardcoded.

---

### Requirement 15 — Compliance Constraints (Non-Functional)

**User Story:** As a legal/compliance stakeholder, I want the pipeline to respect all source
licence terms and automation constraints that were identified during the validation phase,
so that the system does not create legal exposure.

#### Acceptance Criteria

1. THE system SHALL NOT ingest any individual business records from Statistics Canada — only
   aggregate benchmark data. Individual-business data from the Business Register is
   confidential under the Statistics Act.

2. THE system SHALL NOT perform bulk enumeration of BC OrgBook. The 10-page limit enforced
   by OrgBook exists specifically to prevent bulk extraction.

3. THE system SHALL NOT use Quebec REQ (Registre des entreprises du Québec) for any
   automated data extraction. REQ restricts non-commercial use.

4. THE system SHALL NOT ingest NL CADO data. The disclaimer explicitly prohibits use in a
   value-added product.

5. THE system SHALL NOT automate PEI OCBR. Authentication is required and no valid
   unauthenticated path exists.

6. THE system SHALL NOT scrape or bulk-copy NB corporate registry search results.

7. WHEN NNI data is processed THEN it SHALL be flagged as `terms_status = UNRESOLVED` until
   the NNI Regulations PDF is reviewed and a confirmed legal basis is established.

8. WHEN the Corporations Canada API is called THEN the `user-key` header SHALL be present
   on every request and the 60 req/min limit SHALL be enforced by the adapter.

9. THE system SHALL respect `robots.txt` for any source that publishes one. Adapters for
   sources with known `robots.txt` restrictions (e.g. Airmec in VR19) SHALL check and honour
   the exclusion list.

10. ALL sources used in production SHALL be licensed for commercial use. The confirmed
    commercial-use licences are: OGL-Canada (federal), OGL-Ontario (ON sources), OGL-BC (BC
    Indigenous), OGL-Vancouver (Vancouver), CC-BY 4.0 (Montréal, Québec City), Calgary Open
    Data, Edmonton Open Data, Saskatoon Open Data, Winnipeg Open Data.
