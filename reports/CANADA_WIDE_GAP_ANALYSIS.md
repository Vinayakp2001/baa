# Canada-Wide Gap Analysis

**Date:** 2026-09-25
**Status:** Complete — Phase 1 (Source Discovery) finished; Phase 2 (Technical Validation) next
**Covers:** All 13 provinces/territories + federal sources
**Purpose:** Map assignment requirements to sources, identify gaps, prioritise validation queue

---

## 1. The Biggest Finding

There is no single free, current, Canada-wide source that gives us:

```
business identity + address + registration + employees +
website + phone + email + decision-makers + new-business data
```

The assignment necessarily requires a multi-source composite pipeline.
This is consistent with how Canadian government data is actually structured.

> We need to assemble a pipeline — not search for a "free Canadian Apollo."

---

## 2. Architecture Constraint — StatsCan Individual-Business Data is Confidential

> **This is a confirmed legal/policy constraint, not a gap in our search effort.**

Statistics Canada's Business Register is the internal administrative frame used to produce aggregate counts and statistics. StatsCan's own documentation explicitly states that identifiable individual-business information from the Business Register is **confidential and cannot be publicly disclosed** under the *Statistics Act*.

This means:

- There is no free StatsCan bulk dataset of individual Canadian businesses available programmatically
- Searching further for a "StatsCan individual business list" is not warranted — it does not exist as a public product
- StatsCan's role in this pipeline is **permanently fixed**: aggregate benchmark and validation only
- Individual-business records must come from: government registries, municipal licences, and other public open-data sources

This distinction is important for the technical defense: the absence of a StatsCan individual-business source is not a pipeline gap — it is a statutory constraint that applies to every system attempting to use StatsCan data for individual-lead purposes.

---

## 3. Assignment Requirements → Source Class Mapping

| Required capability | Best source class | Coverage | Main gap |
| --- | --- | --- | --- |
| Legal business name | Registries | ✅ Broad | Entity types differ |
| Operating / DBA name | Registries + licences | ✅/🟡 | Not universal |
| Business status | Registries + licences | ✅ | Different status semantics |
| Registration date | Registries | ✅/🟡 | Not all businesses are corporations |
| Address | Registries + licences | ✅ | Registered ≠ operating location |
| Postal code | Registries / licences | ✅ | Some records incomplete |
| Province / city | Government datasets | ✅ | Usually solvable |
| Industry / NAICS | ODBus + specialized + classification | 🟡 | Quality/coverage varies |
| Employee count | StatsCan/selected datasets/enrichment | 🔴 | No universal individual-level source |
| Website | Website discovery | 🟡 | Needs enrichment |
| Phone | Website/licence/directory | 🟡 | Needs enrichment |
| Email | Website/licence/directory | 🟡 | Needs enrichment |
| Owner/founder | Registry/ISC/website | 🟡 | Entity-type dependent |
| President/director | Registries | 🟡/✅ | Provincial variation |
| Manager/GM/IT/procurement | Website/public sources | 🔴 | Major enrichment gap |
| New business | Registry + licence + change signals | 🟡 | No single definition |
| Daily new business | Multi-source event detection | 🔴 | Must derive |
| 7-day new business | Multi-source event detection | 🔴 | Must derive |
| 30-day new business | Multi-source event detection | 🟡 | More feasible |
| Source / provenance | All sources | ✅ | We control this |
| Last verified | Our pipeline | ✅ | Derived |
| Quality score | Our pipeline | ✅ | Derived |
| Deduplication | Our pipeline | ✅ | Derived |
| CRM-ready export | Our pipeline | ✅ | Derived |

**Red rows = hardest gaps requiring the most architecture work.**

---

## 3. Six Major Gaps

### GAP-01 — Canada-wide current business discovery
No single free source covers all Canadian businesses currently.
**Solution:** Multi-source discovery (ODBus + Corp Canada + municipal licences + provincial open data)

### GAP-02 — Employee size
No consistent individual-level Canada-wide employee count source.
**Solution:** Source-specific employee data + normalization + enrichment/fallback + confidence flag.
Retain original raw value alongside normalized bucket.

### GAP-03 — New business detection
No single individual-level "new business" feed.
**Solution:** Combine registration/licence/location/status events; maintain event provenance.
Derive `new_business_confidence` rather than a single boolean flag.

### GAP-04 — Decision-makers
No free Canada-wide structured source for manager/GM/IT/procurement contacts.
**Solution:** Public-web enrichment (about/team/leadership pages) + government corporate people where available.

### GAP-05 — Contact information (phone/email/website)
Fragmented across websites, licences, and directories.
**Solution:** Deterministic extraction + verification + provenance.
Missing contact = `null` — never fabricated.

### GAP-06 — Identity / deduplication
Multiple sources describe the same entity at different grains/names.
**Solution:** Entity resolution, but only after measuring real source overlaps in Phase 2.

---

## 4. Employee-Size Problem in Detail

The assignment requires these exact buckets:
```
1–4 / 5–9 / 10–19 / 20–49 / 50–99 / 100–199 / 200–499 / 500–999 / 1000+
```

Even ODBus uses multiple inconsistent formats:
```
1 / 2 / 3 / 1--4 / 1 to 4 / 5--9 / 10--19 / 20--49 / 50--99 /
100--499 / .. / NOT AVAILABLE
```

Two separate problems:
- **Problem A — Missing:** Many government sources simply don't provide employee count
- **Problem B — Semantics:** Even when a number exists, it may mean employees at establishment / employees of the legal corporation / estimated employees / employment range / payroll employees / total workers

Employee classification will require:
```
Government employee data
    + source-specific interpretation rules
    + normalization
    + possibly external/public enrichment
    ↓
standard employee bucket + confidence + provenance
```

Original raw value must always be retained.

---

## 5. New Business Detection — Event Model Required

Multiple distinct events discovered across sources:

| Event | Source |
| --- | --- |
| Corporation incorporated | Federal/provincial registries |
| Business name registered | Provincial/territorial registries |
| Business licence issued | Municipal/provincial licence data |
| Licence renewed | Same — not necessarily new business |
| Business location opened | Discovery sources / website |
| Business starts employing people | Statistics Canada (aggregate only) |
| Business appears on website | Website enrichment |
| Business appears in municipal directory | Municipal open data |

**None of these is equivalent to the others.**

StatsCan's Monthly Business Openings definition specifically uses employment/payroll activity (CRA PD7 data), not incorporation. A company can incorporate months before hiring anyone.

Required architecture response:
```
Do NOT use a single new_business = true flag.
Create an event model:
    registration_event
    licence_event
    location_event
    website_event
    employment_activity_event
    status_event

Then derive: new_business_confidence
```

---

## 6. Decision-Maker Gap

Government sources can provide (for some entity types):
- Directors (Corporations Canada API, some provincial registries)
- Officers — president, VP, CFO, secretary, treasurer (NS RJSC, some others)
- Partners (NS RJSC)
- ISC/significant control (Corporations Canada — CBCA corps from Jan 2024)

Government sources cannot provide:
- IT Manager
- Procurement Manager
- Operations Manager
- Office Manager
- GM (unless filed as a corporate officer)

These require public-web enrichment:
```
Business → website → About/Team/Leadership/Contact pages
    → extract public people
    → role classification
    → public business email/phone if explicitly published
    → source + timestamp
```

Rules:
- Public information only
- No CAPTCHA bypass, no login, no private profiles
- No fabricated emails or phone numbers
- Missing = null, not invented

---

## 7. Source Layer Architecture (Confirmed After 8 Rounds)

```
CLASS A — IDENTITY / FOUNDATION
    Corporations Canada (federal)
    Provincial/territorial registries
    ODBus (historical base)
    Municipal business licence datasets

CLASS B — FRESHNESS / EVENTS
    Incorporation transactions (Corporations Canada monthly)
    Registry filings (MB weekly, NS RJSC activity)
    Municipal new licences (Saskatoon new-biz list)
    Licence expiry/status changes
    Business-name registrations
    New locations
    Website discovery/changes

CLASS C — ENRICHMENT
    Business websites (contact, team, leadership pages)
    Public business directories (where terms permit)
    Specialized government datasets
    Public officers/directors/ISC (registries)
    Public team/leadership pages

CLASS D — BENCHMARK / VALIDATION
    Statistics Canada Business Counts (June 2026)
    Statistics Canada Business Openings/Closures (monthly)
    Provincial/territorial economic statistics
    Yukon business statistics
```

---

## 8. Source Overlap Warning

The same business can appear in:
```
ODBus → municipal licence → provincial registry → federal corporation → website → specialized licence dataset
```

With different names:
```
ABC Technologies Inc.
ABC Technologies
ABC Tech
ABC Technologies Calgary
ABC Technologies - Downtown
```

Deduplication cannot be `business_name == business_name`.

Candidate identity signals (to be validated in Phase 2):
- Federal Corporation Number
- Provincial registry number
- CRA Business Number (BN) — most consistent cross-source key found
- Licence number
- Normalized legal name
- Operating name
- Website domain
- Phone
- Address + postal code

**Do not freeze the identity hierarchy yet — Phase 2 will reveal actual overlap patterns.**

---

## 9. All-13 Jurisdiction Summary

| Jurisdiction | Registry | Free bulk master | Useful open/business sources | New-business potential |
| --- | --- | --- | --- | --- |
| BC | ✅ | ❌ | OrgBook API (targeted) | ✅ |
| Alberta | ✅ | ❌ | Open datasets (aggregate) | Partial |
| Saskatchewan | ✅ | ❌ | Saskatoon municipal licences | ✅ |
| Manitoba | ✅ | ❌ | Weekly filing listings | ✅ |
| Ontario | ✅ | ❌ | Select Licence + municipal | ✅ |
| Quebec | ✅ | ⚠️ licence issue | Open data | Partial |
| New Brunswick | ✅ | ❌ restricted | Municipal/open data | Partial |
| Nova Scotia | ✅ | ❓ unverified | RJSC + open data | ✅ |
| PEI | ✅ | ❌ | Open data | Partial |
| Newfoundland & Labrador | ✅ | ❌ | Specialized open data | Partial |
| Yukon | ✅ | ❌ | Supplier directory + open data | Partial |
| NWT | ✅ | ❌ | BIP + open data | Partial |
| Nunavut | ⚠️ | ❌ | NNI registry + municipal | Partial |
| Federal | ✅ Corporations Canada | ✅ daily bulk | ODBus + StatsCan | ✅ |

**Note:** "Free bulk master" = free, general-purpose, bulk-downloadable/queryable individual-business dataset.
Most provinces do not have one.

---

## 10. Source Roles Clarified

| Source | Correct role | NOT |
| --- | --- | --- |
| Corporations Canada | Federal identity + status + corporate events | Canada-wide master |
| ODBus | Historical base/discovery candidate | Current master database |
| Statistics Canada | Benchmark/validation | Lead source or employee enrichment |
| BC OrgBook | Targeted BC identity verification | BC bulk discovery |
| Ontario Select Licence | Specialized (6 types) + contact enrichment | Ontario master |
| NS RJSC | Broad NS entity verification (pending bulk confirmation) | Complete NS population |
| Saskatoon licences | Municipal discovery + new-biz signal | SK provincial master |
| MB weekly filings | Change/new-registration signal | Complete MB registry |
| Municipal datasets generally | Local discovery + freshness | Provincial master |
| Business websites | Contact + decision-maker enrichment | Primary discovery |

---

## 11. Technical Validation Queue (Phase 2)

### Priority A — Core (do first)

| # | Source | What to validate |
| --- | --- | --- |
| A1 | Corporations Canada bulk CSV | Row count, IDs, statuses, dates, addresses, director coverage, transaction types, overlap potential |
| A2 | ODBus underlying source links | Which original municipal sources are still current; identify candidates to replace historical ODBus records |
| A3 | Statistics Canada CSVs | Employee-size label mapping, NAICS levels, geography values, suppression markers |

### Priority B — Freshness sources

| # | Source | What to validate |
| --- | --- | --- |
| B1 | Saskatoon business/new-business files | Format, row count, fields, phone/email presence, stable ID, licence, update frequency |
| B2 | Manitoba weekly Companies Office filings | Format, downloadability, fields, new-registration identification, RSS/API endpoint, terms |
| B3 | Ontario Select Licence dataset | Profile Aug 2026 business + individual datasets — field quality, record count, coverage |

### Priority C — API/search technical inspection

| # | Source | What to verify |
| --- | --- | --- |
| C1 | BC OrgBook API | `/v4/credential-type`, actual response fields, commercial terms |
| C2 | Nova Scotia RJSC | Network capture of 1–2 searches — JSON endpoint? fields? terms? |
| C3 | PEI OCBR | Same as NS |
| C4 | NL CADO | Same as NS |
| C5 | Yukon Supplier Directory | Download current file, check last-modified, field list |
| C6 | NWT BIP Registry | Check interface, machine-readable endpoint? |
| C7 | Nunavut NNI Registry | Inspect public directory — what fields are actually shown? |

### Priority D — Specialized (after A/B/C)

- Provincial specialized datasets
- Additional municipal portals not in ODBus
- Regulated-industry datasets
- Other public datasets as needed

### Deliberately deferred

- Google Places, LinkedIn, paid databases — measure government/open-data gaps first
- Dozens of individual municipal portals — assess after core sources are validated
- Quebec REQ — licence review must happen first (non-commercial restriction)

---

## 12. Revised Research Roadmap

```
SOURCE DISCOVERY              ✅ COMPLETE (8 rounds, all 13 jurisdictions)
        │
        ▼
CANADA-WIDE GAP ANALYSIS      ✅ COMPLETE (this document)
        │
        ▼
TECHNICAL SOURCE VALIDATION   ← NEXT (Phase 2)
        │
        ▼
DATA PROFILING
        │
    ┌───┴───┐
coverage  overlap  field quality
    └───┬───┘
        │
        ▼
ARCHITECTURE REVIEW
        │
        ▼
DB SCHEMA DESIGN
        │
        ▼
KIRO IMPLEMENTATION
```

---

## 13. Key Principles Confirmed by Gap Analysis

1. No single source solves the full assignment — composite architecture required
2. Government registries = identity/verification layer, not contact/employee layer
3. Municipal licence data = best free discovery layer for most provinces
4. Employee size requires normalization + provenance, not a direct field copy
5. New business = event model with multiple signal types, not a boolean flag
6. Decision-makers (GM/IT/procurement) require public-web enrichment
7. Source provenance must be preserved for every field value
8. Deduplication must use multiple identity signals, not just business name
9. Statistics Canada = validation benchmark only — not individual leads
10. ODBus = historical discovery base — not current master database
11. Quebec = blocked until commercial licence is resolved
12. Do not design the schema until Phase 2 measures actual source overlaps
