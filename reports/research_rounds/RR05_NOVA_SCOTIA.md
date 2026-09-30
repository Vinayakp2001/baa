# Research Round 05 — Nova Scotia

**Date:** 2026-09-25
**Source:** GPT research pass — Nova Scotia Registry of Joint Stock Companies (RJSC), Nova Scotia Open Data Portal
**Status:** Research complete — bulk/API access unverified; technical inspection pending

---

## TL;DR

Nova Scotia's Registry of Joint Stock Companies (RJSC) is a stronger source than the open-data catalogue suggested.
It covers a broad range of entity types (sole props, partnerships, companies, societies, co-ops, business names) and publicly exposes legal name, registration date, status, address, directors, officers, partners, and activity history.
**Critical gap:** No confirmed free bulk download or public API for enumeration — automation permission is unverified.
The open-data portal has useful specialized datasets but no general-purpose business directory bulk export.

---

## 1. Registry of Joint Stock Companies (RJSC) — Key Findings

### Entity types covered

Broader than Corporations Canada:

| Entity type | RJSC |
| --- | --- |
| Sole proprietorship | ✅ |
| Partnership | ✅ |
| Company | ✅ |
| Society | ✅ |
| Co-operative | ✅ |
| Business/operating name | ✅ |

Most Nova Scotia businesses are required by law to register with the RJSC before operating — making this a broad provincial discovery source (with caveats for "most" not "all").

### Confirmed public fields

| Field | RJSC |
| --- | --- |
| Legal name | ✅ |
| Operating/DBA name | ✅ |
| Registry ID (7-digit) | ✅ |
| Entity type | ✅ |
| Status | ✅ (active/inactive search + profile) |
| Jurisdiction | ✅ |
| Registered office address | ✅ |
| Mailing address | ✅ |
| Registration date | ✅ |
| Previous names | ✅ |
| Activity history | ✅ (filed documents, reports, events) |
| Related registrations | ✅ |
| Directors | ✅ |
| Officers | ✅ (President, VP, CFO, Secretary, Treasurer, etc.) |
| Partners | ✅ |
| Recognized agents | ✅ |
| Nature of business | Potentially — unverified coverage/quality |
| Phone | ❓ — not documented as standard field |
| Email | ❓ — not documented as standard field |
| Website | ❓ — not documented as standard field |
| Employee count | ❌ |
| NAICS | ❌ (nature of business field exists but unverified) |
| CRA BN | Potentially — help docs mention BN linkage, not confirmed in public search |

---

## 2. People Information — Valuable for Decision-Makers

Registry publicly exposes people associated with organizations:
- Directors, officers, partners, recognized agents
- Positions confirmed in indexed profiles: Director, President, Vice President, CFO, Corporate Secretary, Treasurer, Recognized Agent
- Names and addresses where publicly filed

**Important semantic distinction:**
```
RJSC gives us: legally filed corporate/registry roles
NOT automatically: IT manager, procurement manager, telecom decision-maker
```
RJSC provides leadership/registered-role signals. Operational decision-makers still require website/public-business research.

**Extra care needed:** People sections may include civic/mailing addresses. These should not automatically become sales-contact fields — distinguish business contact information from personal residential details in public filings.

---

## 3. Registration Date and Activity History

Registration date is explicitly available — useful for newly registered business detection.
Activity history includes filed documents, reports, and corporate events (registration, amendments, changes, dissolution, other filings).

**Distinction to preserve:**
```
newly registered ≠ newly opened/operating
```
Same finding as Corporations Canada — registration is one lifecycle signal, not proof of business commencement.

---

## 4. Nature of Business — Unverified

Some indexed RJSC profiles contain a "Nature of Business" field, but some records have it blank.
- Coverage consistency: unknown
- Format (structured vs free text): unknown
- NAICS mapping: unknown

**Do not treat as NAICS substitute yet.** Needs profiling from actual data.

---

## 5. Registry ID and BN as Cross-Source Identifiers

Nova Scotia explicitly uses a 7-digit Registry ID.
Nova Scotia help documentation mentions BN (9-digit CRA Business Number) linkage to the registry account.

Growing identifier landscape:

| Jurisdiction | Primary ID | Secondary |
| --- | --- | --- |
| Federal | Corporation Number | BN |
| BC | BC Registry ID | BN (sometimes) |
| Nova Scotia | RJSC Registry ID (7-digit) | BN (linkage documented) |

BN is emerging as the most consistent cross-provincial matching key where available.

---

## 6. Cost Structure

| Access type | Cost |
| --- | --- |
| Basic public search (name, status, type) | Free |
| Full public profile | Free |
| Most documents | $12.45 |
| Articles of Association / amalgamation / by-laws | $24.95 |

**Architecture boundary:**
- Basic profile → free → use this
- Document retrieval → paid → do NOT build architecture around purchasing documents

---

## 7. Critical Gap — Bulk / API Access UNVERIFIED

Searched documentation and open-data catalogue for:
- RJSC bulk dataset
- Public RJSC API
- Downloadable registry database
- Machine-readable full registry export

**Result: Not found.**

| Dimension | Status |
| --- | --- |
| Bulk download | ❓ Unknown |
| Public API | ❓ Unknown |
| Automated enumeration permitted | ❓ Unknown |
| Targeted public lookup | ✅ Confirmed free |

**Do NOT start Playwright/Selenium enumeration.** We have public confirmation of the registry and basic search, but no confirmation that automated bulk extraction is permitted.

---

## 8. Technical Inspection Required (Before Any Automation)

When ready, a small network inspection script should answer:

1. Does the search submit to a JSON/XHR API endpoint?
2. Is that endpoint publicly accessible without authentication?
3. Does it expose only the requested search result (no bulk)?
4. Can a single profile be retrieved by Registry ID?
5. What fields does the response contain?
6. Is pagination available, and to what depth?
7. Are there explicit rate limits in headers/docs?
8. Are there terms prohibiting automated requests?
9. Can a known business profile be retrieved without login?

**Scope of test:** One or two ordinary searches + response capture only. No enumeration, no CAPTCHA bypass, no rate-limit evasion.

If the search uses an internal UI-only API with terms prohibiting automation → stop.
If it is a documented/public read endpoint → research further.

---

## 9. Nova Scotia Open Data Portal

The NS open-data portal is active with a Business and Economy category.

**What we found:**
- Licensed Food Establishments dataset exists but current public visualization is returning an error/private/deleted state — do not count as validated
- Specialized licensed-business datasets exist (tourism, accommodation, regulated industries)
- No current general-purpose "all Nova Scotia businesses" bulk dataset found

**Pattern — same as Ontario:**
```
Nova Scotia
    ├── RJSC — broad legal/business registration (primary target)
    ├── Food licences
    ├── Accommodation licences
    ├── Industry-specific licences
    ├── Municipal business data
    └── Other specialized government datasets
```

RJSC is the important piece to investigate first. Specialized portal datasets are secondary candidates.

---

## 10. Comparison With Sources Researched So Far

| Capability | Corp. Canada | BC OrgBook | ON Select Licence | NS RJSC |
| --- | --- | --- | --- | --- |
| Individual businesses | ✅ | ✅ | Limited (6 types) | ✅ |
| Sole proprietors | Limited | ✅ | ❌ | ✅ |
| Legal name | ✅ | ✅ | ✅ | ✅ |
| Operating/DBA name | ✅ history | ✅ | ✅ | ✅ |
| Registration date | ✅ | ✅ | ❌ | ✅ |
| Status | ✅ | ✅ | Licence status | ✅ |
| Address | ✅ | ❌ | ✅ | ✅ |
| Phone | ❌ | ❌ | ✅ | ❓ |
| Email | ❌ | ❌ | ✅ | ❓ |
| Website | ❌ | ❌ | ✅ | ❓ |
| Directors | ✅ API | ❌ | ❌ | ✅ |
| Officers | Limited | ❌ | ❌ | ✅ |
| Partners | ❌ | ❌ | ❌ | ✅ |
| Activity history | ✅ | ✅ | Licence-level | ✅ |
| Bulk download | ✅ | ❌ prohibited | ✅ | ❓ |
| Public API | ✅ | ✅ | CKAN API | ❓ |
| Automation permitted | ✅ | Targeted only | ✅ | ❓ |
| Employee count | ❌ | ❌ | ❌ | ❌ |
| NAICS | ❌ | ❌ | ❌ | ❓ nature of biz |

---

## 11. Confirmed Source Profile

| Dimension | Finding |
| --- | --- |
| Source | Nova Scotia Registry of Joint Stock Companies (RJSC) |
| Operator | Nova Scotia Registry of Joint Stock Companies |
| Jurisdiction | Nova Scotia |
| Entity types | Sole prop, partnership, company, society, co-op, business name |
| Coverage | Broad — most NS businesses required to register |
| Individual records | Yes |
| Legal name + operating name | Yes |
| Registry ID | Yes (7-digit) |
| CRA BN | Potentially — not confirmed in public search |
| Status | Yes |
| Registration date | Yes |
| Address | Yes |
| Directors / officers / partners | Yes |
| Activity history | Yes |
| Nature of business | Potentially — quality/coverage unverified |
| Phone / email / website | Unknown — not documented as standard fields |
| Employee count / NAICS | No |
| Bulk download | Unknown — not found |
| Public API | Unknown — not found |
| Automation permission | Unverified |
| Basic search | Free |
| Documents | Paid ($12.45–$24.95) |
| Best current role | Strong provincial candidate — targeted lookup confirmed; enumeration permission pending |

---

## 12. Next Actions

- [ ] Technical inspection: run one/two ordinary RJSC searches, capture network requests, identify JSON/XHR endpoints, check for auth/terms/rate limits
- [ ] Check RJSC terms of use specifically for automated access
- [ ] Inspect NS Open Data Portal for licensed food/accommodation datasets — validate whether any are current and accessible
- [ ] Systematically check Nova Scotia catalogue for other individual-business datasets
- [ ] Confirm whether BN is exposed in public RJSC search results
- [ ] Profile "Nature of Business" field coverage and format
- [ ] Continue to next province (Saskatchewan) in parallel — do not block on RJSC technical inspection
