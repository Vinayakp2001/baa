# VR01 — Corporations Canada (Federal) — Validation Report

**Date:** 2026-09-25
**Asset:** ASSET-02
**Phase:** 2 — Source Validation
**Status:** ✅ VALIDATED (active business corporations CSV profiled)

---

## 1. Source Location

| Item | Value |
| --- | --- |
| Open Government Portal | https://open.canada.ca/data/en/dataset/0032ce54-c5dd-4b66-99a0-320a7b5e99f2 |
| Data services page | https://ised-isde.canada.ca/site/corporations-canada/en/data-services |
| Publisher | Innovation, Science and Economic Development Canada |
| Licence | Open Government Licence – Canada (commercial use permitted) |
| Update frequency | Typically daily |

> Note: The old dataset ID `ab7df418-afa0-4f8c-9f58-c5f74e5e7a37` and all ised-isde.canada.ca direct ZIP paths are dead (HTTP 404). The new dataset ID is `0032ce54-c5dd-4b66-99a0-320a7b5e99f2` and files are served from CloudFront.

---

## 2. Dataset Structure — All 4 Splits Confirmed Accessible

| Dataset | URL | HTTP | Size |
| --- | --- | --- | --- |
| Active business corps (CBCA) | https://d4bf66bykfyaf.cloudfront.net/corporations-active-cbca-en.csv | 200 ✅ | 98.8 MB |
| Other active corps (non-CBCA) | https://d4bf66bykfyaf.cloudfront.net/corporations-active-non-cbca-en.csv | 200 ✅ | 8.8 MB |
| Inactive business corps (CBCA) | https://d4bf66bykfyaf.cloudfront.net/corporations-inactive-or-dissolved-cbca-en.csv | 200 ✅ | 150.1 MB |
| Other inactive corps (non-CBCA) | https://d4bf66bykfyaf.cloudfront.net/corporations-inactive-or-dissolved-non-cbca-en.csv | 200 ✅ | 8.1 MB |

All 4 files: `text/csv; charset=utf-8`, no auth required, direct download.

---

## 3. Active Business Corporations CSV — Full Profile

**File:** `corporations-active-cbca-en.csv`
**Size:** 98.80 MB
**Rows:** 645,005
**Columns:** 18

### 3.1 Columns

| # | Column | Missing | Missing % | Notes |
| --- | --- | --- | --- | --- |
| 1 | `Corporation number` | 0 | 0.00% | Primary stable federal ID |
| 2 | `Business number (BN)` | 1,580 | 0.24% | CRA cross-source matching key |
| 3 | `Corporate name - form 1` | 0 | 0.00% | Primary legal name |
| 4 | `Corporate name - form 2` | 616,476 | 95.58% | Alternate name — rarely used |
| 5 | `Governing legislation` | 0 | 0.00% | All = "Canada Business Corporations Act" |
| 6 | `Status` | 0 | 0.00% | All = "Active" in this file |
| 7 | `Status Detail` | 617,473 | 95.73% | Edge cases only (e.g. dissolution pending) |
| 8 | `Anniversary date` | 0 | 0.00% | Annual return anniversary — NOT incorporation date |
| 9 | `Year of last annual filing` | 154,016 | 23.88% | Missing for ~24% of corps |
| 10 | `Date of last annual meeting` | 220,978 | 34.26% | Missing for ~34% of corps |
| 11 | `Street` | 50 | 0.01% | Registered office |
| 12 | `Street 2` | 548,315 | 85.01% | Suite/unit — usually blank |
| 13 | `City/town` | 1 | 0.00% | Near-complete |
| 14 | `Province/territory` | 0 | 0.00% | 100% present — distribution not yet captured (see open questions) |
| 15 | `Country` | 0 | 0.00% | All = "CA" |
| 16 | `Postal code` | 4 | 0.00% | Near-complete |
| 17 | `Minimum number of directors` | 5 | 0.00% | Integer — not names |
| 18 | `Maximum number of directors` | 5 | 0.00% | Integer — not names |

### 3.2 Status Distribution

| Status | Rows |
| --- | --- |
| Active | 645,005 |

All rows in this file are Active — this is expected (file is the active subset).

### 3.3 Province/Territory Distribution

Not captured in this run — the profiler had a column name case mismatch (`Province/territory` vs expected `Province/Territory`). Distribution must be measured in a follow-up pass.

### 3.4 Director Range Distribution (sample)

| Min directors | Rows |
| --- | --- |
| 1 | 632,383 |
| 2 | 9,175 |
| 3 | 2,807 |
| 4+ | 640 |

Note: these are director count limits, not actual director names. Director names are in the API only.

### 3.5 Sample Records

```
Corporation number: 8660115
Business number (BN): 835752437
Corporate name - form 1: MINDANGLER CAPITAL INC.
Status: Active
Anniversary date: 2013-10-10
Year of last annual filing: 2025
Street: 515 Legget Drive, Suite 800
City/town: Ottawa
Province/territory: ON
Postal code: K2K 3G4

Corporation number: 821080
Business number (BN): 100094283
Corporate name - form 1: AIRMEC CLIMATISATION LTEE
Status: Active
Status Detail: Active - Dissolution Pending (non-compliance)
Anniversary date: 1979-02-26
Year of last annual filing: 2000
Street: 7961 RUE VAUBAN
City/town: ANJOU
Province/territory: QC
Postal code: H1J2V1
```

---

## 4. Confirmed Field Availability

| Field | Available in bulk CSV | Notes |
| --- | --- | --- |
| Corporation number | ✅ | 100% present |
| Business Number (BN) | ✅ | 99.76% present |
| Legal name | ✅ | 100% present |
| Status | ✅ | 100% present |
| Registered address | ✅ | Near-complete |
| Province/territory | ✅ | 100% present (distribution pending) |
| Postal code | ✅ | Near-complete |
| Anniversary date | ✅ | 100% present |
| Year of last filing | ⚠️ | 23.88% missing |
| Director min/max count | ✅ | Integer limits only |
| Director names | ❌ | API only |
| ISC (ownership/control) | ❌ | API only |
| Incorporation date | ❌ | API `activities[]` only |
| Employee count | ❌ | Not available anywhere in this source |
| NAICS / industry | ❌ | Not available anywhere in this source |
| Phone / email / website | ❌ | Not available anywhere in this source |

---

## 5. Standardized Source Profile

```
SOURCE:               Corporations Canada — Active Business Corporations (CBCA)
ASSET:                ASSET-02
CATEGORY:             Federal corporate registry
ACCESS:               Direct CSV download — no auth, no API key required
PROGRAMMATIC ACCESS:  YES — confirmed
ROWS (active CBCA):   645,005
COLUMNS:              18
FILE SIZE:            98.80 MB
CURRENTNESS:          Daily update (publisher-stated)
INDIVIDUAL RECORDS:   YES

IDENTIFIERS:
  Corporation number  — 100% present, primary stable key
  Business Number (BN) — 99.76% present, CRA cross-source key

GEOGRAPHIC COVERAGE:  Federal CBCA corporations — all provinces/territories
                      Does NOT cover provincial/territorial corps, sole props, partnerships

EMPLOYEES:            NOT AVAILABLE
NAICS:                NOT AVAILABLE
PHONE:                NOT AVAILABLE
EMAIL:                NOT AVAILABLE
WEBSITE:              NOT AVAILABLE
DIRECTOR NAMES:       NOT IN BULK CSV — API only
ISC / OWNERSHIP:      NOT IN BULK CSV — API only
INCORPORATION DATE:   NOT IN BULK CSV — API activities[] only

NEW BUSINESS SIGNAL:  Partial — anniversary date present; incorporation date requires API
                      Monthly transactions dataset (not yet profiled) is the stronger signal

PRIMARY ROLE:         Federal identity + status layer
SECONDARY ROLE:       Change detection (via monthly transactions — pending)
TERTIARY ROLE:        Decision-maker enrichment (via API directors/ISC — pending)

LIMITATIONS:
  — Federal CBCA corps only (~645k active)
  — Provincial/territorial corps not covered
  — No contact or employee data
  — Province distribution not yet measured

LICENCE:              Open Government Licence – Canada
VALIDATION STATUS:    VALIDATED (active CBCA CSV)
PENDING:              Inactive CSV, other active/inactive, monthly transactions, API
```

---

## 6. Open Questions

- [ ] Province/territory distribution — run targeted profiling pass (column name fix needed)
- [ ] Profile inactive CBCA CSV (150 MB — will show dissolved/historical corps)
- [ ] Profile monthly transactions dataset — what transaction types exist for new-business detection?
- [ ] API: is ISC accessible programmatically or only via web UI?
- [ ] What % of all Canadian businesses are federal CBCA corps? (requires cross-source overlap)
- [ ] Sample-match federal corps against ODBus by name + postal code to measure overlap

---

## 7. Scripts

| Script | Purpose |
| --- | --- |
| `scripts/discover_corporations_dataset.py` | URL accessibility check for all 4 splits |
| `scripts/profile_corporations_canada.py` | Downloads and profiles the active CBCA CSV |

*Machine-readable: `reports/validation_rounds/VR01_CORPORATIONS_CANADA.json`*
