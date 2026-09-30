# Design Document
# Canada B2B Business Data Pipeline

**Version:** 1.0
**Date:** 2026-09-27
**Status:** Architecture Phase — pre-implementation
**Based on:** VR01–VR20 validated source landscape (frozen). Requirements document v1.0.

---

## Overview

This document defines the complete technical architecture for the Canada B2B Business Data
Pipeline. The system ingests business records from 17+ validated open-data sources across
Canada, normalises them, resolves them to canonical entities, enriches them, and exposes
them via a REST API and web dashboard for telecom sales operations.

The architecture is driven entirely by the validated source landscape. Technology selections
follow from the problem structure — not the other way around.

**Core architectural principle:** No source overwrites another source. Every observation is
traceable to its origin. The canonical entity is a synthesis of observations — not a
replacement for them.

---

## Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        n8n Orchestration                       │
│  (schedules, triggers, HTTP calls to Python services,          │
│   retries, error routing, source-specific workflows)           │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP
            ┌───────────────┼───────────────┐
            ↓               ↓               ↓
┌──────────────────┐ ┌─────────────┐ ┌────────────────┐
│  Ingestion       │ │ Normalise   │ │ Entity         │
│  Service         │ │ Service     │ │ Resolution     │
│  (fetch + parse) │ │             │ │ Service        │
└────────┬─────────┘ └──────┬──────┘ └───────┬────────┘
         │                  │                │
         └──────────────────┼────────────────┘
                            ↓
                  ┌─────────────────┐
                  │   PostgreSQL    │
                  │ (canonical DB)  │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
       ┌──────────┐ ┌──────────┐ ┌───────────┐
       │Enrichment│ │ Events   │ │ Quality   │
       │ Service  │ │ Service  │ │ Service   │
       └──────────┘ └──────────┘ └───────────┘
                           │
                  ┌────────┴────────┐
                  │   FastAPI       │
                  │   REST API      │
                  └────────┬────────┘
                           │
                  ┌────────┴────────┐
                  │  Next.js        │
                  │  Dashboard      │
                  └─────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Orchestration | n8n (self-hosted, Docker) | Multi-source scheduling, visual workflows, built-in retry/error routing, HTTP/file/API nodes, aligns with role's automation focus |
| Domain processing | Python 3.11+ | Normalisation, entity resolution, confidence scoring — complex stateful logic that must not live in n8n Code nodes |
| Persistence | PostgreSQL 16 | Relational integrity, JSONB for raw payloads, PostGIS-ready for future geo, mature, auditable |
| ORM + migrations | SQLAlchemy 2.x + Alembic | Pythonic schema management, migration versioning |
| Validation | Pydantic v2 | Request/response models, field validation, data contracts between services |
| API | FastAPI | Async, OpenAPI auto-generation, pairs naturally with Pydantic |
| HTTP client | httpx | Async-capable, used in Python services for API adapters |
| HTML parsing | BeautifulSoup4 + lxml | Proven in probes (VR03, VR15) |
| PDF parsing | pdfplumber | Proven in Manitoba weekly PDF probe (VR08) |
| Excel parsing | openpyxl | Proven in Saskatoon XLSX probe (VR07) |
| Fuzzy matching | RapidFuzz | Entity resolution — faster than fuzzywuzzy, C extension |
| Browser automation | Playwright | Only where HTTP fails (NS RJSC if unblocked, deferred sources) |
| Frontend | Next.js 14 (App Router) | SSR, API routes, good ecosystem |
| UI components | Tailwind CSS + shadcn/ui | Rapid, accessible component assembly |
| Containers | Docker Compose | Single-command local + production deployment |
| Reverse proxy | Nginx | Routes /api → FastAPI, / → Next.js, /n8n → n8n |
| Testing | pytest + httpx (async test client) | Unit + integration tests for Python services |
| Logging | Python structlog (JSON output) | Structured logs queryable in production |
| Queue/cache | Redis (deferred) | Not required at launch — introduce if rate-limit buffering or caching becomes necessary |

---

## Components and Interfaces

### 1. Source Registry

Stored in PostgreSQL `source` table. n8n reads this table to determine which adapters are
enabled, their schedules, and their configuration.

Each row represents one data source:

```
source
├── source_id          UUID PK
├── source_key         VARCHAR UNIQUE  -- e.g. "corporations_canada_csv"
├── source_name        VARCHAR
├── adapter_class      VARCHAR         -- e.g. "CorporationsCanadaCSVAdapter"
├── province           CHAR(2)         -- NULL = federal
├── source_type        ENUM(CSV, JSON, API, HTML, PDF, GeoJSON, XLSX)
├── source_class       ENUM(A, B, C, D)
├── licence            VARCHAR
├── schedule_cron      VARCHAR         -- cron expression
├── is_enabled         BOOLEAN
├── rate_limit_rpm     INTEGER         -- NULL = no limit
├── base_url           TEXT
├── auth_header_key    VARCHAR         -- NULL if no auth
├── terms_status       ENUM(CLEARED, UNRESOLVED, BLOCKED, NOT_SUITABLE)
├── notes              TEXT
├── created_at         TIMESTAMPTZ
└── updated_at         TIMESTAMPTZ
```

### 2. Source Adapters (Python Ingestion Service)

Each adapter implements a common interface:

```python
class SourceAdapter(ABC):
    source_key: str

    @abstractmethod
    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch raw data from source. Returns artifact with payload + metadata."""

    @abstractmethod
    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        """Parse raw artifact into list of raw records."""

    @abstractmethod
    def validate(self, records: list[RawRecord]) -> ValidationResult:
        """Validate parsed records against expected schema."""

    @abstractmethod
    def get_metadata(self) -> SourceMetadata:
        """Return source configuration metadata."""
```

`RawArtifact`:
```python
@dataclass
class RawArtifact:
    source_key: str
    ingestion_run_id: UUID
    retrieval_url: str
    retrieval_timestamp: datetime
    http_status: int | None
    content_type: str | None
    checksum_sha256: str
    payload_ref: str      # filepath or inline JSONB reference
    source_version: str | None   # e.g. dataset date if available
```

`RawRecord`:
```python
@dataclass
class RawRecord:
    source_key: str
    ingestion_run_id: UUID
    source_record_id: str    # source-provided ID or row hash
    raw_payload: dict        # original parsed row as dict
    source_grain: SourceGrain  # CORPORATION | LICENCE | EVENT | REGISTRATION | ESTABLISHMENT
```

Adapter implementations:

| Adapter | Source | Format | Key fields |
|---|---|---|---|
| `CorporationsCanadaCSVAdapter` | CBCA active CSV | CSV | corp_number, BN, name, address, status |
| `CorporationsCanadaHTMLAdapter` | Monthly incorporations | HTML | name, jurisdiction, date (VR03) |
| `CorporationsCanadaAPIAdapter` | Directors API | REST JSON | directors[].firstName/lastName/serviceAddress |
| `CalgaryAdapter` | Calgary licences | Socrata CSV | name, address, first_iss_dt, coordinates |
| `EdmontonAdapter` | Edmonton licences | Socrata CSV | name, address, originalissuedate |
| `VancouverAdapter` | Vancouver licences | OpenDataSoft CSV | name, address, status, issueddate, numberofemployees |
| `WinnipegAdapter` | Winnipeg licences | Socrata CSV | trade_name, address, status (Class B only) |
| `ManitobaWeeklyPDFAdapter` | MB Companies Office | PDF | company_name, file_no, category, registered_office |
| `SaskatoonAllBizAdapter` | Saskatoon all-biz | XLSX | name, address, NAICS |
| `SaskatoonNewBizAdapter` | Saskatoon new-biz | XLSX | name, address, NAICS, Business_License_Id |
| `OntarioSelectLicenceAdapter` | ON Select Licence | CKAN CSV | name, address, phone, email, website, licence_type |
| `OntarioRegulatedAdapters` (×6) | Dairy/Tobacco/Fuel/Meat/CSBIF | CKAN CSV | name, address, phone, licence_number |
| `MontrealCommercialPremisesAdapter` | Montréal premises | CSV/GeoJSON | name, address, SCIAN, category, coordinates |
| `QuebecCityPermitsAdapter` | QC City permits | CSV | permit_number, issue_date, property_info |
| `BCIndigenousAdapter` | BC Indigenous listings | Direct CSV | name, phone, email, website, contact_name, employee_range |
| `BCOrgBookAPIAdapter` | BC OrgBook | REST JSON | legal_name, status, registration_date, credential_history |
| `NNIAdapter` | NNI Nunavut | Drupal HTML | name, address, phone, email, contact_name, employee_count, sectors |

### 3. Normalisation Service

Stateless Python service. Receives a `RawRecord`, returns a `NormalisedRecord`.

Normalisation functions:

```python
# Business name
def normalise_business_name(raw: str) -> str:
    # lowercase → expand abbreviations (LTD→LIMITED, etc.) → remove punctuation variants
    # return normalised form; preserve raw_name separately

# Phone — E.164 + CA NPA validation
def normalise_phone(raw: str) -> PhoneResult:
    # strip formatting → validate 10-digit → check NPA against CA area code list
    # return: normalised_phone (E.164), phone_valid (bool), raw_phone

# Address
def normalise_address(raw_street: str, raw_city: str, raw_province: str, raw_postal: str) -> AddressResult:
    # standardise street type abbreviations (St→Street, Ave→Avenue, etc.)
    # normalise unit/suite formats
    # uppercase province code
    # format postal as "A1A 1A1"
    # validate postal format

# Email
def normalise_email(raw: str) -> EmailResult:
    # treat "N/A" → NULL (Ontario Select Licence)
    # lowercase domain portion
    # validate RFC 5321

# Employee value
def normalise_employee(raw: str | int | float) -> EmployeeResult:
    # see Requirement 7 rules
    # returns: raw_employee_value, employee_min, employee_max,
    #          employee_bucket, employee_exact, data_quality_flag (if ambiguous)

# NAICS
def normalise_naics(raw: str) -> NAICSResult:
    # preserve source_naics
    # map to 2-digit naics_sector where unambiguous
    # do NOT infer if source doesn't provide

# Status
def normalise_status(raw: str, source_key: str) -> StatusResult:
    # map source-specific strings to canonical: ACTIVE/INACTIVE/SUSPENDED/DISSOLVED/PENDING/UNKNOWN
    # preserve raw_status

# Date
def normalise_date(raw: str) -> datetime | None:
    # parse various formats → ISO 8601 UTC
```

`NormalisedRecord` schema mirrors source fields but with both `raw_*` and `normalised_*`
variants for every field that requires normalisation.

When one source record explicitly identifies a record from another source, its normalized
payload may carry `source_references: [{source_key, source_record_id}]`. These references are
exact provenance links, not inferred matches; unresolved rows must not be linked from address
or fuzzy similarity alone.

```python
class SourceRecordReference(BaseModel):
    source_key: str
    source_record_id: str

class NormalisedRecord(BaseModel):
    # existing normalized business/source fields...
    source_references: list[SourceRecordReference] = []
```

### 4. Entity Resolution Service

The most complex Python service. Operates on `NormalisedRecord` inputs, produces
entity-resolution decisions.

#### Resolution Pipeline

```
NormalisedRecord
      │
      ▼
┌─────────────────────────────────────────┐
│  Step 1: Strong Identifier Lookup        │
│  corp_number → exact match               │
│  business_number_bn → exact match        │
│  source_licence_id (within same source)  │
└────────────────┬────────────────────────┘
                 │ no match
                 ▼
┌─────────────────────────────────────────┐
│  Step 2: Composite Deterministic Match   │
│  domain + postal_code                    │
│  phone + postal_code                     │
│  normalised_name + normalised_address    │
└────────────────┬────────────────────────┘
                 │ no match
                 ▼
┌─────────────────────────────────────────┐
│  Step 3: Fuzzy Match                     │
│  RapidFuzz token_sort_ratio on           │
│  normalised_name + postal_code           │
│  threshold: configurable (default 88)    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Confidence Assignment                   │
│  HIGH   → corp_number, BN, 2x strong    │
│  MEDIUM → domain+postal, phone+postal,  │
│           name+address exact            │
│  LOW    → fuzzy only                    │
└────────────────┬────────────────────────┘
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
    HIGH       MEDIUM      LOW
  auto-merge  candidate  new entity
              queue
```

#### Merge Behaviour

- HIGH: merge immediately → update canonical entity + append `field_observation` records
- MEDIUM: insert into `merge_candidate` table with both entity_ids → operator review queue
- LOW: create new canonical entity → link as candidate via `merge_candidate` with `auto_resolved=false`
- No match with insufficient identity (no source-provided business name or stable business identifier): retain the source record with `entity_id=NULL` and `resolution_status=UNRESOLVED`; do not create a canonical business.
- No match with sufficient identity: create a new canonical business with `resolution_status=NEW`.

No ambiguous record is silently merged. Every MEDIUM and LOW decision is visible to operators.

#### Unresolved Source Records — Decision Record (2026-09-28)

**Previous assumption:** the resolver's no-match branch created a new canonical business, while
`business_event.entity_id` was required. This did not account for valid source observations
that do not identify a business, as demonstrated by the validated Québec City municipal
permit feed. Its permit number, date, address, and property details identify a permit, not a
business.

**Decision:** source observations exist independently of canonical businesses. When a record
has neither a source-provided business name nor a stable business identifier, retain its raw
and normalised payload in `source_record`, leave `entity_id` NULL, and set
`resolution_status=UNRESOLVED`. Do not discard the observation or fabricate a business.

When a later normalized record resolves to a canonical entity and explicitly references an
unresolved row by its exact `source_key` and `source_record_id`, update that existing
`source_record` link and preserve its original source/run provenance. Do not infer cross-source
links from address or fuzzy similarity alone. Create applicable `field_observation` and
`business_event` rows only after the canonical entity link exists. Event creation must be
idempotent. If there is no exact reference, the record remains unresolved.

This is a generic provenance and entity-resolution rule, not a Québec-specific exception.
`business_event.entity_id` remains required; unresolved source records do not produce
`business_event` rows until they are linked to a business.

### 5. Canonical Data Model (PostgreSQL Schema)

#### Core Entity Tables

```sql
-- Pipeline-generated canonical business entity
CREATE TABLE business (
    entity_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name      VARCHAR(500) NOT NULL,
    legal_name          VARCHAR(500),
    trade_name          VARCHAR(500),
    entity_type         VARCHAR(100),   -- CORPORATION | SOLE_PROPRIETOR | PARTNERSHIP | OTHER
    province            CHAR(2),
    status              VARCHAR(20),    -- ACTIVE | INACTIVE | SUSPENDED | DISSOLVED | PENDING | UNKNOWN
    sales_ready         BOOLEAN DEFAULT false,
    lead_quality_score  SMALLINT,       -- 0-100 derived composite
    province_gap_flag   BOOLEAN DEFAULT false,
    first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_verified_at    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One business can have multiple locations (multi-location businesses)
CREATE TABLE business_location (
    location_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    address_line1       VARCHAR(300),
    address_line2       VARCHAR(100),
    city                VARCHAR(100),
    province            CHAR(2),
    postal_code         CHAR(7),
    country             CHAR(2) DEFAULT 'CA',
    latitude            NUMERIC(10,7),
    longitude           NUMERIC(10,7),
    raw_address         TEXT,
    location_type       VARCHAR(50),    -- REGISTERED | OPERATING | MAILING
    is_primary          BOOLEAN DEFAULT false,
    source_id           UUID REFERENCES source(source_id),
    ingestion_run_id    UUID REFERENCES ingestion_run(run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cross-source identifiers for an entity
CREATE TABLE business_identifier (
    identifier_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    id_type             VARCHAR(50),    -- CORP_NUMBER | BN | LICENCE_ID | BC_REG_ID | NNI_NUMBER | OTHER
    id_value            VARCHAR(200) NOT NULL,
    source_id           UUID REFERENCES source(source_id),
    is_primary          BOOLEAN DEFAULT false,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(id_type, id_value)
);

-- Persons associated with a business (directors, contacts, owners)
CREATE TABLE person (
    person_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    person_name         VARCHAR(300) NOT NULL,
    role_type           VARCHAR(50),    -- DIRECTOR | OWNER | PRESIDENT | GENERAL_MANAGER |
                                        -- IT_CONTACT | PROCUREMENT_CONTACT | PRIMARY_CONTACT | OTHER
    role_label_raw      VARCHAR(200),   -- source-provided role string
    source_id           UUID REFERENCES source(source_id),
    source_url          TEXT,
    confidence          VARCHAR(10),    -- HIGH | MEDIUM | LOW
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Contact fields (phone, email, website) with provenance
CREATE TABLE business_contact (
    contact_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    contact_type        VARCHAR(20),    -- PHONE | EMAIL | WEBSITE
    raw_value           TEXT NOT NULL,
    normalised_value    TEXT,
    is_valid            BOOLEAN,
    source_id           UUID REFERENCES source(source_id),
    enrichment_source   VARCHAR(100),   -- website_crawl | source_provided | etc.
    confidence          VARCHAR(10),
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### Employee Data Table

```sql
CREATE TABLE business_employee_data (
    employee_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    raw_employee_value  TEXT NOT NULL,          -- exactly as source returned it
    employee_min        INTEGER,
    employee_max        INTEGER,                 -- NULL if unbounded (500+)
    employee_bucket     VARCHAR(20),             -- 1-4|5-9|10-19|20-49|50-99|100-199|200-499|500-999|1000+|500+
    employee_exact      BOOLEAN NOT NULL DEFAULT false,
    employee_source     UUID REFERENCES source(source_id),
    source_record_id    UUID REFERENCES source_record(record_id),
    data_quality_flag   TEXT,                   -- non-null if anomaly detected (e.g. "55-99 ambiguity")
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### Industry / NAICS Table

```sql
CREATE TABLE business_industry (
    industry_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    source_naics        VARCHAR(20),            -- source-provided NAICS code
    naics_sector        CHAR(2),                -- 2-digit sector, mapped where unambiguous
    source_industry_str TEXT,                   -- raw industry/sector string from source
    industry_source     UUID REFERENCES source(source_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### Provenance Tables

```sql
-- Every ingestion job run
CREATE TABLE ingestion_run (
    run_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id               UUID NOT NULL REFERENCES source(source_id),
    run_started_at          TIMESTAMPTZ NOT NULL,
    run_completed_at        TIMESTAMPTZ,
    run_status              VARCHAR(20),    -- RUNNING | COMPLETED | FAILED | PARTIAL
    source_url              TEXT,
    retrieval_timestamp     TIMESTAMPTZ,
    source_version_or_date  VARCHAR(100),
    checksum_sha256         VARCHAR(64),
    record_count_raw        INTEGER,
    record_count_normalised INTEGER,
    record_count_new        INTEGER,
    record_count_updated    INTEGER,
    record_count_flagged    INTEGER,
    error_message           TEXT,
    retry_count             SMALLINT DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Raw record as received from source
CREATE TABLE source_record (
    record_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id           UUID NOT NULL REFERENCES source(source_id),
    ingestion_run_id    UUID NOT NULL REFERENCES ingestion_run(run_id),
    source_record_id    VARCHAR(200),       -- source-provided row ID or hash
    source_grain        VARCHAR(30),        -- CORPORATION|LICENCE|EVENT|REGISTRATION|ESTABLISHMENT
    raw_payload         JSONB NOT NULL,     -- original row as parsed
    normalised_payload  JSONB,              -- post-normalisation
    entity_id           UUID REFERENCES business(entity_id),   -- NULL until resolved
    resolution_status   VARCHAR(20),        -- PENDING | MATCHED | NEW | CANDIDATE | UNRESOLVED | SKIPPED
    resolution_confidence VARCHAR(10),      -- HIGH | MEDIUM | LOW | NULL
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every field value observed from any source — the provenance spine
CREATE TABLE field_observation (
    observation_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    field_name          VARCHAR(100) NOT NULL,   -- e.g. "canonical_name", "phone", "address_line1"
    raw_value           TEXT,
    normalised_value    TEXT,
    source_id           UUID NOT NULL REFERENCES source(source_id),
    ingestion_run_id    UUID NOT NULL REFERENCES ingestion_run(run_id),
    source_record_id    UUID REFERENCES source_record(record_id),
    observed_at         TIMESTAMPTZ NOT NULL,
    confidence          VARCHAR(10),
    is_current          BOOLEAN DEFAULT true,    -- false when superseded
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### Event and History Tables

```sql
-- All business lifecycle events
CREATE TABLE business_event (
    event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    event_type          VARCHAR(50) NOT NULL,
    -- FEDERAL_INCORPORATION | PROVINCIAL_REGISTRATION | MUNICIPAL_LICENCE_FIRST_ISSUE
    -- MUNICIPAL_LICENCE_RENEWAL | LICENCE_STATUS_CHANGE | REGISTRY_FILING
    -- NNI_REGISTRATION_RENEWAL | MUNICIPAL_PERMIT_ISSUED
    -- BUSINESS_DISCOVERED | BUSINESS_UPDATED
    -- STATUS_CHANGED | LOCATION_ADDED | LOCATION_CHANGED | NAME_CHANGED
    -- LICENCE_ISSUED | LICENCE_EXPIRED
    event_date          DATE,
    event_source        UUID REFERENCES source(source_id),
    raw_value           TEXT,               -- source raw value for this event
    previous_value      TEXT,               -- for STATUS_CHANGED, NAME_CHANGED etc.
    ingestion_run_id    UUID REFERENCES ingestion_run(run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Business status transitions over time
CREATE TABLE business_status_history (
    history_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    old_status          VARCHAR(20),
    new_status          VARCHAR(20) NOT NULL,
    changed_at          TIMESTAMPTZ NOT NULL,
    source_id           UUID REFERENCES source(source_id),
    ingestion_run_id    UUID REFERENCES ingestion_run(run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Merge candidates for operator review
CREATE TABLE merge_candidate (
    candidate_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id_a         UUID NOT NULL REFERENCES business(entity_id),
    entity_id_b         UUID NOT NULL REFERENCES business(entity_id),
    confidence          VARCHAR(10) NOT NULL,   -- MEDIUM | LOW
    match_method        VARCHAR(100),           -- what triggered the candidate
    match_score         NUMERIC(5,2),
    auto_resolved       BOOLEAN DEFAULT false,
    resolved_by         VARCHAR(100),
    resolved_at         TIMESTAMPTZ,
    resolution          VARCHAR(20),            -- MERGED | REJECTED | DEFERRED
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### Quality and Sales Layer Tables

```sql
-- Component confidence scores per entity
CREATE TABLE business_quality_score (
    score_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id               UUID NOT NULL REFERENCES business(entity_id),
    identity_confidence     SMALLINT,   -- 0-100
    address_confidence      SMALLINT,
    phone_confidence        SMALLINT,
    email_confidence        SMALLINT,
    employee_confidence     SMALLINT,
    industry_confidence     SMALLINT,
    contact_confidence      SMALLINT,
    recency_confidence      SMALLINT,
    source_reliability      SMALLINT,
    lead_quality_score      SMALLINT,   -- derived composite 0-100
    scored_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(entity_id)
);

-- Data quality flags (anomalies, known issues)
CREATE TABLE data_quality_flag (
    flag_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID REFERENCES business(entity_id),
    source_id           UUID REFERENCES source(source_id),
    flag_type           VARCHAR(100),   -- EMPLOYEE_RANGE_AMBIGUITY | MULTI_LICENCE_CONFLICT | etc.
    flag_detail         TEXT,
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved            BOOLEAN DEFAULT false,
    resolved_at         TIMESTAMPTZ
);

-- Province coverage gaps (first-class flags)
CREATE TABLE province_coverage_gap (
    gap_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    province            CHAR(2) NOT NULL UNIQUE,
    gap_level           VARCHAR(20),    -- CONFIRMED | PARTIAL | DEFERRED
    reason              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Sales/DNC layer — completely separate from canonical data
CREATE TABLE lead_flag (
    flag_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES business(entity_id),
    flag_type           VARCHAR(50),    -- DNC | CONTACTED | QUALIFIED | DISQUALIFIED | IN_PROGRESS
    flag_value          TEXT,
    set_by              VARCHAR(100),
    set_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes               TEXT
);
```

#### Pre-populated Province Gap Records

At schema migration time, insert known gaps:

```sql
INSERT INTO province_coverage_gap (province, gap_level, reason) VALUES
  ('NS', 'CONFIRMED', 'RJSC WAF-blocked; no open-data alternative found (VR20)'),
  ('NB', 'CONFIRMED', 'No municipal open-data source found (VR20)'),
  ('PE', 'CONFIRMED', 'OCBR auth required — NOT SUITABLE'),
  ('NL', 'CONFIRMED', 'CADO explicitly prohibits value-added use'),
  ('ON', 'PARTIAL', 'No general discovery source; regulated-sector enrichment only (VR20)'),
  ('QC', 'PARTIAL', 'Montréal city only; no provincial master (VR20)'),
  ('YT', 'DEFERRED', 'Supplier Directory 403; OGL confirmed; manual download needed'),
  ('NT', 'DEFERRED', 'CROS URL confirmed; basic info free; browser-only access');
```

---

## n8n Workflow Design

n8n is the orchestration layer only. It does not contain business logic.

### Workflow Topology

```
n8n Workflow: ingest-source
  ├── Trigger: Cron (per source schedule)
  ├── Node: Read source config from PostgreSQL
  ├── Node: POST /ingestion/start → Ingestion Service
  │     returns: run_id
  ├── Node: POST /ingestion/fetch → Ingestion Service
  │     returns: raw_artifact_ref
  ├── Node: POST /normalise → Normalisation Service
  │     returns: normalised_record_ids[]
  ├── Node: POST /resolve → Entity Resolution Service
  │     returns: resolution_results[]
  ├── Node: POST /events/detect → Events Service
  │     returns: events_created
  ├── Node: POST /quality/score → Quality Service
  │     returns: scores_updated
  ├── Node: POST /ingestion/complete → Ingestion Service
  │     records: run stats
  └── Error branch: POST /ingestion/fail → Ingestion Service
        records: error, increments retry_count

n8n Workflow: enrich-directors
  ├── Trigger: On new FEDERAL_INCORPORATION event
  ├── Node: GET new corp_numbers since last run
  ├── Node: POST /enrich/directors (batched, rate-limited 60/min)
  └── Error branch: log failure, do not deactivate existing data

n8n Workflow: enrich-orgbook
  ├── Trigger: On new BC entity detected
  ├── Node: POST /enrich/orgbook (targeted lookup)
  └── Error branch: log failure

n8n Workflow: merge-review-notify
  ├── Trigger: Daily
  ├── Node: GET /merge-candidates?status=pending
  └── Node: (optional) notify operator of pending reviews
```

Each n8n workflow calls Python services via HTTP. Python services handle all logic.
n8n Code nodes contain zero business logic — only control flow and simple data reshaping.

---

## Python Services Architecture

Python runs as a set of FastAPI microservices internally (or a single modular monolith
behind a router during early development — this is a deployment decision, not an architecture
one).

### Service Boundaries

```
ingestion_service/
├── routes/
│   ├── POST /ingestion/start          → create ingestion_run record
│   ├── POST /ingestion/fetch          → call adapter.fetch() + adapter.parse()
│   ├── POST /ingestion/complete       → update run stats
│   └── POST /ingestion/fail           → record failure
├── adapters/                          → all SourceAdapter implementations
└── models/                            → RawArtifact, RawRecord Pydantic models

normalisation_service/
├── routes/
│   └── POST /normalise                → receive RawRecord[], return NormalisedRecord[]
├── normalizers/
│   ├── name.py
│   ├── address.py
│   ├── phone.py
│   ├── email.py
│   ├── employee.py
│   ├── naics.py
│   ├── status.py
│   └── date.py
└── models/

entity_resolution_service/
├── routes/
│   └── POST /resolve                  → receive NormalisedRecord[], return ResolutionResult[]
├── matchers/
│   ├── exact_identifier.py            → corp_number, BN, licence_id
│   ├── composite_deterministic.py     → domain+postal, phone+postal, name+address
│   └── fuzzy.py                       → RapidFuzz token_sort_ratio
├── merger.py                          → merge_candidate creation + auto-merge logic
└── models/

events_service/
├── routes/
│   └── POST /events/detect            → detect new events from ingestion diff
├── detectors/
│   ├── new_business.py
│   ├── status_change.py
│   └── field_change.py
└── models/

enrichment_service/
├── routes/
│   ├── POST /enrich/directors         → Corps Canada API director fetch
│   ├── POST /enrich/orgbook           → BC OrgBook targeted lookup
│   └── POST /enrich/website           → optional website phone extraction
└── models/

quality_service/
├── routes/
│   └── POST /quality/score            → compute component scores + lead_quality_score
├── scorers/
│   ├── identity.py
│   ├── address.py
│   ├── phone.py
│   ├── email.py
│   ├── employee.py
│   ├── industry.py
│   ├── contact.py
│   └── recency.py
└── composite.py                       → derive lead_quality_score from components

api_service/                           → public-facing FastAPI (dashboard + integrations)
├── routes/
│   ├── businesses.py                  → GET /businesses, /businesses/{id}, etc.
│   ├── events.py
│   ├── sources.py
│   ├── stats.py
│   └── export.py
└── models/
```

### Quality Score Composite Formula

Component scores (0–100 each) derived as:

```
identity_confidence  = 100 if (legal_name + province + (corp_number OR BN)) else partial
address_confidence   = 100 if (street + city + province + valid_postal) else partial
phone_confidence     = 100 if (phone_valid + CA_NPA_pass) else 0
email_confidence     = 100 if (email_valid_format + source != website_crawl) else partial
employee_confidence  = 100 if employee_exact else 60 if range else 0
industry_confidence  = 100 if source_naics else 50 if mapped_naics else 0
contact_confidence   = 100 if any(person record) else 0
recency_confidence   = 100 if last_verified < 30d else linear decay to 0 at 365d
source_reliability   = weighted: Class A=100, Class B=70, Class C=50, Class D=0

lead_quality_score = (
    identity_confidence  * 0.25 +
    address_confidence   * 0.20 +
    phone_confidence     * 0.15 +
    email_confidence     * 0.10 +
    contact_confidence   * 0.10 +
    recency_confidence   * 0.10 +
    employee_confidence  * 0.05 +
    industry_confidence  * 0.05
)
```

This formula is documented, deterministic, and visible in the API response.

---

## Data Models (Pydantic — API Layer)

```python
class BusinessSummary(BaseModel):
    entity_id: UUID
    canonical_name: str
    province: str | None
    status: str
    sales_ready: bool
    lead_quality_score: int | None
    has_phone: bool
    has_email: bool
    has_website: bool
    has_director: bool
    employee_bucket: str | None
    naics_sector: str | None
    last_verified_at: datetime | None

class BusinessDetail(BaseModel):
    entity_id: UUID
    canonical_name: str
    legal_name: str | None
    trade_name: str | None
    entity_type: str | None
    province: str | None
    status: str
    sales_ready: bool
    lead_quality_score: int | None
    locations: list[LocationModel]
    identifiers: list[IdentifierModel]
    contacts: list[ContactModel]
    employees: EmployeeModel | None
    industry: IndustryModel | None
    persons: list[PersonModel]
    events: list[EventModel]
    sources: list[SourceContributionModel]
    quality_components: QualityComponentsModel
    province_gap_flag: bool
    first_seen_at: datetime
    last_verified_at: datetime | None

class EventModel(BaseModel):
    event_id: UUID
    event_type: str
    event_date: date | None
    event_source_name: str
    raw_value: str | None
    created_at: datetime

class QualityComponentsModel(BaseModel):
    identity_confidence: int
    address_confidence: int
    phone_confidence: int
    email_confidence: int
    employee_confidence: int
    industry_confidence: int
    contact_confidence: int
    recency_confidence: int
    source_reliability: int
    lead_quality_score: int
```

---

## Error Handling

### Ingestion Failures
- HTTP errors (4xx, 5xx, timeout): recorded in `ingestion_run.error_message`, `run_status=FAILED`
- n8n retries via exponential backoff: 1min → 5min → 30min → 1h (configurable per source)
- Source unavailability does NOT deactivate existing canonical records (NNI VR18 precedent)
- After max retries: `run_status=FAILED`, operator notified via n8n notification node

### Normalisation Errors
- Per-field: invalid values flagged in `data_quality_flag`, field stored as NULL — record not dropped
- Structural parse errors: `source_record.resolution_status=SKIPPED`, error logged in run

### Entity Resolution Errors
- MEDIUM confidence: insert `merge_candidate` — never block ingestion
- Unresolvable records: create new entity with `resolution_confidence=LOW`
- No silent failures: every record gets a `resolution_status`

### API Errors
- 404: entity not found — standard JSON error body
- 400: invalid filter parameters — detailed validation error from Pydantic
- 500: logged with structlog request ID — generic error body exposed to client

### Rate Limit Handling
- Corps Canada API (60 rpm): token bucket implemented in `CorporationsCanadaAPIAdapter`
  using `asyncio.sleep` calculated from request timestamps
- n8n can add additional HTTP throttling at the workflow level as a secondary guard

---

## Testing Strategy

### Unit Tests (pytest)
- Normalisation functions: phone, address, name, employee — edge cases per VR findings
  - "385.0" → integer → bucket
  - "55 to 99" → flag ambiguity
  - "500 plus" → min=500, max=NULL, bucket=500+, exact=false
  - "N/A" email → NULL
  - "(416) 123-4567" == "+14161234567"
- Entity resolution: exact match, composite match, fuzzy threshold, no-match → new entity
- Quality scoring: known inputs → expected component scores + composite

### Integration Tests (pytest + httpx async client)
- Ingestion → normalisation → entity resolution pipeline for each adapter (using fixture data)
- API endpoint responses: pagination, filtering, history endpoint
- Idempotency: run same ingestion twice → no duplicate entities

### Adapter Tests (pytest + fixture data from VR probe outputs)
- Each adapter tested against a real sample from its validation round data
- CorporationsCanadaCSVAdapter: sample from 645k CSV
- VancouverAdapter: sample with employee count "385.0" and multi-licence conflict case
- BCIndigenousAdapter: "55 to 99" and "500 plus" employee ranges
- ManitobaWeeklyPDFAdapter: Sep 19 + Sep 12 PDFs — confirm zero cross-run duplicates

### End-to-End Test
- Docker Compose up → seed fixture data → run full ingestion pipeline → query API → verify
  entity created with correct provenance chain

---

## Docker Compose Service Topology

```yaml
services:
  postgres:
    image: postgres:16
    volumes: [postgres_data:/var/lib/postgresql/data]
    environment: [POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]

  n8n:
    image: n8nio/n8n:latest
    environment: [N8N_BASIC_AUTH_*, DB_TYPE=postgresdb, DB_POSTGRESDB_*]
    volumes: [n8n_data:/home/node/.n8n]
    depends_on: [postgres]

  api:                         # FastAPI — public API + internal Python services
    build: ./backend
    environment: [DATABASE_URL, CORPS_CANADA_API_KEY, ...]
    depends_on: [postgres]

  frontend:                    # Next.js dashboard
    build: ./frontend
    environment: [NEXT_PUBLIC_API_URL]
    depends_on: [api]

  nginx:
    image: nginx:alpine
    volumes: [./nginx.conf:/etc/nginx/conf.d/default.conf]
    ports: ["80:80"]
    depends_on: [api, frontend, n8n]

volumes:
  postgres_data:
  n8n_data:
```

Nginx routing:
- `/api/*` → FastAPI (port 8000)
- `/n8n/*` → n8n (port 5678)
- `/*` → Next.js (port 3000)

---

## Next.js Dashboard Component Structure

```
frontend/
├── app/
│   ├── page.tsx               → Dashboard home (stats, KPIs, coverage map)
│   ├── businesses/
│   │   ├── page.tsx           → Business list with filters
│   │   └── [id]/page.tsx      → Business detail view
│   ├── events/page.tsx        → Event stream
│   └── sources/page.tsx       → Source registry + run status
├── components/
│   ├── BusinessTable.tsx      → Paginated, sortable list
│   ├── BusinessDetail.tsx     → Full entity view with tabs
│   ├── FilterPanel.tsx        → Province/city/NAICS/employee/status filters
│   ├── EventTimeline.tsx      → Visual event history
│   ├── SourceStatusCard.tsx   → Last run, record count, status per source
│   ├── ProvenancePanel.tsx    → field_observation history table
│   ├── QualityBadge.tsx       → Visual component scores + composite
│   └── ExportButton.tsx       → CSV/JSON export with current filters
```

---

## Design Decisions and Rationale

| Decision | Rationale |
|---|---|
| n8n over Celery | This system is fundamentally orchestration of heterogeneous sources with different schedules and retrieval mechanisms. n8n fits this problem natively. Celery is stronger for high-volume distributed task execution — not our primary bottleneck. |
| Python services for domain logic | Normalisation, entity resolution, and confidence scoring are complex, stateful, testable code. They must not live in n8n Code nodes — that becomes unmaintainable at 200+ lines. |
| PostgreSQL JSONB for raw payloads | Source schemas vary wildly. JSONB preserves the full raw payload without schema-coupling the provenance layer to every source's field names. Indexed JSONB columns support efficient querying where needed. |
| `field_observation` as provenance spine | Rather than a simple audit log, every field value from every source is a first-class record. This enables answering "why does this business have this phone number" precisely. |
| No Redis at launch | Redis is useful for rate-limit buffering and caching but introduces operational complexity. The Corps Canada API rate limit is handled in the adapter. Caching can be added if API performance proves insufficient. |
| Pipeline-generated entity_id | Borrowing a source's ID (e.g. corp_number) as the canonical PK creates a dependency on one source's identity model. A pipeline-generated UUID is source-neutral and survives source changes. |
| Separate `lead_flag` / sales layer | Sales-process state (DNC, contacted, qualified) must never corrupt canonical data. These are system-operational facts about our pipeline's interaction with a business, not facts about the business itself. |
| Province gaps as first-class records | NS, NB, ON, QC gaps are architectural facts, not data absences. Making them explicit in `province_coverage_gap` means the dashboard can distinguish "no data" from "no source for this province." |
