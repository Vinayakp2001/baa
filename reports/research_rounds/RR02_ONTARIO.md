# Research Round 02 — Ontario

**Date:** 2026-09-25
**Source:** GPT research pass — Ontario Data Catalogue, Select Licence and Registration Data, Ontario Business Registry, specialized Ontario datasets
**Status:** Research complete — no download/profiling done yet

---

## TL;DR

Ontario does NOT have a free general-purpose bulk business registry equivalent to Corporations Canada.
What Ontario DOES have is a useful ecosystem of specialized licensed-business datasets.
The most valuable confirmed source is Select Licence and Registration Data — current, monthly, machine-readable, and unusually field-rich (phone + email + website + operating name).
But it only covers 6 specific licence types — it is not the Ontario business universe.

---

## 1. Select Licence and Registration Data — Confirmed High-Value Specialized Source

**Catalogue URL:** Ontario Data Catalogue — Select Licence and Registration Data
**Licence:** Open Government Licence – Ontario
**Update frequency:** Monthly
**Last updated:** September 11, 2026 (August 2026 data)
**Formats:** CSV, TSV, JSON, XML, CKAN Data API

### Business licence types currently covered

- Collection Agency
- Consumer Reporting Agency
- Distributor — Ontario-wide
- Lender
- Loan Broker
- Bailiff (Business)

### Confirmed fields — Business dataset

| Field | Present |
| --- | --- |
| Legal name | ✅ |
| Operating / DBA name | ✅ |
| Street address | ✅ |
| City | ✅ |
| Province | ✅ |
| Postal code | ✅ |
| Country | ✅ |
| Telephone | ✅ |
| Website | ✅ |
| Email | ✅ |
| Licence type | ✅ |
| Licence number | ✅ |
| Licence status | ✅ |
| Expiry date | ✅ |

**Key point:** This source directly provides phone + website + email — fields that are completely absent from Corporations Canada bulk CSV.

### What it does NOT contain

- General incorporation/registration date
- Employee count / size bucket
- NAICS / industry (licence type only)
- Decision-maker hierarchy (president, GM, IT, etc.)
- General Ontario business population

---

## 2. Critical Caveat — Not the Ontario Business Universe

This is a list of businesses holding 6 specific regulated licence types.

A manufacturer, restaurant, software company, trucking company, or construction company will NOT appear here simply because it is an Ontario business.

**Use this as:** specialized licence/business enrichment source
**Do NOT use this as:** Ontario master business discovery source

---

## 3. Licence Status + Expiry Date as Change Signals

The dataset contains `licence status` and `expiry date`.

Potentially useful for detecting:
- Active vs inactive licensed business
- Licence approaching expiry
- Licence no longer valid
- New records appearing between monthly snapshots

**Important semantic distinction:**
```
new licence record ≠ new business
```
A business may have existed for years and recently obtained one of these licences.
Record this distinction explicitly — do not conflate licence creation with business creation.

---

## 4. Individual Dataset — Confirmed Useful for Person-Business Linking

Ontario also publishes a separate **Individual** dataset.

### Individual licence types currently covered

- Bailiff — Owner
- Bailiff — Employee
- Bailiff — Assistant (Reg)
- Bailiff — Assistant (Appointed)
- Personal Information Investigator

### Confirmed fields — Individual dataset

- First name, last name
- Legal name of employing business/organization
- Operating name
- Workplace address, city, province, postal code
- Telephone, website, email
- Licence type, licence number, expiry date

### Why this matters

This is one of the first sources found that explicitly connects:
```
Person → Business → Contact information → Licence role
```

For covered professions, the "Owner" licence type gives a stronger ownership signal than inferring ownership from a company website.

**Caveat:** Only applies to the specific regulated occupations listed above — do not generalize to all Ontario employees or decision-makers.

---

## 5. Ontario Business Registry — General Bulk Export NOT Found

Searched the current Ontario Data Catalogue specifically for a free general-purpose bulk export of all Ontario registered businesses.

**Result:** Not found.

The Ontario Business Registry Partner Portal dataset exists but is NOT the registry itself — it is a list of authorized intermediary organizations with fields: organization name, business category, email, city, phone, website.
Not useful as Ontario business universe.

---

## 6. Ontario Environment Business Directory — Mark as STALE

- Contains 900+ Ontario environmental companies
- Has company names, sector, website, contact, location, description
- **Has NOT been updated since 2019**
- Catalogue explicitly marks it for historical reference only

**Decision:** Do not use as a current production source. Mark stale in tracker.

---

## 7. Ontario Has a Large Ecosystem of Specialized Datasets

The broader Ontario catalogue contains many specialized business/registrant datasets:

- Community Small Business Investment Funds (has name, address, contact, registration date)
- Labour Sponsored Investment Funds
- Tobacco tax registrant lists
- Fuel/gasoline tax registrant lists
- Dairy distributors
- Licensed contractors
- Regulated industry directories

**Key insight for architecture:**
```
Ontario's open data isn't one "business registry."
It is many specialized registries that together can cover different industry verticals.
```
This is the same pattern as ODBus — a collection of government datasets is collectively more powerful than any single one.

**Next action:** Systematically mine the Ontario catalogue for all datasets containing individual business records — do not stop at Select Licence and Registration Data.

---

## 8. Cross-Source Field Comparison (After 2 Rounds)

| Assignment field | Corporations Canada | Ontario Select Licence |
| --- | --- | --- |
| Legal name | ✅ | ✅ |
| Operating name | Via API name history | ✅ |
| Address | ✅ | ✅ |
| Postal code | ✅ | ✅ |
| Phone | ❌ | ✅ |
| Email | ❌ | ✅ |
| Website | ❌ | ✅ |
| Licence/reg. status | ✅ | ✅ |
| Incorporation date | API activities[] | ❌ |
| Industry / NAICS | ❌ | Licence type only |
| Employees | ❌ | ❌ |
| Directors | ✅ (API) | ❌ |
| Owner signal | ISC + directors | "Owner" licence role (narrow) |
| Decision-maker title | ❌ | ❌ |
| New-business signal | Strong (federal) | New licence only (not new business) |
| Freshness | Daily | Monthly |

This confirms: multiple sources are required. No single source solves the full assignment.

---

## 9. Source Quality Distinctions for Ontario

Not all Ontario government sources are equivalent:

| Source | Type | Strength | Limitation |
| --- | --- | --- | --- |
| Select Licence and Registration | Government, monthly | Strong evidence, phone/email/web | Only 6 licence types |
| Ontario Env. Business Directory | Government, stale | Historical only | Not updated since 2019 |
| Municipal business directories | Government, varies | Current individual businesses | Geographically limited |
| Specialized tax/industry registrants | Government, varies | Strong for regulated industries | Narrow industry population |

---

## 10. What NOT to Conclude From This Round

- Ontario Select Licence = Ontario master dataset ❌
- Ontario Business Registry bulk data is available for free ❌
- Licence appearance = new business ❌
- Licensed individual = general business decision-maker ❌
- All Ontario companies can be linked to this dataset ❌
- This source solves Ontario contact enrichment generally ❌

---

## 11. Confirmed Source Profile

| Dimension | Finding |
| --- | --- |
| Source name | Ontario Select Licence and Registration Data |
| Source type | Provincial government licence dataset |
| Coverage | Ontario — 6 specific licence types only |
| Individual records | Yes |
| Freshness | Monthly (August 2026 current) |
| API / machine-readable | Yes — CKAN Data API + CSV/JSON/XML |
| Legal name | Yes |
| Operating name | Yes |
| Address + postal code | Yes |
| Phone | Yes |
| Email | Yes |
| Website | Yes |
| Licence status + expiry | Yes |
| Incorporation date | No |
| Employee count | No |
| NAICS | No (licence type only) |
| Directors | No |
| Licence | OGL – Ontario |
| Cost | Free |
| Automation permitted | Yes |
| Role | Class A specialized (6 licence types) + Class C enrichment |

---

## 12. Next Actions

- [ ] Download August 2026 business dataset — profile fields, record count, coverage
- [ ] Download August 2026 individual dataset — validate person-business link quality
- [ ] Systematically inventory the Ontario catalogue for all other individual-business datasets
- [ ] Assess Community Small Business Investment Funds dataset (has registration date)
- [ ] Check which Ontario municipal portals have been updated since ODBus v1 (2022)
- [ ] Confirm OGL – Ontario permits commercial use
