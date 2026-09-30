# Research Round 04 — Statistics Canada: Business Counts + Openings/Closures

**Date:** 2026-09-25
**Source:** GPT research pass — Statistics Canada Canadian Business Counts (June 2026), Monthly Business Openings and Closures
**Status:** Research complete — local CSV download/profiling recommended as next step

---

## TL;DR

Statistics Canada gives us excellent national benchmarks for employee size, industry, geography, and business dynamics.
These are **aggregate datasets only** — no individual business names, addresses, or contacts.
They cannot generate leads. They validate and benchmark what our pipeline collects.
The opening/closure dataset also provides a critical conceptual clarification: "opening business" ≠ "newly incorporated corporation" — they measure different events.

---

## 1. Canadian Business Counts — June 2026

**Table:** 33-10-1174-01 — Canadian Business Counts, with employees, June 2026
**Released:** August 14, 2026
**Frequency:** Semi-annual
**Licence:** Open Government Licence – Canada
**Format:** CSV, XML (machine-readable)
**Cost:** Free

Provides business-location counts broken down by:
- Geography (Canada + provinces/territories)
- Employment-size range
- NAICS

**Companion table:** 33-10-1176-01 — Canadian Business Counts, with employees, CMA and CSD, June 2026
- Extends geography to Census Metropolitan Areas (CMAs) and Census Subdivisions (CSDs)
- Useful for city/municipality-level validation

**Separate table:** 33-10-1175-01 — Canadian Business Counts, **without employees**, June 2026
- Important: distinguishes businesses-with-employees from businesses-without-employees
- Reinforces: missing employee count ≠ zero employees (same finding as ODBus)

---

## 2. What Business Counts Can and Cannot Do

| Capability | Business Counts |
| --- | --- |
| Individual business names | ❌ |
| Addresses | ❌ |
| Phone / email / website | ❌ |
| Corporation ID | ❌ |
| Province aggregate | ✅ |
| CMA aggregate | ✅ |
| CSD aggregate | ✅ (separate table) |
| NAICS breakdown | ✅ |
| Employee-size breakdown | ✅ |
| New-business signal | ❌ |
| Benchmarking | ✅ — primary use |

**Use this for:** validating pipeline coverage by province × NAICS × employee size
**Do NOT use this for:** individual lead generation, employee count enrichment for specific companies

---

## 3. Employee-Size Coverage — Important Caveat

The dataset provides employment-size ranges, but the **exact published category labels** have not yet been verified against our required nine buckets:

```
1–4 / 5–9 / 10–19 / 20–49 / 50–99 / 100–199 / 200–499 / 500–999 / 1000+
```

The catalogue confirms the employment-size dimension exists, but the complete category definitions need to be confirmed from the actual downloaded CSV — not assumed from catalogue metadata.

**Action required:** Download and inspect the actual CSV to verify label mapping.

---

## 4. Multi-Location Business Limitation

A single business operating in multiple industries or geographies can appear in counts for each.
Do NOT sum arbitrary cells and interpret the result as unique companies.
This affects how the benchmark is used — comparisons should be made at consistent geographic + NAICS + size levels, not across aggregated sums.

---

## 5. Monthly Business Openings and Closures

**Table:** 33-10-0722-01 — Experimental estimates for business openings and closures by employment size
**Frequency:** Monthly
**History:** January 2015 onward
**Geography:** Canada / provinces / territories / CMAs
**NAICS:** 2-digit
**Employee size:** Yes
**Licence:** Open Government Licence – Canada
**Status:** Explicitly marked as **experimental estimates** — subject to revision

### Definitions (Statistics Canada)

| Term | Definition |
| --- | --- |
| Opening | Business has employees this month but did not last month |
| Closure | Business had employees last month but does not this month |
| Continuing | Business has employees in both months |
| Reopening | Business opens again after previously being active |
| Entrant | Opening business that was not previously active |

Underlying methodology uses CRA PD7 payroll deduction files + Statistics Canada Business Register.

---

## 6. Critical Finding — "Opening" ≠ "Newly Incorporated"

This is the most important conceptual finding from this round.

Statistics Canada's "opening" is based on **employment/payroll activity**, not corporate registration.

```
Corporations Canada: New incorporation
        ≠
Statistics Canada: Opening business
```

**Example:**
```
ABC Telecom Ltd.
  → Incorporated: January 2026  (Corporations Canada signal)
  → First employees/payroll: April 2026  (Statistics Canada opening signal)
```

Neither is wrong — they measure different stages of the business lifecycle.

**Implication for our system:** New-business detection should preserve multiple event types rather than collapsing everything into one `new_business = true` flag.

We now have at least three distinct lifecycle signal types:

| Signal type | Source | Event measured |
| --- | --- | --- |
| Corporate registration | Corporations Canada / provincial registries | Entity legally incorporated |
| Licence registration | Ontario Select Licence, ODBus, etc. | Business obtained a regulated licence |
| Employment opening | Statistics Canada | Business began having employees/payroll |

These can happen at different times for the same business.

---

## 7. What Openings/Closures Can and Cannot Do

| Capability | Openings/Closures |
| --- | --- |
| Individual business names | ❌ |
| Addresses / contact info | ❌ |
| Monthly new-business count | ✅ aggregate |
| Monthly closure count | ✅ aggregate |
| Reopening / entrant distinction | ✅ aggregate |
| Province-level breakdown | ✅ |
| CMA-level breakdown | ✅ |
| NAICS breakdown | ✅ 2-digit |
| Employee-size breakdown | ✅ |
| Daily / 7-day / 30-day individual list | ❌ — monthly aggregate only |
| Direct support for assignment's daily/7-day view | ❌ |

**The assignment requires daily/7-day/30-day individual-business views.**
Statistics Canada's monthly aggregate cannot supply those views.
It can only tell us if our observed monthly patterns are wildly inconsistent with national/provincial trends.

---

## 8. Experimental Data and Revisions

The opening/closure series is **explicitly experimental**.
Every new month can revise earlier estimates due to:
- Seasonal adjustment
- New version/vintage of the Business Register

Do not treat historical numbers as permanently immutable.
Do not cite specific monthly counts as definitive figures.

---

## 9. How to Use These Datasets in Our Pipeline

### Business Counts — validation use cases

- After collecting Ontario businesses, compare province × NAICS × employee-size distribution against Statistics Canada
- If our pipeline shows 3% of Ontario businesses in 1–4 bucket but StatsCan shows 60%, we know we're missing most micro-businesses
- Identify suspicious over/under-representation per province/industry

### Openings/Closures — benchmark use cases

- After building new-business detection, compare our monthly "new business" counts against StatsCan opening estimates
- Identify whether our pipeline captures a plausible share of business openings
- Validate that our closure/inactive signals track against StatsCan closures

---

## 10. Source Architecture Position

These datasets now clearly belong to a separate class from the discovery sources:

**Discovery / individual lead sources:**
- ODBus — historical broad discovery
- Corporations Canada — federal legal entities + corporate events
- Ontario Select Licence — current specialized businesses + contact info
- BC OrgBook — targeted BC legal-entity verification

**Statistical validation sources:**
- Canadian Business Counts → benchmark by geography × NAICS × employee size
- Monthly Openings/Closures → benchmark business dynamics by month × geography × NAICS × size

Keeping these classes separate prevents a common mistake: using aggregate statistics as if they were individual records.

---

## 11. Confirmed Source Profiles

### ASSET-04a — Canadian Business Counts (with employees)

| Dimension | Finding |
| --- | --- |
| Table | 33-10-1174-01 |
| Publisher | Statistics Canada |
| Current release | June 2026 |
| Frequency | Semi-annual |
| Geography | Canada + provinces/territories |
| Companion table | CMA + CSD (33-10-1176-01) |
| NAICS | Yes |
| Employee size | Yes (exact labels need CSV verification) |
| Individual businesses | No |
| Licence | OGL – Canada |
| Format | CSV, XML |
| Cost | Free |
| Role | Class D — validation/benchmark |

### ASSET-04b — Canadian Business Counts (without employees)

| Dimension | Finding |
| --- | --- |
| Table | 33-10-1175-01 |
| Publisher | Statistics Canada |
| Current release | June 2026 |
| Frequency | Semi-annual |
| Purpose | Distinguishes businesses with vs without employees |
| Role | Class D — benchmark; reinforces: missing count ≠ zero |

### ASSET-04c — Monthly Business Openings and Closures

| Dimension | Finding |
| --- | --- |
| Table | 33-10-0722-01 |
| Publisher | Statistics Canada |
| Frequency | Monthly |
| History | January 2015 onward |
| Geography | Canada / provinces / territories / CMAs |
| NAICS | 2-digit |
| Employee size | Yes |
| Opening definition | Employees this month, not last month |
| Closure definition | Employees last month, not this month |
| Status | Experimental — subject to revision |
| Individual businesses | No |
| Licence | OGL – Canada |
| Format | CSV, XML |
| Cost | Free |
| Role | Class D — benchmark for new-business/closure patterns |

---

## 12. Next Actions

- [ ] Download June 2026 Business Counts CSV → place in `data/raw/` → inspect exact employment-size labels, NAICS levels, geography values, suppression markers
- [ ] Download CMA/CSD companion table → validate city-level breakdown granularity
- [ ] Download "without employees" table → confirm category alignment
- [ ] Download Monthly Openings/Closures → inspect column names, geography levels, NAICS, employment-size categories
- [ ] Write `scripts/inspect_statscan_business_counts.py` to profile these files and output a benchmark reference document
- [ ] Confirm exact employment-size label mapping against our 9 required buckets
