# Research Round 06 — Saskatchewan + Manitoba

**Date:** 2026-09-25
**Source:** GPT research pass — Saskatchewan Corporate Registry (ISC), Saskatoon open data, City of Regina, Manitoba Companies Office, Manitoba weekly filing listings
**Status:** Research complete — local file inspections pending for Saskatoon downloads and Manitoba weekly filings

---

## TL;DR

Both provincial registries are public and contain useful identity/registration data, but neither has a confirmed free bulk dataset or public API.
Saskatchewan's most useful free source is Saskatoon's business licence open data — which includes a **new businesses as of August 2026** list, a direct new-business signal.
Manitoba's most useful free source is the **weekly Companies Office filing listings** — a change/new-registration discovery feed through September 2026.
Neither province provides a zero-cost scalable bulk foundation on its own. Both are best used as verification + signal layers on top of municipal/open data discovery.

---

## 1. Saskatchewan

### Saskatchewan Corporate Registry (ISC)

Administered by Information Services Corporation (ISC).

**Entity types covered:**
Business corporations, sole proprietorships, partnerships, limited partnerships, LLPs, co-operatives, and other entities.
The legislation establishes SKCR as a public registry — searches by name or number are permitted, along with inspection/copying of registry documents.

**Confirmed fields:**
- Business name
- Registration information
- Status
- Address
- Directors/owners (potentially, depending on entity type)

**Cost structure — critical issue:**

| Access type | Cost |
| --- | --- |
| Individual Profile Report | $10 per company |
| Bulk Information Service | Starts at $200 minimum + estimate required |
| Free individual search | ❌ / unclear |
| Free bulk dataset | ❌ Not available |
| Public API | Not found |

**Decision:** Do NOT treat Saskatchewan Corporate Registry as a zero-cost bulk foundation.
ISC's bulk information is commercially sold. Misuse can result in account suspension.
Registry can be used for targeted identity verification if needed, but cost per record makes bulk ingestion unsuitable.

---

### Saskatoon Business Licences — HIGH VALUE FREE SOURCE ⭐

This is the most important Saskatchewan finding.

The City of Saskatoon publishes downloadable business licence information:

| Dataset | Content |
| --- | --- |
| All commercial/home-based businesses | As of Dec. 31, 2025 |
| **New businesses** | **As of August 31, 2026** |
| Historical business reports | Available |

- Every business in Saskatoon generally requires a business licence for each location (subject to listed exemptions)
- Open Data program — free to use, reuse and redistribute
- Directly provides a **new-business signal** (not just incorporation — actual licence issuance)

**Why this matters:**
This is one of the first sources where we have an explicit "new businesses" list rather than inferring new registrations from a corporate registry. This is closer to what the assignment requires.

**Potential fields (to be verified by local inspection):**
Business name, address, licence date, business type/category — phone/email unknown

**Local inspection needed:**
- Exact file format (CSV/XLSX?)
- Row count
- Exact fields
- Whether phone/email exist
- Whether there is a stable business/licence ID
- Update frequency
- Exact licence/usage statement

---

### City of Regina — Needs Follow-Up

Regina has an open-data program with 1,300+ datasets.
Business licence application captures: business name, owner(s), business phone, email, address, nature/type.

**Unresolved:** Whether Regina actually publishes the business records themselves or only describes the application process.
Mark as candidate — needs direct validation before counting as a confirmed source.

---

## 2. Manitoba

### Manitoba Companies Office

Registers: corporations, business names, sole proprietorships, partnerships, and other entity types.
Public can search for: who is doing business under a trade name, where the business is located, officers/directors.

**Confirmed fields (Companies Online system):**

| Field | Available |
| --- | --- |
| Entity name | ✅ |
| Registry number | ✅ |
| Registration/incorporation date | ✅ |
| Current status | ✅ |
| Officers / directors | ✅ potentially |
| Address | ✅ |
| Phone / email / website | Not established |
| Employee count | Not established |

**Cost structure:**

| Access type | Cost |
| --- | --- |
| Free basic entity search | ✅ Free |
| File Summary (detailed) | $5 per company |
| Free bulk dataset | Not found |
| Public API | Not found |

Basic lookup is free — better than Saskatchewan. But no confirmed bulk/API path.

---

### Manitoba Weekly Filing Listings — HIGH VALUE CHANGE SIGNAL ⭐

The Manitoba Companies Office publishes **weekly listings of recent filings**.
Current page has listings through **September 19, 2026**.

**This is a strong new-business/change detection feed candidate.**

**Important limitation (explicitly stated by Manitoba):**
- These notices are limited and do not include annual returns and business-name renewals
- They are NOT an official transcript — underlying registry documents remain authoritative

**Use as:** change/new-registration discovery signal
**Do NOT use as:** complete business registry

**Local inspection needed:**
- Exact file format
- Whether historical weekly files are downloadable programmatically
- Fields available (business name, registration number, entity type, date)
- Whether new registrations are explicitly identified vs other filing types
- Whether files can be downloaded programmatically
- Whether there is an RSS/API/direct endpoint
- Automation/usage restrictions

---

## 3. Side-by-Side Comparison

| Requirement | Saskatchewan | Manitoba |
| --- | --- | --- |
| Provincial registry | ✅ | ✅ |
| Individual businesses | ✅ | ✅ |
| Registration date | ✅ | ✅ |
| Status | ✅ | ✅ |
| Address | ✅ | ✅ |
| Owners/officers/directors | Potentially ✅ | ✅ potentially |
| Free basic lookup | ⚠️ unclear | ✅ |
| Free bulk dataset | ❌ | ❌ |
| Public API | ❓ | ❓ |
| Employee count | ❌ | ❌ |
| General contact info | ❓ | ❓ |
| New-business signal | ✅ Saskatoon licences | ✅ Weekly filings |
| Municipal/open data | ✅ Saskatoon (strong) | 🟡 needs investigation |
| Zero-cost bulk foundation | ❌ | ❌ |
| Worth integrating | Yes, selectively | Yes, selectively |

---

## 4. Emerging Architecture Pattern

After 6 rounds, a consistent pattern is becoming clear across provinces:

```
Open datasets / municipal licences
        ↓
   Business discovery
        ↓
Provincial / federal registries
        ↓
Identity + registration verification
        ↓
   Business website
        ↓
Phone / email / staff / decision-makers
        ↓
Employee-size classification
        ↓
  Deduplicate + quality score
```

Provincial registries are NOT the discovery layer for most provinces — they are the verification/enrichment layer.
Municipal licence data and open datasets are the discovery layer.

This is a significant architectural insight that should inform the Phase 4 design.

---

## 5. Confirmed Source Profiles

### ASSET-11 — Saskatchewan

| Dimension | Finding |
| --- | --- |
| Provincial registry | ISC Corporate Registry — identity/verification only (paid bulk) |
| Registry fields | Name, registration, status, address, directors potentially |
| Bulk download | ❌ Paid ($200+ minimum) |
| Free bulk | ❌ |
| API | Not found |
| Key free source | Saskatoon business licence open data |
| Saskatoon datasets | All businesses (Dec 2025) + **New businesses (Aug 2026)** + historical |
| Saskatoon licence | Open Data — free to use/reuse/redistribute |
| Saskatoon fields | To be verified by local inspection |
| Regina | Potential — unverified whether records are published |
| Role | Class A (Saskatoon municipal) + Class B (new-business signal) + Class C (registry verification if needed) |

### ASSET-12 — Manitoba

| Dimension | Finding |
| --- | --- |
| Provincial registry | Manitoba Companies Office — free basic lookup |
| Registry fields | Name, registry number, reg date, status, officers/directors |
| Bulk download | ❌ Not found |
| API | Not found |
| File Summary | $5 per company |
| Key free source | Weekly Companies Office filing listings |
| Weekly listings | Through Sep 19, 2026 — new registrations + changes |
| Weekly listings limitation | Not official transcript; excludes annual returns/renewals |
| Role | Class A (registry targeted lookup) + Class B (weekly new-registration signal) |

---

## 6. Local Technical Inspections Required

### Saskatchewan — Saskatoon Business Licence Files

When ready, inspect the Saskatoon "New Businesses" and "Licensed Businesses" downloads:

- [ ] Exact file format (CSV/XLSX/other?)
- [ ] Row count
- [ ] Exact field list
- [ ] Business name, address, licence date, business type/category present?
- [ ] Phone/email fields present?
- [ ] Stable business/licence ID present?
- [ ] Update frequency confirmed?
- [ ] Exact licence/usage statement confirmed?

### Manitoba — Weekly Companies Office Filing Listings

When ready, inspect the weekly filing listing files:

- [ ] Exact file format
- [ ] Whether historical weekly files are downloadable (how far back?)
- [ ] Fields available (name, number, entity type, date, filing type)
- [ ] Whether new registrations are explicitly identifiable vs other filing types
- [ ] Whether files can be downloaded programmatically
- [ ] Whether there is an RSS/API/direct endpoint
- [ ] Automation/usage restrictions

**Scope:** Inspection only — no scraping, no enumeration, no CAPTCHA bypass.

---

## 7. Next Research Round

PEI + Newfoundland & Labrador — continuing the provincial coverage pass.
