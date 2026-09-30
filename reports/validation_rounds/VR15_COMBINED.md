# VR15 Combined — Corporations Canada API + Website Discovery + Website Enrichment

**Generated:** 2026-09-26T10:34:52Z
**Script:** `scripts/probe_vr15_combined.py`
**Status:** ✅ PART A VALIDATED | ❌ PART B NOT SUITABLE | ⚠️ PART C PARTIALLY VALIDATED

---

## Part A — Corporations Canada API (VR15.2.2) ✅ VALIDATED

### Endpoint configuration confirmed

| Parameter | Value |
|---|---|
| Base URL | `https://apigateway-passerelledapi.ised-isde.canada.ca/corporations/api` |
| Corporation lookup | `/v1/corporations/{corporation_id}.json?lang=eng` |
| Directors | `/v2/corporations/{number}/directors` |
| Auth header | `user-key: <API_KEY>` |
| Rate limit | 60 req/min (Public Plan) — throttle at 1.2s/req |
| ISC endpoint | Not exposed in current OpenAPI spec — do not use |

All 5 corporations × 2 endpoints = 10 requests returned HTTP 200.

### Corporation lookup — confirmed response schema

```
[
  {
    "corporationId": "8660115",
    "act": "Canada Business Corporations Act",
    "status": "Active",
    "corporationNames": [
      { "CorporationName": { "name": "...", "nameType": "Primary", "current": true, "effectiveDate": "..." } }
    ],
    "adresses": [...],
    "directorLimits": {...},
    "businessNumbers": [...],
    "annualReturns": [...],
    "activities": [...]
  },
  ...
]
```

Note: field is spelled `"adresses"` (single 'd') in the API response — not a typo in this report.

### Directors endpoint — confirmed response schema

```
{
  "_embedded": {
    "directors": [
      {
        "firstName": "Nigel",
        "lastName": "Stokes",
        "serviceAddress": {
          "line1": "60 Boswell Avenue",
          "city": "Toronto",
          "subdivisionCode": "ON",
          "subdivisionNames": { "en": "Ontario", "fr": "Ontario" }
        }
      }
    ]
  },
  "_links": { "self": { "href": "..." } }
}
```

### Per-corporation results

| Corp # | Name | Lookup | Status field | Directors HTTP | Directors found |
|---|---|---|---|---|---|
| 8660115 | MINDANGLER CAPITAL INC. | ✅ 200 | Active | ✅ 200 | Nigel Stokes (Toronto ON) |
| 821080 | AIRMEC CLIMATISATION LTEE | ✅ 200 | Active - Dissolution Pending (Non-compliance) | ✅ 200 | MARIO TESTA (Montreal QC) |
| 4396626 | AIR CANADA | ✅ 200 | Active | ✅ 200 | KATHLEEN TAYLOR (Saint Laurent QC) + others |
| 158072 | CANADIAN TIRE CORPORATION LIMITED | ✅ 200 | "could not find corporation 158072" | ✅ 200 | No directors (empty `_links` only) |
| 271517 | ROGERS COMMUNICATIONS INC. | ✅ 200 | "could not find corporation 271517" | ✅ 200 | No directors (empty `_links` only) |

### Key observations

**Corp numbers 158072 and 271517 not found** — these numbers resolve to HTTP 200 but the API
returns `"could not find corporation"`. This confirms the earlier lesson: corp numbers must be
sourced from the CBCA CSV dataset, not manually assembled. 8660115, 821080, and 4396626 were
from the dataset and returned real records.

**Director data is real and structured** — Nigel Stokes and MARIO TESTA are confirmed as actual
directors (not false positives as in the HTML probe). Air Canada returned KATHLEEN TAYLOR with
a full service address. The `_embedded.directors` array is the correct extraction path.

**Status field is informative** — `"Active - Dissolution Pending (Non-compliance)"` for corp
821080 is a meaningful lifecycle signal for the pipeline. Not just a boolean.

**ISC not exposed** — no ISC endpoint exists in the current OpenAPI spec. Do not attempt to
construct one. Director data is the available person-enrichment layer from this API.

### Architecture assessment

| Capability | Assessment |
|---|---|
| Corporation identity lookup (name, act, status, addresses) | ✅ Confirmed — `/v1/corporations/{id}.json` |
| Director name + service address | ✅ Confirmed — `/v2/corporations/{id}/directors` |
| Corporation status (Active/Dissolution/etc.) | ✅ Confirmed — status field in lookup response |
| Business numbers | ✅ Present in response schema |
| Annual returns | ✅ Present in response schema |
| ISC (individuals with significant control) | ❌ Not available via API — no endpoint in spec |
| Rate limit (Public Plan) | 60 req/min — throttle at 1.2s/req |

**VR15.2.2 is CLOSED. API is production-viable.**

---

## Part B — Website/Business Directory Discovery (VR15.3) ❌ NOT SUITABLE

| Source | robots.txt | HTTP | Finding |
|---|---|---|---|
| YellowPages.ca | Disallowed by robots.txt | 403 | Automated access explicitly prohibited + blocked |
| Canada411.ca | Disallowed by robots.txt | 403 | Automated access explicitly prohibited + blocked |
| OpenStreetMap Overpass API | N/A | 504 Gateway Timeout | Overpass server timeout — transient or capacity issue |

### YellowPages.ca and Canada411.ca — NOT SUITABLE

Both sources:
- robots.txt explicitly disallows the pipeline's User-Agent from crawling
- HTTP response is 403 (actively blocked, not just rate-limited)
- Both prohibitions are consistent: not a temporary block

**Decision: YellowPages.ca and Canada411.ca are NOT SUITABLE for automated pipeline use.**
Not a legal ruling — a technical + terms-of-service finding. Both sources disallow automated
access at the robots.txt and HTTP layer.

### OpenStreetMap Overpass API — INCONCLUSIVE (504 timeout)

OSM Overpass returned 504 Gateway Timeout on the test query. This is likely a transient
server-load issue on the public Overpass endpoint, not a prohibition.

OSM business data (nodes with shop/amenity/office tags) is published under ODbL (Open Database
Licence) which permits commercial use with attribution. The Overpass API is the standard
machine-readable query interface.

**Status: DEFERRED — OSM Overpass is worth a follow-up probe with a smaller query or
alternative Overpass instance. Do not close OSM as a candidate based on a single 504.**

### Website discovery conclusion

No tested third-party directory source is suitable for automated bulk enrichment via
standard HTTP from this pipeline environment. The layered hierarchy stands:

| Layer | Mechanism | Status |
|---|---|---|
| 1 | Source website fields (VR06, municipal datasets) | ✅ Validated — use first |
| 2 | Government/corporate records containing domain identifiers | ⚠️ Per-source — investigate per dataset |
| 3a | YellowPages.ca / Canada411.ca | ❌ robots.txt prohibited + 403 |
| 3b | OpenStreetMap Overpass API | ⚠️ Deferred — 504 timeout, ODbL licence is suitable |
| 4 | NOT_FOUND — store metadata | ✅ Valid pipeline outcome |

---

## Part C — Website Enrichment (VR15.4) ⚠️ PARTIALLY VALIDATED

### Test set

| ID | Business | Domain | Access |
|---|---|---|---|
| T04 | RepologiX | repologix.com | ✅ Crawled |
| C01 | Mindangler Capital Inc. | mindangler.com | ✅ Homepage only (404 on all sub-paths) |
| C02 | Sleep Country Canada | sleepcountry.ca | ❌ robots.txt disallowed all paths |
| C03 | Boston Pizza | bostonpizza.com | ✅ Crawled (4 pages) |
| C04 | MEC | mec.ca | ❌ robots.txt disallowed all paths |

### Extraction results

| Business | Phones | Emails | Persons (real) | Notes |
|---|---|---|---|---|
| RepologiX | 5 extracted | 0 | 0 | Phones appear to be tracking/ad pixel numbers — not verified as business phones |
| Mindangler Capital Inc. | 0 | 0 | 0 | Only homepage accessible; no contact data found |
| Sleep Country Canada | 0 | 0 | 0 | robots.txt blocked all paths |
| Boston Pizza | 5 extracted | 0 | 0 (2 false positives) | Phones extracted from homepage. "GoogleTag"/"End Google Tag" matched person regex — false positives |
| MEC | 0 | 0 | 0 | robots.txt blocked all paths |

### Phone extraction — quality issue

**RepologiX phones** (`17537662512`, `19741745350`, `12572432761`, `17195041742`, `16247416551`):
These are likely embedded tracking pixel IDs or analytics parameters that match the phone
regex pattern. They do not resemble Canadian phone numbers (valid CA numbers are 10 digits,
area codes 204–902 range). Verification step needed before treating as business phone.

**Boston Pizza phones** (`+1-604-303-6398`, `+1-604-270-1108`, `+1-905-848-2700`):
These look like real Canadian phone numbers (604=BC, 905=ON). However, these are likely
franchise/location phone numbers embedded in schema markup, not corporate HQ numbers.
Source URL + retrieval timestamp recorded for CASL provenance.

### Person detection — false positives

`"GoogleTag"` and `"End Google Tag"` matched the name+title regex pattern because they
resemble `FirstName LastName` format. Person regex needs a stoplist of known non-person
strings (HTML comment tags, tracking library names, etc.) before production use.

### Email extraction — 0/5 businesses

No email addresses found on any crawled page. Consistent with VR15.1 finding (0/10).
Email is not reliably available on public-facing business websites through this method.

### robots.txt compliance

2/5 businesses (Sleep Country, MEC) disallow automated crawling entirely.
1/5 businesses (Boston Pizza) use Google Tag Manager extensively — signals bot-detection posture.
robots.txt compliance is functioning correctly — disallowed pages were skipped.

### Architecture assessment (Part C)

| Capability | Assessment |
|---|---|
| Phone extraction from known live domain | ⚠️ Regex fires but quality is unreliable (tracking IDs, franchise numbers) |
| Email extraction | ❌ 0/5 businesses — not a viable signal from public web pages |
| Person/decision-maker extraction | ❌ False positives dominate — regex needs stoplist + validation |
| robots.txt compliance | ✅ Working correctly |
| CASL provenance (source_url + retrieved_at) | ✅ Captured on every extracted value |
| Coverage (crawlable businesses) | 3/5 (60%) — robots.txt blocks 2 large businesses |

---

## Combined Architecture Conclusions

### What is confirmed and production-ready

1. **Corporations Canada API** — corporation identity, status, and director name+address via
   authenticated REST API. Corp numbers must come from CBCA CSV. 60 req/min Public Plan.

2. **Website crawl on known domains** — when a domain is known and robots.txt allows,
   pages are reachable and content can be parsed. The extraction layer needs refinement.

3. **robots.txt compliance** — pipeline correctly skips disallowed paths.

### What is not production-ready

1. **Phone extraction regex** — matches tracking IDs and analytics parameters. Needs:
   - Canadian area-code validation filter (valid CA NPA codes)
   - Deduplication against known non-phone patterns
   - Confidence scoring before storing

2. **Person/decision-maker extraction** — regex produces false positives from JS tag names.
   Needs stoplist. Low-confidence signal overall; useful as a hint, not a fact.

3. **Email extraction** — not viable from public web pages. 0% hit rate across both VR15.1
   and VR15.4. Remove from primary enrichment pipeline targets.

4. **Third-party business directory discovery** — YellowPages and Canada411 both prohibited.
   OSM Overpass deferred (504 timeout). No production-ready discovery mechanism beyond
   source-field website URLs.

### Enrichment two-track model (confirmed)

**Track A — Entity/contact enrichment**
```
source_website_field → verify domain → crawl → phone (with validation) → NOT_FOUND if unavailable
```

**Track B — Person/decision-maker enrichment**
```
corp_number (from CBCA CSV) → Corporations Canada API → director name + address
```

These operate independently. Track B does not depend on Track A succeeding.

---

## Compliance Notes

- Corporations Canada API: Public Plan subscription, `user-key` header, 60 req/min, CBCA public data
- robots.txt: checked and respected on all crawled domains
- YellowPages.ca / Canada411.ca: robots.txt disallows + 403 — not accessed for data
- OSM: ODbL licence permits commercial use with attribution — suitable if Overpass access resolved
- CASL provenance fields (`source_url`, `retrieved_at`) captured on all extracted values

---

## Scripts

| Script | Purpose |
|---|---|
| `scripts/probe_vr15_combined.py` | VR15 combined probe — Parts A, B, C |

*Machine-readable: `reports/validation_rounds/VR15_COMBINED.json`*
