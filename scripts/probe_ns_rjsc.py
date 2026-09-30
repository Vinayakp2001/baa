"""
VR10 — Nova Scotia RJSC Technical Validation
Probes the public RJSC search to determine:
  - Whether a JSON/XHR endpoint exists
  - What fields are returned for a targeted business lookup
  - Pagination / search-limit behaviour
  - Auth requirements and rate-limit headers
  - Terms of use signals in HTTP responses

Scope: 1-2 targeted searches only. No enumeration.
Throttle: 2s between requests.
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

THROTTLE = 2.0  # seconds between requests

# Known candidate businesses for test searches
TEST_NAMES = [
    "Sobeys Capital Incorporated",
    "Halifax Water",
]

# RJSC base URL (confirmed from RR05 research)
RJSC_BASE = "https://rjsc.novascotia.ca"

# Candidate API/XHR paths to probe (derived from common NS government portal patterns)
# The RJSC portal is built on a standard provincial registry stack.
# We probe the most likely JSON endpoint patterns first.
CANDIDATE_SEARCH_PATHS = [
    "/api/search",
    "/api/v1/search",
    "/RegistrySearch/api/search",
    "/api/business/search",
    "/search/api",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-script/1.0; +validation-only)",
    "Accept": "application/json, text/html, */*",
}

REPORT = {
    "generated": datetime.now(timezone.utc).isoformat(),
    "source": "Nova Scotia RJSC",
    "base_url": RJSC_BASE,
    "homepage_probe": {},
    "api_endpoint_discovery": [],
    "search_results": [],
    "field_inventory": {},
    "pagination": {},
    "auth_required": None,
    "rate_limit_headers": {},
    "terms_signals": [],
    "summary": {},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(url, params=None, extra_headers=None):
    """HTTP GET, returns (status, headers_dict, body_text). Never raises on HTTP errors."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    if extra_headers:
        for k, v in extra_headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            hdrs = dict(resp.headers)
            return resp.status, hdrs, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, dict(e.headers), body
    except Exception as exc:
        return 0, {}, str(exc)


def throttle():
    time.sleep(THROTTLE)


def is_json(body):
    try:
        json.loads(body)
        return True
    except Exception:
        return False


def safe_json(body):
    try:
        return json.loads(body)
    except Exception:
        return None


def collect_keys(obj, prefix="", depth=0, max_depth=4):
    """Recursively collect all key paths from a JSON object."""
    keys = []
    if depth > max_depth:
        return keys
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            keys.append(path)
            keys.extend(collect_keys(v, path, depth + 1, max_depth))
    elif isinstance(obj, list) and len(obj) > 0:
        keys.extend(collect_keys(obj[0], prefix + "[]", depth + 1, max_depth))
    return keys


# ---------------------------------------------------------------------------
# Step 1 — Homepage probe
# ---------------------------------------------------------------------------

print("\n=== Step 1: Homepage probe ===")
status, hdrs, body = get(RJSC_BASE + "/")
throttle()

REPORT["homepage_probe"] = {
    "url": RJSC_BASE + "/",
    "status": status,
    "content_type": hdrs.get("Content-Type", hdrs.get("content-type", "unknown")),
    "body_length": len(body),
    "appears_html": "<html" in body.lower() or "<!doctype" in body.lower(),
    "appears_json": is_json(body),
}
print(f"  Status: {status}")
print(f"  Content-Type: {REPORT['homepage_probe']['content_type']}")
print(f"  Body length: {len(body)} chars")

# Scan for hints of API/XHR paths in the HTML
api_hints = []
for hint in ["api/", "/api", "XHR", "fetch(", "axios", "json", ".json"]:
    if hint.lower() in body.lower():
        api_hints.append(hint)
REPORT["homepage_probe"]["api_hints_in_html"] = api_hints
print(f"  API hints in HTML: {api_hints}")

# Check for terms/robots signals
terms_keywords = ["automated", "scraping", "robot", "terms of use", "prohibit", "bulk"]
found_terms = [kw for kw in terms_keywords if kw.lower() in body.lower()]
REPORT["terms_signals"].extend(found_terms)
print(f"  Terms keywords in homepage: {found_terms}")

# ---------------------------------------------------------------------------
# Step 2 — Probe candidate JSON API endpoints
# ---------------------------------------------------------------------------

print("\n=== Step 2: API endpoint discovery ===")

working_endpoints = []
for path in CANDIDATE_SEARCH_PATHS:
    url = RJSC_BASE + path
    # Try with a simple query param
    status, hdrs, body = get(url, params={"q": "Sobeys"})
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    result = {
        "path": path,
        "url": url,
        "status": status,
        "content_type": ct,
        "is_json": is_json(body),
        "body_length": len(body),
        "body_preview": body[:300],
    }
    REPORT["api_endpoint_discovery"].append(result)
    print(f"  {path}: status={status}, json={is_json(body)}, ct={ct[:50]}")
    if is_json(body) and status == 200:
        working_endpoints.append(path)
        print(f"    *** JSON 200 found at {path} ***")

# ---------------------------------------------------------------------------
# Step 3 — Try standard NS government RJSC search form submission
# ---------------------------------------------------------------------------

print("\n=== Step 3: Form-based search probe ===")

# Try the main search page to discover actual form action/endpoint
search_page_candidates = [
    "/RegistrySearch",
    "/search",
    "/en/Home/Index",
    "/Home/Search",
    "/en/RegistrySearch",
]

form_endpoint = None
for sp in search_page_candidates:
    url = RJSC_BASE + sp
    status, hdrs, body = get(url)
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    is_html = "<html" in body.lower() or "<!doctype" in body.lower()
    print(f"  {sp}: status={status}, html={is_html}, length={len(body)}")
    if status == 200 and is_html:
        # Look for form action attribute
        lower_body = body.lower()
        action_idx = lower_body.find('action="')
        if action_idx > -1:
            action_end = body.find('"', action_idx + 8)
            form_action = body[action_idx + 8:action_end]
            print(f"    Form action found: {form_action}")
            REPORT["homepage_probe"]["form_action"] = form_action
            form_endpoint = form_action
        # Look for any fetch/XHR URL patterns
        for kw in ["fetch(", "XMLHttpRequest", "/api/", "$.ajax", "axios.get"]:
            if kw in body:
                idx = body.find(kw)
                snippet = body[max(0, idx-20):idx+80]
                print(f"    JS hint [{kw}]: ...{snippet.strip()}...")
        break

# ---------------------------------------------------------------------------
# Step 4 — Try POST to common search form endpoints
# ---------------------------------------------------------------------------

print("\n=== Step 4: POST search probes ===")

post_candidates = [
    "/RegistrySearch/Search",
    "/en/Home/Search",
    "/Search",
    "/api/search",
]

for path in post_candidates:
    url = RJSC_BASE + path
    data = urllib.parse.urlencode({
        "SearchType": "BusinessName",
        "SearchValue": "Sobeys",
        "Status": "Active",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        **HEADERS,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
            hdrs = dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        status = e.code
        hdrs = dict(e.headers)
    except Exception as exc:
        body = str(exc)
        status = 0
        hdrs = {}

    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    print(f"  POST {path}: status={status}, json={is_json(body)}, ct={ct[:50]}")
    throttle()

    if is_json(body) and status == 200:
        print(f"    *** JSON POST response at {path} ***")
        parsed = safe_json(body)
        keys = collect_keys(parsed)
        REPORT["field_inventory"][path] = keys
        REPORT["search_results"].append({
            "path": path,
            "method": "POST",
            "status": status,
            "keys": keys,
            "sample": json.dumps(parsed, indent=2)[:2000],
        })

# ---------------------------------------------------------------------------
# Step 5 — Check robots.txt and terms page
# ---------------------------------------------------------------------------

print("\n=== Step 5: robots.txt and terms ===")

for chk_path in ["/robots.txt", "/terms", "/en/About/TermsOfUse", "/TermsOfUse"]:
    url = RJSC_BASE + chk_path
    status, hdrs, body = get(url)
    throttle()
    print(f"  {chk_path}: status={status}, length={len(body)}")
    if status == 200:
        lower = body.lower()
        hits = [kw for kw in ["disallow", "automated", "scraping", "bulk", "prohibit", "commercial"] if kw in lower]
        if hits:
            REPORT["terms_signals"].extend(hits)
            print(f"    Terms/robots keywords: {hits}")
            # Capture relevant snippet
            for kw in hits[:3]:
                idx = lower.find(kw)
                snippet = body[max(0, idx-80):idx+200].strip()
                REPORT["terms_signals"].append(f"[{chk_path}] snippet: {snippet[:300]}")

# ---------------------------------------------------------------------------
# Step 6 — Rate-limit header scan across collected headers
# ---------------------------------------------------------------------------

print("\n=== Step 6: Rate-limit header check ===")

rl_keys = ["x-ratelimit", "retry-after", "x-rate-limit", "ratelimit", "x-throttle"]
# Re-probe homepage to get fresh headers
status, hdrs, body = get(RJSC_BASE + "/")
throttle()
rl_found = {k: v for k, v in hdrs.items() if any(rk in k.lower() for rk in rl_keys)}
REPORT["rate_limit_headers"] = rl_found
if rl_found:
    print(f"  Rate-limit headers: {rl_found}")
else:
    print("  No rate-limit headers detected in homepage response")

# ---------------------------------------------------------------------------
# Step 7 — Write report JSON
# ---------------------------------------------------------------------------

# Auth determination
REPORT["auth_required"] = False  # default; update if 401/403 observed
for item in REPORT["api_endpoint_discovery"]:
    if item["status"] in (401, 403):
        REPORT["auth_required"] = True
        break

# Summary
REPORT["summary"] = {
    "homepage_reachable": REPORT["homepage_probe"].get("status") == 200,
    "json_api_endpoints_found": working_endpoints,
    "search_results_captured": len(REPORT["search_results"]),
    "field_keys_captured": list(REPORT["field_inventory"].keys()),
    "auth_required": REPORT["auth_required"],
    "rate_limit_headers_found": bool(REPORT["rate_limit_headers"]),
    "terms_signals_found": list(set(
        s for s in REPORT["terms_signals"] if not s.startswith("[")
    )),
}

report_path = "reports/validation_rounds/VR10_NS_RJSC.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(REPORT, f, indent=2, ensure_ascii=False)

print(f"\n=== Report written: {report_path} ===")
print(json.dumps(REPORT["summary"], indent=2))
