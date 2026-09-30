# Canadian Business Data Automation — Research Findings

> **Document type:** Living research notebook
> **Purpose:** Preserve verified findings, source decisions, limitations, and open questions throughout the project.

---

## 2026-09-25 — Initial Research Baseline

### Assignment objective

Build a production-oriented, Canada-wide B2B business-data automation system for a telecom sales operation.

The system should discover and continuously refresh Canadian businesses using legitimate public/authorized data sources while minimizing recurring third-party data-provider costs.

---

## Core Finding #1 — No single free source contains everything

No single source identified so far reliably provides all of:

```text
Business identity
+
address
+
website
+
phone
+
email
+
industry
+
NAICS
+
employee count
+
registration date
+
status
+
decision-makers
```

Therefore the eventual system will require a composite-source architecture.

---

## Core Finding #2 — Public does not automatically mean scrapeable

A source being publicly searchable does not automatically mean unrestricted automated bulk extraction is permitted.

Every source must be evaluated for:

* Terms
* Licence
* Commercial use
* Automation restrictions
* Rate limits
* API requirements
* Bulk-download permissions

New Brunswick Corporate Registry is an example where automated copying of groups of search results is restricted.

---

## Core Finding #3 — Federal Corporations Canada is a strong structured source

Federal corporation datasets provide useful corporate identity and registry information.

Potential information includes:

* Corporation identifier
* Name
* Status
* Registered office
* Directors
* Dates
* Other corporate information

Bulk datasets should be preferred for bulk ingestion.

The API should primarily be used for targeted/current verification rather than indiscriminate high-volume requests.

### Limitation

Federal corporations are not equivalent to all Canadian businesses because provincially/territorially incorporated entities are not automatically represented.

---

## Core Finding #4 — ODBus is a useful historical discovery dataset

Statistics Canada's Open Database of Businesses contains approximately 450,000 published business records.

Documented fields include:

* Business name
* Business ID
* Business sector
* Licence information
* NAICS
* Employees
* Status
* Address
* Municipality
* Province
* Postal code
* Latitude
* Longitude

### Limitation

The published dataset is historical and should not be treated as a current daily registry.

### Current status

ODBus ZIP has been downloaded locally.

Actual field coverage has **not yet been measured**.

### Next action

Run:

```text
python scripts/inspect_odbus.py
```

and record the resulting measurements in:

```text
reports/ODBUS_PROFILE.md
```

---

## Core Finding #5 — ODBus website/phone/email coverage is not assumed

The documented ODBus variables do not establish that website, phone, and email are available.

Therefore these fields must be measured from the actual downloaded data.

Do not design the enrichment architecture around assumed ODBus contact coverage.

---

## Core Finding #6 — Québec has rich registry data but a licence concern

Québec's enterprise data can provide valuable information including:

* Enterprise number
* Names
* Registration date
* Status
* Economic activity
* Employee information
* Establishments
* Addresses

However, the downloadable dataset has a non-commercial-use restriction relevant to this commercial telecom prospecting assignment.

### Decision

Do not make the Québec downloadable dataset a production dependency until its commercial-use permissions are resolved.

---

## Core Finding #7 — Ontario does not currently have an established free bulk registry source in our research

Ontario Business Registry provides public searches and useful information.

However, a free equivalent to a large downloadable corporate registry has not yet been established.

Potential strategy:

```text
Ontario public registry
+
Ontario open data
+
other permitted sources
+
website enrichment
```

---

## Core Finding #8 — BC has an interesting targeted verification source

BC OrgBook provides organization information through an open API.

However, this should not be interpreted as permission to bulk-download or scrape the entire database.

Potential role:

```text
Known business
    ↓
Targeted lookup
    ↓
Verification/enrichment
```

BC's primary registry API involves account/API access and fees, so it is not currently a preferred zero-cost foundation.

---

## Core Finding #9 — Aggregate Statistics Canada data is not an individual lead database

Canadian Business Counts provides aggregate information by:

* Geography
* NAICS
* Employee-size range

Useful for:

* Coverage validation
* Industry context
* Size distribution

Not suitable as the primary individual business-lead source.

---

## Core Finding #10 — Enrichment will likely require multiple sources

No confirmed free nationwide Apollo/ZoomInfo-equivalent source has been identified.

Likely strategy:

```text
Structured data
      ↓
Website discovery
      ↓
Official website extraction
      ↓
Public leadership/contact discovery
```

Deterministic extraction should be attempted before using LLMs.

---

# Source Decision Table

| Source                            | Potential Role                | Current Decision                            |
| --------------------------------- | ----------------------------- | ------------------------------------------- |
| Corporations Canada bulk data     | Federal corporate discovery   | Investigate/use                             |
| Corporations Canada API           | Targeted verification         | Investigate/use                             |
| ODBus                             | Historical/base discovery     | Currently profiling                         |
| Québec enterprise dataset         | Rich provincial data          | Licence review required                     |
| Ontario Business Registry         | Provincial discovery          | Research                                    |
| BC OrgBook                        | Targeted verification         | Investigate                                 |
| BC Registry API                   | Provincial registry           | Avoid as mandatory zero-cost dependency     |
| Nova Scotia open data             | Vertical discovery/enrichment | Investigate                                 |
| New Brunswick Registry            | Corporate discovery           | Do not bulk scrape without permitted method |
| Saskatchewan Registry             | Corporate discovery           | Research                                    |
| Manitoba Companies Office         | Corporate discovery           | Research                                    |
| Alberta Corporate Registry        | Corporate discovery           | Avoid as zero-cost foundation               |
| Statistics Canada Business Counts | Coverage validation           | Use as aggregate context                    |

---

# Open Questions

## ODBus

* Exact files contained in ZIP?
* Exact record count?
* Exact columns?
* Website coverage?
* Phone coverage?
* Email coverage?
* Employee coverage?
* NAICS coverage?
* Duplicate IDs?
* Province distribution?
* Status distribution?
* Source distribution?

## Federal

* Exact bulk dataset structure?
* Exact fields?
* Record count?
* Date coverage?
* Director coverage?
* Address coverage?
* Matching identifiers?

## Cross-source

* How much ODBus overlap exists with federal corporations?
* Which source provides unique information?
* What matching keys work best?
* What percentage remains unmatched?
* How many potential false matches occur?

## Enrichment

* What permitted mechanisms can discover official websites at scale?
* Which public datasets already contain websites/phones?
* What legitimate public sources provide business emails?
* What legitimate public sources provide decision-makers?
* What are acceptable rate limits?
* What sources permit commercial use?

---

# Research Rules

1. Prefer official government/open-data sources.
2. Prefer bulk/API/structured data over browser automation.
3. Use browser automation only where it is appropriate and permitted.
4. Never bypass authentication, CAPTCHA, access controls, or technical restrictions.
5. Preserve raw source data.
6. Preserve source provenance.
7. Do not overwrite conflicting source observations.
8. Do not fabricate missing business or contact information.
9. Verify commercial-use permissions before using a source for the commercial system.
10. Measure real datasets before making architectural assumptions.
11. Keep exploratory research separate from production code.
12. Record important decisions and rejected approaches.

---

# Current Phase

```text
RESEARCH / DATA FEASIBILITY
```

## Current task

```text
ODBus
  ↓
Inspect
  ↓
Profile
  ↓
Document findings
```

## After ODBus

```text
Federal dataset
  ↓
Profile
  ↓
Compare with ODBus
  ↓
Matching experiment
```

Only after these steps should the production schema and application architecture be finalized.
