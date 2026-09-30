"""VR11.1 PEI OCBR probe using confirmed live URLs."""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

THROTTLE = 2.0

# Confirmed live URLs
PEI_GOV_BASE = "https://www.princeedwardisland.ca"
NEW_REGISTRY_PAGE = "/en/feature/pei-business-corporate-registry"
ORIG_REGISTRY_PAGE = "/en/feature/pei-business-corporate-registry-original"
OCBR_BASE = "https://ocbr.princeedwardisland.ca"

# Known PEI businesses for test searches
TEST_NAMES = ["Sobeys Capital", "PEI Mutual"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-script/1.0; +validation-only)",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-CA,en;q=0.9",
}

REPORT = {
    "generated": datetime.now(timezone.utc).isoformat(),
    "source": "PEI OCBR — confirmed URLs",
    "registry_pages": {},
    "api_probes": [],
    "ocbr_host_probes": [],
    "search_results": [],
    "field_inventory": {},
    "terms_signals": [],
    "rate_limit_headers": {},
    "summary": {},
}


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


def scan_html_for_api(body, label):
    """Scan HTML body for XHR/API/form hints."""
    hints = {}
    lower = body.lower()

    # Form action
    idx = lower.find('action="')
    if idx > -1:
        end = body.find('"', idx + 8)
        hints["form_action"] = body[idx + 8:end]

    # JS fetch/XHR patterns
    js_hints = []
    for kw in ["fetch(", "xmlhttprequest", "$.ajax", "axios.get", "axios.post"]:
        if kw in lower:
            i = lower.find(kw)
            js_hints.append(body[max(0, i - 10):i + 100].strip())
    if js_hints:
        hints["js_fetch_hints"] = js_hints

    # API URL patterns in JS/HTML
    api_urls = []
    for kw in ["/api/", "/search/", "/registry/", "/ocbr/", "/businesses/", "/corporate/"]:
        i = lower.find(kw)
        while i > -1:
            snippet = body[max(0, i - 5):i + 80].strip()
            api_urls.append(snippet)
            i = lower.find(kw, i + 1)
            if len(api_urls) > 10:
                break
    if api_urls:
        hints["api_url_snippets"] = api_urls[:10]

    # CSRF token
    for csrf_kw in ["csrf", "_token", "requestverificationtoken", "x-csrf"]:
        if csrf_kw in lower:
            hints["csrf_hint"] = csrf_kw

    if hints:
        print(f"  [{label}] HTML hints: {list(hints.keys())}")
        for k, v in hints.items():
            if isinstance(v, list):
                for item in v[:3]:
                    print(f"    {k}: {str(item)[:120]}")
            else:
                print(f"    {k}: {str(v)[:120]}")

    return hints


# ---------------------------------------------------------------------------
# Step 1 — Fetch both public registry pages
# ---------------------------------------------------------------------------

print("\n=== Step 1: Fetch public registry pages ===")

for label, path in [("NEW", NEW_REGISTRY_PAGE), ("ORIG", ORIG_REGISTRY_PAGE)]:
    url = PEI_GOV_BASE + path
    status, hdrs, body = get(url)
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    is_html = "<html" in body.lower() or "<!doctype" in body.lower()
    print(f"\n  [{label}] {url}")
    print(f"  Status: {status}, CT: {ct[:60]}, len: {len(body)}, html: {is_html}")

    entry = {
        "url": url,
        "status": status,
        "content_type": ct,
        "is_json": is_json(body),
        "is_html": is_html,
        "body_length": len(body),
    }

    if status == 200 and is_html:
        hints = scan_html_for_api(body, label)
        entry["html_hints"] = hints
        # Look for embedded search iframe/widget URL
        for kw in ["ocbr.princeedwardisland.ca", "registry", "search", "iframe", "embed"]:
            if kw in body.lower():
                idx = body.lower().find(kw)
                snippet = body[max(0, idx - 20):idx + 120].strip()
                print(f"    keyword [{kw}]: {snippet[:150]}")
        # Terms keywords
        hits = [kw for kw in ["automated", "scraping", "robot", "terms", "prohibit", "commercial", "copyright", "eula"] if kw in body.lower()]
        if hits:
            REPORT["terms_signals"].extend(hits)
            print(f"    Terms keywords: {hits}")

    REPORT["registry_pages"][label] = entry

# ---------------------------------------------------------------------------
# Step 2 — Probe OCBR host for public search/API endpoints
# ---------------------------------------------------------------------------

print("\n=== Step 2: OCBR host API probes ===")

OCBR_PATHS = [
    "/",
    "/ocbr/",
    "/ocbr/search",
    "/ocbr/api/search",
    "/ocbr/api/v1/search",
    "/ocbr/public/search",
    "/ocbr/businesses",
    "/ocbr/api/businesses",
    "/api/search",
    "/api/v1/search",
    "/api/businesses",
    "/search",
    "/public/search",
]

for path in OCBR_PATHS:
    url = OCBR_BASE + path
    status, hdrs, body = get(url)
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    is_j = is_json(body)
    is_html = "<html" in body.lower() or "<!doctype" in body.lower()
    entry = {
        "url": url,
        "status": status,
        "content_type": ct[:80],
        "is_json": is_j,
        "is_html": is_html,
        "body_length": len(body),
        "body_preview": body[:200],
    }
    REPORT["ocbr_host_probes"].append(entry)
    print(f"  {path}: {status}, json={is_j}, html={is_html}, len={len(body)}, ct={ct[:40]}")

    if status == 200 and is_j:
        parsed = safe_json(body)
        keys = collect_keys(parsed)
        entry["field_keys"] = keys
        REPORT["field_inventory"][url] = keys
        REPORT["search_results"].append({
            "url": url, "status": status, "keys": keys,
            "sample": json.dumps(parsed, indent=2)[:2000],
        })
        print(f"    *** JSON 200 *** keys: {keys[:20]}")

    if status == 200 and is_html:
        hints = scan_html_for_api(body, path)
        entry["html_hints"] = hints

# ---------------------------------------------------------------------------
# Step 3 — Try GET search queries against OCBR host
# ---------------------------------------------------------------------------

print("\n=== Step 3: OCBR search query probes ===")

search_paths = [
    "/ocbr/api/search",
    "/ocbr/search",
    "/api/search",
    "/search",
    "/ocbr/public/businesses/search",
    "/ocbr/businesses/search",
]

param_variants = [
    {"q": "Sobeys"},
    {"name": "Sobeys"},
    {"businessName": "Sobeys"},
    {"searchTerm": "Sobeys"},
    {"query": "Sobeys"},
]

for path in search_paths:
    for params in param_variants[:2]:
        url = OCBR_BASE + path
        status, hdrs, body = get(url, params=params)
        throttle()
        ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
        if is_json(body) and status == 200:
            parsed = safe_json(body)
            keys = collect_keys(parsed)
            print(f"  *** JSON 200 *** {path}?{urllib.parse.urlencode(params)}")
            print(f"    Keys: {keys[:20]}")
            REPORT["search_results"].append({
                "url": OCBR_BASE + path, "params": params,
                "status": status, "keys": keys,
                "sample": json.dumps(parsed, indent=2)[:2000],
            })
        elif status not in (404, 0):
            print(f"  {path}?{urllib.parse.urlencode(params)}: {status}, ct={ct[:40]}, len={len(body)}")

# ---------------------------------------------------------------------------
# Step 4 — Probe PEI gov site for embedded registry API
# ---------------------------------------------------------------------------

print("\n=== Step 4: PEI gov site registry API probes ===")

PEI_API_PATHS = [
    "/api/registry/search",
    "/api/businesses/search",
    "/api/corporate/search",
    "/api/v1/registry/search",
    "/en/api/registry/search",
    "/sites/default/files",  # Drupal static
]

for path in PEI_API_PATHS:
    url = PEI_GOV_BASE + path
    status, hdrs, body = get(url, params={"q": "Sobeys"})
    throttle()
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    print(f"  {path}: {status}, json={is_json(body)}, ct={ct[:40]}")
    if is_json(body) and status == 200:
        parsed = safe_json(body)
        keys = collect_keys(parsed)
        print(f"    *** JSON 200 *** keys: {keys[:20]}")
        REPORT["search_results"].append({
            "url": url, "status": status, "keys": keys,
            "sample": json.dumps(parsed, indent=2)[:2000],
        })

# ---------------------------------------------------------------------------
# Step 5 — robots.txt and terms on both hosts
# ---------------------------------------------------------------------------

print("\n=== Step 5: robots.txt and terms ===")

for host_label, host in [("PEI_GOV", PEI_GOV_BASE), ("OCBR", OCBR_BASE)]:
    for chk in ["/robots.txt", "/terms-conditions", "/privacy", "/en/about/terms-conditions"]:
        url = host + chk
        status, hdrs, body = get(url)
        throttle()
        print(f"  [{host_label}] {chk}: {status}, len={len(body)}")
        if status == 200:
            lower = body.lower()
            hits = [kw for kw in ["disallow", "automated", "scraping", "bulk", "prohibit", "commercial", "copyright", "eula"] if kw in lower]
            if hits:
                REPORT["terms_signals"].extend(hits)
                for kw in hits[:2]:
                    idx = lower.find(kw)
                    snippet = body[max(0, idx - 60):idx + 200].strip()
                    REPORT["terms_signals"].append(f"[{host_label}{chk}]: {snippet[:300]}")
                print(f"    Terms keywords: {hits}")

# ---------------------------------------------------------------------------
# Step 6 — Rate-limit headers
# ---------------------------------------------------------------------------

print("\n=== Step 6: Rate-limit headers ===")
rl_keys = ["x-ratelimit", "retry-after", "x-rate-limit", "ratelimit"]
status, hdrs, _ = get(OCBR_BASE + "/")
throttle()
rl_found = {k: v for k, v in hdrs.items() if any(rk in k.lower() for rk in rl_keys)}
REPORT["rate_limit_headers"] = rl_found
print(f"  OCBR host rate-limit headers: {rl_found if rl_found else 'none'}")

# ---------------------------------------------------------------------------
# Step 7 — Write report
# ---------------------------------------------------------------------------

all_statuses = (
    [e.get("status") for e in REPORT["ocbr_host_probes"]] +
    [v.get("status") for v in REPORT["registry_pages"].values()]
)

REPORT["summary"] = {
    "new_registry_page_status": REPORT["registry_pages"].get("NEW", {}).get("status"),
    "orig_registry_page_status": REPORT["registry_pages"].get("ORIG", {}).get("status"),
    "json_responses_found": len(REPORT["search_results"]),
    "field_keys_captured": list(REPORT["field_inventory"].keys()),
    "any_403": any(s == 403 for s in all_statuses),
    "rate_limit_headers": bool(REPORT["rate_limit_headers"]),
    "terms_signals": list(set(s for s in REPORT["terms_signals"] if not s.startswith("["))),
}

report_path = "reports/validation_rounds/VR11_PEI_OCBR.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(REPORT, f, indent=2, ensure_ascii=False)

print(f"\n=== Report written: {report_path} ===")
print(json.dumps(REPORT["summary"], indent=2))
