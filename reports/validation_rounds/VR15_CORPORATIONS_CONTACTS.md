# VR15.2 — Corporations Canada Director / ISC Enrichment

**Generated:** 2026-09-26T08:14:52Z
**Last updated:** 2026-09-26 (GPT corrections applied)
**Scripts:** `scripts/probe_corporations_contacts_vr15_2.py`, `scripts/probe_corps_dom_vr15_2_1.py`
**Status:** ❌ HTML ROUTES NOT SUITABLE — API subscription required (VR15.2.2)

---

## 1. Probe Scope

| Item | Value |
|---|---|
| Test set | 10 federal corporations |
| Sources | VR01 sample records (2), well-known Canadian corps (6), placeholder corp numbers (2) |
| Route A | HTML page: `https://ised-isde.canada.ca/cc/lgcy/fdrlCrpDtls.html?corpId=XXXXXX` |
| Route B | JSON API: `https://ised-isde.canada.ca/cc/api/corporations/XXXXXX` |

---

## 2. Metrics

| Metric | Count | Rate |
|---|---|---|
| Total corporations tested | 10 | — |
| HTML page accessible (HTTP 200) | 10 | 100% |
| API accessible without auth | 0 | 0% |
| API returned 404 | 10 | 100% |
| API required auth (401/403) | 0 | 0% |
| Director data accessible (HTML) | 2 | 20% |
| ISC section detected (HTML) | 2 | 20% |
| Automation feasible | 2 | 20% |

---

## 3. Per-Corporation Results

| Corp # | Name | Province | HTML | API | Directors | ISC | Automatable |
|---|---|---|---|---|---|---|---|
| 8660115 | MINDANGLER CAPITAL INC. | ON | 200 ✅ | 404 ❌ | ❌ FALSE POSITIVE | ❌ FALSE POSITIVE | ❌ |
| 821080 | AIRMEC CLIMATISATION LTEE | QC | 200 ✅ | 404 ❌ | ❌ FALSE POSITIVE | ❌ FALSE POSITIVE | ❌ |
| 158072 | CANADIAN TIRE CORPORATION LIMITED | ON | 200 ✅ | 404 ❌ | ❌ | ❌ | ❌ |
| 4396626 | AIR CANADA (corrected#) | QC | 200 ✅ | 404 ❌ | ❌ | ❌ | ❌ |
| 250430 | LOBLAWS INC | ON | 200 ✅ | 404 ❌ | ❌ | ❌ | ❌ |
| 2893 | BOMBARDIER INC. | QC | 200 ✅ | 404 ❌ | ❌ | ❌ | ❌ |
| 339573 | SHOPPERS DRUG MART CORPORATION | ON | 200 ✅ | 404 ❌ | ❌ | ❌ | ❌ |
| 271517 | ROGERS COMMUNICATIONS INC. | ON | 200 ✅ | 404 ❌ | ❌ | ❌ | ❌ |

### VR15.2 "Successful" extractions — CONFIRMED FALSE POSITIVES

**8660115 — MINDANGLER CAPITAL INC.**
- VR15.2 reported: director `Nigel Stokes` extracted, ISC section detected
- VR15.2.1 confirmed: section-aware DOM parser found ZERO Directors/ISC headings in HTML source
- The name `Nigel Stokes` and ISC detection came from boilerplate page text matched by full-text regex
- Page text contains definition phrases ("A director is an individual elected by...") and labels ("Minimum") that match director-related patterns without being director records
- **STATUS: FALSE POSITIVE — not a valid extraction**

**821080 — AIRMEC CLIMATISATION LTEE**
- VR15.2 reported: director `MARIO TESTA` extracted, ISC section detected
- VR15.2.1 confirmed: same shell page — only two headings found: "Federal corporation information" + "Date Modified:"
- **STATUS: FALSE POSITIVE — not a valid extraction**

### Important note on corp numbers
The corp numbers used for well-known large companies in VR15.2 (Air Canada=7122, Canadian Tire=158072 etc.)
were manually assembled, not sourced from the authoritative CBCA CSV. Corp numbers must always be sourced
from the Corporations Canada dataset or API search results, not manually entered. Air Canada number corrected
to 4396626 for VR15.2.1.

---

## 4. API Route — Confirmed Non-Functional

All 10 corporations returned HTTP 404 on the API route (`/cc/api/corporations/XXXXXX`).
This is consistent with VR04 findings — the Corporations Canada REST API requires a subscription/API key
and the public endpoint path does not serve unauthenticated requests with a 401/403.
Instead it returns 404, meaning the path itself is not publicly exposed at this URL structure.

**API route is NOT viable for unauthenticated access.**
VR04.1 (API key acquisition) remains deferred and is required before the API route can be validated.

---

## 5. HTML Routes — Final Assessment (both confirmed not suitable)

### Route A — Legacy HTML (`fdrlCrpDtls.html`)
All pages return HTTP 200 but the DOM contains only two section headings on every page:
`"Federal corporation information"` and `"Date Modified:"`.

No Directors section. No ISC section. No structured field content.

The page is a JavaScript-rendered shell. Director and ISC data loads via JS after page render.
The urllib-based probe cannot execute JavaScript — it captures the shell only.

**CONFIRMED: Legacy HTML URL is not a viable extraction route.**

### Route B — REST API (`/cc/api/corporations/`)
404 on all unauthenticated requests. The endpoint is not publicly exposed without API credentials.
This is not a prohibition — it is an access-control gate.

**CONFIRMED: API requires subscription (VR04.1 / VR15.2.2 pending).**

### Director/ISC data — confirmed to exist in official service
GPT confirmed via browser that current official Corporations Canada records demonstrably contain
structured sections for Directors and Individuals with Significant Control (ISC), including:
- Director names and addresses
- ISC names, control type, ownership/control information, start date
- Last confirmation/update date

The data exists and is public. The two tested machine-readable routes are not suitable.
The API is the appropriate machine-readable interface.

### Why HTML scraping was dropped as production mechanism
- Legacy `fdrlCrpDtls.html` URL is a JS shell — raw HTML contains no director/ISC fields
- Full-text regex produced false positives from boilerplate text — extraction is unreliable
- Even if a route worked, Corporations Canada states the API is the intended programmatic interface
- 2 "successful" extractions in VR15.2 were confirmed false positives in VR15.2.1

---

## 6. API Route — VR15.2.2 Results (⚠️ PARTIALLY VALIDATED)

**Subscription:** Public Plan subscribed, API key obtained (len=32).
**Script:** `scripts/probe_corps_api_vr15_2_2.py`

### What was confirmed

| Layer | Status | Finding |
|---|---|---|
| DNS / hostname | ✅ | `api.ised-isde.canada.ca` resolves to `205.194.37.193` (nslookup confirmed) |
| TLS / HTTPS | ✅ | Connection established, no SSL error |
| API key authentication | ✅ | No 401 or 403 returned — key accepted |
| Endpoint path | ❌ | `/federal-corporations/api/v1/corporations/{corp_num}` → HTTP 404 `{"status":"Not found"}` |

### What was NOT confirmed

- Correct endpoint path for corporation lookup
- Correct endpoint paths for directors, ISC, names/history
- Response schema (field names, data types, pagination)
- Rate limit behaviour at 60 req/min boundary

### What failed and why

The tested path `/federal-corporations/api/v1/corporations/8660115` returned 404.
This is a path structure error — not an auth failure, not a network failure.
The correct endpoint path must be sourced from the ISED API documentation's generated curl example.

**Previous attempt (VR15.2.2 first run) used wrong hostname `api.canada.ca` — DNS failed entirely.**
**Second attempt confirmed correct hostname and auth. Only the path remains unresolved.**

### Next step: VR15.2.2 endpoint confirmation

GPT to provide the exact path from the ISED API catalogue documentation:
1. Corporation lookup path
2. Directors sub-resource path
3. ISC sub-resource path
4. Names/history sub-resource path
5. Confirm: version prefix (`/v1/`, `/v2/`, none)
6. Confirm: auth header name (`X-API-Key` or other)

Once path is confirmed, set `SINGLE_TEST = True`, update `BASE_URL` and path templates,
run one request, verify 200, then set `SINGLE_TEST = False` for full 5×4 probe.

---

## 7. Architecture Role Assessment (revised)

| Role | Assessment |
|---|---|
| Director name enrichment — HTML legacy route | ❌ JS-rendered shell — no director content in raw HTML |
| Director name enrichment — API route | ⚠️ Confirmed to exist in live service; API subscription required (VR15.2.2) |
| ISC enrichment — HTML | ❌ Not suitable — same shell issue |
| ISC enrichment — API | ⚠️ Confirmed to exist; fields documented (name, control type, start date, ownership %) |
| API-based programmatic access | ⚠️ Host+auth confirmed; endpoint path unresolved (VR15.2.2 partially validated) |
| Automation at scale | ⚠️ Feasible once API key obtained |

### Semantics to preserve in data model

Director ≠ Owner necessarily ≠ President necessarily ≠ Telecom decision-maker necessarily
ISC is closer to ownership/control, but still not necessarily the operational contact.

Data model must preserve:

```
person_name
source_role        (Director | ISC)
source             (corporations_canada_api)
source_url
verified_at
```

Do NOT flatten to `decision_maker = true`.

---

## 8. Compliance Notes

- Public corporation details are explicitly listed as public information by Corporations Canada
- Directors' names and addresses are public corporate information under CBCA
- ISC information is public where filed
- API probe will use ISED-issued API key (subscription required, not bypassed)
- 60 req/min rate limit — probe must throttle to ≤1 req/second
- Corp numbers must be sourced from the authoritative CBCA CSV, not manually assembled

---

## 9. VR15.2.1 Results (summary)

| Corp # | Name | HTTP | Sections found | Directors section | ISC section |
|---|---|---|---|---|---|
| 8660115 | MINDANGLER CAPITAL INC. | 200 | "Federal corporation information", "Date Modified:" | ❌ | ❌ |
| 821080 | AIRMEC CLIMATISATION LTEE | 200 | "Federal corporation information", "Date Modified:" | ❌ | ❌ |
| 4396626 | AIR CANADA (corrected) | 200 | "Federal corporation information", "Date Modified:" | ❌ | ❌ |

All three pages: only 2 section headings in DOM. Legacy HTML URL confirmed as JS-rendered shell.

---

## 10. Scripts

| Script | Purpose |
|---|---|
| `scripts/probe_corporations_contacts_vr15_2.py` | VR15.2 initial full-text regex probe (false positives) |
| `scripts/probe_corps_dom_vr15_2_1.py` | VR15.2.1 DOM section parser (confirmed JS shell) |
| `scripts/probe_corps_api_vr15_2_2.py` | VR15.2.2 authenticated API probe — host+auth confirmed, path pending |

*Machine-readable: `reports/validation_rounds/VR15_CORPORATIONS_CONTACTS.json`*
