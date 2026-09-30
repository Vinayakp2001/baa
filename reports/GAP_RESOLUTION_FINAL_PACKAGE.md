# Gap Resolution Final Package — For GPT Architecture Discussion

**Prepared by:** Kiro
**Date:** 2026-09-26
**Purpose:** Single document to paste to GPT covering:
1. VR19 probe results (email + decision-maker enrichment methods)
2. Gap resolution findings from existing VR evidence review
3. Final gap decision table
4. What GPT needs to research before architecture is frozen

---

## Part 1 — VR19 Results (Kiro probe)

### What was tested
One combined probe on 15 businesses tested two previously untested email methods and two
improved decision-maker methods that VR15 had not used correctly:
- Email via `mailto:` href (VR15 only tested visible text regex)
- Email via JSON-LD `schema.org` email property
- Decision-makers via JSON-LD `schema.org Person` entity
- Decision-makers via stoplist-filtered name+title regex (VR15 had false positives from broken regex)

### What the data showed

| Method | Result |
|---|---|
| Email — mailto href | 0/15 businesses = 0% |
| Email — JSON-LD schema.org | 0/15 businesses = 0% |
| Email — any method | 0/30 businesses cumulative (VR15 + VR19) = 0% |
| Person — JSON-LD schema.org | 0/15 businesses = 0% |
| Person — stoplist regex (improved) | 0/15 businesses = 0% |
| Person — any method | 0/30 businesses cumulative = 0% |
| Phone — with CA area-code validation | ~2/15 confirmed real (13%) |

### Interpretation (factual only — GPT to confirm)

5 of 15 businesses were actually reachable and crawled (including one fully crawled across
all 9 paths including /about and /team). Zero structured person data found. Zero email
addresses in any format on any crawled page.

The 0% email result across 3 methods and 30 businesses is consistent. This appears to be a
real content pattern, not a tooling limitation.

The 0% person result on a fully-crawled /team page suggests Canadian SMB websites do not
implement schema.org Person markup and do not publish name+title text in machine-parseable
plain-text format on public pages.

---

## Part 2 — Gap Resolution Findings from Existing VR Evidence

### Gap 1 — Role-specific decision-makers

What was tested across VR15 + VR19:
- Corps Canada HTML (confirmed false positives — JS-rendered shell)
- Corps Canada API (confirmed: director firstName + lastName + serviceAddress for federal CBCA corps only)
- Website full-text regex (false positives from JS tag names — VR15)
- Website stoplist regex (0 valid matches — VR19)
- Website JSON-LD Person (0 matches — VR19)

What was NOT tested: NS RJSC officer fields (President/VP/CFO/Secretary confirmed in research
but WAF blocks all automated access — VR10 deferred status unchanged).

**Kiro assessment:** General-purpose role-specific contacts (GM/IT/procurement/ops) cannot be
obtained from public website crawl for Canadian SMBs at meaningful coverage. The only confirmed
automated source for person data is Corporations Canada API (director name/address, federal
CBCA corps only). Contact name also available from NNI and BC Indigenous (sector-specific only).

**Question for GPT:** Is the architecture treatment correct — decision-maker layer = optional
enrichment layer, not a required field for core lead quality scoring? And: does GPT know of any
public, lawful, automation-friendly Canadian source for officer/role data that we have not
investigated?

---

### Gap 2 — Public business email

Cumulative result: 0 emails from 30 businesses across 3 methods (visible text regex, mailto
href, JSON-LD schema.org).

**Kiro assessment:** This is a fundamental content limitation, not a method problem. Canadian
SMB websites do not publish emails in machine-parseable formats. Email data is available only
from Ontario Select Licence (81%), BC Indigenous (89%), NNI (present) — these three sources
cover a small geographic/sector population.

**Architecture treatment proposed:** Email = nullable, no estimation. Source-provided email
only. Website crawl does not contribute to email field.

---

### Gap 3 — NAICS / industry classification

Sources with confirmed NAICS: Saskatoon only (86 distinct codes, source-provided).
Sources with industry strings that could map to NAICS:
- BC Indigenous: Industry Sector (free text, not NAICS)
- NNI: Sectors/Goods/Services (controlled vocabulary, not NAICS)
- Vancouver: `businesstype` and `businesssubtype` fields (confirmed present in data,
  distinct values not yet profiled — Kiro will profile these from existing data)
- Ontario Select Licence: licence type only (6 types — mappable to approximate NAICS)
- Calgary/Edmonton/Manitoba: no industry field confirmed

**Architecture treatment proposed:**
- source_provided_naics: Saskatoon only
- mapped_naics: where source industry string maps cleanly to a NAICS 2-digit code
- inferred_naics: NOT to be used — do not silently classify
- Preserve original source industry string regardless

---

### Gap 4 — Employee count coverage

Confirmed sources with employee data:
- Vancouver: 206,024 rows, 100% integer, licence-grain
- BC Indigenous: ~52.6% range strings
- NNI: conditional integer, 187 businesses

All other confirmed sources (Calgary/Edmonton/Saskatoon/Manitoba/Corps Canada/Ontario): no
employee data.

**Clarification on "80% null" figure:** This was a projection from source coverage analysis,
not a measurement from a combined dataset. It is well-founded (5 of 8 confirmed discovery
sources have zero employee data) but should be labelled "projected from source coverage" not
"measured."

---

### Gap 5 — Province coverage (what Kiro can determine from existing evidence)

| Province | Current status from VR work | What remains unresolved |
|---|---|---|
| ON | Select Licence = 674 rows, 6 types only. Toronto WAF. Ontario catalogue noted to have many specialized datasets (RR02) but never systematically mined. | Are there other automatable ON datasets beyond Select Licence? |
| QC | REQ = non-commercial blocked. Municipal portals (Montreal/QC City) never investigated. | Do Montreal or Quebec City open data portals publish business licence data? |
| NS | RJSC WAF-blocked. NS open data portal has specialized datasets but general business directory not found. | Any NS open data alternative? |
| NB | Automated copying of registry search results restricted. Fredericton portal alive, dataset URL unresolved. | Any NB municipal open data source? |
| PE | OCBR auth required — confirmed NOT SUITABLE | CLOSED |
| NL | CADO explicitly prohibits value-added use — confirmed NOT SUITABLE | CLOSED |

---

## Part 3 — What GPT Needs to Research

These require browser/web research that Kiro cannot do. One targeted pass only — do not
restart broad source discovery.

### GPT Research Task 1 — Ontario Data Catalogue beyond Select Licence

RR02 explicitly noted Ontario has "many specialized datasets" in its catalogue and recommended
systematic mining. This was never done.

Specifically: are there any additional Ontario open data sources that provide individual
business records (not just aggregates), are machine-readable, are under OGL-Ontario, and
cover sectors/populations beyond the 6 regulated licence types in Select Licence?

Candidates mentioned in RR02: Community Small Business Investment Funds (has registration date),
tobacco/fuel tax registrant lists, dairy distributors, licensed contractors, regulated industry
directories. Are any of these current, machine-readable, and commercially usable?

For each, classify: IMPLEMENTABLE / PARTIALLY USABLE / REFERENCE ONLY / NOT SUITABLE

### GPT Research Task 2 — Quebec municipal (Montreal / Quebec City)

REQ (provincial registry) is blocked due to non-commercial licence restriction.
But Quebec municipal portals were never investigated.

Does the City of Montreal open data portal (donnees.montreal.ca) publish individual business
licence records? Does Quebec City? If yes: what fields, what licence, machine-readable?

For each, classify: IMPLEMENTABLE / PARTIALLY USABLE / REFERENCE ONLY / NOT SUITABLE

### GPT Research Task 3 — Nova Scotia alternatives

RJSC is WAF-blocked. But the NS open data portal was noted to have Business and Economy
datasets. A Licensed Food Establishments dataset was found but appeared to be in an error
state. Are there any current, automatable NS open data sources covering individual businesses?

For each, classify: IMPLEMENTABLE / PARTIALLY USABLE / REFERENCE ONLY / NOT SUITABLE

### GPT Research Task 4 — New Brunswick

NB corporate registry restricts automated copying of search results.
Fredericton open data portal was confirmed alive. Are there NB municipal open data sources
(Fredericton, Moncton, Saint John) with individual business licence datasets?

For each, classify: IMPLEMENTABLE / PARTIALLY USABLE / REFERENCE ONLY / NOT SUITABLE

---

## Part 4 — Proposed Final Gap Decision Table (for GPT to confirm/correct)

| Gap | Can improve? | Method/source | Expected coverage | Confidence | Legal status | Architecture treatment |
|---|---|---|---|---|---|---|
| Email from websites | NO | None found across 3 methods, 30 businesses | 0% | High (confirmed) | N/A | Category C: NULL for non-source-provided email |
| Role contacts (GM/IT/procurement) | NO (general) | No public automatable source found | 0% general | High (confirmed) | N/A | Category C: optional enrichment layer only |
| Director names | YES (limited) | Corps Canada API — federal CBCA corps only | ~645k corps | High (validated VR15) | OGL-Canada | Category B: enrichment after core pipeline |
| Contact name | YES (limited) | NNI + BC Indigenous — sector/geo specific | ~3k businesses | High (validated) | Conditional | Category B: enrichment, sector-specific |
| NAICS — source provided | YES (partial) | Saskatoon + Vancouver businesstype mapping | <10% of records | Medium | OGL | Category B: preserve source value + map where clean |
| NAICS — general | NO | No general source found | N/A | High | N/A | Category C: nullable, preserve source industry string |
| Employee count | YES (partial) | Vancouver + BC Indigenous + NNI | ~5-10% of records | High (validated) | OGL | Category B: enrich where source provides; NULL elsewhere |
| Ontario general discovery | UNKNOWN | Ontario catalogue not fully mined | Unknown | Low | Needs check | GPT to determine |
| Quebec general discovery | UNKNOWN | Municipal portals not investigated | Unknown | Low | Needs check | GPT to determine |
| NS discovery | UNKNOWN | Open data portal alternatives not investigated | Unknown | Low | Needs check | GPT to determine |
| NB discovery | UNKNOWN | Municipal open data not investigated | Unknown | Low | Needs check | GPT to determine |
| PE | NO | Auth required — confirmed | 0% | High (confirmed) | N/A | Category C: known gap |
| NL | NO | Explicitly prohibited | 0% | High (confirmed) | N/A | Category C: known gap |

---

## Part 5 — Stopping Rule Confirmation

After GPT returns findings on the 4 province gaps above, source landscape is frozen.

No further source discovery rounds.

Next stage after GPT responds:
source freeze → canonical data model → provenance model → event model → entity resolution →
ingestion architecture → enrichment architecture → scheduling/retry model →
API/dashboard architecture → implementation plan

---

## Notes on "~80% employee NULL" language

The prior readiness report stated "~80%+ of records will have null employee data."
This was a projection from source coverage analysis — not a measurement from a combined dataset.

Correct statement: Based on source coverage, employee data is expected to be NULL for records
sourced from Calgary, Edmonton, Saskatoon, Manitoba, Corps Canada, and Ontario (the majority
of the pipeline's discovery layer). Actual null rate across the combined dataset will only be
measurable once the pipeline is built and data is ingested.
