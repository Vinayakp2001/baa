# Research Round 01 — Corporations Canada

**Date:** 2026-09-25
**Source:** GPT research pass — Corporations Canada federal open data, API, monthly transactions, ISC
**Status:** Research complete — profiling/download not yet done

---

## TL;DR

Corporations Canada is a confirmed high-value source — stronger than previously assessed.
Best used as the federal legal-identity + current-status + change-detection layer.
It does NOT replace provincial sources, ODBus, or contact enrichment.

---

## 1. What It Covers

- Corporations created under the **Canada Business Corporations Act (CBCA)** only
- Does NOT cover: provincial/territorial corporations, sole proprietors, partnerships, financial-legislation corporations
- Reorganized April 2026 into 4 datasets (each in EN + FR):
  - Active business corporations
  - Other active corporations
  - Inactive business corporations
  - Other inactive corporations
- Files typically updated **daily**

---

## 2. Bulk Dataset — Confirmed Fields

| Field | Value for assignment |
| --- | --- |
| Corporation number | Very high — stable federal ID |
| Business Number (BN) | Very high — cross-source matching key |
| Corporate name form 1 | Very high |
| Corporate name form 2 | High — alternate legal name |
| Governing legislation | High |
| Status | Very high |
| Status detail | Very high |
| Anniversary date | High |
| Year of last annual filing | Medium/high |
| Date of last annual meeting | Medium/high |
| Street | Very high |
| Street 2 | High |
| City/town | Very high |
| Province/territory | Very high |
| Country | High |
| Postal code | Very high |
| Min/max number of directors | Medium |

**Hard gaps in bulk CSV — NOT present:**
- Phone, email, website
- NAICS / industry
- Employee count / size bucket
- Owner / founder / manager fields

---

## 3. API — Significantly Richer Than Bulk CSV

The API is the most important finding from this round.

**API provides real-time access to:**
- Status
- Registered office address
- Directors
- Corporation names + history
- Business number
- Annual returns
- Corporate activities (with dates)
- Incorporation/activity dates

**API response structure (confirmed):**
```
corporationId
act
status
corporationNames[]
    name / nameType / current / effectiveDate / expiryDate
addresses[]
    addressLine / city / postalCode / provinceCode / countryCode
directorLimits
    minimum / maximum
businessNumbers
    businessNumber
annualReturns[]
    annualMeetingDate / yearOfFiling
activities[]
    activity / date
```

**Rate limit:** 60 requests/minute (public plan — requires login/subscription, free)

**Key insight:** `activities[]` can expose an Incorporation activity with a date — useful for new-business detection without relying on website discovery.

---

## 4. Directors — Confirmed Public

- Director information is legally public corporate information
- Required to be updated within 15 days of any change
- API provides directors in real time
- Public info includes: name, address/address for service, corporate relationship

**Important semantic note:**
Director ≠ owner ≠ telecom decision-maker.
Directors are valid public decision-maker candidates but must not be auto-labelled as "president", "IT manager", etc. in the system.

---

## 5. Individuals with Significant Control (ISC) — Major New Finding

Since January 22, 2024, CBCA corporations must file ISC information with Corporations Canada.

**Publicly available ISC info can include:**
- Full legal name
- Residential address or address for service
- Start/end date of control
- Description of significant control

**For eligible federal corporations we potentially have:**
```
Corporation → Director(s) → ISC(s)
```

This is a legitimate government source for people associated with federal corporations — stronger than scraping company websites.

**Caveat:** ISC = legal ownership/control signal, not automatically a "sales decision-maker."
Also need to validate: is ISC accessible via API programmatically, or only on the public web page?

---

## 6. New-Business / Change Detection — Genuinely Viable

**Monthly transactions dataset provides:**
- Corporation number
- Corporation name
- Transaction type/notice
- Transaction date
- Corporate file number

**Certificates of Incorporation publication contains:**
- Corporation number
- Corporation name
- Registered office
- Effective date (= incorporation date)

**Other transaction types confirmed:**
- Certificates of Discontinuance (with original incorporating jurisdiction — useful for provincial cross-reference)
- Continuance
- Amalgamation
- (Others — need full profiling)

**Operational limitation:**
- Public page currently exposes only the latest month directly
- Older months are archived and may require a request
- Do NOT assume unlimited historical transaction archive is programmatically accessible — needs validation
- Latest available publication: July 2026

---

## 7. Identifiers — Particularly Valuable

Two cross-source matching keys:
- **Corporation Number** — primary Corporations Canada ID
- **9-digit Business Number (BN)** — CRA-issued, appears in other government datasets

Both can be used to look up a specific corporation via the API.

---

## 8. Licensing

- Published under **Open Government Licence – Canada**
- Free for commercial use (subject to OGL terms)
- API access is free (public plan) — but "free" ≠ "unrestricted automated usage"
- Must separately verify API subscription terms and applicable usage conditions before production use

---

## 9. Geographic Coverage — Keep Expectations Realistic

| Question | Answer |
| --- | --- |
| Canada-wide geography? | Yes |
| All Canadian businesses? | No |
| Federal CBCA corporations? | Yes |
| Provincial corporations? | No |
| Sole proprietors / partnerships? | Not generally |
| Active federal corporations? | Yes |
| Historical / inactive federal? | Yes |

Provincial/territorial source research remains essential for full Canada coverage.

---

## 10. Hard Gaps (Confirmed)

| Gap | Impact |
| --- | --- |
| Employee count / size bucket | Cannot fulfill assignment employee requirement from this source alone |
| NAICS / industry | No industry classification — enrichment required |
| Phone / email / website | Not a contact-data source |
| Provincial corporations | Significant missing population — exact % unknown |
| Sole proprietors / partnerships | Not represented |

---

## 11. Date Fields — Important Semantic Distinction

Multiple date concepts exist — do NOT collapse into one generic `registration_date`:

| Field | Source | Meaning |
| --- | --- | --- |
| Anniversary date | Bulk CSV | Annual return anniversary |
| Year of last annual filing | Bulk CSV | Most recent annual return year |
| Incorporation activity date | API `activities[]` | Actual incorporation date |
| Effective date | Monthly transactions (Cert. of Inc.) | Transaction effective date |
| Annual meeting date | API `annualReturns[]` | Meeting date |

Record these as separate fields with source attribution.

---

## 12. Relationship to ODBus

These are complementary — neither replaces the other:

| Dimension | ODBus | Corporations Canada |
| --- | --- | --- |
| Origin | Compiled from municipal/open datasets | Authoritative federal registry |
| Identifier | Internal `idx` / `business_id_no` | Corporation Number + BN |
| Legal identity layer | No | Yes |
| Director / ISC info | No | Yes |
| Employee data | Yes (messy) | No |
| NAICS | Yes (partial) | No |
| Freshness | Historical ~2022 | Daily |
| API | No | Yes |
| Provincial businesses | Yes (via municipal licences) | No |

**Potential identity bridge:** ODBus record → match by name + postal code → federal corporation → Corporation Number + BN + directors

---

## 13. Upgrades From Previous Understanding

| Before | After |
| --- | --- |
| "Registration date + status + address + directors in some datasets" | Confirmed: bulk + API + directors + ISC + corporate activity + BN + corp ID + daily updates + transactions |
| "Enrichment/verification source only" | Now a primary discovery + change-detection candidate for federal corporations |
| "Decision-makers require website scraping" | Directors + ISC give us a legitimate government signal for federal corporations |

---

## 14. Next Actions Required (Before This Source Is Production-Ready)

- [ ] Download current active corporations CSV — profile row count, encoding, null patterns, status values, province distribution, duplicate corp numbers, BN uniqueness, date distributions
- [ ] Test live API — exact response schema, director structure, ISC availability, whether all fields come from one call, auth/subscription mechanics
- [ ] Profile monthly transaction categories — which types support "new business" detection
- [ ] Sample-match federal CSV against ODBus by name + postal code — measure overlap
- [ ] Verify API usage terms — automated production use, attribution, request limits
- [ ] Confirm whether ISC is accessible programmatically via API (not just on the public web page)

---

## 15. Confirmed Source Profile (Updated)

| Dimension | Finding |
| --- | --- |
| Source type | Federal corporate registry / open data |
| Coverage | Federal CBCA corporations only |
| Geography | Canada |
| Individual records | Yes |
| Daily bulk refresh | Yes |
| Real-time API | Yes (60 req/min public plan) |
| Legal name + history | Yes |
| Corporation ID | Yes |
| Business Number (BN) | Yes |
| Status + status detail | Yes |
| Registered address + postal code | Yes |
| Incorporation / activity dates | Yes (API + transactions) |
| Directors | Yes (API + public corp info) |
| ISC (ownership/control) | Yes (for applicable CBCA corps) |
| Employee count / bucket | No |
| NAICS | No |
| Website / phone / email | No |
| Licence | OGL – Canada |
| Cost | Free |
| All Canadian businesses? | No |
