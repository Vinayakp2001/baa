"""
VR13.1 (v2) — NNI Business Registry — correct path probe
Key finding from v1: real business search is at /index.php/business/search
robots.txt: /search/ is disallowed (Drupal site search), but /index.php/business/search is NOT disallowed.
Site is Drupal 10.

Goals:
1. Fetch /index.php/business/search — confirm it loads, inspect form fields and any embedded results
2. Try POST/GET variations to trigger community list, name search, supplier search
3. Fetch robots.txt lines relevant to /index.php/business/ to confirm no block
4. Fetch /index.php/documents and /index.php/node/2143 — likely terms/regulations pages
5. Dump full HTML of business search page for manual inspection

Run: python scripts/probe_nni_vr13_2.py
Output: reports/validation_rounds/VR13_1_NNI_V2.json
        reports/validation_rounds/VR13_1_NNI_BUSINESS_PAGE.html  (raw page dump)
"""

import json
import time
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone

BASE_URL = "https://nni.gov.nu.ca"
OUTPUT_JSON  = "reports/validation_rounds/VR13_1_NNI_V2.json"
OUTPUT_HTML  = "reports/validation_rounds/VR13_1_NNI_BUSINESS_PAGE.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
}

results = {}


def fetch(url, extra_headers=None):
    hdrs = {**HEADERS, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            return r.status, body.decode("utf-8", errors="replace"), len(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body, len(body)
    except Exception as ex:
        return 0, str(ex), 0


def post(url, data_dict, extra_headers=None):
    hdrs = {**HEADERS, "Content-Type": "application/x-www-form-urlencoded",
            **(extra_headers or {})}
    body = urllib.parse.urlencode(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = r.read()
            return r.status, resp.decode("utf-8", errors="replace"), len(resp)
    except urllib.error.HTTPError as e:
        resp = e.read().decode("utf-8", errors="replace")
        return e.code, resp, len(resp)
    except Exception as ex:
        return 0, str(ex), 0


# ---------------------------------------------------------------------------
# 1. Main business search page
# ---------------------------------------------------------------------------
print("[1] Fetching /index.php/business/search ...")
s, body, blen = fetch(BASE_URL + "/index.php/business/search")
results["business_search_page"] = {"status": s, "bytes": blen}
print(f"    status={s} bytes={blen}")

# Save full HTML for manual inspection
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(body)
print(f"    Full HTML saved → {OUTPUT_HTML}")

# Extract form fields
form_actions = re.findall(r'<form[^>]+action=["\']([^"\']+)["\']', body, re.I)
form_inputs  = re.findall(r'<input[^>]+>', body, re.I)
form_selects = re.findall(r'<select[^>]+name=["\']([^"\']+)["\']', body, re.I)
input_names  = re.findall(r'name=["\']([^"\']+)["\']', " ".join(form_inputs), re.I)
input_values = re.findall(r'value=["\']([^"\']*)["\']', " ".join(form_inputs), re.I)

results["business_search_page"]["form_actions"] = form_actions
results["business_search_page"]["input_names"]  = list(set(input_names))
results["business_search_page"]["select_names"] = form_selects
results["business_search_page"]["snippet"]      = body[:3000]

print(f"    form actions: {form_actions}")
print(f"    input names:  {list(set(input_names))}")
print(f"    select names: {form_selects}")

# Extract all option values from selects (community list, categories, etc.)
select_options = {}
for sel_match in re.finditer(
        r'<select[^>]+name=["\']([^"\']+)["\'][^>]*>(.*?)</select>',
        body, re.I | re.DOTALL):
    sel_name = sel_match.group(1)
    opts = re.findall(r'<option[^>]*value=["\']([^"\']*)["\'][^>]*>([^<]*)</option>',
                      sel_match.group(2), re.I)
    select_options[sel_name] = opts
results["business_search_page"]["select_options"] = select_options
print(f"    select options: { {k: len(v) for k, v in select_options.items()} }")

# Look for JSON data embedded in page (Drupal drupalSettings etc.)
drupal_settings = re.findall(r'drupalSettings\s*=\s*(\{.{0,2000}\})', body)
results["business_search_page"]["drupal_settings_snippet"] = drupal_settings[:2] if drupal_settings else []

# Extract any XHR/fetch/ajax patterns
xhr_hints = re.findall(r'(?:url|action|endpoint|path)["\']?\s*[:=]\s*["\']([^"\']+)["\']', body, re.I)
results["business_search_page"]["xhr_hints"] = list(set(xhr_hints))[:20]

time.sleep(1)

# ---------------------------------------------------------------------------
# 2. Try alternate path variants
# ---------------------------------------------------------------------------
print("[2] Trying path variants ...")
variants = [
    "/index.php/business/search",           # already done above
    "/business/search",
    "/index.php/en/business/search",
    "/en/business/search",
    "/index.php/business",
    "/index.php/business-search",
]
variant_results = {}
for v in variants[1:]:  # skip first — already fetched
    s, b, bl = fetch(BASE_URL + v)
    variant_results[v] = {"status": s, "bytes": bl,
                           "title": re.search(r'<title>([^<]+)</title>', b, re.I).group(1)
                                    if re.search(r'<title>([^<]+)</title>', b, re.I) else ""}
    print(f"    {v} → {s} ({bl}b) title={variant_results[v]['title']!r}")
    time.sleep(0.6)
results["path_variants"] = variant_results

# ---------------------------------------------------------------------------
# 3. GET params on the confirmed /index.php/business/search path
# ---------------------------------------------------------------------------
print("[3] Trying GET params on /index.php/business/search ...")
base = BASE_URL + "/index.php/business/search"
get_probes = [
    "?community=Iqaluit",
    "?community=all",
    "?community=",
    "?name=Arctic",
    "?type=community",
    "?type=name",
    "?type=supplier",
    "?search_api_fulltext=Arctic",
    "?field_community=Iqaluit",
]
get_results = {}
for qstr in get_probes:
    url = base + qstr
    s, b, bl = fetch(url)
    rows = len(re.findall(r'<tr[^>]*>', b))
    links_in_page = re.findall(r'href=["\']([^"\']+business[^"\']*)["\']', b, re.I)
    get_results[qstr] = {
        "status": s,
        "bytes": bl,
        "tr_count": rows,
        "business_links_count": len(links_in_page),
        "differs_from_base": bl != blen,
    }
    print(f"    {qstr} → {s} ({bl}b, tr={rows}, biz_links={len(links_in_page)}, "
          f"differs={bl != blen})")
    time.sleep(0.6)
results["get_probes"] = get_results

# ---------------------------------------------------------------------------
# 4. POST to the form action (if found) or to /index.php/business/search
# ---------------------------------------------------------------------------
print("[4] Attempting POST submissions ...")
post_target = form_actions[0] if form_actions else "/index.php/business/search"
if not post_target.startswith("http"):
    post_target = BASE_URL + post_target

post_payloads = [
    {"type": "community", "community": "Iqaluit"},
    {"type": "community", "community": ""},
    {"type": "name",      "name": "Arctic"},
    {"type": "supplier",  "community": ""},
    {"search_api_fulltext": "Arctic"},
    {"field_community_target_id": "Iqaluit"},
]
post_results = {}
for payload in post_payloads:
    key = urllib.parse.urlencode(payload)
    s, b, bl = post(post_target, payload)
    rows = len(re.findall(r'<tr[^>]*>', b))
    post_results[key] = {
        "status": s,
        "bytes": bl,
        "tr_count": rows,
        "differs_from_base": bl != blen,
    }
    print(f"    POST {key} → {s} ({bl}b, tr={rows}, differs={bl != blen})")
    time.sleep(0.8)
results["post_probes"] = post_results

# ---------------------------------------------------------------------------
# 5. Documents page — likely terms/regulations
# ---------------------------------------------------------------------------
print("[5] Fetching /index.php/documents ...")
s, b, bl = fetch(BASE_URL + "/index.php/documents")
results["documents_page"] = {
    "status": s, "bytes": bl,
    "snippet": b[:2000] if s == 200 else "",
    "links": re.findall(r'href=["\']([^"\']+)["\']', b)[:30],
}
print(f"    /index.php/documents → {s} ({bl}b)")
time.sleep(0.5)

# ---------------------------------------------------------------------------
# 6. Node 2143 (home page linked to this — likely an important content page)
# ---------------------------------------------------------------------------
print("[6] Fetching /index.php/node/2143 ...")
s, b, bl = fetch(BASE_URL + "/index.php/node/2143")
results["node_2143"] = {
    "status": s, "bytes": bl,
    "title": re.search(r'<title>([^<]+)</title>', b, re.I).group(1)
             if re.search(r'<title>([^<]+)</title>', b, re.I) else "",
    "snippet": b[:2000] if s == 200 else "",
}
print(f"    /index.php/node/2143 → {s} ({bl}b) "
      f"title={results['node_2143']['title']!r}")
time.sleep(0.5)

# ---------------------------------------------------------------------------
# 7. Node 75 (also linked from home)
# ---------------------------------------------------------------------------
print("[7] Fetching /index.php/node/75 ...")
s, b, bl = fetch(BASE_URL + "/index.php/node/75")
results["node_75"] = {
    "status": s, "bytes": bl,
    "title": re.search(r'<title>([^<]+)</title>', b, re.I).group(1)
             if re.search(r'<title>([^<]+)</title>', b, re.I) else "",
    "snippet": b[:2000] if s == 200 else "",
}
print(f"    /index.php/node/75 → {s} ({bl}b) "
      f"title={results['node_75']['title']!r}")
time.sleep(0.5)

# ---------------------------------------------------------------------------
# 8. Drupal Views JSON endpoint pattern (common for Drupal business directories)
# ---------------------------------------------------------------------------
print("[8] Probing Drupal Views JSON patterns ...")
views_endpoints = [
    "/index.php/business/search?_format=json",
    "/business/search?_format=json",
    "/index.php/api/business",
    "/api/v1/business",
    "/jsonapi/node/business",
    "/index.php/views/business_search",
    "/views/business_search/page_1?_format=json",
    "/index.php/views/business/page_1?_format=json",
]
views_results = {}
for ep in views_endpoints:
    s, b, bl = fetch(BASE_URL + ep,
                     extra_headers={"Accept": "application/json, */*"})
    is_json = False
    try:
        json.loads(b)
        is_json = True
    except Exception:
        pass
    views_results[ep] = {
        "status": s, "bytes": bl, "is_json": is_json,
        "snippet": b[:300] if s != 404 else "404",
    }
    print(f"    {ep} → {s} ({bl}b, json={is_json})")
    time.sleep(0.5)
results["drupal_views_json"] = views_results

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------
results["generated"] = datetime.now(timezone.utc).isoformat()
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nJSON saved → {OUTPUT_JSON}")
print("Full HTML saved → " + OUTPUT_HTML)
print("\nKey findings to check:")
print(f"  - Business search page status: {results['business_search_page']['status']}")
print(f"  - Form actions: {results['business_search_page']['form_actions']}")
print(f"  - Select fields (potential community/category dropdowns): "
      f"{ {k: len(v) for k, v in results['business_search_page'].get('select_options', {}).items()} }")
print(f"  - Any GET probe that differs from base: "
      f"{ [k for k,v in results['get_probes'].items() if v['differs_from_base']] }")
print(f"  - Any POST that differs from base: "
      f"{ [k for k,v in results['post_results'].items() if v['differs_from_base']] }"
      if "post_results" in results else "  - POST results: see JSON")
print("Done.")
