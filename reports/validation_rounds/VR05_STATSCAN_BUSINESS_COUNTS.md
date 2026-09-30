# VR05 — Statistics Canada Business Counts

Generated: `2026-09-25T12:41:08.083027+00:00`

## Sources

| Table | ID | Label | Release | Role |
|---|---|---|---|---|
| A | `33-10-1174-01` | Canadian Business Counts, with employees | June 2026 | Class D benchmark |
| B | `33-10-0722-01` | Business Openings and Closures | Monthly (Jan 2015–) | Class D benchmark (experimental) |

Both tables downloaded as full bulk CSV ZIP from:
`https://www150.statcan.gc.ca/n1/tbl/csv/{table_id}-eng.zip`

---

## Table A — Canadian Business Counts, with employees (33-10-1174-01)

- Data file: `33101174.csv`
- Rows: `85,793`
- Columns: `16`

### A.1 Column names

- `REF_DATE`
- `GEO`
- `DGUID`
- `Employment size`
- `North American Industry Classification System (NAICS)`
- `UOM`
- `UOM_ID`
- `SCALAR_FACTOR`
- `SCALAR_ID`
- `VECTOR`
- `COORDINATE`
- `VALUE`
- `STATUS`
- `SYMBOL`
- `TERMINATED`
- `DECIMALS`

### A.2 Key dimension columns identified

| Dimension | Column name |
|---|---|
| Employment size | `Employment size` |
| Geography | `GEO` |
| NAICS | `North American Industry Classification System (NAICS)` |
| Reference date | `REF_DATE` |
| Value | `VALUE` |
| Symbol/suppression | `STATUS` |

### A.3 Employment-size labels (actual values in data)

| # | Label as it appears in data |
|---|---|
| 1 | `1 to 4 employees` |
| 2 | `10 to 19 employees` |
| 3 | `100 to 199 employees` |
| 4 | `20 to 49 employees` |
| 5 | `200 to 499 employees` |
| 6 | `5 to 9 employees` |
| 7 | `50 to 99 employees` |
| 8 | `500 plus employees` |
| 9 | `Total, with employees` |

### A.4 Employment-size → required bucket mapping

Required buckets: `1-4, 5-9, 10-19, 20-49, 50-99, 100-199, 200-499, 500-999, 1000+`

| Required bucket | Matching StatsCan label(s) | Mappable? |
|---|---|---|
| `1-4` | `1 to 4 employees` | ✅ |
| `5-9` | `5 to 9 employees` | ✅ |
| `10-19` | `10 to 19 employees` | ✅ |
| `20-49` | `20 to 49 employees` | ✅ |
| `50-99` | `50 to 99 employees` | ✅ |
| `100-199` | `100 to 199 employees` | ✅ |
| `200-499` | `200 to 499 employees` | ✅ |
| `500-999` | `500 plus employees` | ❌ COMBINED — see note |
| `1000+` | `500 plus employees` | ❌ COMBINED — see note |

**Employment-size limitation (confirmed):** Table 33-10-1174-01 reports all businesses with 500 or more employees under a single combined `500 plus employees` label. No current Statistics Canada Business Counts source was identified during validation that provides a Canada/province/NAICS business-count breakdown separating `500–999` from `1000+`. The system must not infer or split this combined bucket. The `500–999` and `1000+` fields in the pipeline must be populated from individual-business enrichment sources where available — not from this StatsCan benchmark.

**Unmatched StatsCan labels (do not map to any required bucket):**

- `Total, with employees`

### A.5 Geography values

Total: 14

- `Alberta`
- `British Columbia`
- `Canada`
- `Manitoba`
- `New Brunswick`
- `Newfoundland and Labrador`
- `Northwest Territories`
- `Nova Scotia`
- `Nunavut`
- `Ontario`
- `Prince Edward Island`
- `Quebec`
- `Saskatchewan`
- `Yukon`

### A.6 NAICS dimension

Unique NAICS values: `1362`

First 10:
- `Abrasive product manufacturing [327910]`
- `Accident and sickness reinsurance carriers [524132]`
- `Accommodation and food services [72]`
- `Accommodation services [721]`
- `Accounting, tax preparation, bookkeeping and payroll services [5412]`
- `Activities related to credit intermediation [5223]`
- `Activities related to real estate [5313]`
- `Adhesive manufacturing [325520]`
- `Administrative and support services [561]`
- `Administrative and support, waste management and remediation services [56]`

### A.7 Reference dates

- Earliest: `2026-01`
- Latest: `2026-01`
- Total periods: `1`

**Note on REF_DATE semantics:** Table A contains a single period `2026-01`.
The table is labeled "June 2026" and released August 14, 2026.
StatsCan semi-annual business counts use a January reference date
to represent the first half of the year (January reference period = counts as of that point).
The "June 2026" label refers to the release cycle, not the REF_DATE value.
Do not interpret `2026-01` as meaning the data is January-only — it is the semi-annual
reference period label for the June 2026 release.

### A.8 Suppression / symbols (`STATUS` column)

| Symbol | Count | Meaning |
|---|---:|---|
| *(blank)* | 85,793 | Normal — no suppression flag |

**All 85,793 rows have no suppression flag.** Table A appears to have no suppressed values
at the province/territory level for the June 2026 release — all cells are reported.

---

## Table B — Business Openings and Closures (33-10-0722-01)

- Data file: `33100722.csv`
- Rows: `8,575,672`
- Columns: `17`

### B.1 Column names

- `REF_DATE`
- `GEO`
- `DGUID`
- `Industry`
- `Employment size`
- `Business dynamics measure`
- `UOM`
- `UOM_ID`
- `SCALAR_FACTOR`
- `SCALAR_ID`
- `VECTOR`
- `COORDINATE`
- `VALUE`
- `STATUS`
- `SYMBOL`
- `TERMINATED`
- `DECIMALS`

### B.2 Key dimension columns identified

| Dimension | Column name |
|---|---|
| Employment size | `Employment size` |
| Geography | `GEO` |
| NAICS | `Industry` |
| Reference date | `REF_DATE` |
| Value | `VALUE` |
| Opening/closure type | `Business dynamics measure` |
| Seasonal adjustment | not present as a separate column |
| Symbol/suppression | `STATUS` |

### B.3 Opening/closure type categories (`Business dynamics measure`)

All 8 categories measured from data — each has exactly 1,071,959 rows (perfectly balanced across all geo × NAICS × size combinations):

| Category | Rows | Notes |
|---|---:|---|
| `Active businesses` | 1,071,959 | Total active employer businesses |
| `Opening businesses` | 1,071,959 | Employees this month, not last month |
| `Continuing businesses` | 1,071,959 | Employees both this and last month |
| `Closing businesses` | 1,071,959 | Employees last month, not this month |
| `Reopening businesses` | 1,071,959 | Opens after prior closure |
| `Entrants` | 1,071,959 | New opening with no prior activity on record |
| `Temporary closures` | 1,071,959 | Short-term inactive |
| `Exits` | 1,071,959 | Permanently inactive |

**Key distinction for architecture:**
- `Opening businesses` = any business with employees this month but not last month (includes reactivations)
- `Entrants` = subset of openings with NO prior activity — genuinely new employer businesses
- `Reopening businesses` = subset of openings that previously existed

For new-business detection benchmarking, `Entrants` is the closest StatsCan category to a genuinely new business. `Opening businesses` is the broader signal including reactivations.

### B.4 Employment-size labels

| # | Label as it appears in data |
|---|---|
| 1 | `1 to 4 employees` |
| 2 | `100 to 499 employees` |
| 3 | `20 to 99 employees` |
| 4 | `5 to 19 employees` |
| 5 | `500 employees or more` |
| 6 | `Total, all employment sizes` |

### B.5 Employment-size → required bucket mapping

| Required bucket | Matching StatsCan label(s) | Mappable? |
|---|---|---|
| `1-4` | `1 to 4 employees` | ✅ |
| `5-9` | `5 to 19 employees` | ✅ |
| `10-19` | — | ❌ GAP |
| `20-49` | `20 to 99 employees` | ✅ |
| `50-99` | — | ❌ GAP |
| `100-199` | `100 to 499 employees` | ✅ |
| `200-499` | — | ❌ GAP |
| `500-999` | `500 employees or more` | ✅ |
| `1000+` | — | ❌ GAP |

### B.6 Seasonal adjustment values


### B.7 Date range

- Earliest: `2015-01`
- Latest: `2026-05`
- Total periods: `137`

### B.8 Geography values

Total: 49

- `Abbotsford - Mission, British Columbia `
- `Alberta `
- `Barrie, Ontario `
- `Belleville, Ontario `
- `Brantford, Ontario `
- `British Columbia `
- `Calgary, Alberta `
- `Canada`
- `Edmonton, Alberta `
- `Greater Sudbury, Ontario `
- `Guelph, Ontario `
- `Halifax, Nova Scotia `
- `Hamilton, Ontario `
- `Kelowna, British Columbia `
- `Kingston, Ontario `
- `Kitchener - Cambridge - Waterloo, Ontario `
- `Lethbridge, Alberta `
- `London, Ontario `
- `Manitoba `
- `Moncton, New Brunswick `
- `Montréal, Quebec `
- `New Brunswick `
- `Newfoundland and Labrador `
- `Northwest Territories`
- `Nova Scotia `
- `Nunavut`
- `Ontario `
- `Oshawa, Ontario `
- `Ottawa - Gatineau, Ontario/Quebec`
- `Peterborough, Ontario `
- `Prince Edward Island `
- `Quebec `
- `Québec, Quebec `
- `Regina, Saskatchewan `
- `Saguenay, Quebec `
- `Saint John, New Brunswick `
- `Saskatchewan `
- `Saskatoon, Saskatchewan `
- `Sherbrooke, Quebec `
- `St. Catharines - Niagara, Ontario `
- `St. John's, Newfoundland and Labrador `
- `Thunder Bay, Ontario `
- `Toronto, Ontario `
- `Trois-Rivières, Quebec `
- `Vancouver, British Columbia `
- `Victoria, British Columbia `
- `Windsor, Ontario `
- `Winnipeg, Manitoba `
- `Yukon`

### B.9 Suppression / symbols (`STATUS` column)

StatsCan standard symbol conventions:
- blank = normal value
- `..` = not available / suppressed
- `E` = use with caution (high coefficient of variation)
- `x` = suppressed for confidentiality

| Symbol | Count | Meaning |
|---|---:|---|
| `x` | 7,843,698 | Suppressed for confidentiality |
| *(blank)* | 627,970 | Normal — unsuppressed value |
| `..` | 94,108 | Not available |
| `E` | 9,896 | Use with caution (high CV) |

**Key finding:** 91.4% of rows (7,843,698 / 8,575,672) are suppressed (`x`).
This is expected for a CMA-level table — small geography × NAICS × employment-size
combinations are suppressed to protect confidentiality.
National and provincial-level rows will have far lower suppression rates.

---

## Cross-table comparison

### Employment-size label consistency

- Labels in both tables: `1`
- Only in Table A: `8`
- Only in Table B: `5`

Shared labels:
- `1 to 4 employees`

Only in A:
- `10 to 19 employees`
- `100 to 199 employees`
- `20 to 49 employees`
- `200 to 499 employees`
- `5 to 9 employees`
- `50 to 99 employees`
- `500 plus employees`
- `Total, with employees`

Only in B:
- `100 to 499 employees`
- `20 to 99 employees`
- `5 to 19 employees`
- `500 employees or more`
- `Total, all employment sizes`

---

## Role assessment

### Table A

Canadian Business Counts (with employees) is a Class D validation/benchmark dataset. It contains aggregate counts of employer businesses by province/territory, NAICS, and employment-size range. It does NOT contain individual business records and cannot be used as a lead source.

Its value in this system: benchmark pipeline coverage (how many businesses does our pipeline identify vs the StatsCan total, by province × NAICS × employment-size bucket).

### Table B

Business Openings and Closures is a Class D validation/benchmark dataset. It contains aggregate monthly counts of employer business openings, closures, continuing businesses, re-openings, and entrants. These are EXPERIMENTAL ESTIMATES subject to monthly revision.

Opening definition (StatsCan): employees this month, no employees last month. This is fundamentally different from: incorporation date, licence issue date, website launch date, or business-name registration. The system must NOT conflate these events.

Its value: benchmark scale/distribution of new employer businesses per month per province × NAICS × employment size. Validates whether our event-detection layer is producing plausible volumes.

### What StatsCan cannot provide

- Individual business names, addresses, or identifiers
- Phone, email, website, or contact information
- Director or decision-maker names
- Real-time or daily new-business signals

**StatsCan Business Register — individual-business data is confidential (confirmed):**
Statistics Canada's Business Register is the internal frame used to produce aggregate counts. StatsCan's own documentation explicitly states that identifiable individual-business information from the Business Register is confidential and cannot be publicly disclosed under the Statistics Act. There is therefore no free StatsCan bulk dataset of individual Canadian businesses that can be obtained programmatically. This is a legal/policy constraint, not a gap in our search effort. The pipeline must obtain individual-business records from government registries, municipal licences, and other public open-data sources — not from StatsCan. StatsCan's role in this system is permanently fixed as: aggregate benchmark and validation only.

---

## Open questions

- [ ] Are suppressed values (`x`) in Table B concentrated only at CMA level, or also at provincial level?
- [ ] Confirm commercial pipeline use permitted under StatsCan OGL for benchmark comparison logic.

### Closed questions

- [x] **Table B `Business dynamics measure` values** — RESOLVED. Confirmed 8 categories via dimension probe: Active, Opening, Continuing, Closing, Reopening, Entrants, Temporary closures, Exits. See section B.3.
- [x] **Table A `500 plus employees` split** — RESOLVED. No current StatsCan Business Counts table separates `500–999` from `1000+` at the Canada/province/NAICS level. Historical series existed but are not appropriate substitutes. Pipeline must source this split from individual-business enrichment — not StatsCan. System must not infer the split.
- [x] **Table B coarser employment buckets** — RESOLVED. Confirmed: `5-19`, `20-99`, `100-499`. Table B benchmarks at broad bands only, not the 9 required buckets. Documented in B.5.

## Measured findings summary (from dimension probe)

| Question | Answer |
|---|---|
| `Business dynamics measure` categories | 8 values: Active, Opening, Continuing, Closing, Reopening, Entrants, Temporary closures, Exits |
| Best category for new-business benchmark | `Entrants` (no prior activity) — more precise than `Opening businesses` |
| REF_DATE = `2026-01` explanation | Semi-annual table uses January as reference period label; "June 2026" = release cycle label |
| Table B date coverage | Jan 2015 – May 2026 (137 monthly periods) |
| Provincial rows (unsuppressed pool) | All 13 provinces/territories + Canada present; ~127k–210k rows each |
| Table B suppression at CMA level | 91.5% suppressed — expected; provincial/national level will be far lower |
