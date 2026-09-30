# Research Round 08 — Northwest Territories + Nunavut

**Date:** 2026-09-25
**Source:** GPT research pass — NWT Corporate Registries (CROS), NWT BIP Registry, NWT Open Data, Nunavut Corporate Registries, Nunavut business licensing, NNI Business Registry
**Status:** Research complete — Phase 1 (Source Discovery) now complete for all 13 jurisdictions

---

## TL;DR

NWT has a functional online registry (CROS) plus a procurement-oriented BIP Registry that is a useful discovery/enrichment candidate. NWT Open Data has 76 datasets worth mining.
Nunavut's corporate registry is technically inaccessible for our purposes (no public bulk/search API found). The NNI Business Registry is a potentially high-value enrichment source with strong field coverage, but public field exposure needs verification.
Phase 1 (Source Discovery) is now complete across all 13 Canadian provinces and territories.

---

## 1. Northwest Territories

### NWT Corporate Registries (CROS)

Covers: NWT corporations, extra-territorial corporations, sole-proprietorship business names, partnerships, limited partnerships, societies, co-operatives.

**Confirmed fields:**

| Field | NWT CROS |
| --- | --- |
| Corporations | ✅ |
| Extra-territorial corporations | ✅ |
| Sole proprietorships | ✅ |
| Partnerships | ✅ |
| Business names | ✅ |
| Status | ✅ |
| Legal name | ✅ |
| Entity type | ✅ |
| Full entity profile | 💰 Fee-based |
| Free bulk download | ❌ Not found |
| Public API | ❌ Not found |
| Employee count | ❌ |
| Phone / email / website | ❌ not established |
| Registration/change info | Partial |

Basic information (legal name, status, entity type) is explicitly free.
Full profiles and filed documents require payment.

**Role:** Targeted identity/status verification — NOT a free bulk foundation.

---

### NWT Business Incentive Policy (BIP) Registry ⭐ Interesting Discovery Source

The GNWT maintains a searchable BIP Registry of businesses eligible for procurement-related benefits.

**Public search exposes:**
- Company/business name
- Region
- Community
- Searchable category

**Coverage:** Both incorporated entities AND operating/business names — broader than corporate registry alone.

**Important caveat:** Purpose is specifically to identify BIP-eligible businesses — NOT a complete NWT business population. Do not treat as exhaustive NWT business directory.

**Technical status:** Web-based searchable interface — no documented bulk API found. Local inspection needed before any automation.

---

### NWT Open Data

Active portal with Business and Economy category — currently **76 datasets**.
Worth systematic mining for specialized industry/business datasets.
No current general all-business master dataset found.

**NWT source stack:**
```
NWT Corporate Registry → identity/status verification
BIP Registry → business discovery / procurement-oriented enrichment
NWT Open Data → specialized industry/business datasets
Business website → phone/email/staff enrichment
```

---

## 2. Nunavut

### Nunavut Corporate Registries

Department of Justice corporate registries function.

Business-name registration requirement: any person/company carrying on business in Nunavut under a name other than their own must register within 60 days.

**Critical finding:** No equivalent to a public, searchable, machine-readable Nunavut corporate registry found (comparable to BC OrgBook or NWT CROS). Available official material primarily provides registration forms, submission instructions, and administrative procedures — not a public bulk/search API.

**Status:** Registry exists but technically inaccessible for our purposes until verified.

---

### Nunavut Business Licensing

Consumer Affairs office issues:
- General Business Licences (Nunavut-wide / outside municipal boundaries)
- Real Estate Agent licences
- Employment Agency licences
- Collection Agency / Vendor / Direct Seller licences
- Pawnbroker / Second-Hand Dealer licences
- Annual renewal cycle confirmed

**Important:** Businesses operating within municipal boundaries obtain licences from the applicable municipality — municipal layer is relevant.

**Status:** Licence system confirmed. No public downloadable bulk licence dataset found.

| Capability | Nunavut |
| --- | --- |
| Business licence system | ✅ |
| Nunavut-wide licences | ✅ |
| Municipal licences | ✅ (separate from territorial) |
| Annual renewal | ✅ |
| Public bulk licence dataset | ❌ Not found |
| Public API | ❌ Not found |
| Individual business discovery | ⚠️ |
| New-business signal | Potential via licensing |

---

### Nunavut NNI Business Registry ⭐ HIGH-VALUE ENRICHMENT CANDIDATE

The Nunavummi Nangminiqaqtunik Ikajuuti (NNI) Business Registry is a directory of businesses qualifying as Nunavut businesses under NNI rules.

**Registration:** Free, renewed every 2 years.

**Eligibility requires:** Nunavut registered office + resident manager with final decision-making authority over day-to-day operations.

**Fields collected in NNI application:**
| Field | NNI |
| --- | --- |
| Legal business name | ✅ |
| Operating name(s) | ✅ |
| Resident manager full name | ✅ |
| Main office address | ✅ |
| Registered office address | ✅ |
| Operating community | ✅ |
| Business type | ✅ |
| Phone | ✅ |
| Mailing address | ✅ |
| Email | ✅ |

**Critical distinction:** Application form demonstrates these fields are **collected** — it does not confirm all fields are **publicly exposed** in the machine-readable directory.

**Status:** Potentially high-value enrichment source — public field exposure and API access still need verification.

---

## 3. All 13 Jurisdictions — Final Summary

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
| Nunavut | ⚠️ inaccessible | ❌ | NNI registry + municipal | Partial |
| Federal | ✅ Corporations Canada | ✅ daily bulk | ODBus + StatsCan | ✅ |

**Note:** "Free bulk master" means a free, general-purpose, bulk-downloadable/queryable individual-business dataset. Most provinces do not have one.

---

## 4. Phase 1 Complete — What We Know

**Source Discovery is now complete for all 13 provinces/territories + federal.**

### What consistently works across Canada

- Every province/territory has some form of public corporate/business registry
- Most registries support free basic identity/status lookup
- None (except Corporations Canada federally) provides a free general-purpose bulk machine-readable dataset
- Municipal business licence open data is the most practical free discovery layer for many provinces
- Specialized government datasets (licence, procurement, industry-specific) fill vertical gaps
- Employee count, phone, email, website are NOT reliably available from any registry

### What doesn't work

- Using provincial registries as zero-cost bulk discovery foundations — most are paid or restricted
- Assuming "newly registered" = "newly opened" — four distinct lifecycle signals exist
- Assuming any single source covers all Canadian businesses — composite architecture required

---

## 5. Phase 1 → Phase 2 Transition

**Phase 1 (Source Discovery) = COMPLETE**

**Phase 2 = Source Validation**

For each promising source:
```
Can we download/query it?
    ↓
What does one real record look like?
    ↓
How many records?
    ↓
Which fields are actually populated?
    ↓
How current is it?
    ↓
What's the duplicate rate?
    ↓
What's the licence/commercial-use status?
    ↓
Can we automate it legitimately?
    ↓
Does it add unique coverage beyond what we already have?
```

### Priority validation queue (in order)

| Priority | Source | Asset | Reason |
| --- | --- | --- | --- |
| 1 | Corporations Canada bulk CSV | ASSET-02 | Primary federal discovery + daily updates |
| 2 | Saskatoon business/new-business data | ASSET-11b | Explicit new-biz signal, open data |
| 3 | Manitoba weekly Companies Office filings | ASSET-12b | New-registration change feed |
| 4 | Nova Scotia RJSC | ASSET-08a | Broad entity types + directors |
| 5 | Ontario Select Licence dataset | ASSET-07a | Phone/email/website confirmed |
| 6 | BC OrgBook API | ASSET-03 | Targeted BC verification |
| 7 | Statistics Canada CSVs | ASSET-04 | Benchmark baselines |
| 8 | PEI OCBR | ASSET-16 | Tech inspection — endpoint check |
| 9 | NL CADO | ASSET-17 | Tech inspection — endpoint check |
| 10 | Yukon Supplier Directory | ASSET-18b | Freshness validation |
| 11 | NWT BIP Registry | ASSET-19a | Field/accessibility check |
| 12 | Nunavut NNI Registry | ASSET-20a | Field/public exposure check |
| 13 | ODBus underlying source links | ASSET-09 | Check which municipal portals updated since 2022 |
| 14 | Quebec REQ | ASSET-06 | Licence review — commercial use status |

---

## 6. Confirmed Source Profiles

### ASSET-19 — NWT

#### ASSET-19a — NWT Corporate Registries (CROS)
| Dimension | Finding |
| --- | --- |
| Coverage | NWT — all entity types |
| Key fields | Name, type, status; full profile = paid |
| Bulk / API | ❌ Not found |
| Free basic | ✅ |
| Role | Class C — targeted verification |

#### ASSET-19b — NWT BIP Registry
| Dimension | Finding |
| --- | --- |
| Coverage | NWT BIP-eligible businesses (corps + operating names) |
| Fields | Business name, region, community, category |
| Interface | Web search — no documented bulk API |
| Licence | ? |
| Role | Class A candidate — tech inspection needed |

#### ASSET-19c — NWT Open Data (76 datasets)
| Dimension | Finding |
| --- | --- |
| Coverage | NWT — specialized industry/business datasets |
| Individual businesses | Some specialized datasets |
| Role | Class A specialized + Class D benchmark |

### ASSET-20 — Nunavut

#### ASSET-20a — Nunavut NNI Business Registry
| Dimension | Finding |
| --- | --- |
| Coverage | Nunavut businesses qualifying under NNI rules |
| Fields collected | Name, operating name, manager name, address, phone, email, business type |
| Public field exposure | ❓ Unverified — application shows fields collected, not confirmed as public |
| Renewal | Every 2 years |
| Role | Class C/A candidate — public exposure needs verification |

#### ASSET-20b — Nunavut Business Licensing
| Dimension | Finding |
| --- | --- |
| Coverage | Nunavut-wide businesses + regulated categories |
| Bulk dataset | ❌ Not found |
| Annual renewal | ✅ |
| Role | Change-signal candidate if published |

---

## 7. Local Technical Inspections Needed

- [ ] NWT CROS: 1–2 searches + network capture — check for JSON endpoint
- [ ] NWT BIP Registry: check interface, determine if machine-readable endpoint exists
- [ ] Nunavut NNI Registry: inspect public directory — what fields are actually shown?
- [ ] Nunavut corporate registry: check whether any public search interface exists
