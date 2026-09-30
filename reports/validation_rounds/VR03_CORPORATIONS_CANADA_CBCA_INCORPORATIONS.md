# VR03 — Corporations Canada CBCA Incorporations

Generated: `2026-09-25T12:08:21.723733+00:00`

## Source

- URL: `https://ised-isde.canada.ca/site/corporations-canada/en/data-services/monthly-transactions/certificates-incorporation-cbca`
- Publisher: Innovation, Science and Economic Development Canada
- Dataset: Monthly Transactions — Certificates of Incorporation (CBCA)
- Format: HTML table

## Record count

- Parsed records: `6,890`

## Fields

| Field | Missing |
|---|---:|
| *(none missing)* | 0 |

## Effective-date range

- Minimum: `2026-04-08`
- Maximum: `2026-10-12`

## Province distribution

| Registered office | Records |
|---|---:|
| `ON` | 5,218 |
| `QC` | 664 |
| `BC` | 335 |
| `AB` | 311 |
| `MB` | 120 |
| `NS` | 75 |
| `SK` | 66 |
| `NB` | 53 |
| `NL` | 26 |
| `PE` | 17 |
| `NU` | 2 |
| `YT` | 2 |
| `NT` | 1 |

## Duplicate corporation numbers

- Duplicate IDs: `0`


## Malformed dates

- Count: `0`


## Transaction type classification (from GPT research)

| Transaction | Research value |
|---|---|
| Incorporation | New federal registration signal |
| Amalgamation | Entity relationship/change signal |
| Name change | Identity resolution signal |
| Registered-office change | Address refresh signal |
| Other amendment | Potential attribute-change signal |
| Continuance | Entity identity/lifecycle signal |
| Discontinuance | Entity lifecycle/geography signal |
| Revival | Reactivation signal |
| Dissolution | Churn/inactive signal |
| Intent to dissolve | Early lifecycle warning |
| Correction/cancellation | Data-quality/event correction |
| Arrangement | Corporate structural event |

## Architecture notes

- Only the latest month is available on the website.
  Older months require contacting Corporations Canada.
  Production job must capture and archive locally on publication.

- OGL permits commercial reuse with attribution.
  Automation rate/frequency must still respect site terms and robots.txt.
  Do not mark scraping as unconditionally permitted based on OGL alone.

## Research interpretation

This is an official Corporations Canada publication under the Monthly Transactions section. The currently published CBCA incorporation table contains multiple effective-date months; the exact publication-window semantics require further validation. Do not assume a single-month feed — the page may be a rolling window, a fiscal-period accumulation, or an incrementally updated table where older records remain visible.

The effective date must not automatically be interpreted as the date the business began operating. It represents the effective date of the incorporation transaction.

This source represents a federal registration event signal, not a complete operating-business opening signal. It must be combined with provincial/territorial registry events, municipal licensing data, and other operating signals for Canada-wide new-business detection.

## Recommended production model

```
Fetch published CBCA incorporation table
    → Archive raw HTML snapshot + retrieval timestamp

Parse corporation number + effective date
    → Compare against previous snapshot
    → Identify newly observed records

Store event with:
    corporation_number
    effective_date
    source = corporations_canada_monthly_transactions
    retrieval_date = when our system observed it
```

Note: do not hard-code month-boundary assumptions. Use snapshot diffing to detect
additions regardless of how ISED changes the publication window over time.

## Open questions

- [ ] **VR03.1 (pending — time-dependent):** Download the page again after 24–48 hours, diff corporation numbers against the current snapshot. Determines whether the page is a rolling window, a period accumulation, or incrementally updated. Resolves the production ingestion model.
- [ ] What is the exact publication-window policy? Does ISED publish a new page each month and retire the old one, or does the same URL accumulate records?
- [ ] Are future-dated effective dates (e.g. 2026-10-12 observed on 2026-09-25) pre-approved incorporations or data artifacts?
- [ ] Confirm robots.txt and crawl-delay for this domain before production automation.

## Confirmed event fields for production use

| Field | Automation value |
|---|---|
| `Corporation Number` | Strong federal entity/event identifier |
| `Name of Corporation` | Initial business identity |
| `Registered Office` | Geographic signal (province) |
| `Effective Date` | Incorporation-event date |
| `retrieval_date` (derived) | When our system observed the record |
