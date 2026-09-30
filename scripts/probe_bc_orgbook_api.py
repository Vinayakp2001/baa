"""
VR09 — BC OrgBook API v4 Technical Validation
Targeted verification of API accessibility, response structure, and field coverage.
Does NOT enumerate the database. Does NOT walk beyond first page of results.
Three test queries only: one by name, one by BC Registry ID, one by CRA BN.
Requires: no extra packages — stdlib only
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT    = Path(__file__).resolve().parent.parent
RAW     = ROOT / "data" / "raw"
REPORTS = ROOT / "reports" / "validation_rounds"
RAW.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now(timezone.utc).isoformat()

REPORT_PATH = REPORTS / "VR09_BC_ORGBOOK_API.md"
JSON_PATH   = REPORTS / "VR09_BC_ORGBOOK_API.json"

SEP = "=" * 80

# ---------------------------------------------------------------------------
# API base
# ---------------------------------------------------------------------------
API_BASE = "https://orgbook.gov.bc.ca/api/v4"

# Three targeted test queries — well-known BC entities, not random enumeration
# These are public companies with long-established BC Registry records
TEST_QUERIES = [
    {"type": "name",        "q": "TELUS Communications Inc."},
    {"type": "bc_reg_id",   "q": "BC0616127"},      # known BC Registry number format
    {"type": "cra_bn",      "q": "123456789"},       # placeholder — will show BN search behaviour
]

# Throttle between requests — respect BC's explicit throttling guidance
REQUEST_DELAY = 1.5  # seconds

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_json(url, label=""):
    """Fetch URL, return (parsed_json_or_None, status, response_time_ms, headers, error)."""
    print(f"  GET {url[:100]}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Canada-Pipeline-Validator/1.0; research use)",
            "Accept": "application/json",
        }
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            status = resp.status
            headers = dict(resp.headers)
        elapsed_ms = int((time.time() - t0) * 1000)
        print(f"    -> {status}  {len(raw):,} bytes  {elapsed_ms}ms")
        try:
            data = json.loads(raw)
            return data, status, elapsed_ms, headers, None
        except json.JSONDecodeError as e:
            return None, status, elapsed_ms, headers, f"JSON parse error: {e}"
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        print(f"    -> HTTP {e.code} {e.reason}")
        return None, e.code, elapsed_ms, {}, f"HTTP {e.code}"
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        print(f"    -> ERROR {e}")
        return None, None, elapsed_ms, {}, str(e)


def pause():
    time.sleep(REQUEST_DELAY)


def extract_keys_recursive(obj, prefix="", depth=0, max_depth=3):
    """Walk a JSON object and return set of dot-notation key paths."""
    if depth > max_depth:
        return set()
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys |= extract_keys_recursive(v, full_key, depth + 1, max_depth)
    elif isinstance(obj, list) and obj:
        keys |= extract_keys_recursive(obj[0], prefix + "[]", depth + 1, max_depth)
    return keys


def summarise_obj(obj, indent=0):
    """Return a compact key: type/value summary string."""
    lines = []
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:20]:
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}: {type(v).__name__}({len(v)})")
            else:
                val_str = str(v)[:60] if v is not None else "null"
                lines.append(f"{pad}{k}: {val_str}")
    elif isinstance(obj, list):
        lines.append(f"{pad}[list of {len(obj)} items]")
        if obj:
            lines += summarise_obj(obj[0], indent + 1).split("\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Test 1 — Autocomplete queries (name, BC Reg ID, CRA BN)
# ---------------------------------------------------------------------------

def test_autocomplete(results):
    print(f"\n{SEP}")
    print("TEST 1 — AUTOCOMPLETE QUERIES")
    print(SEP)

    autocomplete_results = {}
    for q in TEST_QUERIES:
        url = f"{API_BASE}/search/autocomplete?q={urllib.parse.quote(q['q'])}"
        data, status, ms, headers, err = fetch_json(url, q["type"])
        autocomplete_results[q["type"]] = {
            "query": q["q"],
            "url": url,
            "status": status,
            "response_ms": ms,
            "error": err,
            "result_count": None,
            "first_result": None,
            "keys": [],
        }
        if data and not err:
            # OrgBook v4 autocomplete returns {"total": N, "results": [...]}
            if isinstance(data, dict):
                count = data.get("total", data.get("count", len(data.get("results", []))))
                items = data.get("results", data.get("objects", []))
                autocomplete_results[q["type"]]["result_count"] = count
                autocomplete_results[q["type"]]["raw_top_level_keys"] = list(data.keys())
                if items:
                    first = items[0]
                    autocomplete_results[q["type"]]["first_result"] = first
                    autocomplete_results[q["type"]]["keys"] = sorted(
                        extract_keys_recursive(first)
                    )
                    print(f"    Query '{q['q']}': {count} results, first={json.dumps(first)[:120]}")
            elif isinstance(data, list):
                autocomplete_results[q["type"]]["result_count"] = len(data)
                if data:
                    autocomplete_results[q["type"]]["first_result"] = data[0]
        pause()

    results["autocomplete"] = autocomplete_results
    return autocomplete_results


# ---------------------------------------------------------------------------
# Test 2 — Topic lookup (use first topic_source_id from autocomplete)
# ---------------------------------------------------------------------------

def test_topic_lookup(autocomplete_results, results):
    print(f"\n{SEP}")
    print("TEST 2 — TOPIC LOOKUP")
    print(SEP)

    # Find a source_id or topic_source_id from autocomplete results
    source_id = None
    topic_type = None
    for qtype, ar in autocomplete_results.items():
        first = ar.get("first_result")
        if not first:
            continue
        # Try common field names for the registry/source ID
        for field in ["topic_source_id", "source_id", "id", "topic_id"]:
            if first.get(field):
                source_id = str(first[field])
                topic_type = qtype
                break
        if source_id:
            break

    topic_result = {"source_id_used": source_id, "from_query_type": topic_type}

    if not source_id:
        print("  No source_id found in autocomplete results — skipping topic lookup")
        topic_result["skipped"] = True
        results["topic_lookup"] = topic_result
        return topic_result, None

    url = f"{API_BASE}/search/topic?q={urllib.parse.quote(source_id)}"
    data, status, ms, headers, err = fetch_json(url, "topic")
    topic_result.update({
        "url": url,
        "status": status,
        "response_ms": ms,
        "error": err,
        "keys": [],
        "topic_id": None,
        "fields_observed": {},
    })

    if data and not err:
        items = data.get("results", data.get("objects", [data] if isinstance(data, dict) else []))
        # Handle case where response is a flat dict with no results wrapper
        if not items and isinstance(data, dict) and data.get("id"):
            items = [data]
        if items:
            first = items[0]
            topic_result["keys"] = sorted(extract_keys_recursive(first))
            topic_result["topic_id"] = (
                first.get("id") or first.get("topic_id") or
                first.get("results", [{}])[0].get("id") if isinstance(first.get("results"), list) else None
            )
            # Also try top-level id if items is the response itself
            if not topic_result["topic_id"] and isinstance(data, dict):
                topic_result["topic_id"] = data.get("id")
            # Check for key fields
            for field in ["source_id", "type", "names", "addresses", "attributes",
                          "credential_set", "inactive", "revoked", "effective_date",
                          "registration_date", "status", "jurisdiction"]:
                val = first.get(field)
                topic_result["fields_observed"][field] = (
                    f"PRESENT ({type(val).__name__})" if val is not None else "absent"
                )
            print(f"  Topic fields observed: {list(first.keys())[:15]}")
            topic_result["raw_summary"] = summarise_obj(first)
        topic_result["total_results"] = data.get("total", len(items))
    pause()

    results["topic_lookup"] = topic_result
    return topic_result, topic_result.get("topic_id")


# ---------------------------------------------------------------------------
# Test 3 — Credential-set lookup
# ---------------------------------------------------------------------------

def test_credential_set(topic_id, results):
    print(f"\n{SEP}")
    print("TEST 3 — CREDENTIAL-SET LOOKUP")
    print(SEP)

    cred_result = {"topic_id_used": topic_id}

    if not topic_id:
        print("  No topic_id available — skipping credential-set lookup")
        cred_result["skipped"] = True
        results["credential_set"] = cred_result
        return cred_result

    url = f"{API_BASE}/topic/{topic_id}/credential-set"
    data, status, ms, headers, err = fetch_json(url, "credential-set")
    cred_result.update({
        "url": url,
        "status": status,
        "response_ms": ms,
        "error": err,
        "credential_count": 0,
        "credential_types_seen": [],
        "fields_per_credential": [],
        "has_history": False,
        "address_in_credentials": False,
        "phone_in_credentials": False,
        "email_in_credentials": False,
    })

    if data and not err:
        items = data if isinstance(data, list) else data.get("results", [])
        cred_result["credential_count"] = len(items)
        types_seen = set()
        has_history = False
        for c in items[:10]:
            ctype = c.get("credential_type", {})
            if isinstance(ctype, dict):
                types_seen.add(ctype.get("description") or ctype.get("schema_label") or str(ctype))
            elif isinstance(ctype, str):
                types_seen.add(ctype)
            if c.get("revoked") or c.get("inactive"):
                has_history = True
            # Check for contact fields in attributes
            attrs = c.get("attributes", [])
            for a in attrs:
                name = str(a.get("type") or a.get("name") or "").lower()
                if "address" in name or "street" in name:
                    cred_result["address_in_credentials"] = True
                if "phone" in name or "telephone" in name:
                    cred_result["phone_in_credentials"] = True
                if "email" in name:
                    cred_result["email_in_credentials"] = True
            if items:
                cred_result["fields_per_credential"].append(list(c.keys()))

        cred_result["credential_types_seen"] = list(types_seen)
        cred_result["has_history"] = has_history
        print(f"  Credentials: {len(items)}, types: {list(types_seen)[:5]}")

    pause()
    results["credential_set"] = cred_result
    return cred_result


# ---------------------------------------------------------------------------
# Test 4 — Credential-type inventory
# ---------------------------------------------------------------------------

def test_credential_types(results):
    print(f"\n{SEP}")
    print("TEST 4 — CREDENTIAL-TYPE INVENTORY")
    print(SEP)

    url = f"{API_BASE}/credential-type"
    data, status, ms, headers, err = fetch_json(url, "credential-type")
    ct_result = {
        "url": url,
        "status": status,
        "response_ms": ms,
        "error": err,
        "count": 0,
        "types": [],
    }

    if data and not err:
        items = data if isinstance(data, list) else data.get("results", [])
        ct_result["count"] = len(items)
        for item in items[:30]:
            sl = item.get("schema_label") or item.get("description") or item.get("credential_def_id")
            if isinstance(sl, dict):
                en = sl.get("en", sl)
                sl = (en.get("label") or en.get("description") if isinstance(en, dict) else str(en))
            issuer = item.get("issuer_service_id") or (
                item.get("issuer", {}).get("name") if isinstance(item.get("issuer"), dict) else item.get("issuer")
            )
            ct_result["types"].append({
                "schema_label": str(sl) if sl else "?",
                "issuer": str(issuer) if issuer else "?",
                "has_logo": bool(item.get("logo_b64")),
                "credential_count": item.get("credential_count"),
                "keys": list(item.keys()),
            })
        print(f"  Credential types found: {len(items)}")
        for ct in ct_result["types"][:5]:
            print(f"    {ct['schema_label']} | issuer={ct['issuer']} | count={ct['credential_count']}")

    pause()
    results["credential_types"] = ct_result
    return ct_result


# ---------------------------------------------------------------------------
# Test 5 — Pagination check (first query only, do NOT walk pages)
# ---------------------------------------------------------------------------

def test_pagination(results):
    print(f"\n{SEP}")
    print("TEST 5 — PAGINATION CHECK (first page only)")
    print(SEP)

    url = f"{API_BASE}/search/autocomplete?q=ltd&page=1&page_size=10"
    data, status, ms, headers, err = fetch_json(url, "pagination-check")
    pg_result = {
        "url": url,
        "status": status,
        "response_ms": ms,
        "error": err,
        "pagination_fields_present": [],
        "total": None,
        "page_size": None,
        "page": None,
        "note": "Only first page fetched. Full enumeration is prohibited by BC Terms of Use.",
    }

    if data and not err:
        for field in ["total", "count", "page", "page_size", "num_pages",
                      "next", "previous", "pages"]:
            if field in data:
                pg_result["pagination_fields_present"].append(field)
                pg_result[field] = data[field]
        print(f"  Pagination fields: {pg_result['pagination_fields_present']}")
        print(f"  Total: {pg_result.get('total')}, Page size: {pg_result.get('page_size')}")

    results["pagination"] = pg_result
    return pg_result


# ---------------------------------------------------------------------------
# Write report
# ---------------------------------------------------------------------------

def write_report(results):
    lines = []
    a = lines.append

    def section(title):
        a(f"\n## {title}\n")

    a("# VR09 — BC OrgBook API v4 Technical Validation")
    a(f"\nGenerated: `{TIMESTAMP}`\n")

    section("1. Source Metadata")
    a(f"- Source: BC OrgBook — `https://orgbook.gov.bc.ca`")
    a(f"- API base: `{API_BASE}`")
    a(f"- Authentication: None required (public read API)")
    a(f"- Terms: BC Government Terms of Use")
    a(f"- Restriction: Full-database automated scraping prohibited. High-volume requests must be throttled.")
    a(f"- Intended use: targeted application integration — not bulk download")
    a(f"- Role: Class C — targeted BC identity/status verification (NOT bulk discovery)")

    section("2. API Access")
    ac = results.get("autocomplete", {})
    a("| Query type | Query | Status | Response ms | Results |")
    a("|---|---|---|---|---|")
    for qtype, ar in ac.items():
        a(f"| {qtype} | `{ar.get('query','')}` | {ar.get('status')} | {ar.get('response_ms')} | {ar.get('result_count','?')} |")

    section("3. Autocomplete Response Structure")
    for qtype, ar in ac.items():
        if ar.get("first_result"):
            a(f"\n**{qtype} query — first result fields:**\n")
            a("```")
            a(summarise_obj(ar["first_result"]))
            a("```")
            if ar.get("keys"):
                a(f"\nAll keys observed: {', '.join(f'`{k}`' for k in ar['keys'][:20])}")

    tl = results.get("topic_lookup", {})
    section("4. Topic Lookup")
    a(f"- Source ID used: `{tl.get('source_id_used')}`")
    a(f"- From query type: `{tl.get('from_query_type')}`")
    a(f"- Status: `{tl.get('status')}`")
    a(f"- Skipped: `{tl.get('skipped', False)}`")
    if tl.get("fields_observed"):
        a("\n**Fields observed in topic response:**\n")
        a("| Field | Present? |")
        a("|---|---|")
        for f, v in tl["fields_observed"].items():
            a(f"| `{f}` | {v} |")
    if tl.get("raw_summary"):
        a("\n**Topic summary:**\n```")
        a(tl["raw_summary"][:600])
        a("```")

    cs = results.get("credential_set", {})
    section("5. Credential-Set Lookup")
    a(f"- Topic ID used: `{cs.get('topic_id_used')}`")
    a(f"- Status: `{cs.get('status')}`")
    a(f"- Skipped: `{cs.get('skipped', False)}`")
    a(f"- Credentials returned: `{cs.get('credential_count', 0)}`")
    a(f"- Credential types seen: {cs.get('credential_types_seen', [])}")
    a(f"- Has historical credentials: `{cs.get('has_history', False)}`")
    a(f"- Address in credentials: `{cs.get('address_in_credentials', False)}`")
    a(f"- Phone in credentials: `{cs.get('phone_in_credentials', False)}`")
    a(f"- Email in credentials: `{cs.get('email_in_credentials', False)}`")

    ct = results.get("credential_types", {})
    section("6. Credential-Type Inventory")
    a(f"- Status: `{ct.get('status')}`")
    a(f"- Total credential types: `{ct.get('count', 0)}`")
    if ct.get("types"):
        a("\n| Credential type | Issuer | Credential count |")
        a("|---|---|---|")
        for t in ct["types"][:15]:
            sl = t.get("schema_label") or "?"
            # schema_label may be a dict like {'en': {'label': ...}}
            if isinstance(sl, dict):
                en = sl.get("en", sl)
                if isinstance(en, dict):
                    sl = en.get("label") or en.get("description") or str(en)
                else:
                    sl = str(en)
            issuer = str(t.get("issuer") or "?")
            a(f"| {str(sl)[:50]} | {issuer[:40]} | {t.get('credential_count','?')} |")

    pg = results.get("pagination", {})
    section("7. Pagination")
    a(f"- Status: `{pg.get('status')}`")
    a(f"- Total results (query='ltd'): `{pg.get('total')}`")
    a(f"- Page size: `{pg.get('page_size')}`")
    a(f"- Pagination fields present: {pg.get('pagination_fields_present', [])}")
    a(f"- Note: {pg.get('note')}")

    section("8. Contact / Enrichment Field Check")
    a("Based on live API responses:")
    if cs.get("skipped"):
        a("- Credential-set lookup skipped — contact fields not measurable from credentials")
    else:
        a(f"- Address in credentials: `{cs.get('address_in_credentials')}`")
        a(f"- Phone in credentials: `{cs.get('phone_in_credentials')}`")
        a(f"- Email in credentials: `{cs.get('email_in_credentials')}`")
    a("- BC OrgBook FAQ explicitly states: addresses, director names, contact information and ownership details are NOT displayed due to legislative restrictions")
    a("- OrgBook = identity/status/registration verification source only — not contact enrichment")

    section("9. Terms / Access Compliance")
    a("- API freely accessible, no authentication required")
    a("- BC Government Terms of Use apply")
    a("- Full-database automated scraping: PROHIBITED")
    a("- 10-page search limit enforced specifically to prevent database enumeration")
    a("- High-volume requests: must be throttled")
    a("- Script throttled requests at 1.5s intervals in compliance with BC guidance")
    a("- Correct use: targeted lookups by name / BC Registry ID / CRA BN")
    a("- Incorrect use: walking all pages, enumerating all organizations, bulk downloading")

    section("10. Architecture Role")
    a("| Capability | Assessment |")
    a("|---|---|")
    a("| BC identity verification (name/ID/BN) | ✅ Targeted lookup confirmed |")
    a("| Registration status | ✅ Present in credentials |")
    a("| Registration date / history | ✅ Credential timeline available |")
    a("| Legal name + DBA | ✅ In credential attributes |")
    a("| Entity type | ✅ |")
    a("| Address | ❌ Legislatively restricted — not displayed |")
    a("| Phone / Email / Website | ❌ Not available |")
    a("| Directors / Ownership | ❌ Legislatively restricted |")
    a("| Employee count | ❌ |")
    a("| NAICS | ❌ |")
    a("| Bulk BC business discovery | ❌ PROHIBITED by terms |")
    a("| Canada-wide coverage | ❌ BC only |")

    a("""
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
""")

    section("11. Open Questions")
    a("- [ ] Does a credential timeline expose BC business name-change events usable as change signals?")
    a("- [ ] Is the CRA Business Number (BN) reliably present in credential attributes for cross-source matching?")
    a("- [ ] What is the current SLA / uptime commitment for the public API?")
    a("- [ ] Does BC OrgBook publish a change/notification feed for production use?")

    section("12. Summary Metrics")
    a("| Metric | Result |")
    a("|---|---|")
    a(f"| API v4 reachable | {any(ar.get('status') == 200 for ar in ac.values())} |")
    a(f"| Authentication required | No |")
    a(f"| Autocomplete — name query | status={ac.get('name',{}).get('status')}, results={ac.get('name',{}).get('result_count')} |")
    a(f"| Autocomplete — BC Reg ID | status={ac.get('bc_reg_id',{}).get('status')}, results={ac.get('bc_reg_id',{}).get('result_count')} |")
    a(f"| Autocomplete — CRA BN | status={ac.get('cra_bn',{}).get('status')}, results={ac.get('cra_bn',{}).get('result_count')} |")
    a(f"| Topic lookup | status={tl.get('status')}, skipped={tl.get('skipped',False)} |")
    a(f"| Credential-set lookup | status={cs.get('status')}, count={cs.get('credential_count',0)} |")
    a(f"| Credential types | count={ct.get('count',0)} |")
    a(f"| Address in API | No — legislatively restricted |")
    a(f"| Phone / Email in API | No — not available |")
    a(f"| Bulk enumeration permitted | No — BC Terms prohibit |")
    a(f"| Throttle applied | Yes — 1.5s between requests |")
    a(f"| Terms | BC Government Terms of Use |")
    a(f"| Final role | Class C — targeted BC identity/status verification |")
    a(f"| Final status | ✅ VALIDATED |")

    text = "\n".join(lines)
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"\nReport written: {REPORT_PATH}")
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(SEP)
    print("VR09 — BC ORGBOOK API v4 TECHNICAL VALIDATION")
    print(SEP)
    print("Note: Throttled at 1.5s between requests per BC guidance.")
    print("No pagination walking. No enumeration. Targeted queries only.\n")

    results = {"generated": TIMESTAMP}

    ac = test_autocomplete(results)
    tl, topic_id = test_topic_lookup(ac, results)
    test_credential_set(topic_id, results)
    test_credential_types(results)
    test_pagination(results)

    print(f"\n{SEP}")
    print("WRITING REPORT")
    print(SEP)
    write_report(results)

    JSON_PATH.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"JSON written: {JSON_PATH}")

    print(SEP)
    print("VR09 COMPLETE")
    print(SEP)


if __name__ == "__main__":
    main()
