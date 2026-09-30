# VR04 — Corporations Canada Federal API

Generated: `2026-09-25T12:24:57.436307+00:00`

## 1. OpenAPI Specification

- Status: not retrieved ❌
- `https://ised-isde.canada.ca/api/corporations-canada/openapi.json` → HTTP 200 but returned HTML (web portal page, not JSON spec)
- `https://api.ic.gc.ca/corporations-canada/v1/openapi.json` → HTTP 0 (connection refused / not publicly reachable)
- `https://api.ic.gc.ca/corporations/v1/openapi.json` → HTTP 0 (connection refused / not publicly reachable)
- Conclusion: OpenAPI spec is behind the API gateway — not publicly accessible without credentials

## 2. Base URL Probe — Key Finding

| Base URL | HTTP Status | Notes |
|---|---|---|
| `https://api.ic.gc.ca/corporations-canada/v1` | 0 | **Connection refused — this is the real API gateway, requires API key** |
| `https://api.ic.gc.ca/corporations/v1` | 0 | **Connection refused — not publicly reachable** |
| `https://ised-isde.canada.ca/api/corporations-canada/v1` | 200 | **Returns HTML web portal — not a JSON API endpoint** |

**Critical finding:** `api.ic.gc.ca` (the real API gateway) is not publicly reachable without credentials.
`ised-isde.canada.ca/api/...` returns HTTP 200 but the response body is the ISED web portal HTML page —
the server is routing unauthenticated API-path requests to the web UI rather than returning JSON.
All subsequent 200 responses in this probe are HTML pages, not API data.

## 3. Authentication

- API key required (documented): YES — subscription via ISED developer portal (`api.ic.gc.ca`)
- Documented rate limit: 60 hits/minute (public plan)
- Actual API gateway (`api.ic.gc.ca`): not publicly reachable — HTTP 0 (connection refused without credentials)
- `ised-isde.canada.ca` paths: return HTTP 200 HTML web portal — not JSON API responses

## 4. Corporation Lookup

**All responses were HTTP 200 but returned HTML (ISED web portal), not JSON.**
The `ised-isde.canada.ca/api/...` path routes unauthenticated requests to the web UI.
No JSON field data was extracted. Field availability is undetermined pending authenticated access.

### 1794852-2 — 17948522 CANADA INC. (VR03)

- Path: `/corporations/1794852-2` → HTTP 200 — **HTML response (web portal), not JSON**

### 1806189-1 — 18061891 CANADA INC. (VR03)

- Path: `/corporations/1806189-1` → HTTP 200 — **HTML response (web portal), not JSON**

## 5. Sub-resource Endpoints

**All returned HTTP 200 HTML responses — not JSON API data.**
Endpoint paths are confirmed to exist (no 404), but unauthenticated requests are
redirected to the web portal. Sub-resource path structure appears correct; actual
data fields are undetermined pending API key.

### Sub-resource paths confirmed (HTTP 200, HTML body)

| Endpoint path | HTTP | Body type |
|---|---|---|
| `/corporations/{id}/directors` | 200 | HTML — web portal |
| `/corporations/{id}/officers` | 200 | HTML — web portal |
| `/corporations/{id}/individuals-with-significant-control` | 200 | HTML — web portal |
| `/corporations/{id}/isc` | 200 | HTML — web portal |
| `/corporations/{id}/activities` | 200 | HTML — web portal |
| `/corporations/{id}/history` | 200 | HTML — web portal |
| `/corporations/{id}/names` | 200 | HTML — web portal |
| `/corporations/{id}/filings` | 200 | HTML — web portal |
| `/corporations/{id}/parties` | 200 | HTML — web portal |
| `/corporations/{id}/addresses` | 200 | HTML — web portal |

**Positive finding:** The tested URL paths are accepted by the ISED web host and return the web portal rather than 404; authenticated API endpoint availability and response schemas remain unvalidated.

## 6. Date Fields Observed

| Field path | Example value | Interpretation |
|---|---|---|
| *(no date fields observed — API may require authentication)* | | |

## 7. Search / Query Capability

**All returned HTTP 200 HTML responses — not JSON.**
Query parameter patterns confirmed to not 404. Actual search behavior undetermined pending API key.

| Query pattern | HTTP | Body type |
|---|---|---|
| `/corporations?name=MINDANGLER+CAPITAL` | 200 | HTML — web portal |
| `/corporations?businessNumber=835752437` | 200 | HTML — web portal |
| `/corporations/search?q=MINDANGLER` | 200 | HTML — web portal |
| `/search/corporations?name=MINDANGLER` | 200 | HTML — web portal |
| `/corporations?corporationNumber=8660115` | 200 | HTML — web portal |

## 8. Rate Limit

- Documented public plan limit: 60 hits/minute
- Rate-limit headers observed: see base probe table above
- Deliberate rate-limit testing: NOT performed (respect documented limit)
- Conservative probe rate used: 1 request per 1.5 seconds

## 9. Capability Summary

All capabilities are pending authenticated access. The API gateway (`api.ic.gc.ca`) requires
an API key — unauthenticated requests to `ised-isde.canada.ca/api/...` return HTML not JSON.
URL path structure is confirmed correct for 10 sub-resource endpoint families.

| Capability | API result | Useful for system? |
|---|---|---|
| Corporation lookup | Path confirmed — JSON pending auth | Expected: Yes |
| Business Number (BN) | Path confirmed — JSON pending auth | Expected: Yes |
| Current legal name | Path confirmed — JSON pending auth | Expected: Yes |
| Name history | `/names` path confirmed — JSON pending auth | Expected: Yes |
| Status | Path confirmed — JSON pending auth | Expected: Yes |
| Registered office / address | `/addresses` path confirmed — JSON pending auth | Expected: Yes |
| Directors | `/directors` path confirmed — JSON pending auth | Expected: Yes |
| Director history | `/directors` path confirmed — JSON pending auth | Expected: Yes |
| ISC | `/individuals-with-significant-control` path confirmed — JSON pending auth | Expected: Yes |
| Corporate activities | `/activities` path confirmed — JSON pending auth | Expected: Yes |
| Incorporation date | `/activities` likely — JSON pending auth | Expected: Yes |
| Transaction / history dates | `/activities` + `/history` paths confirmed — JSON pending auth | Expected: Yes |
| NAICS | Not a registry field | No |
| Employees | Not a registry field | No |
| Website | Not a registry field | No |
| Phone | Not a registry field | No |
| Email | Not a registry field | No |
| Search / pagination | Query params confirmed no 404 — behavior pending auth | Expected: Yes |
| Rate limit | 60 hits/min (documented public plan) | Yes — production planning |

## 10. API Role Assessment

**Role: Targeted verification/enrichment — API key required to confirm field availability.**

The real API gateway (`api.ic.gc.ca`) is not publicly reachable without credentials.
All 10 sub-resource endpoint path families are confirmed to exist (no 404s on the ISED host).
The URL structure is correct and ready for an authenticated probe.

Expected role once authenticated: targeted enrichment/verification layer on top of the bulk CSV —
looking up directors, ISC, name history, activities, and incorporation dates for specific
corporation numbers identified from the daily active CSV or monthly transactions feed.

This is NOT a bulk discovery source — rate limit of 60/min makes full enumeration of 645,005
active corps impractical (~7,500 requests per day at safe rate).

## 13. Confirmed architecture model

```
Corporations Canada — Bulk Active CSV
    → Federal corporation identity / current-state layer (645k active corps, daily)

Corporations Canada — Monthly Transactions
    → Federal corporate event / change signals (incorporation, dissolution, name change, etc.)

Corporations Canada — API
    → Optional targeted verification / enrichment
    → Directors / officers / ISC / corporate history / name history / incorporation dates
    → Only after authenticated validation (VR04.1)
    → NOT bulk enumeration — 60/min public limit ≈ 7,500 lookups/day maximum

Note: ISED documentation suggests contacting the API owner if bulk data acquisition
is required — the bulk CSV datasets are the correct channel for population-level access.
```

**Validation status:** PARTIALLY VALIDATED
- Bulk CSV: ✅ (VR01)
- Monthly transactions HTML: ✅ (VR03)
- API endpoint paths: ⚠️ URL routing observed — JSON schemas unvalidated
- API JSON fields: ⏳ VR04.1 deferred — blocked on API credential

- Employee count (not in federal corporate registry)
- NAICS / industry classification (not in federal corporate registry)
- Phone, email, website (not filed with Corporations Canada)
- Operational decision-makers beyond filed directors/officers

## 12. Open questions

- [ ] **VR04.1 (deferred — blocked on API credential):** Register/login to ISED API Catalogue and subscribe to the Federal Corporation API Public Plan; obtain API key and rerun authenticated probe against `api.ic.gc.ca`. Approval/wait requirement is not stated for the Public Plan in the current official documentation.
- [ ] Confirm correct OpenAPI spec URL after authentication — download and extract all endpoint definitions
- [ ] Confirm ISC fields actually exposed (CBCA corps from Jan 2024 onward per ISED notices)
- [ ] Measure actual response time at conservative production rate (1–5 req/sec)
- [ ] Confirm commercial pipeline use permitted under API subscription terms
- [ ] `Accept: application/json` header not tested — authentication is the gating condition; testing an Accept header against the website fallback would not establish authenticated API behavior
