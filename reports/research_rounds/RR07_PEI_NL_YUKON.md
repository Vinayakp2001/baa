# Research Round 07 — PEI + Newfoundland & Labrador + Yukon

**Date:** 2026-09-25
**Source:** GPT research pass — PEI OCBR, NL Registry of Companies (CADO), NL Open Data, Yukon YCOR, Yukon Supplier Directory, Yukon business statistics
**Status:** Research complete — local technical inspections pending for all three registries

---

## TL;DR

Consistent pattern continues: registries are verification sources, not free bulk discovery sources.
PEI has a functional online registry (OCBR) with useful fields but no confirmed bulk/API.
NL has a substantial registry (~50k incorporations, ~26k active) via CADO but no free bulk; **no business-name registry** (coverage gap).
Yukon has YCOR for registry verification plus a Supplier Directory (open licence but freshness needs validation) and aggregate business statistics.
None of the three provides a free bulk dataset suitable as a discovery foundation.

---

## 1. Prince Edward Island

### PEI Online Corporate and Business Names Registry (OCBR)

Currently transitioning — users may need to search both new and original registries.

**Confirmed public fields:**
| Field | PEI OCBR |
| --- | --- |
| Legal/business name | ✅ |
| Business type | ✅ |
| Status | ✅ |
| Registered address | ✅ |
| Business number | ✅ |
| Registration/incorporation info | ✅ likely |
| Shareholder/ISC info | ⚠️ available through regulatory filings — not confirmed as bulk public |
| Phone / email / website | ❓ |
| Employee count / NAICS | ❌ |
| Free search | ✅ |
| Free bulk dataset | ❌ Not found |
| Public API | ❌ Not found |
| Commercial automation | ⚠️ Needs verification |

**PEI corporate transparency:** Corporations required to file shareholder information and maintain an ISC register — but this does not mean a freely downloadable public owner database.

**Role:** Registry verification source — not a bulk discovery source.

**Local inspection needed:**
- Perform 1–2 normal OCBR searches with browser DevTools/network logging
- Check whether search uses a public JSON/XHR endpoint
- Identify exact response fields
- Check terms before any automation

---

## 2. Newfoundland & Labrador

### Registry of Companies / Companies and Deeds Online (CADO)

**Scale:**
- ~50,000 incorporations on record
- ~26,000 active companies
- All corporations operating in NL must be incorporated or registered

**CADO public functionality:**
- Company searches
- Company name availability
- Current company information
- Certificates of good standing
- Incorporation filings
- Annual returns
- Registered office changes
- Director changes

**Confirmed fields:**
| Field | NL CADO |
| --- | --- |
| Corporation name | ✅ |
| Company status | ✅ |
| Registered office | ✅ |
| Registration/incorporation info | ✅ |
| Directors | ✅ |
| Annual filings | ✅ |
| Change filings | ✅ |
| Business/trade-name registry | ❌ — NL has NO business-name registry legislation |
| Phone / email / website | ❓ |
| Employee count / NAICS | ❌ |
| Free bulk dataset | ❌ Not found |
| Public API | ❌ Not found |
| Online search | ✅ |
| Search/document fees | ⚠️ Some paid services |
| Commercial automation | ⚠️ Needs verification |

**Critical coverage gap:**
```
NL does not have legislation governing a Business Name Registry.
```
The Registry of Companies covers incorporated entities only — sole proprietors and unincorporated businesses operating under trade names are NOT in this registry. This is a material coverage limitation.

**ISC/significant control:**
NL introduced ISC register requirements for corporations from April 1, 2022.
This is an internal corporate requirement — it does not mean a freely downloadable public owner database.

**NL Open Data:**
- Active open-data portal under Open Government Licence
- "Companies" tag exists but no current general all-business dataset found
- Mining Companies and Commodities dataset exists — has company name, production status, commodities, profile, contact info — but **last modified 2015** — historical/specialized only
- Use NL open data for specialized enrichment, not general business master

**Role:** Registry verification for NL corporations + change signals via CADO filings. Coverage gap for unincorporated/trade-name businesses.

**Local inspection needed:**
- 1–2 CADO searches, capture network requests
- Determine response mechanism and fields
- Check whether a public read endpoint exists
- Confirm terms and rate limits before any automation

---

## 3. Yukon

### Yukon Corporate Online Registry (YCOR)

Covers: business corporations, partnerships, business names, societies, and related entities.

**Confirmed fields:**
| Field | YCOR |
| --- | --- |
| Business/entity name | ✅ |
| Entity type | ✅ |
| Status | ✅ |
| Registration information | ✅ |
| Registry number | ✅ |
| Registered address | ✅ |
| Directors / filing information | ✅ |
| Phone / email / website | ❓ |
| Employee count / NAICS | ❌ |
| Free status search | ✅ |
| Paid entity profile | ✅ |
| Free bulk dataset | ❌ Not found |
| Public API | ❌ Not found |
| Commercial automation | ⚠️ Needs verification |

**Role:** Registry verification — targeted lookup only until bulk/API status verified.

**Local inspection needed:**
- Inspect YCOR free status-search with 1–2 searches + network capture
- Determine whether machine-readable endpoint exists

---

### Yukon Government Supplier Directory ⭐ Potential Enrichment Source

Published under **Open Government Licence – Yukon**.

**Fields:** Business name, description, Yukon community/communities, whether Yukon business.

**Freshness concern:**
- Open-data metadata: last updated 2022
- Yukon procurement document (2026): says directory is updated annually

**Status:** Useful enrichment/discovery source — freshness needs direct validation. NOT sufficient for Yukon-wide business coverage.

**Local inspection needed:** Download current file, check actual last-modified date and record count.

---

### Yukon Business Statistics — Class D Benchmark

Dataset: "Number of businesses and workers by Yukon community"
- Updated May 20, 2026
- Based on Yukon Business Survey
- Provides counts by community
- **Aggregate only — not individual leads**
- Excellent for validation/benchmark

---

## 4. Consolidated Three-Province Comparison

| Capability | PEI | NL | Yukon |
| --- | --- | --- | --- |
| Provincial/territorial registry | ✅ | ✅ | ✅ |
| Business names coverage | ✅ | ❌ gap | ✅ |
| Status | ✅ | ✅ | ✅ |
| Registration info | ✅ | ✅ | ✅ |
| Directors/people | ✅ likely | ✅ | ✅ |
| Address | ✅ | ✅ | ✅ |
| Employee count | ❌ | ❌ | ❌ |
| Website/email/phone | ❓ | ❓ | ❓ |
| Free bulk dataset | ❌ | ❌ | ❌ |
| Public API | ❓ | ❓ | ❓ |
| Open-data business dir | ❓ | Specialized/stale | Supplier dir (stale?) |
| New-business signal | Registry events | CADO filings | Registry events |
| Aggregate benchmark | ❓ | ❓ | ✅ |
| Worth keeping | Yes — verification | Yes — verification | Yes — verification |

---

## 5. Emerging Architecture — Now Confirmed Across 11 Jurisdictions

After 7 research rounds covering 11 of 13 jurisdictions, the layered architecture is consistently supported:

```
LAYER 1 — DISCOVERY
    Municipal business licences
    Provincial open datasets
    Specialized government datasets
    ODBus
    Other legitimate open-data sources

LAYER 2 — REGISTRATION / IDENTITY VERIFICATION
    Corporations Canada
    Provincial registries (NS RJSC, MB Companies Office, PEI OCBR, NL CADO, YCOR, etc.)
    BC OrgBook (targeted only)
    Municipal licence records

LAYER 3 — ENRICHMENT
    Business websites (contact, about, team, leadership pages)
    Public business contact pages
    Permitted directories
    Specialized government sources

LAYER 4 — BENCHMARKING
    Statistics Canada (Business Counts + Openings/Closures)
    Provincial/territorial business statistics
    Yukon business statistics
```

**Key finding locked in:** Employee count and contact information (phone/email/website) are NOT reliably available from government registries in any province/territory researched so far. These require enrichment from other sources.

---

## 6. Important Correction to Expectations

Do not expect all 13 provinces/territories to provide:
- Employee counts → enrichment/classification layer required
- Contact information → website enrichment required
- "New business" equivalent to "new incorporation" → multiple lifecycle signals needed

**Four distinct business lifecycle signals confirmed:**
| Signal | Source type |
| --- | --- |
| Corporate registration / incorporation | Provincial/federal registries |
| Business licence issuance | Municipal licence open data |
| Physical location opened | Discovery sources / website |
| Business starts employing people | Statistics Canada (aggregate only) |

These events happen at different times. The system must distinguish and preserve all four — not collapse into `new_business = true`.

---

## 7. Local Technical Inspections Required

### PEI OCBR
- [ ] 1–2 normal searches + browser DevTools network capture
- [ ] Identify JSON/XHR endpoint (if any)
- [ ] Confirm exact response fields
- [ ] Check terms before any automation

### NL CADO
- [ ] 1–2 normal company searches + network capture
- [ ] Determine response mechanism and fields
- [ ] Check whether a public read endpoint exists
- [ ] Confirm terms and rate limits

### Yukon YCOR
- [ ] 1–2 normal free-status searches + network capture
- [ ] Determine whether machine-readable endpoint exists
- [ ] Confirm terms

### Yukon Supplier Directory
- [ ] Download current file
- [ ] Check actual last-modified date and record count
- [ ] Confirm field list matches description

---

## 8. Confirmed Source Profiles

### ASSET — PEI OCBR
| Dimension | Finding |
| --- | --- |
| Coverage | PEI — corporations + business names |
| Individual records | Yes |
| Key fields | Name, type, status, address, business number |
| ISC | Available through filings — not confirmed as bulk public |
| Bulk / API | ❌ Not found |
| Free search | Yes |
| Automation | Unverified |
| Role | Class C — targeted verification |

### ASSET — NL CADO
| Dimension | Finding |
| --- | --- |
| Coverage | NL — corporations only (~26k active) |
| Business-name registry | ❌ Does not exist in NL |
| Key fields | Name, status, address, directors, filings |
| Bulk / API | ❌ Not found |
| Free search | Yes (some paid services) |
| Automation | Unverified |
| Role | Class C — targeted verification; coverage gap for unincorporated businesses |

### ASSET — Yukon YCOR
| Dimension | Finding |
| --- | --- |
| Coverage | Yukon — corps, partnerships, business names, societies |
| Key fields | Name, type, status, address, registry number, directors |
| Bulk / API | ❌ Not found |
| Free status search | Yes |
| Paid profile | Yes |
| Automation | Unverified |
| Role | Class C — targeted verification |

### ASSET — Yukon Supplier Directory
| Dimension | Finding |
| --- | --- |
| Coverage | Yukon government-registered suppliers |
| Fields | Business name, description, community, Yukon-business flag |
| Licence | Open Government Licence – Yukon |
| Freshness | Last updated 2022 (metadata) — annual update claimed in 2026 doc |
| Role | Class C — enrichment; freshness pending validation |

### ASSET — Yukon Business Statistics
| Dimension | Finding |
| --- | --- |
| Coverage | Yukon — aggregate by community |
| Individual records | No |
| Updated | May 20, 2026 |
| Role | Class D — validation/benchmark |

---

## 9. Progress After RR07

Researched: Federal + ODBus + Statistics Canada + Ontario + BC + Nova Scotia + Saskatchewan + Manitoba + PEI + NL + Yukon = **11 of 13 jurisdictions**

Remaining: Northwest Territories + Nunavut

After NWT + Nunavut → Canada-wide gap analysis recommended before moving to Phase 3 (data profiling).
