# VR12 — Newfoundland & Labrador CADO Technical Validation

Generated: `2026-09-26`
Script: `scripts/probe_cado_vr12.py`
JSON: `reports/validation_rounds/VR12_NL_CADO.json`

---

## 1. Source Metadata

| Attribute | Value |
|---|---|
| Source | Companies and Deeds Online (CADO) |
| Operator | Government of Newfoundland and Labrador |
| Host | `https://cado.eservices.gov.nl.ca` |
| Registry | Registry of Companies and Deeds |
| Coverage | Newfoundland and Labrador — corporations, condominiums, co-operatives, deeds, mechanics liens, lobbyists |
| Registry size (documented) | ~50,000 incorporations, ~26,000 active companies |
| Role (from RR07) | Candidate — NL corporate registry |

---

## 2. Technical Probe Results

### Step 1 — robots.txt

CADO host returns HTTP 404 for `/robots.txt` — no robots exclusion file exists. No bot rules apply.

### Step 2 — CADO home page

| Item | Result |
|---|---|
| URL | `https://cado.eservices.gov.nl.ca/` |
| HTTP status | 200 |
| Response size | 14,992 bytes |
| Login wall | ⚠️ Home page mentions "login" — but this is a navigation link to the licensed-user login, not a block on public search |

Home page text confirms the public services offered:
> *"The ability to search for Companies, Condominiums, Co-operatives, Deeds, Mechanics Liens, and Lobbyists information. The filing of Articles of Incorporation for Local Companies. The filing of annual returns, changes to directors for local companies, changes to mailing addresses and changes to registered office addresses."*

### Step 3 — Search page (GET)

| Item | Result |
|---|---|
| URL | `/Company/CompanyNameNumberSearch.aspx` |
| HTTP status | 200 |
| Response size | 13,186 bytes |
| Login required | ❌ No — page loads without auth |
| Payment required | ❌ No — no payment signals on search page |
| Application type | ASP.NET WebForms — server-rendered HTML |

**ASP.NET hidden fields confirmed:**
- `__VIEWSTATE`
- `__VIEWSTATEGENERATOR`
- `__EVENTVALIDATION`

**Search input fields confirmed:**
- `txtNameKeywords1` — first name keyword
- `txtNameKeywords2` — second name keyword (AND logic)
- `txtCompanyNumber` — company number search
- `btnSearch` — submit button

### Step 4 — Search POST (partial — script gap)

The POST sent an empty payload because the script's field-name matching fallback did not resolve to `txtNameKeywords1`. The server returned the identical blank search form (13,186 bytes). **This is a script gap, not a CADO access block.**

What is confirmed from this step:
- The server accepted the POST without requiring auth or redirecting
- The form structure is fully known: `txtNameKeywords1` is the correct field name
- A corrected POST with `txtNameKeywords1=Muskrat+Falls` and the ViewState tokens would execute the search

The search itself was not executed. Search result fields and detail page fields are **not yet observed**.

### Step 5 — Detail page

Skipped — no detail links found because the search did not execute.

### Step 6 — Disclaimer / Terms (fully captured)

The disclaimer page returned HTTP 200 with 17,746 bytes. Full text was captured.

**Key copyright clause — exact text:**

> *"the CADO user shall not copy, distribute, loan, lease, sell or use data as part of a value added product or otherwise make the data available to any other party without the prior written approval of Government of Newfoundland and Labrador"*

**Licensing flags from full text:**

| Flag | Present |
|---|---|
| Government copyright owner | ✅ Yes |
| Value-added product use prohibited | ✅ Yes — explicit |
| Distribution to third parties prohibited | ✅ Yes — explicit |
| Copying prohibited | ✅ Yes |
| Selling prohibited | ✅ Yes — "sell" named explicitly |
| Prior written government approval required | ✅ Yes |
| Non-commercial restriction only | ❌ No — restriction covers all use as value-added product |
| Open Government Licence | ❌ No |
| Automated use mentioned | ❌ Not explicitly, but value-added/distribution clauses cover it |

---

## 3. Capability Assessment

| Capability | Status |
|---|---|
| Search page accessible anonymously | ✅ Confirmed |
| ASP.NET form structure known | ✅ Confirmed — all field names captured |
| JSON API | ❌ Not found — server-rendered HTML only |
| Search results observed | ❓ Not captured — script POST gap (fixable) |
| Detail page fields observed | ❓ Not captured — dependent on search working |
| Login required for search | ❌ No |
| Payment required for search | ❓ Unknown — not encountered, but general-user vs licensed-user distinction exists |
| robots.txt | ❌ Not present |
| Value-added use permitted | ❌ Explicitly prohibited |
| Distribution to third parties permitted | ❌ Explicitly prohibited |
| Prior written government approval required | ✅ Required for any restricted use |
| Open licence | ❌ No |

---

## 4. Licensing Analysis

The CADO disclaimer is unambiguous. The government grants public use of the website with an explicit carve-out:

**Prohibited without prior written approval:**
- Copying CADO data
- Distributing CADO data
- Loaning or leasing CADO data
- Selling CADO data
- Using CADO data as part of a **value-added product**
- Making CADO data available to **any other party**

This pipeline is a commercial B2B prospecting/sales product. That use is a value-added product that would be made available to another party (telecom sales team). Both conditions are directly named in the restriction.

**The licensing gate is closed** regardless of the technical findings.

This is different from sources like BC OrgBook (terms-unclear) or PEI OCBR (EULA unread) — the NL CADO terms are explicit, retrieved, and unambiguous.

---

## 5. What Remains Unobserved

These are technical gaps from the script POST failure — not licensing unknowns:

1. **Search result fields** — what columns appear in a result list
2. **Detail page fields** — company name, registration number, status, incorporation date, registered office, mailing address, directors, history
3. **Payment boundary for detail** — whether detailed company info is free or paid
4. **Licensed-user vs general-user distinction** — scope of the pricing difference

These could be observed with a fixed script or a manual browser session, but are secondary given the licensing outcome.

---

## 6. Summary Metrics

| Metric | Result |
|---|---|
| Host reachable | ✅ HTTP 200 |
| Search page accessible anonymously | ✅ Confirmed |
| Application type | ASP.NET WebForms — HTML form postback |
| JSON API | ❌ Not found |
| Search executed by script | ❌ Script POST gap — field `txtNameKeywords1` not populated |
| Search result fields observed | ❓ Not captured |
| Detail fields observed | ❓ Not captured |
| robots.txt | ❌ Not present |
| Copyright | ✅ Government of NL owns all CADO data |
| Value-added use prohibited | ✅ Explicit — named in disclaimer |
| Prior written approval required | ✅ Explicit |
| Open Government Licence | ❌ No |
| Commercial automation permitted | ❌ Prohibited by published terms |
| Final status | ❌ NOT SUITABLE — disclaimer explicitly prohibits value-added / distribution use; prior written NL Government approval required; pipeline use is directly covered by the restriction |
