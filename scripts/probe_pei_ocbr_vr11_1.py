"""
VR11.1 — PEI OCBR JS Inspection
Objective: Fetch the three public static JS assets from the OCBR host and search
           their contents for API endpoint strings and request patterns.
           If an endpoint is found, fire ONE targeted probe against a known
           business name and record the full request/response.

Rules:
- No login, no session bypass, no CSRF bypass
- No enumeration — at most one test lookup if an anonymous endpoint is found
- Read-only: we are reading public static files the browser itself downloads

Output:
- reports/validation_rounds/VR11_1_PEI_OCBR_JS.json
"""

import urllib.request
import urllib.error
import json
import re
import sys
import time

BASE = "https://ocbr.princeedwardisland.ca"

JS_ASSETS = [
    "/ocbr/resources/js/search/BasicBusinessSearch.js",
    "/ocbr/resources/js/search/basicSearch.js",
    "/ocbr/resources/js/search/SearchCommon.js",
]

# Strings that might surround an API endpoint in the JS source
API_PATTERNS = [
    r'/api/[^\s\'"`,;)]+',
    r'url\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
    r'URL\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
    r'endpoint\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
    r'fetch\([\'"]([^\'"]+)[\'"]',
    r'\$\.ajax\(\s*\{[^}]*url\s*:\s*[\'"]([^\'"]+)[\'"]',
    r'\$\.get\([\'"]([^\'"]+)[\'"]',
    r'\$\.post\([\'"]([^\'"]+)[\'"]',
    r'XMLHttpRequest',
    r'authenticate',
    r'csrf',
    r'x-csrf',
    r'search',
    r'business',
    r'registry',
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/javascript, text/javascript, */*",
    "Referer": "https://ocbr.princeedwardisland.ca/ocbr/",
}


def fetch(url, extra_headers=None, timeout=15):
    hdrs = dict(HEADERS)
    if extra_headers:
        hdrs.update(extra_headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            ct = r.headers.get("Content-Type", "")
            return r.status, ct, raw
    except urllib.error.HTTPError as e:
        return e.code, "", b""
    except Exception as ex:
        return 0, str(ex), b""


def extract_api_hints(js_text, asset_path):
    """Search JS source for API-related strings. Return structured findings."""
    findings = {
        "asset": asset_path,
        "size_bytes": len(js_text.encode("utf-8")),
        "url_candidates": [],
        "keyword_hits": {},
        "raw_excerpts": [],
    }

    # Search for URL-like strings
    url_re = re.compile(r'[\'"`](/[a-zA-Z0-9/_\-\.?=&%{}]+)[\'"`]')
    for m in url_re.finditer(js_text):
        candidate = m.group(1)
        # Only interested in paths, skip static assets
        if any(skip in candidate for skip in [".css", ".png", ".jpg", ".gif", ".woff"]):
            continue
        if candidate not in findings["url_candidates"]:
            findings["url_candidates"].append(candidate)

    # Keyword presence + short excerpt
    keywords = [
        "fetch(", "$.ajax", "$.get(", "$.post(", "XMLHttpRequest",
        "/api/", "search", "authenticate", "csrf", "x-csrf",
        "business", "registry", "endpoint", "baseUrl", "BASE_URL",
    ]
    for kw in keywords:
        idx = js_text.lower().find(kw.lower())
        if idx != -1:
            start = max(0, idx - 80)
            end = min(len(js_text), idx + 160)
            excerpt = js_text[start:end].replace("\n", " ").strip()
            findings["keyword_hits"][kw] = True
            findings["raw_excerpts"].append({
                "keyword": kw,
                "excerpt": excerpt,
            })
        else:
            findings["keyword_hits"][kw] = False

    return findings


def probe_endpoint(endpoint_url, test_name="Sobeys"):
    """Fire one anonymous GET probe at a discovered endpoint with a known name."""
    import urllib.parse
    params = urllib.parse.urlencode({"name": test_name, "q": test_name, "search": test_name})
    url = f"{endpoint_url}?{params}"
    print(f"  Probing endpoint: {url}")
    status, ct, body = fetch(url, extra_headers={"Accept": "application/json, */*"})
    try:
        parsed = json.loads(body.decode("utf-8", errors="replace"))
    except Exception:
        parsed = None
    return {
        "url": url,
        "status": status,
        "content_type": ct,
        "response_bytes": len(body),
        "json_parsed": parsed is not None,
        "json_preview": str(parsed)[:500] if parsed else None,
        "raw_preview": body.decode("utf-8", errors="replace")[:500] if body else None,
    }


def also_fetch_robots():
    """Re-read robots.txt from both hosts to capture full Disallow scope."""
    results = {}
    for host in [BASE, "https://www.princeedwardisland.ca"]:
        url = f"{host}/robots.txt"
        status, ct, body = fetch(url)
        results[host] = {
            "status": status,
            "content": body.decode("utf-8", errors="replace") if body else "",
        }
        time.sleep(0.5)
    return results


def main():
    report = {
        "round": "VR11.1",
        "objective": "PEI OCBR JS inspection — discover backend API endpoint",
        "js_assets": [],
        "api_candidates": [],
        "endpoint_probe": None,
        "robots": {},
        "conclusions": {},
    }

    # --- Step 1: Fetch and inspect each JS file ---
    print("=== Step 1: Fetching JS assets ===")
    for path in JS_ASSETS:
        url = BASE + path
        print(f"  GET {url}")
        status, ct, body = fetch(url)
        text = body.decode("utf-8", errors="replace") if body else ""
        print(f"    → {status}  {len(body)} bytes  ct={ct}")

        asset_record = {
            "path": path,
            "url": url,
            "http_status": status,
            "content_type": ct,
            "size_bytes": len(body),
        }

        if status == 200 and body:
            findings = extract_api_hints(text, path)
            asset_record["findings"] = findings
            # Collect URL candidates into top-level list for easier review
            for c in findings["url_candidates"]:
                if c not in report["api_candidates"]:
                    report["api_candidates"].append(c)
        else:
            asset_record["findings"] = None

        report["js_assets"].append(asset_record)
        time.sleep(1)

    # --- Step 2: Identify the most likely API endpoint ---
    print("\n=== Step 2: Identifying API endpoint candidates ===")
    strong_candidates = []
    for c in report["api_candidates"]:
        lower = c.lower()
        if any(kw in lower for kw in ["/api/", "search", "business", "registry", "query"]):
            strong_candidates.append(c)
            print(f"  Candidate: {c}")

    if not strong_candidates:
        print("  No strong API endpoint candidates found in JS sources.")

    report["strong_endpoint_candidates"] = strong_candidates

    # --- Step 3: Probe the best candidate (if found and looks anonymous) ---
    # Only probe if we find a path that doesn't look like it requires auth
    probe_target = None
    for c in strong_candidates:
        lower = c.lower()
        if "search" in lower or "business" in lower or "query" in lower:
            # Skip anything that looks login-specific
            if "login" not in lower and "auth" not in lower and "token" not in lower:
                probe_target = c
                break

    if probe_target:
        full_url = BASE + probe_target if probe_target.startswith("/") else probe_target
        print(f"\n=== Step 3: Probing endpoint {full_url} ===")
        report["endpoint_probe"] = probe_endpoint(full_url)
        print(f"    → {report['endpoint_probe']['status']}  {report['endpoint_probe']['response_bytes']} bytes")
        if report["endpoint_probe"]["json_parsed"]:
            print(f"    → JSON parsed ✓")
            print(f"    → Preview: {report['endpoint_probe']['json_preview']}")
    else:
        print("\n=== Step 3: No anonymous-looking endpoint found — skipping probe ===")
        report["endpoint_probe"] = {"skipped": True, "reason": "No strong anonymous endpoint candidate identified in JS"}

    # --- Step 4: robots.txt full read ---
    print("\n=== Step 4: Reading robots.txt ===")
    report["robots"] = also_fetch_robots()
    for host, rb in report["robots"].items():
        print(f"  {host}: {rb['status']}  {len(rb['content'])} chars")
        if rb["content"]:
            print(f"    Content:\n{rb['content'][:800]}")

    # --- Step 5: Conclusions ---
    print("\n=== Step 5: Building conclusions ===")
    js_fetched = [a for a in report["js_assets"] if a["http_status"] == 200]
    api_found = bool(probe_target)
    probe_ok = (
        report["endpoint_probe"]
        and not report["endpoint_probe"].get("skipped")
        and report["endpoint_probe"].get("status") == 200
        and report["endpoint_probe"].get("json_parsed")
    )

    report["conclusions"] = {
        "js_assets_fetched": len(js_fetched),
        "js_assets_attempted": len(JS_ASSETS),
        "api_endpoint_identified": api_found,
        "anonymous_probe_succeeded": probe_ok,
        "probe_target": probe_target,
        "vr11_closeable": (
            api_found and probe_ok
        ),
        "recommended_next": (
            "VR11 can be closed — API confirmed, fields recorded."
            if probe_ok
            else (
                "JS fetched but endpoint not confirmed — DevTools session needed."
                if js_fetched
                else "JS assets not accessible — DevTools session required."
            )
        ),
    }

    # --- Write report ---
    out_path = "reports/validation_rounds/VR11_1_PEI_OCBR_JS.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Report written: {out_path}")
    print(f"  JS assets fetched: {len(js_fetched)}/{len(JS_ASSETS)}")
    print(f"  API endpoint identified: {api_found}")
    print(f"  Anonymous probe succeeded: {probe_ok}")
    print(f"  VR11 closeable: {report['conclusions']['vr11_closeable']}")
    print(f"  Recommended next: {report['conclusions']['recommended_next']}")


if __name__ == "__main__":
    main()
