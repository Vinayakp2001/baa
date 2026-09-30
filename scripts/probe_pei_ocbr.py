"""
VR11 — PEI OCBR Technical Validation
Probes PEI's Online Corporate and Business Names Registry (OCBR).

PEI is mid-transition: both new registry and original registry must be tested.
Scope: 1-2 targeted searches per registry only. No enumeration.
Throttle: 2s between requests.

Goals:
  - Determine if new/original OCBR expose a JSON/XHR endpoint
  - Capture field structure from targeted search results
  - Check auth / session / CSRF requirements
  - Check robots.txt and terms signals
  - Check rate-limit headers
  - Record response content type (JSON vs HTML)
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

THROTTLE = 2.0

# Known PEI businesses for test searches (large/well-known to maximise hit rate)
TEST_NAMES = ["Sobeys Capital", "PEI Mutual Insurance"]

# Candidate base URLs for new and original registry
# Primary: new OCBR system
# Original: legacy registry still active during transition
NEW_REGISTRY_BASES = [
    "https://eservices.gov.pe.ca/OCBR",
    "https://eservices.gov.pe.ca/peiocbr",
    "https://eservices.gov.pe.ca/ocbr",
    "https://eservices.gov.pe.ca/RegistrySearch",
    "https://eservices.gov.pe.ca/BusinessRegistry",
    "https://eservices.gov.pe.ca/BusinessNames",
    "https://eservices.gov.pe.ca/CorporateRegistry",
    "https://eservices.gov.pe.ca/Registry",
]

ORIGINAL_REGISTRY_BASES = [
    "https://eservices.gov.pe.ca/CorporateOnline",
    "https://eservices.gov.pe.ca/corporateonline",
    "https://eservices.gov.pe.ca/Corporations",
    "https://eservices.gov.pe.ca/corporations",
]

# Common search/API path suffixes to probe
SEARCH_SUFFIXES = [
    "/",
    "/api/search",
    "/api/v1/search",
    "/api/businesses/search",
    "/Search",
    "/search",
    "/BusinessSearch",
    "/en/Home/Index",
    "/Home/Search",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-script/1.0; +validation-only)",
    "Accept": "application/json, text/html, */*",
}

REPORT = {
    "generated": datetime.now(timezone.utc).isoformat(),
    "source": "PEI OCBR (new + original registry)",
    "new_registry_probe": [],
    "original_registry_probe": [],
    "search_results": [],
    "field_inventory": {},
    "terms_signals": [],
    "rate_limit_headers": {},
    "summary": {},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(url, params=None, extra_headers=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    if extra_headers:
        for k, v in extra_headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")
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


def collect_keys(obj, prefix="", depth=0, max_depth=5):
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


def probe_base(base_url, label, results_list):
    """Probe a registry base URL: homepage + search suffixes."""
    print(f"\n  [{label}] Base: {base_url}")
    for suffix in SEARCH_SUFFIXES:
        url = base_url + suffix
        # Try plain GET first
        status, hdrs, body = get(url)
        throttle()
        ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
        is_j = is_json(body)
        is_html = "<html" in body.lower() or "<!doctype" in body.lower()
        entry = {
            "url": url,
            "method": "GET",
            "status": status,
            "content_type": ct[:80],
            "is_json": is_j,
            "is_html": is_html,
            "body_length": len(body),
            "body_preview": body[:200],
        }
        results_list.append(entry)
        print(f"    GET {suffix}: {status}, json={is_j}, html={is_html}, ct={ct[:50]}")

        # If 200 HTML, scan for XHR/API hints and form actions
        if status == 200 and is_html:
            lower = body.lower()
            hints = [kw for kw in ["fetch(", "xmlhttprequest", "/api/", "$.ajax", "axios", ".json"] if kw in lower]
            if hints:
                entry["api_hints"] = hints
                print(f"      JS/API hints: {hints}")
            action_idx = lower.find('action="')
            if action_idx > -1:
                end = body.find('"', action_idx + 8)
                form_action = body[action_idx + 8:end]
                entry["form_action"] = form_action
                print(f"      Form action: {form_action}")

        # If 200 JSON, extract keys
        if status == 200 and is_j:
            parsed = safe_json(body)
            keys = collect_keys(parsed)
            entry["field_keys"] = keys
            REPORT["field_inventory"][url] = keys
            REPORT["search_results"].append({
                "url": url,
                "method": "GET",
                "status": status,
                "keys": keys,
                "sample": json.dumps(parsed, indent=2)[:2000],
            })
            print(f"      *** JSON 200 *** Keys: {keys[:20]}")

        # Only probe suffixes beyond "/" if "/" was reachable (200/301/302)
        if suffix == "/" and status not in (200, 301, 302, 403):
            print(f"      Base not reachable ({status}), skipping remaining suffixes")
            break


# ---------------------------------------------------------------------------
# Step 0 — Confirm eservices.gov.pe.ca host is live + enumerate known paths
# ---------------------------------------------------------------------------

print("\n=== Step 0: eservices.gov.pe.ca host enumeration ===")

ESERVICES_BASE = "https://eservices.gov.pe.ca"
ESERVICES_PATHS = [
    "/",
    "/OCBR/",
    "/OCBR",
    "/ocbr/",
    "/CorporateOnline/",
    "/CorporateOnline",
    "/Registry/",
    "/RegistrySearch/",
    "/BusinessNames/",
    "/CorporateRegistry/",
    "/Corporations/",
    "/peiocbr/",
    "/PEIOCBR/",
    "/BusinessRegistry/",
    "/en/",
    "/en/Home",
    "/en/Search",
    "/api/",
    "/api/v1/",
]

live_eservices_paths = []
for path in ESERVICES_PATHS:
    url = ESERVICES_BASE + path
    status, hdrs, body = get(url)
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    is_j = is_json(body)
    is_html = "<html" in body.lower() or "<!doctype" in body.lower()
    print(f"  {path}: {status}, json={is_j}, html={is_html}, ct={ct[:40]}, len={len(body)}")
    if status in (200, 301, 302):
        live_eservices_paths.append({"path": path, "status": status, "ct": ct, "is_json": is_j})
        if is_html:
            lower = body.lower()
            for kw in ["fetch(", "xmlhttprequest", "/api/", "axios", "ocbr", "corporate", "registry"]:
                if kw in lower:
                    idx = lower.find(kw)
                    snippet = body[max(0, idx-10):idx+60].strip()
                    print(f"    hint [{kw}]: {snippet}")
        if is_j:
            parsed = safe_json(body)
            keys = collect_keys(parsed)
            print(f"    JSON keys: {keys[:15]}")

print(f"\n  Live eservices paths: {[p['path'] for p in live_eservices_paths]}")

# ---------------------------------------------------------------------------
# Step 1 — Probe new registry candidates
# ---------------------------------------------------------------------------

print("\n=== Step 1: New OCBR registry candidates ===")

reachable_new = None
for base in NEW_REGISTRY_BASES:
    status, hdrs, body = get(base + "/")
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    print(f"  {base}/: status={status}, ct={ct[:50]}")
    if status in (200, 301, 302, 403):
        # Record the first reachable base for deeper probing
        if reachable_new is None and status in (200, 301, 302):
            reachable_new = base
        entry = {
            "url": base + "/",
            "status": status,
            "content_type": ct[:80],
            "is_json": is_json(body),
            "is_html": "<html" in body.lower(),
            "body_length": len(body),
        }
        REPORT["new_registry_probe"].append(entry)
        # Check for robot/terms keywords
        lower = body.lower()
        hits = [kw for kw in ["robot", "automated", "scraping", "terms", "prohibit"] if kw in lower]
        if hits:
            REPORT["terms_signals"].extend(hits)

if reachable_new:
    print(f"\n  Probing reachable new registry: {reachable_new}")
    probe_base(reachable_new, "NEW", REPORT["new_registry_probe"])
else:
    print("  No reachable new registry base found — all returned connection errors or unexpected status")

# ---------------------------------------------------------------------------
# Step 2 — Probe original registry candidates
# ---------------------------------------------------------------------------

print("\n=== Step 2: Original registry candidates ===")

reachable_orig = None
for base in ORIGINAL_REGISTRY_BASES:
    status, hdrs, body = get(base + "/")
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    print(f"  {base}/: status={status}, ct={ct[:50]}")
    if status in (200, 301, 302):
        if reachable_orig is None:
            reachable_orig = base
        entry = {
            "url": base + "/",
            "status": status,
            "content_type": ct[:80],
            "is_json": is_json(body),
            "is_html": "<html" in body.lower(),
            "body_length": len(body),
        }
        REPORT["original_registry_probe"].append(entry)

if reachable_orig:
    print(f"\n  Probing reachable original registry: {reachable_orig}")
    probe_base(reachable_orig, "ORIG", REPORT["original_registry_probe"])
else:
    print("  No reachable original registry base found")

# ---------------------------------------------------------------------------
# Step 3 — Try GET search queries on reachable bases
# ---------------------------------------------------------------------------

print("\n=== Step 3: GET search queries ===")

search_param_variants = [
    {"q": "Sobeys"},
    {"businessName": "Sobeys"},
    {"name": "Sobeys"},
    {"search": "Sobeys"},
    {"SearchValue": "Sobeys"},
    {"query": "Sobeys"},
]

bases_to_search = []
if reachable_new:
    bases_to_search.append((reachable_new, "NEW"))
if reachable_orig:
    bases_to_search.append((reachable_orig, "ORIG"))

for base, label in bases_to_search:
    for path in ["/api/search", "/search", "/Search", "/BusinessSearch"]:
        for params in search_param_variants[:3]:  # limit to 3 param variants per path
            url = base + path
            status, hdrs, body = get(url, params=params)
            throttle()
            ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
            if is_json(body) and status == 200:
                parsed = safe_json(body)
                keys = collect_keys(parsed)
                print(f"  [{label}] *** JSON 200 *** GET {path}?{urllib.parse.urlencode(params)}")
                print(f"    Keys: {keys[:20]}")
                REPORT["search_results"].append({
                    "url": url,
                    "params": params,
                    "method": "GET",
                    "status": status,
                    "keys": keys,
                    "sample": json.dumps(parsed, indent=2)[:2000],
                })
                REPORT["field_inventory"][f"{url}?{urllib.parse.urlencode(params)}"] = keys
            elif status == 200:
                print(f"  [{label}] GET {path}?{urllib.parse.urlencode(params)}: 200 HTML/text, len={len(body)}")
            else:
                print(f"  [{label}] GET {path}?{urllib.parse.urlencode(params)}: {status}")

# ---------------------------------------------------------------------------
# Step 4 — robots.txt and terms
# ---------------------------------------------------------------------------

print("\n=== Step 4: robots.txt and terms ===")

all_bases = list({b for b in [reachable_new, reachable_orig] if b})
if not all_bases:
    # eservices host is confirmed reachable — probe terms paths directly
    all_bases = [
        "https://eservices.gov.pe.ca/OCBR",
        "https://eservices.gov.pe.ca/CorporateOnline",
    ]

for base in all_bases:
    for chk in ["/robots.txt", "/terms", "/en/About/TermsOfUse", "/TermsOfUse", "/eula", "/privacy"]:
        url = base + chk
        status, hdrs, body = get(url)
        throttle()
        print(f"  {url}: {status}, len={len(body)}")
        if status == 200:
            lower = body.lower()
            hits = [kw for kw in ["disallow", "automated", "scraping", "bulk", "prohibit", "commercial", "robot"] if kw in lower]
            if hits:
                REPORT["terms_signals"].extend(hits)
                for kw in hits[:2]:
                    idx = lower.find(kw)
                    snippet = body[max(0, idx-80):idx+200].strip()
                    REPORT["terms_signals"].append(f"[{chk}] {snippet[:300]}")
                print(f"    Terms keywords: {hits}")

# ---------------------------------------------------------------------------
# Step 5 — Rate-limit headers
# ---------------------------------------------------------------------------

print("\n=== Step 5: Rate-limit headers ===")

rl_keys = ["x-ratelimit", "retry-after", "x-rate-limit", "ratelimit", "x-throttle"]
probe_base_url = (reachable_new or reachable_orig or "https://eservices.gov.pe.ca") + "/"
status, hdrs, body = get(probe_base_url)
throttle()
rl_found = {k: v for k, v in hdrs.items() if any(rk in k.lower() for rk in rl_keys)}
REPORT["rate_limit_headers"] = rl_found
print(f"  Rate-limit headers: {rl_found if rl_found else 'none detected'}")

# ---------------------------------------------------------------------------
# Step 6 — Write report
# ---------------------------------------------------------------------------

all_statuses = (
    [e.get("status") for e in REPORT["new_registry_probe"]] +
    [e.get("status") for e in REPORT["original_registry_probe"]]
)

REPORT["summary"] = {
    "new_registry_reachable": reachable_new,
    "original_registry_reachable": reachable_orig,
    "json_responses_found": len(REPORT["search_results"]),
    "field_keys_captured": list(REPORT["field_inventory"].keys()),
    "auth_blocked_403": any(s == 403 for s in all_statuses),
    "rate_limit_headers_found": bool(REPORT["rate_limit_headers"]),
    "terms_signals_found": list(set(
        s for s in REPORT["terms_signals"] if not s.startswith("[")
    )),
}

report_path = "reports/validation_rounds/VR11_PEI_OCBR.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(REPORT, f, indent=2, ensure_ascii=False)

print(f"\n=== Report written: {report_path} ===")
print(json.dumps(REPORT["summary"], indent=2))
