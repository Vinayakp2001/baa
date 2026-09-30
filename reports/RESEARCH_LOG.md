# Research Log

## Entry: ODBus 2023 Initial Dataset Inspection

**Date:** 2026-09-25
**Source:** Statistics Canada Open Database of Businesses (ODBus), downloaded as `ODBus_2023.zip`
**Inspection script:** `scripts/inspect_odbus.py`
**Report:** `reports/ODBUS_INSPECTION_REPORT.md`

### Result

The downloaded ODBus archive contains six members:

* ODBus metadata DOCX
* ODBus metadata PDF
* ODBus record layout CSV
* ODBus sources CSV
* ODBus main dataset CSV
* archive directory entry

The main dataset is:

`ODBus_v1/ODBus_v1.csv`

It contains **446,575 records and 32 columns**.

### Main fields observed

The dataset contains fields for:

* business name
* alternate business name
* business sector/subsector
* business description
* business identifier
* licence number/type
* NAICS and NAICS descriptions
* latitude/longitude
* full address
* postal code
* address components
* city
* province/territory
* employee information
* status
* provider
* geographic source
* CSD/PR identifiers

### Important findings

#### 1. ODBus is potentially useful as a discovery/base dataset

It provides substantial structured business information that can support the initial business-master/discovery layer.

However, it does not contain the full set of fields required by the telecom sales system.

Missing/absent from the inspected 32-column schema are obvious fields for:

* website
* phone
* email
* owner/founder
* president
* manager
* GM
* operations contact
* IT contact
* procurement contact

Therefore ODBus must be treated as one source in a multi-source enrichment architecture rather than the final lead database.

#### 2. Geographic coverage requires investigation

The observed province/territory distribution is:

* Ontario: 205,122
* British Columbia: 163,200
* Alberta: 76,526
* Northwest Territories: 1,445
* Nunavut: 171
* New Brunswick: 110
* Missing: 1

No records for several Canadian provinces/territories appear in this initial distribution.

**Decision:** Do not describe ODBus as Canada-wide coverage until the metadata/source files explain the geographic scope and coverage.

#### 3. Employee data requires normalization

`total_no_employees` contains:

* exact employee counts
* ranges such as `1--4`, `5--9`, `10--19`
* alternate range formatting such as `1 to 4`
* unknown values represented by `..`
* `NOT AVAILABLE`
* broader ranges such as `100--499` and `100 to 299`

Some values can be deterministically mapped to the assignment's required employee buckets.

Broader ranges cannot always be mapped safely.

**Decision:** Preserve the raw employee value and create a normalized employee bucket only when the source value supports an unambiguous classification.

#### 4. Status requires normalization

Observed status values include:

* `Active`
* `Pending`
* `Not Active`
* `..`

A missing/unknown source status must not be treated as inactive.

**Decision:** Preserve raw status and normalize into controlled values such as:

* ACTIVE
* PENDING
* NOT_ACTIVE
* UNKNOWN

#### 5. Duplicate indicators require deeper analysis

The initial inspection reports many repeated `business_id_no` and business names.

These counts must **not** be interpreted as confirmed duplicate businesses.

The dataset may contain multiple records per business because of locations, licences, providers, source records, or other source-level characteristics.

**Decision:** Determine the actual record grain from the ODBus metadata and source files before designing entity-resolution rules.

#### 6. Provider/source provenance is important

The dataset contains a `provider` field and a separate ODBus source table.

This may allow the system to retain source-level provenance and distinguish observations coming from different contributing datasets.

**Decision:** Preserve provider/source information in the eventual business-source/observation model.

### Current role of ODBus

**Proposed role:**

`ODBus → business discovery/base records → entity resolution → enrichment from additional sources`

It should not be treated as the sole Canada-wide source.

### Open questions

Before incorporating ODBus into the production pipeline, investigate:

1. Exact dataset date/reference period.
2. Licensing and commercial-use permissions.
3. Meaning and uniqueness of `business_id_no`.
4. Exact record grain.
5. Explanation for geographic concentration.
6. Meaning of `provider`.
7. Meaning and construction of `derived_NAICS`.
8. Meaning of `total_no_employees`.
9. Source-specific employee coverage.
10. Whether records represent businesses, establishments, licences, or a mixture.
11. Which fields are sourced from which providers.
12. Whether ODBus can contribute to new-business detection or should primarily serve as historical/base discovery data.

### Current decision

Do not build the production ingestion adapter yet.

First complete metadata and source analysis, then design the ODBus adapter around the verified record semantics.
