# VR02 — Corporations Canada — Province Distribution + Monthly Transactions

**Date:** 2026-09-25
**Asset:** ASSET-02 (continued from VR01)
**Phase:** 2 — Source Validation
**Status:** ✅ Province distribution measured | ✅ Monthly transactions structure mapped

---

## 1. Province/Territory Distribution (Active CBCA Corps)

**Source file:** `data/raw/corporations-active-cbca-en.csv`
**Total rows:** 645,005

| Province/Territory | Corporations | % of total |
|---|---:|---:|
| `ON` | 446,144 | 69.17% |
| `QC` | 117,253 | 18.18% |
| `BC` | 28,502 | 4.42% |
| `AB` | 25,010 | 3.88% |
| `MB` | 9,216 | 1.43% |
| `NS` | 5,707 | 0.88% |
| `SK` | 5,091 | 0.79% |
| `NB` | 3,712 | 0.58% |
| `PE` | 2,148 | 0.33% |
| `NF` | 1,455 | 0.23% |
| `NU` | 297 | 0.05% |
| `NT` | 236 | 0.04% |
| `YT` | 234 | 0.04% |
| `<MISSING>` | 0 | 0.00% |

**Key observations:**
- ON + QC = 87.35% of all active federal CBCA corporations
- ON alone = 69.17% — heavily Ontario-skewed
- All 13 provinces/territories represented — no gaps
- 0 missing province values — province field is complete
- This distribution reflects where federal CBCA corps choose to register their office, not necessarily where they operate

---

## 2. Monthly Transactions — Structure Mapping

### 2.1 Index Page

**URL:** `https://ised-isde.canada.ca/site/corporations-canada/en/data-services/monthly-transactions`
**Size:** 24,179 characters
**Latest month linked:** June 2026 (URL slug: `monthly-transactions-june-2026`)

Only one month directly linked from the index — confirms GPT's finding that only the latest month is directly accessible. Older months require archive/contact access.

### 2.2 CBCA Incorporations Page

**URL:** `.../monthly-transactions/certificates-incorporation-cbca`
**Size:** 2,050,944 characters (2 MB)

This page is very large — 2 MB of HTML. This strongly suggests it contains a full listing of incorporation records (corp number + name + province + effective date), not just a summary table. The data is embedded in the HTML, not a separate CSV/JSON endpoint.

**Key implication:** To extract individual incorporation records, we need to parse this HTML page. It is not a bulk download — it is a rendered web page.

### 2.3 June 2026 Monthly Index

**URL:** `.../monthly-transactions/monthly-transactions-june-2026`
**Size:** 31,448 characters

This page links to all transaction type sub-pages for the month. Full transaction type list discovered:

**New business signals (relevant):**
- `certificates-incorporation-cbca` ← primary new-business signal
- `certificates-incorporation-coop-0`
- `certificates-incorporation-nfp-act`

**Change/lifecycle signals (relevant for status tracking):**
- `certificates-amendment-cbca-changes-registered-office`
- `certificates-amendment-cbca-name-changes`
- `certificates-amendment-cbca-other`
- `certificates-continuance-cbca`
- `certificates-discontinuance-cbca`
- `certificates-revival-cbca`
- `certificates-arrangement-cbca`

**Dissolution/end signals:**
- `certificates-dissolution-cbca-section-210-or-211`
- `certificates-dissolution-cbca-section-212`
- `certificates-intent-dissolve-cbca`
- `notice-intent-dissolve-corporations-canada-cbca-cbca`

**Correction signals:**
- `notices-correction-cancellation-certificates-cbca`

**Non-CBCA (NFP Act, Co-ops):**
- Separate pages for NFP Act and Co-op equivalents of all above

---

## 3. Critical Finding — Monthly Transactions Are HTML, Not Bulk CSV

The CBCA incorporations page is 2 MB of HTML. This means:

- Individual incorporation records are embedded in the page as rendered HTML tables/lists
- There is no direct CSV/ZIP download for this data
- Extraction requires HTML parsing (BeautifulSoup or similar)
- This is fundamentally different from the bulk CSV approach used for the active corps file

**Before writing a parser, GPT needs to:**
1. Inspect the actual HTML structure of the incorporations page to confirm fields (corp number, name, province, effective date)
2. Confirm whether this constitutes a bulk scrape or a legitimate data access method under the OGL terms
3. Determine if there is a machine-readable alternative (e.g. the API `activities[]` endpoint)

---

## 4. Role Assessment Update

Based on VR01 + VR02:

```
Corporations Canada — confirmed role breakdown:

Active CSV (daily bulk)
  → 645,005 federal identity records
  → Province, address, BN, corp number
  → No contacts, no employees, no NAICS
  → Role: federal identity/status layer

Monthly Incorporations page (HTML)
  → New CBCA registrations per month
  → Corp number + name + province + effective date (to be confirmed by HTML parsing)
  → Only latest month directly accessible
  → Role: federal new-registration signal (monthly granularity only)
  → NOT suitable for daily new-business detection by itself

API (not yet validated)
  → Director names, ISC, incorporation dates, real-time status
  → Role: targeted enrichment/verification
  → Needs its own validation pass
```

**Conclusion:** Corporations Canada cannot solve daily new-business detection alone. Monthly granularity + HTML-only format for transaction data means it is a supplementary signal, not a primary daily feed.

---

## 5. Open Questions for GPT

- [ ] Inspect HTML structure of the 2 MB incorporations page — what fields are actually in the table?
- [ ] Is HTML scraping of this page permitted under OGL terms or does it count as automated copying?
- [ ] Is there a machine-readable (JSON/CSV) endpoint for monthly transactions, or is HTML the only format?
- [ ] Is the June 2026 page the actual latest, or does July 2026 exist? (FR URL slug says `juillet-2026`)
- [ ] API validation: confirm `activities[]` endpoint exposes incorporation date programmatically

---

## 6. Scripts

| Script | Purpose |
| --- | --- |
| `scripts/profile_corps_province.py` | Province distribution from local CSV |
| `scripts/probe_corps_monthly_transactions.py` | Maps monthly transaction page structure |

*Part of VR02 — builds on VR01 (`VR01_CORPORATIONS_CANADA.md`)*
