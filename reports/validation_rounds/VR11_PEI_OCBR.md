# VR11 — PEI OCBR Technical Validation

Generated: `2026-09-26`
Scripts: `scripts/vr11_pei_probe.py` (initial probe) · `scripts/probe_pei_ocbr_vr11_1.py` (VR11.1 JS inspection)
JSON: `reports/validation_rounds/VR11_PEI_OCBR.json`

---

## 1. Source Metadata

- Source: PEI Online Corporate and Business Names Registry (OCBR)
- New registry public search page: `https://www.princeedwardisland.ca/en/feature/pei-business-corporate-registry`
- Original registry public search page: `https://www.princeedwardisland.ca/en/feature/pei-business-corporate-registry-original`
- OCBR application host: `https://ocbr.princeedwardisland.ca/ocbr/`
- OCBR login: `https://ocbr.princeedwardisland.ca/ocbr/login`
- Terms: EULA present — provincial copyright confirmed in RR07 — NOT OGL
- Role (from RR07): Candidate — PEI registry for corporations + business names; dual-registry transition period

---

## 2. Technical Probe Results

### Step 1 — PEI gov registry pages

| Registry | URL | Status | Notes |
|---|---|---|---|
| New | `/en/feature/pei-business-corporate-registry` | 200 | HTML, 125,534 bytes — Drupal CMS page |
| Original | `/en/feature/pei-business-corporate-registry-original` | 200 | HTML, 125,534 bytes — same template |

Both pages load successfully. They are Drupal CMS informational pages. JS hints found: generic `fetch()` and `XMLHttpRequest` calls — these belong to the CMS framework (euda API version check), not the registry search. No registry-specific XHR endpoint found embedded in these pages.

Terms keyword found: `robot` in both pages.

### Step 2 — OCBR application host

| Path | Status | Notes |
|---|---|---|
| `/` | 200 | 314 bytes — redirect stub |
| `/ocbr/` | 200 | 10,703 bytes HTML — SPA shell |
| `/ocbr/search` | 200 | 10,703 bytes — same SPA shell |
| `/ocbr/api/search` | 200 | 10,703 bytes — same SPA shell |
| `/ocbr/api/v1/search` | 200 | 10,703 bytes — same SPA shell |
| `/ocbr/public/search` | 200 | 10,703 bytes — same SPA shell |
| `/ocbr/businesses` | 200 | 10,703 bytes — same SPA shell |
| `/ocbr/api/businesses` | 200 | 10,703 bytes — same SPA shell |
| `/api/search` | 404 | Outside `/ocbr/` path — not found |
| `/search` | 404 | Outside `/ocbr/` path — not found |

**Key finding:** All `/ocbr/*` paths return the identical 10,703-byte HTML page. This is a Single Page Application (SPA) — all routing is client-side. The server returns the same shell regardless of path.

**JS files confirmed in SPA shell:**
- `/ocbr/resources/js/search/BasicBusinessSearch.js`
- `/ocbr/resources/js/search/basicSearch.js`
- `/ocbr/resources/js/search/SearchCommon.js`
- `/ocbr/resources/js/login.js`

A client-side search engine exists. The actual API endpoint(s) are called from these JS files, not exposed as static URL patterns.

**CSRF token:** `x-csrf` hint found in HTML — requests require a CSRF token.

**Form action:** `login/authenticate` — the application's form posts to the login endpoint, not directly to a search endpoint. This suggests the search may require an authenticated session.

### Step 3 — Search query probes

All `/ocbr/*` search queries (with params `q=Sobeys`, `name=Sobeys`) returned the same 10,703-byte SPA shell HTML — no JSON. The SPA ignores query parameters passed to the server; routing and data fetching happen entirely in the browser via JS.

### Step 4 — PEI gov API paths

All `/api/*` paths on `www.princeedwardisland.ca` returned 200 HTML (not JSON). These are Drupal CMS routes, not a registry API.

### Step 5 — robots.txt and terms

| Host | Path | Status | Notes |
|---|---|---|---|
| PEI gov | `/robots.txt` | 200 | Contains `Disallow` entries |
| PEI gov | `/privacy` | 200 | 15,055 bytes |
| PEI gov | `/en/about/terms-conditions` | 200 | 125,534 bytes (CMS page) |
| OCBR host | `/robots.txt` | 404 | Not present |
| OCBR host | `/terms-conditions` | 404 | Not present |

PEI gov `robots.txt` has `Disallow` entries — specific paths blocked. Full content not captured in this run (needs a follow-up read to determine if `/ocbr/` or search paths are disallowed).

---

## 3. Interpretation

### The OCBR is a SPA with a hidden backend API

The OCBR application at `ocbr.princeedwardisland.ca/ocbr/` is a fully client-side Single Page Application. This means:

- The actual search API endpoint is embedded in the JS files (`BasicBusinessSearch.js`, `SearchCommon.js`), not visible from URL probing
- Standard HTTP probing cannot discover the API — the JS must be fetched and read, or a real browser DevTools session must capture the XHR calls during a live search

### Login/authenticate form action

The form action is `login/authenticate`. This could mean:
1. The public search is accessible without login but uses the same SPA shell as the authenticated experience
2. The search itself requires an account session

A real browser DevTools session is required to determine which. The fact that the SPA loads without a 401/403 on the `/ocbr/` path suggests the shell is publicly accessible, but the data API may still require auth.

### CSRF token requirement

`x-csrf` is referenced in the HTML. Any API call from the browser will include a CSRF token issued by the server. This means a script replicating the API call would need to:
1. First fetch the SPA shell to obtain a CSRF token
2. Include that token in subsequent API requests

This is technically possible but adds complexity and is sensitive to token rotation.

---

## 4. Capability Assessment (Current State)

| Capability | Evidence |
|---|---|
| OCBR application reachable | ✅ HTTP 200 — SPA shell confirmed |
| Client-side search JS exists | ✅ `BasicBusinessSearch.js`, `SearchCommon.js` confirmed |
| Backend API endpoint URL | ❓ Hidden in JS — not discoverable by URL probing |
| Login required for search | ❓ Unknown — form action is `login/authenticate` but public shell loads |
| CSRF token required | ⚠️ Confirmed — `x-csrf` in HTML |
| JSON search response | ❓ Not captured — needs browser DevTools |
| Fields in search results | ❓ Unknown |
| Registration date | ❓ Unknown from search layer |
| Directors/officers | ❓ Unknown from search layer |
| Bulk download | ❌ Not found |
| EULA / provincial copyright | ⚠️ Confirmed — not OGL |
| Automated commercial use | ❓ Terms not fully retrieved |
| robots.txt Disallow entries | ⚠️ Present — specific paths not yet read |

---

## 5. What Was Unresolved After Initial Probe (Resolved in VR11.1)

These questions were open after the initial VR11 probe and are now answered:

1. **Backend API endpoint** — ✅ Resolved: `/ocbr/search/results?` (extracted from JS source)
2. **Authentication requirement for search** — ✅ Resolved: login required — unauthenticated request returns Login page
3. **CSRF token flow** — ✅ Resolved: `X-CSRF-TOKEN` header required; token issued in meta tag on page load
4. **robots.txt disallow scope** — ✅ Resolved: OCBR host has no robots.txt; PEI gov robots.txt is Drupal CMS only
5. **Exact fields returned** — ❓ Still unknown — login wall prevents JSON response observation
6. **Terms for automated commercial use** — ❓ Still unresolved — provincial copyright confirmed but EULA not retrieved

---

## 6. VR11.1 — JS Inspection Results (2026-09-26)

Scripts: `scripts/probe_pei_ocbr_vr11_1.py`
JSON: `reports/validation_rounds/VR11_PEI_OCBR.json` → `vr11_1_js_inspection`

### JS assets fetched

All three JS assets returned HTTP 200:

| Asset | Size | Status |
|---|---|---|
| `BasicBusinessSearch.js` | 14,348 bytes | ✅ Fetched |
| `basicSearch.js` | 252 bytes | ✅ Fetched (thin entry-point only) |
| `SearchCommon.js` | 23,810 bytes | ✅ Fetched |

### API endpoints extracted from JS source

Four URL candidates were identified directly from the JS source code:

| Endpoint | Source file | Purpose |
|---|---|---|
| `/ocbr/search/results?` | BasicBusinessSearch.js | Primary search — `$.ajax GET` confirmed |
| `/ocbr/search/results/facet?` | BasicBusinessSearch.js | Faceted filter — `$.ajax GET` confirmed |
| `/ocbr/search/results/more` | BasicBusinessSearch.js | Pagination — "Show More" |
| `/ocbr/search/advanced/results/more` | SearchCommon.js | Advanced search pagination |
| `/ocbr/entityHome/{id}` | BasicBusinessSearch.js | Individual entity detail page |

Excerpt from `BasicBusinessSearch.js` (actual source):
```
$.ajax({
    url: '/ocbr/search/results/facet?' + $.param(data),
    type: 'GET',
}).success(function (result) { ...
```

### Authentication finding — CONFIRMED

A GET to `/ocbr/search/results?name=Sobeys&q=Sobeys&search=Sobeys` returned:

```
HTTP 200  text/html;charset=UTF-8  10,703 bytes
<title>Login</title>
<meta name="_csrf_parameter" content="_csrf" />
<meta name="_csrf_header" content="X-CSRF-TOKEN" />
<meta name="_csrf" content="14aaf470-03a9-4baa-bf93-df2b72ca4607" />
```

**The server returned the Login page, not search results.**
This is a confirmed, measured fact: an unauthenticated request to the search endpoint is redirected to login. The search API requires an authenticated session. This is not a hypothesis.

### robots.txt finding

| Host | robots.txt | Notes |
|---|---|---|
| `ocbr.princeedwardisland.ca` | 404 — not present | No bot rules on OCBR host |
| `www.princeedwardisland.ca` | 200 — present | Drupal CMS only — blocks `/admin/`, `/user/`, `/search/` etc. Does NOT reference `/ocbr/` |

The OCBR application (`ocbr.princeedwardisland.ca`) has no robots.txt. The PEI gov robots.txt applies to the Drupal CMS at `www.princeedwardisland.ca` only — it is irrelevant to the OCBR application. There are no robot exclusion rules blocking OCBR access.

---

## 7. Final Assessment

### What is now confirmed

| Question | Answer |
|---|---|
| Live OCBR application | ✅ Confirmed — HTTP 200 |
| SPA architecture | ✅ Confirmed |
| Public static JS assets | ✅ Confirmed — all 3 fetched |
| Backend API endpoint URL | ✅ Confirmed — `/ocbr/search/results?` (plus facet/pagination variants) |
| Request method | ✅ `$.ajax GET` (confirmed in JS source) |
| Authentication required for search | ✅ Confirmed — unauthenticated request returns Login page |
| CSRF token required | ✅ Confirmed — `X-CSRF-TOKEN` header, token in meta tag |
| robots.txt blocks OCBR | ✅ Confirmed NOT blocked — OCBR host has no robots.txt; PEI gov robots.txt is Drupal CMS only |
| Anonymous public search | ❌ Not possible — login required |
| Returned fields (JSON) | ❓ Unknown — never reached; requires auth |
| EULA / commercial use terms | ❓ Unresolved — provincial copyright confirmed but exact automation/commercial terms not retrieved |

### Production suitability — CONFIRMED UNSUITABLE for unauthenticated automation

The OCBR search requires a registered user session. An automated pipeline would need to:
1. Hold a registered OCBR account
2. Authenticate, obtain a session cookie
3. Include `X-CSRF-TOKEN` in every search request

This is technically possible but operationally fragile (session expiry, CSRF rotation, account suspension risk) and raises unanswered commercial-use questions under the provincial EULA.

**Decision:** Do not invest further in PEI OCBR for this pipeline. The assignment requires a scalable Canada-wide system; PEI OCBR is session-authenticated with unresolved commercial terms. Continue to VR12.

---

## 8. Summary Metrics

| Metric | Result |
|---|---|
| PEI gov registry pages | ✅ Both 200 — confirmed reachable |
| OCBR application | ✅ HTTP 200 — SPA shell loads at `/ocbr/` |
| Application type | Single Page Application (SPA) |
| JS search files confirmed | ✅ All 3 fetched — BasicBusinessSearch.js (14KB), basicSearch.js (252B), SearchCommon.js (24KB) |
| Backend API endpoint | ✅ Confirmed — `/ocbr/search/results?` (`$.ajax GET`) |
| JSON search response | ❌ Not captured — unauthenticated request redirected to Login |
| CSRF token required | ✅ Confirmed — `X-CSRF-TOKEN` header required |
| Login required for search | ✅ Confirmed — unauthenticated GET returns Login page |
| robots.txt blocks OCBR | ❌ Not blocked — OCBR host has no robots.txt |
| Bulk download | ❌ Not found |
| EULA / provincial copyright | ⚠️ Confirmed — not OGL |
| Automated commercial use | ❓ Unresolved — EULA not retrieved |
| Final status | ⚠️ PARTIALLY VALIDATED — API endpoint and auth requirement confirmed; anonymous search not possible; production automation requires registered account session + unresolved commercial terms. No further investment recommended. Proceed to VR12. |
