# Canadian Business Data Automation — Research Phase

## 1. Purpose

This repository is the **research and data-feasibility phase** of a larger technical trial.

The eventual objective is to build a production-oriented, Canada-wide B2B business-data automation system for a telecom sales operation.

The final system is expected to continuously discover, collect, normalize, enrich, deduplicate, verify, classify, score, and refresh Canadian business records using legitimate public, government, open-data, and otherwise permitted sources.

This repository is intentionally separate from the eventual production implementation.

---

## 2. Current Project Phase

**Phase: Data Research / Feasibility**

We are currently validating the actual data available from Canadian sources before designing the final production database and application architecture.

### Current milestone

> Inspect Statistics Canada's Open Database of Businesses (ODBus), measure its actual contents, and determine what information is available before web enrichment or additional scraping is introduced.

---

## 3. Final Assignment Requirements

The eventual system should support Canadian B2B business prospecting for:

* Business mobile plans
* Phones/devices
* Business internet
* Telecom services

The system should be Canada-scalable rather than limited to one city.

### Required company information

Where available:

* Legal business name
* Operating/business name
* Province
* City
* Full address
* Postal code
* Website
* Main business phone
* Email
* Industry/category
* NAICS
* Employee count
* Employee-size category
* Incorporation/registration date
* Business status
* Source for each field
* Last verified date

### Employee-size buckets

The final system should classify businesses into:

* 1–4
* 5–9
* 10–19
* 20–49
* 50–99
* 100–199
* 200–499
* 500–999
* 1000+

Exact counts should be preferred.

Estimated counts must be explicitly marked as estimated and supported by evidence.

### Public decision-makers

Where legitimately and publicly available:

* Owner
* Founder
* President
* General Manager
* Office Manager
* Operations Manager
* IT Manager/Director
* Procurement
* Other relevant business decision-makers

For each contact, preserve:

* Name
* Title
* Public business email, if available
* Public business phone, if available
* Source URL
* Verification date
* Confidence

The system must not fabricate missing people or contact information.

---

## 4. New Business Detection

The eventual system must distinguish between different types of events, including:

* Newly registered business
* Newly discovered business
* Recently opened location
* Recently changed business information
* Status change
* Newly added location

The system should support daily, 7-day, and 30-day views where source data permits.

Important distinction:

`registered today` is not necessarily the same as `discovered today` or `opened recently`.

---

## 5. Data Provenance

The final system must preserve source history.

Conflicting source information must not simply overwrite previous observations.

Conceptually:

```text
Business
    |
    +-- Phone
          |
          +-- Source A -> value A -> collected date
          |
          +-- Source B -> value B -> collected date
```

The system should retain source observations containing information such as:

* Business
* Field
* Value
* Source
* Source URL
* Collection timestamp
* Verification timestamp
* Confidence

A canonical value can then be selected using explicit verification logic while preserving the underlying observations.

---

## 6. Deduplication / Entity Resolution

The final system must avoid duplicate businesses across different sources.

Preferred matching order:

1. Strong government/corporate identifier
2. Corporation/business number
3. Domain + postal code
4. Phone + postal code
5. Name + address
6. Name + city + phone
7. Conservative fuzzy matching after deterministic matching

False merges must be avoided.

A business appearing in multiple sources should normally become one business entity with multiple source observations.

---

## 7. Data Quality

The final system should expose an explainable quality/confidence measure.

Potential evidence includes:

* Verified phone
* Verified website
* Verified address
* Employee information
* Decision-maker information
* Multiple independent sources
* Recency of verification

Exact scoring weights and thresholds are **not finalized** and should be determined after examining real source data.

---

## 8. Dashboard Requirements

The eventual application should provide search/filter capabilities for:

* Province
* City
* Industry
* NAICS
* Employee size
* New business
* Registration date
* Business age
* Quality score
* Phone availability
* Email availability
* Decision-maker availability

It should support CSV export.

The architecture should be suitable for later integration with a CRM or dialer.

---

## 9. Automation Requirements

The eventual system should automate:

```text
Collect
  ↓
Normalize
  ↓
Deduplicate
  ↓
Compare
  ↓
Enrich
  ↓
Classify
  ↓
Verify
  ↓
Score
  ↓
Store
```

Scheduled jobs should maintain the database continuously.

Logging should include:

* Source
* Records collected
* New companies
* Updated companies
* Errors
* Last successful run
* Job status

---

## 10. Cost Requirements

The goal is:

> No mandatory recurring paid data-provider dependency.

Preferred sources and technologies include:

* Government open data
* Public datasets
* Permitted public APIs
* Public business websites
* Open-source software
* Python
* PostgreSQL
* Docker
* Local/open-source models where useful

Paid sources may be documented as optional alternatives but should not be required for the core system.

Infrastructure/server cost is separate from third-party data-provider dependency.

---

## 11. Compliance Requirements

The final system must only use information and acquisition methods that are legally and technically permitted.

Do not:

* Bypass authentication
* Bypass CAPTCHA
* Bypass access controls
* Access private accounts
* Circumvent technical restrictions
* Bulk scrape sources that prohibit automated extraction
* Ignore source-specific rate limits or terms
* Fabricate business/contact information

Important principle:

> Publicly viewable data is not automatically permission to perform unrestricted automated bulk extraction.

Each source should therefore be documented with:

* Access method
* Licence/terms
* Automation restrictions
* Rate limits
* Commercial-use status
* Update frequency
* Data coverage

---

# 12. Research Findings So Far

## Federal Corporations Canada

Corporations Canada provides federal corporation data through bulk datasets and APIs.

Potential information includes:

* Corporation identifier
* Corporate name
* Status
* Registered office
* Directors
* Dates
* Other corporate information

The federal datasets are useful for bulk processing.

The API should be reserved primarily for targeted/current verification rather than making hundreds of thousands of individual requests.

Important limitation:

> Federal corporation data does not represent every Canadian business because provincially/territorially incorporated businesses are outside the federal corporate registry.

---

## Statistics Canada — ODBus

The Statistics Canada Open Database of Businesses (ODBus) is a particularly useful historical business-discovery dataset.

The published dataset contains approximately 450,000 records.

The documented variables include information such as:

* Business name
* Business ID
* Business sector
* Licence information
* NAICS
* Number of employees
* Status
* Address
* Municipality
* Province
* Postal code
* Latitude
* Longitude

Important limitation:

The published ODBus version is historical and should not be treated as a current daily business registry.

It should initially be considered a:

> Historical/base discovery and enrichment dataset

rather than the source of truth for current business registration.

### Current ODBus task

The actual ZIP has been downloaded locally.

We must inspect the actual files before making assumptions about:

* Website coverage
* Phone coverage
* Email coverage
* Employee coverage
* NAICS coverage
* Duplicate rate
* Province distribution
* Status distribution
* Source distribution

---

## Québec

Québec's enterprise registry/open-data ecosystem appears technically valuable.

Potential information includes:

* NEQ
* Enterprise name
* Registration date
* Status
* Legal form
* Economic activity
* Employee information
* Establishments
* Addresses
* Other enterprise names

However, the downloadable enterprise dataset has a non-commercial-use restriction that is relevant to this commercial telecom prospecting assignment.

Therefore:

> Do not automatically ingest the Québec downloadable dataset into the production system until its licence/commercial-use position has been resolved.

---

## Ontario

Ontario Business Registry provides public business searches and useful corporate information.

However, an equivalent free bulk corporate dataset has not yet been established.

Potential Ontario strategy:

```text
Public registry
+
Ontario open datasets
+
Permitted business sources
+
Business websites
```

---

## British Columbia

BC has a Business Registry API, but it involves account/API access and fees.

BC OrgBook provides an open API with organization information and is potentially useful for targeted verification/enrichment.

However, it should not be treated as permission to bulk-download or scrape the entire service.

Potential architecture:

```text
Business already discovered
        ↓
Targeted OrgBook lookup
        ↓
Verification/enrichment
```

---

## Nova Scotia

Nova Scotia provides useful open datasets for specific business categories, including regulated/licensed businesses.

These are potentially useful for:

* Vertical-specific discovery
* Business enrichment
* Coverage expansion

They are not assumed to be a complete national business registry.

---

## New Brunswick

The New Brunswick Corporate Registry has restrictions concerning automated copying of groups of search results.

Therefore:

> Do not build a bulk Playwright/Selenium scraper against the registry unless an explicitly permitted automated acquisition method is established.

---

## Saskatchewan

Public corporate registry information exists, but some information/searches involve fees.

A free automated bulk acquisition method has not yet been established.

---

## Manitoba

The Manitoba Companies Office provides public registry searching.

Basic searches can be free while detailed information may involve fees.

A free automated bulk acquisition mechanism has not yet been established.

---

## Alberta

Alberta Corporate Registry information is useful but registry searches involve fees and restrictions.

It should not currently be treated as the foundation of the zero-cost architecture.

Alberta open datasets can still provide useful aggregate/industry/business context.

---

## Statistics Canada Business Counts

Statistics Canada provides aggregate Canadian business counts by:

* Geography
* NAICS
* Employee-size range

These are useful for:

* Coverage validation
* Industry context
* Employee-size context

They are not individual business lead records.

---

# 13. Current Source Strategy

The current strategy is source tiers rather than one universal scraper.

### Tier 1 — Structured/open sources

Examples:

* Federal Corporations Canada
* ODBus
* Provincial open data
* Municipal open data
* Permitted APIs

### Tier 2 — Public business websites

After a business has been discovered:

```text
Website
  ↓
Contact
About
Team
Leadership
Locations
  ↓
Phone
Email
Address
People
```

### Tier 3 — Additional permitted sources

A source should only be added when:

```text
Useful data
+
Permitted automation
+
Acceptable cost
```

### Tier 4 — Paid sources

Paid sources can be documented as optional alternatives but should not be mandatory dependencies for the core system.

---

# 14. Enrichment Strategy

There is currently no confirmed free nationwide equivalent of Apollo/ZoomInfo that provides all required business/contact information.

Therefore enrichment will likely be composite.

### First use structured source data

Do not scrape the web if the source already gives us the required information.

### Then discover official websites

Use business identity information such as:

```text
Legal name
Operating name
City
Province
Postal code
```

to identify the official website using a permitted discovery mechanism.

### Then crawl the business website

Potential pages:

```text
/
 /contact
 /about
 /team
 /leadership
 /management
 /locations
```

### Deterministic extraction first

Potential sources:

* `mailto:`
* `tel:`
* JSON-LD
* Schema.org Organization
* Schema.org LocalBusiness
* Visible address
* Telephone
* Email
* Social links
* Metadata

LLMs/local models should only be introduced where deterministic extraction is insufficient.

---

# 15. Decision-Maker Enrichment

Decision-makers should be found only from legitimate public information.

Potential sources:

* Company websites
* Public team/leadership pages
* Public professional/business pages
* Other permitted public sources

Missing information should remain missing.

Possible states:

```text
confirmed
estimated
not_found
```

Never fabricate a person, role, email, or phone number.

---

# 16. Current Research Repository

Current directory:

```text
baa/
├── baa_env/
├── data/
│   └── raw/
├── reports/
├── scripts/
└── src/
```

Recommended documentation:

```text
reports/
├── research_findings.md
└── ODBUS_PROFILE.md
```

### `research_findings.md`

This is the living research notebook.

It should be updated whenever a meaningful source/technical discovery is made.

Record:

* Finding
* Source
* Date checked
* Evidence
* Interpretation
* Decision
* Open question

### `ODBUS_PROFILE.md`

This should contain measured results generated from the actual ODBus dataset.

Do not manually invent or estimate the values.

---

# 17. Current Immediate Task

We have downloaded the ODBus ZIP.

The next task is:

```text
ODBus ZIP
   ↓
Inspect archive
   ↓
Identify actual data files
   ↓
Load data
   ↓
Profile columns
   ↓
Measure missing values
   ↓
Measure province distribution
   ↓
Measure employee coverage
   ↓
Measure NAICS coverage
   ↓
Measure status
   ↓
Measure duplicate IDs
   ↓
Check website/phone/email fields
   ↓
Generate ODBUS_PROFILE.md
```

The inspection should be reproducible through:

```text
python scripts/inspect_odbus.py
```

---

# 18. Important Development Principle

Do not build the production application around assumptions.

The workflow is:

```text
Research
   ↓
Measure
   ↓
Understand
   ↓
Decide
   ↓
Design
   ↓
Implement
   ↓
Test
   ↓
Deploy
```

The research repository is intentionally separate from the eventual production repository.

The eventual Kiro project should be created after the core data-feasibility research has been completed and the architecture can be based on evidence.

---

# 19. Immediate Definition of Done

For the current research milestone, we are done when we can answer:

1. What files are actually inside ODBus?
2. How many business records are there?
3. What are the exact columns?
4. Which fields have useful coverage?
5. Does ODBus contain website information?
6. Does ODBus contain phone information?
7. Does ODBus contain email information?
8. How complete is NAICS?
9. How complete is employee information?
10. How complete are addresses/postal codes?
11. How many duplicate IDs exist?
12. What provinces are represented?
13. What business statuses exist?
14. What limitations does ODBus have?
15. What role should ODBus play in the eventual system?

After answering these questions, inspect the federal dataset and compare the two sources.

---

# 20. Status

**Current status:**

```text
[x] Assignment understood
[x] Initial Canadian source research
[x] Source restrictions identified
[x] ODBus identified
[x] ODBus downloaded
[x] Research project created
[ ] ODBus profiling
[ ] Federal dataset profiling
[ ] Source comparison
[ ] Matching experiment
[ ] Final source strategy
[ ] Production architecture
[ ] Production implementation
[ ] Dashboard
[ ] Scheduling
[ ] Deployment
```

The next action is **ODBus profiling**. Do not begin the production application until the research findings have been incorporated into the design.
