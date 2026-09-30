# VR10 — Nova Scotia RJSC Technical Validation

Generated: `2026-09-26`

---

## 1. Source Metadata

- Source: Nova Scotia Registry of Joint Stock Companies (RJSC)
- URL: `https://rjsc.novascotia.ca`
- Authentication: Unknown — all requests blocked before auth layer reached
- Terms: Unverified — terms page also returned 403
- Role (from RR05): Candidate — broad provincial registry (sole props, partnerships, companies, societies, co-ops, business names)

---

## 2. Technical Probe Results

Script: `scripts/probe_ns_rjsc.py`
Run date: 2026-09-26

| Probe | Path | HTTP Status | Result |
|---|---|---|---|
| Homepage | `/` | 403 | Blocked |
| API candidate | `/api/search` | 403 | Blocked |
| API candidate | `/api/v1/search` | 403 | Blocked |
| API candidate | `/RegistrySearch/api/search` | 403 | Blocked |
| API candidate | `/api/business/search` | 403 | Blocked |
| API candidate | `/search/api` | 403 | Blocked |
| Search page | `/RegistrySearch` | 403 | Blocked |
| Search page | `/search` | 403 | Blocked |
| Search page | `/en/Home/Index` | 403 | Blocked |
| POST search | `/RegistrySearch/Search` | 403 | Blocked |
| POST search | `/en/Home/Search` | 403 | Blocked |
| robots.txt | `/robots.txt` | 403 | Blocked |
| Terms page | `/en/About/TermsOfUse` | 403 | Blocked |

**All 13 paths returned HTTP 403.** Response body is a consistent ~5,500-char HTML error page containing the keyword `robot`.

---

## 3. Interpretation

This is **not** a path-specific access restriction. Every endpoint — including the homepage, robots.txt, and static pages — returned the same 403 response. This is a **WAF / bot-protection layer** (likely Cloudflare or equivalent NS government gateway) that rejects requests based on IP reputation, user-agent fingerprint, or absence of browser-specific headers (TLS fingerprint, JS challenge, cookies).

Key indicators:
- Uniform 403 across all paths including `/` and `/robots.txt`
- Consistent body length (~5,500 chars) regardless of path — same error template served everywhere
- Keyword `robot` in the 403 page body — confirms bot-detection messaging
- No rate-limit headers returned — the block occurs before the application layer
- No JSON response at any path — the WAF does not pass requests to the backend

**This means:**
- The RJSC backend may or may not have a JSON/XHR API — we cannot determine this from HTTP probing alone
- Standard Python `urllib` / `requests` tooling is insufficient to access this portal
- A real browser session (with full TLS fingerprint, cookies, and potentially JS challenge completion) is required to reach the application

---

## 4. What This Does NOT Mean

- It does not confirm that the RJSC has no public JSON endpoint — the WAF is blocking before we reach any application layer
- It does not confirm automation is prohibited — we could not read the terms of use (also 403'd)
- It does not confirm that a real browser session would be blocked — browser-based manual inspection is still feasible and is the correct next step

---

## 5. Capability Assessment (Current State)

Official Nova Scotia government documentation confirms the following fields are publicly available via the RJSC:

| Capability | Evidence |
|---|---|
| Public business registry exists | ✅ Government confirmed |
| Entity types covered | ✅ Sole prop, partnership, company, society, co-op, business name |
| Legal name + operating name | ✅ Government confirmed — public information |
| Address | ✅ Government confirmed — public information |
| Registration date | ✅ Government confirmed — public information |
| Status | ✅ Government confirmed |
| Directors / officers / partners | ✅ Government confirmed — legally filed roles, publicly available |
| Activity history | ✅ Government confirmed — filings, amendments, events |
| Free basic search | ✅ Government confirmed |
| Machine-readable API | ❓ Not validated — WAF blocked before application layer |
| Automated access permission | ⚠️ Unknown — WAF blocked before terms could be read |
| Bulk download | ❌ Not established |
| HTTP access via script | ❌ Blocked by WAF |
| Terms of use | ❌ Terms page also 403'd — cannot confirm or deny automation permission |
| Role in architecture | Potential targeted identity + decision-maker / event source |

**Important:** The WAF block does NOT indicate that RJSC prohibits automation. The application layer and its terms were never reached. Automation permission remains unknown.

---

## 6. Architecture Impact

The WAF block does not change RJSC's source value — it changes the access method that needs to be validated.

RJSC is confirmed by official government documentation to publicly expose:
- Legal name + operating/DBA name
- Registry ID (7-digit)
- Entity type (sole prop, partnership, company, society, co-op)
- Status (active/inactive)
- Registered office + mailing address
- Registration date
- Directors / officers / partners (legally filed, publicly documented)
- Activity history / filed events
- Previous names

**Decision-maker relevance:** Nova Scotia explicitly requires incorporated companies to file and update director/officer information, and those filings are public record. If a machine-readable retrieval method can be established, RJSC has unusually strong relevance to the assignment's decision-maker requirement — providing legally filed leadership roles (Director, President, VP, CFO, Secretary, Treasurer) attached to NS businesses.

If a JSON endpoint exists behind the WAF, RJSC would be one of the richest provincial sources found so far — comparable to Corporations Canada but NS-specific and covering sole proprietors, with the addition of address and people roles not available in the federal bulk CSV.

---

## 7. Open Questions

- [ ] Does a browser-based manual search succeed? (Expected: yes — WAF targets bots, not human sessions)
- [ ] Is there a documented public API or bulk dataset for RJSC? (NS Open Data portal did not show one in RR05)
- [ ] What XHR/fetch calls does the browser make during a normal RJSC search? (Requires browser DevTools inspection)
- [ ] Do the terms of use permit automated targeted lookups?
- [ ] Is a Cloudflare bypass feasible via session cookies + browser headers? (Legal/compliance question as much as technical)

---

## 8. Recommended Next Step

**Manual browser inspection by GPT or the user:**

1. Open `https://rjsc.novascotia.ca` in a real browser
2. Open DevTools → Network tab → filter XHR/Fetch
3. Search for one known NS business (e.g. "Sobeys Capital")
4. Capture: the request URL, method, headers, query params, and response JSON structure
5. Note any CSRF tokens, session cookies, or auth headers in the request
6. Record what fields appear in the response

This will determine whether a real JSON API exists and what it returns — something the script cannot establish through a WAF block.

If a JSON endpoint is confirmed via browser inspection, a follow-up script (VR10.1) can attempt to replicate the browser session headers to access it programmatically.

---

## 9. Summary Metrics

| Metric | Result |
|---|---|
| Script run | ✅ Completed without errors |
| HTTP access | ❌ All paths 403 — WAF block confirmed |
| JSON API found | ❌ Not determinable — blocked before application layer |
| Fields captured via script | 0 |
| Fields confirmed via official docs | Legal name, operating name, address, registration date, status, entity type, directors/officers/partners, activity history |
| Auth layer reached | ❌ Blocked before auth |
| Terms confirmed | ❌ Terms page also blocked — automation permission unknown |
| Rate-limit headers | None |
| Bot-protection signal | ✅ `robot` keyword in 403 body |
| Decision-maker relevance | ✅ High — legally filed director/officer data confirmed public |
| Final status | ⚠️ DEFERRED — WAF block; browser DevTools inspection required before any further automated testing |
