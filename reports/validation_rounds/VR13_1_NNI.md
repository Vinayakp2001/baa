# VR13.1 — NNI Business Registry — Full Profiling

Generated: `2026-09-26` | Updated: `2026-09-26` (GPT corrections applied — profile fields confirmed, semantics corrected)
Scripts: `probe_nni_vr13_1.py` → `probe_nni_vr13_2.py` → `probe_nni_vr13_3.py` → `probe_nni_vr13_4.py`
HTML dumps: `VR13_1_NNI_LIST_PAGE.html`, `VR13_1_NNI_COMMUNITY_PAGE.html`, `VR13_1_NNI_SUPPLIER_PAGE.html`, `VR13_1_NNI_PRIVACY_PAGE.html`, `VR13_1_NNI_PROFILE_2367.html`, `VR13_1_NNI_PROFILE_2210.html`

---

## 1. Portal Architecture

| Item | Result |
|---|---|
| Base URL | `https://nni.gov.nu.ca` |
| CMS | Drupal 10 |
| List all businesses endpoint | `/business/list` ✅ |
| Community search endpoint | `/business/search/community` ✅ |
| Name search endpoint | `/business/search/name` ✅ |
| Supplier search endpoint | `/business/search/suppliers` ✅ |
| Active date search endpoint | `/business/search/active` ✅ |
| Business number search | `/business/search/number` ✅ |
| Business profile pages | `/business/profile/{id}` ✅ |
| Authentication required | ❌ None — all endpoints public |
| JSON API available | ❌ No (`_format=json` returns 406 "Not acceptable format") |
| robots.txt | `/search/` disallowed (Drupal site search only) — `/business/` paths NOT disallowed |

---

## 2. Business List — `/business/list`

**Status: 200 — full list returned without authentication**

| Metric | Value |
|---|---|
| HTTP status | 200 |
| Page size (bytes) | 55,142 |
| Table rows (`<tr>`) | 188 (187 data rows + 1 header row) |
| Business profile links | 187 unique links to `/business/profile/{id}` |
| Pagination | None observed — full list on one page |
| Fields in list | Company Name (linked), Effective Date (YYYY-MM-DD), Community |
| Sort | Alphabetical by company name |
| Print link | Present (`window.print()`) |

**Effective date range observed:**
- Earliest in visible data: 2024-10-23 (`Eastern Arctic Medical Solutions Inc.`)
- Latest in visible data: 2026-09-21 (`Beland, Patrick o/a Le Grand Elan`)
- Multiple September 2026 entries confirmed (2026-09-10, 2026-09-14, 2026-09-17, 2026-09-21)

**Sample records (first 10):**

| Company Name | Effective Date | Community |
|---|---|---|
| 237 TOV Construction & Supply Ltd. | 2026-03-03 | Iqaluit |
| 506521 NWT Ltd. | 2026-01-26 | Rankin Inlet |
| 5140 Nunavut Ltd. O/A Qillaq Innovations | 2025-01-20 | Cambridge Bay |
| 5296 Nunavut Ltd. | 2026-05-05 | Kugluktuk |
| 5309 Nunavut Ltd. | 2026-04-07 | Pond Inlet |
| 5550 Nunavut Ltd | 2025-02-18 | Iqaluit |
| 5575 Nunavut Ltd. O/A Amaruq Consulting Co. | 2025-02-10 | Baker Lake |
| 5581 Nunavut Ltd. | 2025-12-02 | Iqaluit |
| 5681 Nunavut Inc | 2025-06-23 | Iqaluit |
| 5850 Nunavut Inc. | 2025-07-07 | Iqaluit |

**Business profile URL pattern:** `/business/profile/{integer_id}`
- ID range observed: 1569 – 2441
- This implies IDs are sequentially assigned; higher IDs = more recently registered

**Key observation — effective date semantics:**
The list contains only currently-registered businesses. The "effective date" is the date
the current registration became active — this is a registration/renewal date, not an
incorporation date. Businesses re-register annually (per NNI regulations). This field is
therefore a **renewal/registration date**, not a once-ever founding date.

**Key observation — active-only list:**
The list title is "Business list" and contains only current registrants. There is no
indication of historical/expired registrations in this view. This means the list is
current-active only — no historical records.

---

## 3. Community Search — `/business/search/community`

**Status: 200 — form with full dropdown confirmed**

### Location dropdown (30 options)
Organized into three optgroups:

**All:**
- `all:Nunavut` → All of Nunavut

**Community (26 communities):**
Arctic Bay, Arviat, Baker Lake, Bathurst Inlet, Cambridge Bay, Chesterfield Inlet,
Clyde River, Coral Harbour, Gjoa Haven, Grise Fiord, Hall Beach, Igloolik, Iqaluit,
Kimmirut, Kinngait, Kugaaruk, Kugluktuk, Pangnirtung, Pond Inlet, Qikiqtarjuaq,
Rankin Inlet, Repulse Bay, Resolute Bay, Sanikiluaq, Taloyoak, Whale Cove

**Region (3 regions):**
- `region:Kitikmeot`
- `region:Kivalliq`
- `region:Qikiqtaaluk`

### Sector filter (11 sectors — multi-select):
WILDLIFE, AGRICULTURE, MANUFACTURING, ARTS & CRAFTS, TRAVEL & TOURISM,
TRANSPORTATION / COMMUNICATIONS / UTILITIES, TRADE & SERVICES, CONSTRUCTION,
FISHERIES, FORESTRY, MINERALS / OIL & GAS

### Goods filter (74 options) and Services filter (211 options):
Also present on the community search form — same classification system as the supplier
search. These are the industry/category tags applied to each registered business.

### Community search GET pattern:
```
/business/search/community?sort=asc&order=Name&l=&edit%5Bcommunity%5D=0&op=Search
```
`edit[community]=0` returns all-Nunavut results (from the Directory Summary link on the main page).
Individual community: `edit%5Bcommunity%5D=community%3AIqaluit` etc.

---

## 4. Supplier Search — `/business/search/suppliers`

**Status: 200 — form confirmed**

The supplier search uses a `location` dropdown with 27 options (contract location — slightly
different set than the community search). This is used to find businesses that supply to a
particular location, regardless of where the business is headquartered.

The goods/services/category classification visible on the community form is also used here
to filter by what a business supplies (74 goods categories + 211 services categories).

---

## 5. Name Search — `/business/search/name`

**Status: 200**

Form uses `edit[name]` parameter. A search for "Arctic" returns results (200, 11,794b vs
10,713b for the empty form — byte difference indicates results were returned).

---

## 6. Business Profile Pages — `/business/profile/{id}` ✅ CONFIRMED

Profile pages use a plain HTML `<table>` with label/value `<td>` pairs. No authentication required.

**Confirmed field set (from two independent profiles — 2367 and 2210):**

| Field | HTML label | Profile 2367 | Profile 2210 |
|---|---|---|---|
| Business name | `<h1>` + table header | 237 TOV Construction & Supply Ltd. | Beland, Patrick o/a Le Grand Elan |
| Business number | Business Number | 2367 | 2210 |
| Business type | Business Type | Incorporations | Sole Proprietor / Partnership |
| Street address | Street Address | 588 Atungauyait Dr. | 2539 Paurngaq Crescent |
| Community | City / Community | Iqaluit | Iqaluit |
| Phone | Phone | (867) 222-8455 | *(not present — field absent for this record)* |
| Contact name | Contact Name | Christine Bissou Bilong | Patrick Beland |
| Employee count | No. of Employees | 2 | 1 |
| Sectors | Sectors | CONSTRUCTION, TRADE & SERVICES | ARTS & CRAFTS, TRADE & SERVICES, TRANSPORTATION COMM & UTIL |
| Goods | Goods | 18 items (building materials, electrical, etc.) | 4 items (advertising, clothing, etc.) |
| Services | Services | 45 items | 16 items |
| Territory/Province | Territory / Province | Nunavut Territory | Nunavut |
| Business status | Business Status | Active | Active |
| Effective date | Effective Date | 2026-03-03 | 2026-09-21 |
| Email | Email | 237tovconstructionandservices@gmail.com | patrick@legrandelan.ca |
| Postal code | Postal Code | X0A 0H0 | X0A 2H0 |

**Confirmed absent from profiles:**
- NTI certificate number — NOT present in either scraped profile (GPT reference to this field unconfirmed by direct observation)
- Mailing address (separate from street address) — not present
- Resident manager (as a labelled field) — not present; Contact Name appears to serve this role

**Phone field note:** Profile 2210 (sole proprietor) has no Phone row — this field appears conditional.
Profile 2367 (incorporation) has phone present. Phone is therefore present on some records, absent on others.

**Effective date machine-readable:** The `<time>` element includes a full ISO timestamp with timezone:
`<time datetime="2026-09-21T09:20:00-04:00">2026-09-21</time>`
This confirms server-side timestamp precision to the minute — useful for detecting same-day registrations.

**Employee count note (GPT):** Preserve the raw integer, not converted to assignment buckets.
The pipeline derives the bucket, retains the source value. `2` → bucket `1–4`, but store `2`.

**Effective date semantics (GPT correction):**
Do NOT label as "incorporation date" or "business opening date."
NNI registration is valid for two years and must be renewed. The effective date is the
date the current registration became active — it is a **NNI registration/renewal date**.
`NNI registration date ≠ incorporation ≠ physical opening ≠ first payroll activity`
Fits the event-fusion model: one of several independent lifecycle signals.

---

## 7. Licensing / Reuse Terms

### robots.txt (confirmed)
```
Disallow: /search/     ← Drupal site search only
Disallow: /admin/
Disallow: /user/login
```
`/business/` paths are NOT in robots.txt — no crawl restriction on business pages.

### Privacy page (node/75) — full text:
> "This website is an instrument of the Government of Nunavut. As such, it falls under
> the scope of the Government of Nunavut's **Access to Information and Protection of
> Privacy Act**."

**Assessment:** The privacy statement covers only personal data submitted *to* the website
by visitors. It does NOT restrict commercial reuse of the published business directory.
No "no automated access" clause, no prohibition on value-added products.

### NNI Regulations PDF — retrieved (306KB, confirmed PDF)
The April 2017 NNI Regulations PDF was successfully retrieved at:
`https://nni.gov.nu.ca/sites/nni.gov.nu.ca/files/NNI-Regs-amendment_2.pdf`

**The PDF was NOT parsed in this scripted round** — binary download only confirmed.
Manual review of the PDF is required to answer the specific question:

> Does the NNI legislation/regulation or website terms restrict copying, automated
> extraction, redistribution, commercial use, or creation of a value-added database
> from the public Business Registry?

**Licensing status: ⚠️ UNRESOLVED**
- No explicit prohibition found on privacy page or robots.txt
- No OGL grant observed
- NNI Regulations PDF not yet reviewed for data-use restrictions
- "No explicit restriction found" ≠ "commercial use permitted" — these are different conclusions
- Do not mark as commercially cleared until PDF review complete

---

## 8. Findings Summary

| Question | Answer |
|---|---|
| Total record count | **187 active businesses** (full list, one page, no pagination) |
| Pagination | None — all 187 on single page |
| Fields in list view | Company name (linked), effective date (YYYY-MM-DD), community |
| Fields in profile page | Business name, number, type, street address, community, phone*, contact name, employees, sectors, goods, services, territory, status, effective date, email, postal code |
| Phone field coverage | Conditional — present for some records (e.g. incorporations), absent for others |
| Employee count | ✅ Individual business-level integer (first such source found in this research) |
| Effective date range | 2024-10-23 to 2026-09-21 (active registrations only) |
| Effective date semantics | NNI registration/renewal date — NOT incorporation/opening date |
| Records with 2026 dates | Multiple — including September 2026 entries |
| Community coverage | 26 communities + 3 regions + all-Nunavut |
| Active-only or historical | Active registrations only |
| Duplicate businesses | Possible — same entity can have multiple location entries |
| List downloadable | No direct download — HTML table only |
| HTML vs JSON | HTML — no JSON endpoint available |
| Business profile URL pattern | `/business/profile/{id}` — plain HTML table, no auth |
| Sector classification | 11 sectors + 74 goods categories + 211 services categories |
| robots.txt restriction | `/business/` paths not restricted |
| Reuse / automation terms | ⚠️ No prohibition found; no OGL grant; NNI Regulations PDF not yet reviewed |
| NNI = complete Nunavut business universe | ❌ No — NNI registry covers only qualifying "Nunavut Businesses" per NNI criteria |

---

## 9. Classification

**Class A/B/C hybrid — PARTIALLY VALIDATED — HIGH-VALUE CANDIDATE**

Technical capability is comprehensively validated. The remaining gate is reuse terms.

**Class A (Discovery):**
187 active NNI-registered Nunavut businesses, fully enumerable at `/business/list`.
No auth, no pagination, no bot-protection.
Caveat: not equivalent to all Nunavut businesses — NNI-registered subset only.

**Class B (Fresh/Change detection):**
Effective date field present on both list and profile pages. New registrations
detectable by periodic snapshot comparison of `/business/list`.
Effective date = NNI registration/renewal date (not incorporation or opening).

**Class C (Enrichment):**
Profile pages expose: phone, email, contact name, employee count (individual integer),
postal code, street address, sector + goods + services classification.
First source in this research to expose individual business-level employee count
alongside full contact information.

**Pipeline ingestion pattern (confirmed viable):**
```
GET /business/list
  → 187 rows: business_name, effective_date, community, profile_id
  → for each: GET /business/profile/{id}
    → business_name, business_number, business_type
    → street_address, community, postal_code, territory
    → phone (if present), email, contact_name
    → employee_count (integer — preserve raw, derive bucket in pipeline)
    → status, effective_date (ISO timestamp available)
    → sectors[], goods[], services[]
```

**Employee count handling:**
Store raw integer. Pipeline derives assignment bucket:
`1 → 1–4`, `7 → 5–9`, `17 → 10–19`, etc.

---

## 10. Open Items

| Item | Status |
|---|---|
| Profile fields confirmed | ✅ CLOSED — full field set confirmed from two independent profiles |
| NNI Regulations PDF review | ⚠️ OPEN — PDF retrieved (306KB), manual review needed for data-use restrictions |
| Phone field coverage rate | ⚠️ OPEN — conditional; full rate unknown without scraping all 187 profiles |
| Effective date = renewal vs original registration | ⚠️ OPEN — GPT notes 2-year validity cycle; which date appears on renewal is unconfirmed |
| Multiple-location deduplication strategy | ⚠️ OPEN — same entity can appear multiple times (e.g. EPLS stores) |

---

## 11. Revision of VR13 Status for NNI

| Item | Previous (VR13) | VR13.1 final |
|---|---|---|
| Anonymous search | ❓ Unknown | ✅ Confirmed — no auth |
| Total record count | ❓ Unknown | ✅ 187 active registrations |
| Fields in list | ❓ Unknown | ✅ Name + effective date + community |
| Fields in profile | ❓ Unknown | ✅ Full structured field set confirmed |
| Employee count | ❓ Unknown | ✅ Individual integer — first such source found |
| Phone / email | ❓ Unknown | ✅ Both present on profiles (phone conditional) |
| Contact name | ❓ Unknown | ✅ Present |
| Pagination | ❓ Unknown | ✅ None — full list on one page |
| Sector/goods/services | ❓ Unknown | ✅ 11 sectors + 74 goods + 211 services |
| robots.txt | ❓ Unknown | ✅ /business/ not restricted |
| Reuse terms | ❓ Unknown | ⚠️ No prohibition found; PDF review pending |
| Classification | PROMISING CANDIDATE | PARTIALLY VALIDATED — HIGH-VALUE CANDIDATE (Class A/B/C hybrid) |
