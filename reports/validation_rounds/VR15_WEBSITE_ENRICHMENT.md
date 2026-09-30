# VR15.1 — Company Website Discovery & Enrichment

**Generated:** 2026-09-26T08:12:46Z
**Last updated:** 2026-09-26 (GPT corrections applied — search-engine HTML scraping closed)
**Scripts:** `scripts/probe_company_websites_vr15_1.py`, `scripts/probe_website_discovery_vr15_1_1.py`
**Status:** ⚠️ PARTIAL — crawl validated on known domains; search-engine discovery NOT SUITABLE

---

## 1. Probe Scope

| Item | Value |
|---|---|
| Test set | 10 businesses |
| Sources | VR06 Ontario Select Licence (4), VR01 Corporations Canada (2), manual well-known (3), VR06 no-website (1) |
| Discovery mechanism tested | Known website field (direct), DuckDuckGo Lite HTML search (no-website records) |
| Crawl paths attempted | `/`, `/contact`, `/contact-us`, `/about`, `/about-us`, `/team`, `/leadership`, `/management`, `/locations` |

---

## 2. Metrics

| Metric | Count | Rate |
|---|---|---|
| Total businesses probed | 10 | — |
| Domain found (any route) | 4 | 40% |
| Domain reachable (HTTP 200) | 1 | 10% |
| Phone extracted | 1 | 10% |
| Email extracted | 0 | 0% |
| Leadership signal found | 0 | 0% |
| Leadership page detected | 1 | 10% |

---

## 3. Per-Business Results

| ID | Name | City/Prov | Domain Found | Reachable | Phones | Emails | Error |
|---|---|---|---|---|---|---|---|
| T01 | Sterling Bailiffs Inc. | Toronto ON | ✅ (known) | ❌ | 0 | 0 | DNS resolution failed (getaddrinfo) |
| T02 | Lumbermen's Credit Group Ltd. | Toronto ON | ✅ (known) | ❌ | 0 | 0 | DNS resolution failed (getaddrinfo) |
| T03 | GoDay | Toronto ON | ✅ (known) | ❌ | 0 | 0 | HTTP 403 (WAF/bot protection) |
| T04 | RepologiX | Toronto ON | ✅ (known) | ✅ | 2 | 0 | — |
| T05 | MEC Mountain Equipment Co. | Vancouver BC | ❌ | ❌ | 0 | 0 | DDG returned no usable result |
| T06 | Sleep Country Canada | Toronto ON | ❌ | ❌ | 0 | 0 | DDG returned no usable result |
| T07 | Boston Pizza International | Richmond BC | ❌ | ❌ | 0 | 0 | DDG returned no usable result |
| T08 | Mindangler Capital Inc. | Ottawa ON | ❌ | ❌ | 0 | 0 | DDG returned no usable result |
| T09 | Airmec Climatisation Ltee | Anjou QC | ❌ | ❌ | 0 | 0 | DDG returned no usable result |
| T10 | Big Dog Solutions Limited | Sudbury ON | ❌ | ❌ | 0 | 0 | DDG returned no usable result |

### T04 Detail — RepologiX (only successful crawl)
- Domain: `https://www.repologix.com`
- Pages crawled: `/` (200), `/contact` (200), `/about` (200)
- Phones extracted: `416.248.1229`, `416.248.9484`
- Emails extracted: none
- Leadership page: detected (`/about` path matched)
- Leadership named signals: 0 (no named person+title pattern found)

---

## 4. Failure Analysis

### Failure Mode A — DNS resolution failure (T01, T02)
`getaddrinfo failed` on `sterlingbailiffs.com` and `lcg.ca`.
Website URLs are present in the VR06 source data (government-published), but domains did not resolve at probe time.
Possible causes: domain expired, domain changed, DNS unavailable from probe environment.
This is not a structural failure of the method — it reflects that government-published website fields can be stale.

### Failure Mode B — HTTP 403 / WAF block (T03)
`goday.ca` returned HTTP 403.
Large consumer-facing financial businesses frequently deploy WAF/bot protection.
Same pattern as NS RJSC (VR10). Method is valid; this specific site blocks automated access.

### Failure Mode C — DuckDuckGo Lite returned no usable results (T05–T10)
All 6 businesses without a known website field returned `no_candidate_domain_found`.
The DuckDuckGo Lite HTML interface (`lite.duckduckgo.com/lite/`) returned pages but the
link extractor found no non-directory, non-social URLs in the result set for these queries.
Two possible causes:
  1. DDG Lite may return results in a JS-rendered format that the plain HTML parser does not capture
  2. The result links may be excluded by the exclusion filter (LinkedIn, YellowPages, etc.)

This is a **critical constraint**: the website discovery step (no-website-field case) did not produce
any usable candidates in this probe. The crawl method itself is sound — the discovery step needs
a different mechanism.

---

## 5. What Was Demonstrated

- When a valid website URL is known and the domain is live and accessible, the crawler successfully:
  - Reached the domain (T04: HTTP 200 on `/`, `/contact`, `/about`)
  - Extracted phone numbers via text regex (2 phones from `/contact`)
  - Detected a leadership-candidate page (`/about`)
- The extraction logic (regex, tel: link parsing) functioned correctly on real HTML content
- robots.txt compliance check ran without errors
- Throttling at 2s/request functioned as intended

---

## 6. Search-Engine HTML Scraping — CLOSED (VR15.1.1)

A follow-up probe (`probe_website_discovery_vr15_1_1.py`) tested DDG Lite and Bing HTML as
website discovery mechanisms for records with no source-field website URL.

| Mechanism | Result |
|---|---|
| DuckDuckGo Lite (`lite.duckduckgo.com/lite/`) | 202 bot-detection on all 25 queries |
| Bing HTML (`www.bing.com/search`) | 200 returned but zero extractable links (JS-rendered) |
| Known website field (control group) | 3/5 worked — only mechanism that produced results |

**DECISION: Search-engine HTML scraping is NOT SUITABLE for the Python production pipeline.**

Not a prohibition — a technical stability issue. Neither tested mechanism delivered usable results
at the probe level. Building the production enrichment layer on this would create a fragile,
uncontrollable dependency.

**Also decided: browser automation against Google/Bing is NOT the solution.**
That would create a ToS-sensitive browser-scraping dependency for what should be a simple enrichment step.

---

## 7. Website Discovery Strategy — Layered Hierarchy (GPT-recommended)

The production pipeline should use a priority hierarchy, not a single universal mechanism:

| Layer | Source | Status |
|---|---|---|
| 1 | Existing source website fields (VR06 Ontario, municipal datasets) | ✅ Validated — highest confidence |
| 2 | Public government/corporate records containing domain identifiers | ⚠️ To investigate per source |
| 3 | Permitted Canadian business directories (YellowPages.ca, Canada411, OSM-derived, open-data) | ⚠️ VR15.3 to investigate |
| 4 | No website found — store `website_status=NOT_FOUND` | ✅ Design decision confirmed |

**Layer 4 is a valid outcome.** The pipeline does not require 100% website coverage.
A record with `website=null, website_status=NOT_FOUND, website_checked_at=...` is valid
as long as other fields (address, phone, source, employee_size) are populated.

### What Layer 3 must validate (VR15.3)
For each candidate directory/open-data source, the validation question is:
- Can we legally + technically obtain: business name, address, phone, website
- At useful scale
- Without login/CAPTCHA bypass
- Without paid API dependency
- With acceptable reuse terms

Candidates to investigate: YellowPages.ca, Canada411, OpenStreetMap-derived business data,
other Canadian open-data directories identified during research.

---

## 8. Architecture Role Assessment (revised)

| Role | Assessment |
|---|---|
| Contact enrichment — phone | ✅ Demonstrated on 1 live site. Method valid. Discovery is the bottleneck. |
| Contact enrichment — email | ⚠️ Not demonstrated at scale. Method exists; needs more test coverage. |
| Decision-maker enrichment via website | ⚠️ Not demonstrated. No name/title signal in 1 probe. |
| Website discovery (field present) | ⚠️ Feasible when field is valid and live. 2/4 VR06 fields were stale/blocked. |
| Website discovery (no field) — search engine HTML | ❌ NOT SUITABLE. DDG=202 blocked, Bing=JS-rendered. Closed. |
| Website discovery (no field) — permitted directories | ⚠️ VR15.3 to investigate. Not yet validated. |
| Website discovery (no field) — no result | ✅ Valid outcome. Store NOT_FOUND + metadata. |

---

## 9. Compliance Notes

- `robots.txt` checked before each crawl path (urllib.robotparser)
- User-Agent identifies as research pipeline (not disguised)
- 2-second throttle applied between all requests
- No authentication bypass, no CAPTCHA interaction
- CASL provenance fields (`source_url`, `retrieved_at`) stored in JSON output

---

## 10. Scripts

| Script | Purpose |
|---|---|
| `scripts/probe_company_websites_vr15_1.py` | VR15.1 website crawl probe (10 businesses) |
| `scripts/probe_website_discovery_vr15_1_1.py` | VR15.1.1 discovery multi-mechanism (DDG+Bing both blocked) |

*Machine-readable: `reports/validation_rounds/VR15_WEBSITE_ENRICHMENT.json`*
