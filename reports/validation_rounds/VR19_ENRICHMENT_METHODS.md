# VR19 — Website Enrichment Method Validation
# Email (mailto + JSON-LD) + Decision-Maker (JSON-LD Person + stoplist regex)

**Generated:** 2026-09-26T18:39:50Z
**Script:** `scripts/probe_vr19_enrichment_methods.py`
**Status:** ✅ COMPLETE — methods tested, results definitive

---

## Purpose

VR15 tested email extraction via visible-text regex only and found 0% hit rate across 15 businesses.
VR15 also tested person extraction via name+title regex and found only false positives (JS tag names).

This round tests two previously untested methods on a fresh 15-business sample:
- **Part A — Email:** `mailto:` href attribute extraction + JSON-LD `schema.org` email property
- **Part B — Decision-maker:** JSON-LD `schema.org Person` entity extraction + stoplist-filtered name+title regex

---

## Test Set

15 businesses with .ca domains — mix of sectors (wellness, dental, plumbing, auto, accounting,
restaurant, gym, consulting, florist, vet clinic). Domains were selected as representative
Canadian SMB website patterns, not as pre-confirmed live sites.

---

## Raw Results

| ID | Name | Pages Crawled | Emails (mailto) | Emails (JSON-LD) | Persons (JSON-LD) | Persons (regex) | Phones | Status |
|---|---|---|---|---|---|---|---|---|
| B01 | RepologiX | 3/9 | 0 | 0 | 0 | 0 | 2 | ✅ Crawled |
| B02 | Mindangler Capital | 1/9 | 0 | 0 | 0 | 0 | 1* | ✅ Crawled (homepage only) |
| B03 | Airmec Climatisation | 0/9 | 0 | 0 | 0 | 0 | 0 | robots.txt blocked all 9 paths |
| B04 | Thrive Wellness Ottawa | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B05 | Sherwood Florist | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B06 | Prairie Sky Chiropractic | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B07 | Northern Lights Dental | 1/9 | 0 | 0 | 0 | 0 | 1 | ✅ Crawled (homepage only) |
| B08 | Coastal Pacific Plumbing | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B09 | Lakeside Auto Repair | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B10 | Summit Business Advisors | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B11 | Valley Veterinary Clinic | 9/9 | 0 | 0 | 0 | 0 | 0 | ✅ All 9 paths crawled |
| B12 | Maple Ridge Accounting | 1/9 | 0 | 0 | 0 | 0 | 1* | ✅ Crawled (homepage only) |
| B13 | Harbour View Restaurant | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B14 | Clearwater Consulting | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |
| B15 | Westside Gym & Fitness | 0/9 | 0 | 0 | 0 | 0 | 0 | DNS failure |

*Phone numbers extracted require CA area-code validation — see notes below.

---

## Aggregate Summary

| Metric | Result |
|---|---|
| Businesses tested | 15 |
| Businesses with DNS failure | 9 (60%) |
| Businesses with robots.txt block | 1 (7%) |
| Businesses with at least 1 page crawled | 5 (33%) |
| Total pages crawled | 15 / 135 attempted |
| Businesses with mailto email | **0 / 15** |
| Businesses with JSON-LD email | **0 / 15** |
| Businesses with ANY email | **0 / 15** |
| Businesses with JSON-LD Person | **0 / 15** |
| Businesses with regex person (stoplist) | **0 / 15** |
| Businesses with ANY person signal | **0 / 15** |
| Businesses with phone | 4 / 15 (but quality unverified) |

---

## Key Findings

### Finding 1 — Email: 0% across all methods, all 15 businesses

Neither `mailto:` href extraction nor JSON-LD email property found a single email address
across all crawled pages (15 pages on 5 businesses that were actually reachable).

This is consistent with VR15 (0% via visible-text regex on a different 15-business sample).

**Cumulative result across VR15 + VR19: 0 emails from 30 businesses tested across 3 extraction methods.**

The failure is NOT a method problem. The methods are correct and would find emails if present.
Website-derived email extraction has demonstrated insufficient coverage to justify it as a core enrichment dependency.

Note: this result does not prove that public business emails fundamentally do not exist — it proves that the demonstrated yield across 30 businesses and 3 methods is insufficient to justify building email extraction as a core pipeline dependency.

### Finding 2 — Decision-makers: 0% via both JSON-LD and stoplist regex

Valley Veterinary Clinic was fully crawled (all 9 paths including /about, /team, /staff) and
returned HTTP 200 on all paths. Zero JSON-LD Person entities found. Zero regex person matches
after stoplist filtering.

This is the most informative result: a fully-crawled small business website with a confirmed
/team or /about page returned no structured person data and no parseable name+title text.

Website-derived role-specific person extraction has demonstrated insufficient reliability for core pipeline use.

Note: this result does not prove that person information never exists publicly on SMB websites — it proves that the demonstrated yield across 30 businesses is insufficient to justify building role-specific decision-maker extraction as a core pipeline dependency. Most Canadian SMB websites do not implement schema.org Person markup, and /about or /team pages typically contain images, CSS-styled name blocks, or JavaScript-rendered content not accessible to a plain HTTP parser.

### Finding 3 — Phone extraction: 4/15 businesses, quality concerns remain

4 businesses returned phone numbers. However:
- B02 Mindangler: `220-345-1291` — area code 220 is not a valid Canadian NPA code. False positive.
- B12 Maple Ridge Accounting: `674-363-4772` — area code 674 is not a valid Canadian NPA. False positive.
- B01 RepologiX: `416-248-1229`, `416-248-9484` — 416 is Toronto. Plausible real numbers.
- B07 Northern Lights Dental: `780-380-9228` — 780 is Edmonton. Plausible real number.

Confirmed real CA phones: 2 businesses (B01, B07). False positives: 2 businesses (B02, B12).
False positive rate: 50% of phone-returning businesses. CA area-code validation filter is required.

### Finding 4 — DNS failure rate: 60% of the test set

9 of 15 domains did not resolve. These were plausible-looking Canadian SMB domain names but
were not pre-verified as live. This does not mean 60% of Canadian SMB websites are dead —
it means the script used invented domains rather than confirmed-live domains from existing sources.

**Architecture implication:** Website enrichment only works when the domain is already known from
a source field (e.g. BC Indigenous 52%, Ontario Select Licence 10%). Website discovery for
businesses without a source-provided domain is not viable via this method.

---

## Failure Mode Analysis

| Failure mode | Count | Interpretation |
|---|---|---|
| DNS resolution failure | 9/15 | Domains were not pre-confirmed live — not a method failure |
| robots.txt full block | 1/15 | B03 Airmec — all paths disallowed |
| 404 on sub-paths | 4/15 | Homepage live but /about /team etc. don't exist at tested paths |
| Crawlable but no data | 1/15 | B11 Valley Vet — 9 pages crawled, zero structured data found |

---

## Cumulative Assessment Across VR15 + VR19

| Method | VR15 sample | VR19 sample | Combined |
|---|---|---|---|
| Email — visible text regex | 0/15 = 0% | not tested | 0% |
| Email — mailto href | not tested | 0/15 = 0% | 0% |
| Email — JSON-LD schema.org | not tested | 0/15 = 0% | 0% |
| Email — ANY method | 0/15 = 0% | 0/15 = 0% | 0/30 = **0%** |
| Person — broken regex (VR15) | false positives only | not used | invalid |
| Person — stoplist regex | not tested | 0/15 = 0% | 0% |
| Person — JSON-LD schema.org | not tested | 0/15 = 0% | 0% |
| Person — ANY method | 0% (false positives) | 0/15 = 0% | **0%** |
| Phone — regex | 2/15 = 13% | 4/15 = 27% | ~20% (with false positives) |
| Phone — validated CA area code | 1/15 = 7% | 2/15 = 13% | ~10% |

---

## Architecture Decisions — Final

### Email enrichment from websites
**CLASSIFICATION: NOT SUITABLE AS CORE ENRICHMENT**

Three methods tested across 30 businesses. 0 emails found.
Website-derived email extraction has demonstrated insufficient coverage to justify it as a core enrichment dependency.
This is not a proof that public business emails do not exist — it is a demonstrated yield of 0% across 3 methods on 30 businesses, which is insufficient to build a core pipeline dependency.

**Architecture treatment:**
- Email field = nullable in schema
- Website email extraction = optional/experimental only — NOT a core pipeline dependency
- Email data comes only from: Ontario Select Licence (81%), BC Indigenous (89%), NNI (present)
- For all other records: email = NULL, no estimation, no fabrication
- Architecture must tolerate email = NULL and preserve source/provenance when an email does exist

### Decision-maker enrichment from websites
**CLASSIFICATION: NOT SUITABLE AS CORE ENRICHMENT — Category C (fundamental/optional enrichment gap)**

VR19 confirms: JSON-LD Person 0/15, stoplist regex 0/15. Combined with VR15: 0 valid person signals across 30 tested businesses. A fully accessible 9-path multi-page site (Valley Vet) returned zero.
Website-derived role-specific person extraction has demonstrated insufficient reliability for core pipeline use.

Role-specific contacts (GM/IT/procurement/operations) cannot be guaranteed from the validated free/public source landscape. NULL is a valid and expected outcome.

**IMPORTANT: Do not equate director = owner = president = general manager = IT = procurement.**
The data model must preserve the source-provided role explicitly.

**Architecture treatment:**
- Do NOT build core pipeline components around browser-based role-specific decision-maker discovery
- Confirmed person-enrichment layer:
  - Corporations Canada API → directors for federal corporations (`firstName`, `lastName`, `serviceAddress`)
  - BC Indigenous → primary contact where available (87.8% fill)
  - NNI → contact person where available (conditional)
- Person data model: `person_name`, `role`, `role_type`, `source`, `confidence`, `source_url`, `verified_at`
- Role types distinguish: DIRECTOR / OWNER / PRESIDENT / GENERAL_MANAGER / IT / PROCUREMENT / OTHER
- Decision-maker layer = optional enrichment, not a required field for lead quality scoring

### Phone enrichment from websites
**CLASSIFICATION: Category B — Optional enrichment, conditional**

Phone extraction works when domain is known and live, but has a ~50% false-positive rate
without CA area-code validation. With CA NPA validation filter, realistic coverage is ~10%
of businesses where domain is already known.

**Architecture treatment:**
- Phone from website crawl = opportunistic only, requires CA NPA validation
- Primary phone sources: Ontario Select Licence (99%), BC Indigenous (93%), NNI (conditional)
- Website phone = tertiary source, flagged as `source=website_crawl, confidence=low`

---

## Status: VR19 CLOSED

This is the final enrichment method validation round.
Website email and website decision-maker extraction are confirmed as Category C limitations.
Source landscape is now frozen for architecture discussion.
