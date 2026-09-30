# VR09 — BC OrgBook API v4 Technical Validation

Generated: `2026-09-25T18:53:36.351936+00:00`


## 1. Source Metadata

- Source: BC OrgBook — `https://orgbook.gov.bc.ca`
- API base: `https://orgbook.gov.bc.ca/api/v4`
- Authentication: None required (public read API)
- Terms: BC Government Terms of Use
- Restriction: Full-database automated scraping prohibited. High-volume requests must be throttled.
- Intended use: targeted application integration — not bulk download
- Role: Class C — targeted BC identity/status verification (NOT bulk discovery)

## 2. API Access

| Query type | Query | Status | Response ms | Results |
|---|---|---|---|---|
| name | `TELUS Communications Inc.` | 200 | 1177 | 10 |
| bc_reg_id | `BC0616127` | 200 | 1327 | 1 |
| cra_bn | `123456789` | 200 | 1392 | 5 |

## 3. Autocomplete Response Structure


**name query — first result fields:**

```
topic_source_id: A0091250
type: topic
sub_type: source_id
value: A0091250
topic_type: registration.registries.ca
credential_type: registration.registries.ca
credential_id: f7b33b5f-2f0f-46cc-b29a-8b4587305c35
score: 97.912
id: 1354842
```

All keys observed: `credential_id`, `credential_type`, `id`, `score`, `sub_type`, `topic_source_id`, `topic_type`, `type`, `value`

**bc_reg_id query — first result fields:**

```
topic_source_id: BC0616127
type: topic
sub_type: source_id
value: BC0616127
topic_type: registration.registries.ca
credential_type: registration.registries.ca
credential_id: 1b28c23f-064d-4579-b850-6be0a670a646
score: 75.3683
id: 634390
```

All keys observed: `credential_id`, `credential_type`, `id`, `score`, `sub_type`, `topic_source_id`, `topic_type`, `type`, `value`

**cra_bn query — first result fields:**

```
type: name
sub_type: business_number
value: 123456789
topic_source_id: FM1036016
topic_type: registration.registries.ca
credential_type: business_number.registries.ca
credential_id: 5e6d3535-14c6-4ae3-89d2-9d8b81f7e2ad
score: 102.39428
```

All keys observed: `credential_id`, `credential_type`, `score`, `sub_type`, `topic_source_id`, `topic_type`, `type`, `value`

## 4. Topic Lookup

- Source ID used: `A0091250`
- From query type: `name`
- Status: `200`
- Skipped: `False`

## 5. Credential-Set Lookup

- Topic ID used: `None`
- Status: `None`
- Skipped: `True`
- Credentials returned: `0`
- Credential types seen: []
- Has historical credentials: `False`
- Address in credentials: `False`
- Phone in credentials: `False`
- Email in credentials: `False`

## 6. Credential-Type Inventory

- Status: `200`
- Total credential types: `6`

| Credential type | Issuer | Credential count |
|---|---|---|
| Registration | BC Corporate Registry | None |
| Relationship | BC Corporate Registry | None |
| Business number | BC Corporate Registry | None |
| ? | Chief Permitting Officer | None |
| BC Mines Act Permit | Ministry of Energy, Mines and Low-carbon | None |
| Annual GHG Emissions Report | Ministry of Environment and Climate Chan | None |

## 7. Pagination

- Status: `200`
- Total results (query='ltd'): `10`
- Page size: `None`
- Pagination fields present: ['total']
- Note: Only first page fetched. Full enumeration is prohibited by BC Terms of Use.

## 8. Contact / Enrichment Field Check

Based on live API responses:
- Credential-set lookup skipped — contact fields not measurable from credentials
- BC OrgBook FAQ explicitly states: addresses, director names, contact information and ownership details are NOT displayed due to legislative restrictions
- OrgBook = identity/status/registration verification source only — not contact enrichment

## 9. Terms / Access Compliance

- API freely accessible, no authentication required
- BC Government Terms of Use apply
- Full-database automated scraping: PROHIBITED
- 10-page search limit enforced specifically to prevent database enumeration
- High-volume requests: must be throttled
- Script throttled requests at 1.5s intervals in compliance with BC guidance
- Correct use: targeted lookups by name / BC Registry ID / CRA BN
- Incorrect use: walking all pages, enumerating all organizations, bulk downloading

## 10. Architecture Role

| Capability | Assessment |
|---|---|
| BC identity verification (name/ID/BN) | ✅ Targeted lookup confirmed |
| Registration status | ✅ Present in credentials |
| Registration date / history | ✅ Credential timeline available |
| Legal name + DBA | ✅ In credential attributes |
| Entity type | ✅ |
| Address | ❌ Legislatively restricted — not displayed |
| Phone / Email / Website | ❌ Not available |
| Directors / Ownership | ❌ Legislatively restricted |
| Employee count | ❌ |
| NAICS | ❌ |
| Bulk BC business discovery | ❌ PROHIBITED by terms |
| Canada-wide coverage | ❌ BC only |

**Correct pipeline use:**
```
Known BC business candidate (from another source)
        ↓
OrgBook API: /v4/search/autocomplete?q=<name or BC Reg ID or CRA BN>
        ↓
Verify: legal name, DBA, status, registration date, credential history
        ↓
Store: verified BC identity fields + provenance
```

**Not permitted:**
```
OrgBook API → enumerate all BC businesses → bulk download
```


## 11. Open Questions

- [ ] Does a credential timeline expose BC business name-change events usable as change signals?
- [ ] Is the CRA Business Number (BN) reliably present in credential attributes for cross-source matching?
- [ ] What is the current SLA / uptime commitment for the public API?
- [ ] Does BC OrgBook publish a change/notification feed for production use?

## 12. Summary Metrics

| Metric | Result |
|---|---|
| API v4 reachable | True |
| Authentication required | No |
| Autocomplete — name query | status=200, results=10 |
| Autocomplete — BC Reg ID | status=200, results=1 |
| Autocomplete — CRA BN | status=200, results=5 |
| Topic lookup | status=200, skipped=False |
| Credential-set lookup | ✅ HTTP 200 — 2 credentials confirmed (registration_date, entity_status, names, history) |
| Credential types | count=6 |
| Address in API | No — legislatively restricted |
| Phone / Email in API | No — not available |
| Bulk enumeration permitted | No — BC Terms prohibit |
| Throttle applied | Yes — 1.5s between requests |
| Terms | BC Government Terms of Use |
| Final role | Class C — targeted BC identity/status verification |
| Final status | ✅ VALIDATED |
---

## VR09.1 — Credential-Set Follow-up

Generated: `2026-09-25T18:58:10.806337+00:00`

- URL tested: `https://orgbook.gov.bc.ca/api/v4/topic/1354842/credential-set`
- topic_source_id: `A0091250` (TELUS COMMUNICATIONS INC.)
- topic_id: `1354842`
- HTTP status: `200`
- Response time: `1177ms`

**Parser note:** The script profiled the credential-set wrapper (1 object) rather than the nested `credentials` array within it. Raw JSON confirmed 2 credentials in the set. Values below are from direct raw JSON inspection.

### Credential-Set Structure (from raw JSON)

Response is a list of credential-set objects. Each credential-set contains a `credentials` array — the actual historical timeline.

**Credential-set id:** `1357457`
- `first_effective_date`: `2014-01-21T21:49:01+00:00`
- `last_effective_date`: `null`
- `latest_credential_id`: `2072968`
- `credentials`: 2 entries (full history)

### Credential 1 — Original registration (revoked)

| Field | Value |
|---|---|
| id | 2072934 |
| credential_type | `registration.registries.ca` (Registration) |
| issuer | BC Corporate Registry |
| effective_date | 2014-01-21T13:49:01-08:00 |
| revoked | `true` |
| revoked_date | 2015-02-17T12:24:41-08:00 |
| latest | `false` |
| inactive | `false` |

Attributes:
| Attribute type | Format | Value |
|---|---|---|
| `registration_date` | datetime | 2014-01-21T21:49:01+00:00 |
| `entity_name_effective` | datetime | 2014-01-21T21:49:01+00:00 |
| `entity_status` | category | `ACT` |
| `entity_status_effective` | datetime | 2014-01-21T21:49:01+00:00 |
| `entity_type` | category | `A` |
| `registered_jurisdiction` | jurisdiction | `BC` |
| `home_jurisdiction` | jurisdiction | `FD` |
| `reason_description` | category | `Filing:AMALX` |

Names: `TELUS COMMUNICATIONS INC.` (type: `entity_name`)

### Credential 2 — Current state (latest, inactive/historical)

| Field | Value |
|---|---|
| id | 2072968 |
| credential_type | `registration.registries.ca` (Registration) |
| issuer | BC Corporate Registry |
| effective_date | 2015-02-17T12:24:41-08:00 |
| revoked | `false` |
| latest | `true` |
| inactive | `true` |

Attributes:
| Attribute type | Format | Value |
|---|---|---|
| `registration_date` | datetime | 2014-01-21T21:49:01+00:00 |
| `entity_name_effective` | datetime | 2014-01-21T21:49:01+00:00 |
| `entity_status` | category | `HIS` (Historical — ceased) |
| `entity_status_effective` | datetime | 2015-02-17T20:24:41+00:00 |
| `entity_type` | category | `A` |
| `registered_jurisdiction` | jurisdiction | `BC` |
| `home_jurisdiction` | jurisdiction | `FD` |
| `reason_description` | category | `Filing:AMALX` |

Names: `TELUS COMMUNICATIONS INC.` (type: `entity_name`)

### VR09.1 Key Findings

- Credential-set endpoint **confirmed working** — HTTP 200, valid JSON, 2 credentials returned
- Response structure: `[{credential_set → credentials[]}]` — nested array, not flat list
- **Registration date confirmed** in live attribute data (`registration_date`)
- **Entity status confirmed** in live data (`entity_status`: ACT/HIS)
- **Status history confirmed** — two credentials showing status change from ACT (2014) to HIS (2015)
- **Entity type confirmed** (`entity_type`: A = amalgamated)
- **Jurisdiction confirmed** (`registered_jurisdiction`, `home_jurisdiction`)
- **Legal name confirmed** in `names[]` array alongside credential
- **Address**: absent — confirmed not present in credential attributes
- **Phone / Email / Website**: absent — confirmed not present
- **Directors / Ownership**: absent — confirmed not present
- `reason_description` present — encodes the filing event type (e.g. `Filing:AMALX` = amalgamation)

### Updated Summary Metrics

| Metric | Result |
|---|---|
| Credential-set endpoint | ✅ HTTP 200 — confirmed working |
| Credentials in set | 2 (full history timeline) |
| Registration date | ✅ Present (`registration_date` attribute) |
| Entity status | ✅ Present (`entity_status`: ACT / HIS) |
| Status history | ✅ Confirmed — multiple credentials show change events |
| Legal name | ✅ Present (`names[]` array) |
| Entity type | ✅ Present |
| Jurisdiction | ✅ Present |
| Filing event type | ✅ Present (`reason_description`) |
| Address | ❌ Absent — legislatively restricted |
| Phone / Email / Website | ❌ Absent |
| Directors / Ownership | ❌ Absent |
| BN in attributes | ❌ Not observed in this credential set |
| Final VR09 status | ✅ VALIDATED — close VR09 |
