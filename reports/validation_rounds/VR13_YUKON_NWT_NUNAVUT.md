# VR13 — Yukon + NWT + Nunavut Comparative Validation

Generated: `2026-09-26`
Script: `scripts/probe_territories_vr13.py`
JSON: `reports/validation_rounds/VR13_YUKON_NWT_NUNAVUT.json`

---

## Overview

One combined round covering six sources across three territories. Each source assessed
independently for technical accessibility and licensing suitability. The three-gate rule
applies throughout: useful data + technically automatable + permitted reuse. All three
must pass for a source to enter the production pipeline.

---

## 1. Yukon

### 1.1 Yukon YCOR — Corporate Online Registry

**Technical result: DEFERRED — host unreachable by script**

All requests to `ycor.gov.yk.ca` returned status 0 with zero bytes — not a 403 or
redirect, but a complete connection failure. This is consistent with one of:
- The domain has been retired or migrated
- The host blocks non-browser TLS fingerprints at the TCP/TLS layer
- A network-level block on the script environment

The robots.txt also returned 0 — confirming the host itself is not responding, not
just individual paths.

| Item | Result |
|---|---|
| Host reachable | ❌ Status 0 — no connection |
| robots.txt | ❌ Not reachable |
| Search page | ❌ Not reachable |
| Login required | ❓ Unknown |
| JSON API | ❓ Unknown |
| Fields observed | ❓ None |
| Terms/licensing | ❓ Not retrieved |

**What is established from RR07:**
YCOR covers corporations, partnerships, business names, societies. Basic status search
is free; detailed profiles are paid. No confirmed bulk download or public API.

**Classification: DEFERRED**
Host unreachable by script. Browser DevTools session or confirmed live URL needed
before any further assessment. Do not assume YCOR is dead — the domain may have
moved (e.g. to a GNWT portal or eservices subdomain).

---

### 1.2 Yukon Government Supplier Directory

**Technical result: DEFERRED — open.yukon.ca returns 403**

Both the portal page and direct CSV download paths at `open.yukon.ca` returned HTTP
403. This is a bot-protection or Cloudflare challenge blocking script access — the
same pattern as NS RJSC and Nunavut gov.nu.ca.

| Item | Result |
|---|---|
| Portal page | ❌ HTTP 403 |
| CSV download | ❌ HTTP 403 |
| File format | ❓ Not retrieved |
| Record count | ❓ Not retrieved |
| Last updated | ❓ Not retrieved |
| Licence | ⚠️ OGL – Yukon confirmed from RR07 research (not retrieved this run) |
| Fields | ❓ Not retrieved this run |

**What is established from RR07:**
Dataset published under Open Government Licence – Yukon. Fields include: business
name, description, community, Yukon-business flag. Metadata indicated last updated
2022 but a 2026 government document claims annual updates. This is the highest-priority
Yukon source for the pipeline — OGL means commercial use is permitted if accessible.

**Classification: DEFERRED**
403 is a retrieval block, not a prohibition. A browser session or curl with browser
headers would likely retrieve the CSV. Manual download attempt recommended — if the
file downloads in a browser, it is accessible and the OGL licence makes it usable.

---

## 2. Northwest Territories

### 2.1 NWT CROS — Corporate Registries Online Search

**Technical result: DEFERRED — URL structure has changed**

All tested paths under `hss.gov.nt.ca/en/services/corporate-registries/` returned
HTTP 404 with the HSS department 404 page. The host itself is alive (robots.txt
returned 200, 2,317 bytes). The corporate registry content has moved — likely to
a different department URL or a dedicated eservices portal.

Notably, the 404 page still embedded Drupal site-search form fields
(`search_keys`, `form_build_id`) — these are the CMS global search, not registry
search fields.

| Item | Result |
|---|---|
| Host reachable | ✅ hss.gov.nt.ca alive |
| Registry page at tested path | ❌ HTTP 404 — content moved |
| robots.txt | ✅ 200, 2,317 bytes |
| Search page | ❌ 404 |
| Fields observed | ❓ None |
| Terms | ❌ 404 |

**What is established from RR08:**
CROS covers NWT corporations, extra-territorial corps, sole props, partnerships,
societies, co-ops. Basic name/status is free; full profiles are paid. No confirmed
bulk download or API.

**Classification: DEFERRED**
Correct URL needed. The registry likely moved to `pws.gov.nt.ca`, `justice.gov.nt.ca`,
or an eservices subdomain. One browser visit to `www.gov.nt.ca` → departments →
Justice → Corporate Registries would find the current path.

---

### 2.2 NWT BIP Registry

**Technical result: DEFERRED — URL resolves but routes to wrong CMS page**

Both the home and search page paths under `iti.gov.nt.ca` returned HTTP 200 with
47KB of HTML — but the content is the ITI "Commercial Fishing / Programs and Services"
CMS page, not the BIP Registry. The CMS is routing the path to incorrect content.
The `name=NWT` GET query returned 200 with identical content — not a real search.

No bulk download found at standard file paths.

| Item | Result |
|---|---|
| Host reachable | ✅ iti.gov.nt.ca alive |
| BIP page at tested path | ⚠️ 200 but wrong content — CMS routing error |
| Search executed | ❌ GET params ignored — same page returned |
| Bulk download | ❌ Not found at tested paths |
| Fields observed | ❓ None |
| Licence | ❓ Not retrieved |

**What is established from RR08:**
BIP Registry exposes: business name, region, community, category. Covers BIP-eligible
businesses (corps + operating names) — broader than corporate registry alone. Not a
complete NWT business population. Identified as a useful discovery/enrichment candidate.

**Classification: DEFERRED**
The BIP Registry exists and was accessible from a browser in RR08 research. The URL
has moved or the CMS path changed. A browser visit to `www.iti.gov.nt.ca` → Business
and Economic Development → BIP would find the current path. A manual download of the
BIP list (if one exists) would be the most efficient next step.

---

## 3. Nunavut

### 3.1 Nunavut Corporate Registry

**Technical result: DEFERRED — Cloudflare challenge blocks script access**

All paths under `www.gov.nu.ca` returned HTTP 403 with the Cloudflare "Just a
moment... Enable JavaScript and cookies to continue" challenge page (5,800–6,100
bytes). This is identical to the NS RJSC pattern — a bot-protection challenge, not
a content prohibition.

| Item | Result |
|---|---|
| gov.nu.ca reachable by script | ❌ HTTP 403 — Cloudflare challenge |
| Business/corporate page | ❌ 403 |
| Corporate registry page | ❌ 403 |
| Fields observed | ❓ None |
| Public search interface | ❓ Unknown |
| Terms | ❓ Not retrieved |

**What is established from RR08:**
Nunavut has a corporate registry (business name registration required within 60 days
for businesses operating under a name other than their own). No equivalent to a public
machine-readable search registry was found in RR08. Available material was primarily
registration forms and administrative procedures.

**Classification: DEFERRED**
Cloudflare challenge — not a content block. Browser DevTools session would reveal
whether a public search interface exists. Based on RR08 findings, a public searchable
registry is unlikely, but this is unconfirmed by direct observation.

---

### 3.2 NNI Business Registry

**Technical result: UPGRADED — public search confirmed, live records with 2026 dates observed**

`nni.gov.nu.ca` returned HTTP 200 with 13,822 bytes of actual content. This is a
live, distinct subdomain separate from `gov.nu.ca`. The page content is substantive:

**Confirmed from page content:**
- Site title: "Nunavummi Nangminiqaqtunik Ikajuuti"
- Available in: English, French, Inuinnaqtun, Inuktitut
- Navigation menu items confirmed: **NNI Business Search**, Register Your Business,
  Tenders and RFPs, About NNI, Contact Info, Document Listing, Privacy Bulletins,
  NNI Regulations
- **"Log in"** appears in the user menu — but this is for business registration, NOT
  for the public business search

**GPT correction (2026-09-26):**
The initial probe misread the "Log in" menu item as a search prerequisite. Browser
inspection of the live site confirms the public NNI Business Search is accessible
without authentication. Three search modes are explicitly available:
1. Search by Community
2. Search by Business Name
3. Search for Suppliers (filterable by contract location, goods/services, category)

Live records observed in the public search include effective dates in September 2026.
The all-Nunavut community search currently returns **187 businesses** with
name / effective-date / community structure directly exposed.

The NNI secretariat note about "not maintaining the Inuit Firm list" refers specifically
to a separate Inuit Firm designation — it does not affect the NNI registered business
directory, which the secretariat does maintain and publicly expose.

| Item | Result |
|---|---|
| nni.gov.nu.ca reachable | ✅ HTTP 200, 13,822 bytes |
| Live portal confirmed | ✅ |
| NNI Business Search menu item | ✅ Confirmed |
| Anonymous public search | ✅ CONFIRMED — no login required |
| Three search modes | ✅ By community / by name / supplier search |
| Live records with Sep 2026 dates | ✅ Confirmed by browser inspection |
| All-Nunavut count | ✅ 187 businesses (community search) |
| Fields observed (public list) | ✅ business name, effective date, community |
| Supplier search filters | ✅ contract location, goods/services, category |
| Full detail fields (address/phone) | ❓ Requires click-through on individual record |
| Pagination / total record count | ❓ Requires profiling |
| Reuse / automation terms | ❓ Not yet retrieved |
| NNI registration fee | ✅ No registration/renewal fee (government confirmed) |

**What is established from RR08:**
NNI application collects: legal business name, operating name(s), resident manager,
main/registered office, community, business type, phone, mailing address, email.
Whether full profile fields appear in public search results requires VR13.1 profiling.

**Classification: PROMISING CANDIDATE — upgraded from PARTIALLY VALIDATED**
Public search confirmed accessible without authentication. Live records including
September 2026 entries confirm freshness. 187-business Nunavut-wide count is
consistent with territory population. The supplier search category classification
may provide industry tagging not available from a corporate registry. VR13.1
scripted profiling is the immediate next step.

---

## 4. Comparative Assessment

| Source | Host reachable | Search accessible | Fields observed | Licensing | Classification |
|---|---|---|---|---|---|
| Yukon YCOR | ❌ Status 0 | ❌ | ❓ | ❓ | DEFERRED — low priority |
| Yukon Supplier Directory | ❌ 403 | ❌ | ❓ | ✅ OGL-Yukon (from RR07) | DEFERRED — browser download needed |
| NWT CROS | ✅ host alive | ❌ 404 — moved | ❓ | ❓ | DEFERRED — current URL: justice.gov.nt.ca/app/cros-rsel/search |
| NWT BIP Registry | ✅ host alive | ⚠️ wrong page | ❓ | ❓ | DEFERRED — low priority |
| Nunavut Corporate | ❌ 403 Cloudflare | ❌ | ❓ | ❓ | DEFERRED — low priority |
| NNI Registry | ✅ 200 | ✅ PUBLIC — no login | ✅ name/date/community | ❓ terms pending | PROMISING CANDIDATE |

**Pattern:** Five of six sources are blocked at the retrieval layer by one of:
connection failure (YCOR), Cloudflare challenge (Yukon open data, Nunavut gov),
or URL migration (NWT CROS, NWT BIP). None of these are content prohibitions.

**The key result** is NNI at `nni.gov.nu.ca` — a live portal on its own subdomain
that bypasses the Cloudflare challenge on `gov.nu.ca`, with public anonymous search
confirmed returning live records with September 2026 effective dates.

**NWT CROS note:** GPT confirmed the current official path is
`https://www.justice.gov.nt.ca/app/cros-rsel/search`. The earlier 404s were URL
migration, not source death. Basic search is free; full profiles require payment.
Role will be targeted verification, not bulk discovery.

**Source architecture insight (from GPT):**
Registry sources give authoritative identity/status but often have access or payment
restrictions. Government operational directories (Saskatoon licences, NNI) can give
fresher, directly usable business records without registry access barriers. This
confirms the pipeline strategy: build candidate universe from permitted
discovery/event sources; use registries selectively for identity verification.

---

## 5. Next Actions by Priority

| Priority | Action | Source |
|---|---|---|
| 1 | **VR13.1 — NNI scripted profiling** (script ready: `scripts/probe_nni_vr13_1.py`) | NNI |
| 2 | Manual browser download of Yukon Supplier Directory CSV from `open.yukon.ca` | Yukon SD |
| 3 | One browser search at `justice.gov.nt.ca/app/cros-rsel/search` — confirm free public fields | NWT CROS |
| 4 | Browser visit to find current NWT BIP URL | NWT BIP |
| 5 | Low priority — YCOR and Nunavut Corporate Registry | YCOR / Nunavut Corp |

**After VR13.1 and Yukon SD browser download → proceed to VR14 (ODBus underlying sources).**
Do not spend further time trying to defeat Cloudflare on any territorial source.

---

## 6. Summary Status

| Territory | Best candidate | Status |
|---|---|---|
| Yukon | Supplier Directory (OGL) | DEFERRED — 403 block; manual browser download needed |
| NWT | CROS (current URL confirmed) | DEFERRED — one browser search to confirm free public fields |
| Nunavut | NNI Registry | PROMISING CANDIDATE — public search confirmed, VR13.1 scripted profiling next |

All three territories have small business populations relative to the major provinces.
The combined impact on Canada-wide pipeline coverage is limited. If the Yukon
Supplier Directory is confirmed accessible and current, it adds meaningful territorial
coverage under an OGL licence. NNI is the main discovery from this round —
public anonymous search with live 2026 records and supplier classification makes it
a viable discovery/event source for Nunavut businesses.

**The three corporate registries (YCOR, NWT CROS, Nunavut Corporate) are Class C
verification sources only — not bulk discovery foundations.**

---

## 7. GPT Interpretation Applied (2026-09-26)

Corrections applied to this report based on GPT's post-VR13 analysis:

1. **NNI upgraded**: "Log in" is for business registration, not search — public anonymous
   search confirmed. 187-business all-Nunavut count confirmed. September 2026 effective
   dates confirmed. Upgraded from PARTIALLY VALIDATED to PROMISING CANDIDATE.
2. **NNI Inuit Firm note clarified**: The secretariat note about not maintaining the Inuit
   Firm list refers to a separate designation, not the main NNI registered business directory.
3. **NWT CROS current URL confirmed**: `https://www.justice.gov.nt.ca/app/cros-rsel/search`
   — prior 404s were URL migration. Basic info free; full profiles paid. Role = targeted
   verification, not bulk discovery.
4. **Yukon SD prioritisation**: 403 is access-layer block, not licensing block (OGL-Yukon
   confirmed). Manual browser download is the next step — freshness (last catalogue update
   2022) is the key concern to resolve.
5. **Priority reordering**: NNI scripted profiling (VR13.1) is now priority 1. After
   VR13.1 + Yukon SD browser download → proceed directly to VR14 (ODBus).
6. **Source architecture pattern confirmed**: Operational government directories
   (Saskatoon, NNI) can be better discovery sources than registries for pipeline purposes.
