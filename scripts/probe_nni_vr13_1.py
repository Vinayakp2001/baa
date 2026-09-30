"""
VR13.1 — NNI Business Registry Profiling
Target: nni.gov.nu.ca public business search (no auth required)
Goal: establish total records, pagination, fields, effective-date range,
      community coverage, supplier search classification, and reuse terms.

Run: python scripts/probe_nni_vr13_1.py
Output: reports/validation_rounds/VR13_1_NNI_PROFILE.json
        reports/validation_rounds/VR13_1_NNI_PROFILE.md
"""

import json
import time
import urllib.request
import urllib.parse
import re
from datetime import datetime

BASE_URL = "https://nni.gov.nu.ca"
OUTPUT_JSON = "reports/validation_rounds/VR13_1_NNI_PROFILE.json"
OUTPUT_MD   = "reports/validation_rounds/VR13_1_NNI_PROFILE.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
}

results = {}


def fetch(url, label, extra_headers=None):
    """Fetch a URL and return (status, body_text, body_bytes_len)."""
    hdrs = {**HEADERS, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return r.status, body.decode("utf-8", errors="replace"), len(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body, len(body)
    except Exception as ex:
        return 0, str(ex), 0


def fetch_json(url, label):
    """Fetch a URL expecting JSON; return (status, parsed_obj_or_None, raw_text)."""
    hdrs = {**HEADERS, "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            text = body.decode("utf-8", errors="replace")
            try:
                return r.status, json.loads(text), text
            except Exception:
                return r.status, None, text
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, None, body
    except Exception as ex:
        return 0, None, str(ex)


# ---------------------------------------------------------------------------
# STEP 1 — Home page
# ---------------------------------------------------------------------------
print("[1] Fetching NNI home page ...")
status, body, blen = fetch(BASE_URL + "/", "home")
results["home"] = {"status": status, "bytes": blen}
print(f"    status={status} bytes={blen}")

# Extract all internal links from home page
links = re.findall(r'href=["\']([^"\']+)["\']', body)
internal = sorted({l for l in links if "nni.gov.nu.ca" in l or l.startswith("/")})
results["home_internal_links"] = internal
print(f"    internal links found: {len(internal)}")

# ---------------------------------------------------------------------------
# STEP 2 — Terms / Privacy page
# ---------------------------------------------------------------------------
print("[2] Checking terms/privacy ...")
for path in ["/privacy-bulletins", "/nni-regulations", "/privacy", "/terms"]:
    s, b, bl = fetch(BASE_URL + path, "terms")
    results[f"terms_{path}"] = {"status": s, "bytes": bl,
                                 "snippet": b[:800] if s == 200 else ""}
    print(f"    {path} → {s} ({bl} bytes)")
    time.sleep(0.5)

# ---------------------------------------------------------------------------
# STEP 3 — Business list page (all-Nunavut community search)
# ---------------------------------------------------------------------------
print("[3] Fetching community=all-Nunavut business list ...")
# Try common patterns for a community/all listing
community_urls = [
    BASE_URL + "/nni-business-search",
    BASE_URL + "/business-search",
    BASE_URL + "/en/nni-business-search",
    BASE_URL + "/search/business",
    BASE_URL + "/search",
]
list_status, list_body, list_blen = 0, "", 0
list_url_used = None
for cu in community_urls:
    s, b, bl = fetch(cu, "community_list")
    print(f"    {cu} → {s} ({bl} bytes)")
    if s == 200 and bl > 1000:
        list_status, list_body, list_blen = s, b, bl
        list_url_used = cu
        break
    time.sleep(0.5)

results["business_list_page"] = {
    "url_tried": list_url_used,
    "status": list_status,
    "bytes": list_blen,
    "snippet": list_body[:1500] if list_status == 200 else "",
}

# ---------------------------------------------------------------------------
# STEP 4 — Try XHR/JSON search endpoint discovery
# ---------------------------------------------------------------------------
print("[4] Probing for JSON search endpoints ...")
# Look for data- attributes or script src in body that hint at API paths
api_hints = re.findall(r'(?:fetch|ajax|xhr|url)[^"\']*["\']([^"\']+)["\']', list_body, re.I)
results["api_hints_from_page"] = list(set(api_hints))[:20]
print(f"    API hints found: {len(results['api_hints_from_page'])}")

# Try common JSON endpoint patterns
json_endpoints = [
    "/api/businesses",
    "/api/business/search",
    "/en/api/businesses",
    "/businesses.json",
    "/search/results",
    "/search/results.json",
    "/nni-business-search/results",
    "/views/ajax",
]
json_results = {}
for ep in json_endpoints:
    url = BASE_URL + ep
    s, obj, raw = fetch_json(url, ep)
    json_results[ep] = {
        "status": s,
        "is_json": obj is not None,
        "snippet": raw[:500] if s != 404 else "404",
    }
    print(f"    {ep} → {s} (json={obj is not None})")
    time.sleep(0.5)
results["json_endpoint_probes"] = json_results

# ---------------------------------------------------------------------------
# STEP 5 — Community search via GET params
# ---------------------------------------------------------------------------
print("[5] Trying community search with GET params ...")
community_param_urls = [
    BASE_URL + "/nni-business-search?community=all",
    BASE_URL + "/nni-business-search?community=Iqaluit",
    BASE_URL + "/search?type=community&community=Iqaluit",
    BASE_URL + "/business-search?community=Iqaluit",
]
community_results = {}
for cu in community_param_urls:
    s, b, bl = fetch(cu, "community_param")
    # Extract table rows / list items as a rough record count
    rows = re.findall(r'<tr[^>]*>', b)
    li_items = re.findall(r'<li[^>]*class=["\'][^"\']*business[^"\']*["\']', b, re.I)
    community_results[cu] = {
        "status": s,
        "bytes": bl,
        "tr_count": len(rows),
        "business_li_count": len(li_items),
        "snippet": b[:1000] if s == 200 else "",
    }
    print(f"    {cu} → {s} ({bl}b, tr={len(rows)}, business_li={len(li_items)})")
    time.sleep(0.8)
results["community_search_params"] = community_results

# ---------------------------------------------------------------------------
# STEP 6 — Business name search
# ---------------------------------------------------------------------------
print("[6] Trying business name search ...")
name_search_urls = [
    BASE_URL + "/nni-business-search?name=Arctic",
    BASE_URL + "/business-search?name=Arctic",
    BASE_URL + "/search?name=Arctic",
    BASE_URL + "/search?q=Arctic",
    BASE_URL + "/nni-business-search?search=Arctic",
]
name_results = {}
for nu in name_search_urls:
    s, b, bl = fetch(nu, "name_search")
    rows = re.findall(r'<tr[^>]*>', b)
    name_results[nu] = {
        "status": s,
        "bytes": bl,
        "tr_count": len(rows),
        "snippet": b[:1000] if s == 200 else "",
    }
    print(f"    {nu} → {s} ({bl}b, tr={len(rows)})")
    time.sleep(0.8)
results["name_search"] = name_results

# ---------------------------------------------------------------------------
# STEP 7 — Supplier search
# ---------------------------------------------------------------------------
print("[7] Trying supplier search endpoint ...")
supplier_urls = [
    BASE_URL + "/search-for-suppliers",
    BASE_URL + "/supplier-search",
    BASE_URL + "/nni-business-search?type=supplier",
    BASE_URL + "/search?type=supplier",
]
supplier_results = {}
for su in supplier_urls:
    s, b, bl = fetch(su, "supplier")
    supplier_results[su] = {
        "status": s,
        "bytes": bl,
        "snippet": b[:1000] if s == 200 else "",
    }
    print(f"    {su} → {s} ({bl}b)")
    time.sleep(0.8)
results["supplier_search"] = supplier_results

# ---------------------------------------------------------------------------
# STEP 8 — Robots.txt
# ---------------------------------------------------------------------------
print("[8] Fetching robots.txt ...")
s, b, bl = fetch(BASE_URL + "/robots.txt", "robots")
results["robots_txt"] = {"status": s, "bytes": bl, "body": b if s == 200 else ""}
print(f"    robots.txt → {s} ({bl} bytes)")

# ---------------------------------------------------------------------------
# STEP 9 — Sitemap (helps find actual search paths)
# ---------------------------------------------------------------------------
print("[9] Fetching sitemap.xml ...")
s, b, bl = fetch(BASE_URL + "/sitemap.xml", "sitemap")
results["sitemap"] = {"status": s, "bytes": bl, "body": b[:3000] if s == 200 else ""}
print(f"    sitemap.xml → {s} ({bl} bytes)")
if s == 200:
    locs = re.findall(r'<loc>([^<]+)</loc>', b)
    results["sitemap_locs"] = locs
    print(f"    sitemap locs: {len(locs)}")

# ---------------------------------------------------------------------------
# SAVE JSON
# ---------------------------------------------------------------------------
results["generated"] = datetime.utcnow().isoformat() + "Z"
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nJSON saved → {OUTPUT_JSON}")

# ---------------------------------------------------------------------------
# GENERATE MD REPORT SKELETON
# ---------------------------------------------------------------------------
home_ok = results["home"]["status"] == 200
robots_body = results["robots_txt"].get("body", "")
sitemap_locs = results.get("sitemap_locs", [])

# Summarise JSON endpoint findings
json_hits = [ep for ep, v in results["json_endpoint_probes"].items()
             if v["status"] not in (404, 0) and v["status"] < 400]

# Best community result
best_community = max(
    results["community_search_params"].items(),
    key=lambda x: x[1]["bytes"],
    default=(None, {})
)
best_name = max(
    results["name_search"].items(),
    key=lambda x: x[1]["bytes"],
    default=(None, {})
)
best_supplier = max(
    results["supplier_search"].items(),
    key=lambda x: x[1]["bytes"],
    default=(None, {})
)

md = f"""# VR13.1 — NNI Business Registry Profiling

Generated: `{datetime.utcnow().strftime('%Y-%m-%d')}`
Script: `scripts/probe_nni_vr13_1.py`
JSON: `reports/validation_rounds/VR13_1_NNI_PROFILE.json`

---

## 1. Portal Reachability

| Check | Result |
|---|---|
| Home page (nni.gov.nu.ca) | {'✅ ' + str(results['home']['bytes']) + ' bytes' if home_ok else '❌ status ' + str(results['home']['status'])} |
| robots.txt | {'✅ ' + str(results['robots_txt']['bytes']) + ' bytes' if results['robots_txt']['status'] == 200 else '⚠️ status ' + str(results['robots_txt']['status'])} |
| sitemap.xml | {'✅ ' + str(len(sitemap_locs)) + ' locs found' if results['sitemap']['status'] == 200 else '⚠️ status ' + str(results['sitemap']['status'])} |

### robots.txt content
```
{robots_body[:600] if robots_body else '(not retrieved)'}
```

---

## 2. Search Endpoint Discovery

### JSON/XHR endpoints probed
| Endpoint | Status | JSON? |
|---|---|---|
""" + \
"\n".join(
    f"| `{ep}` | {v['status']} | {'✅' if v['is_json'] else '❌'} |"
    for ep, v in results["json_endpoint_probes"].items()
) + \
f"""

JSON endpoints returning non-404: `{json_hits if json_hits else 'none found'}`

### Sitemap paths (if retrieved)
```
{chr(10).join(sitemap_locs[:30]) if sitemap_locs else '(sitemap not available)'}
```

---

## 3. Community Search Results

| URL attempted | Status | Bytes | TR count |
|---|---|---|---|
""" + \
"\n".join(
    f"| `{u}` | {v['status']} | {v['bytes']} | {v['tr_count']} |"
    for u, v in results["community_search_params"].items()
) + \
f"""

Best result: `{best_community[0]}`
Bytes: {best_community[1].get('bytes', 0)} | TR rows: {best_community[1].get('tr_count', 0)}

**Page snippet:**
```html
{best_community[1].get('snippet', '(none)')[:800]}
```

---

## 4. Business Name Search Results

| URL attempted | Status | Bytes | TR count |
|---|---|---|---|
""" + \
"\n".join(
    f"| `{u}` | {v['status']} | {v['bytes']} | {v['tr_count']} |"
    for u, v in results["name_search"].items()
) + \
f"""

Best result: `{best_name[0]}`
Bytes: {best_name[1].get('bytes', 0)} | TR rows: {best_name[1].get('tr_count', 0)}

**Page snippet:**
```html
{best_name[1].get('snippet', '(none)')[:800]}
```

---

## 5. Supplier Search Results

| URL attempted | Status | Bytes |
|---|---|---|
""" + \
"\n".join(
    f"| `{u}` | {v['status']} | {v['bytes']} |"
    for u, v in results["supplier_search"].items()
) + \
f"""

Best result: `{best_supplier[0]}`

**Page snippet:**
```html
{best_supplier[1].get('snippet', '(none)')[:800]}
```

---

## 6. Terms / Licensing

"""

for path_key, val in results.items():
    if path_key.startswith("terms_") and isinstance(val, dict):
        snippet = val.get("snippet", "")
        if snippet:
            md += f"### `{path_key.replace('terms_', '')}`\n"
            md += f"Status: {val['status']} | Bytes: {val['bytes']}\n\n"
            md += f"```\n{snippet[:600]}\n```\n\n"

md += """
---

## 7. Findings Summary

**TODO — complete after reviewing output above:**

| Question | Answer |
|---|---|
| Total record count (all-Nunavut) | ❓ |
| Pagination mechanism | ❓ |
| Page size | ❓ |
| Fields in list view | ❓ |
| Effective date range (earliest / latest) | ❓ |
| Community coverage (how many communities) | ❓ |
| Active-only or includes historical? | ❓ |
| Duplicate businesses present? | ❓ |
| Downloadable list? | ❓ |
| HTML or JSON/XHR response | ❓ |
| Detail page URL pattern | ❓ |
| Detail page fields (address/phone/email) | ❓ |
| Supplier search categories available | ❓ |
| Reuse / automation terms | ❓ |

---

## 8. Classification

**Pending completion of findings above.**

Candidate roles if public search confirmed and terms permit:
- Class A (discovery) — if full business list enumerable
- Class B (fresh/change) — effective date field enables new-business detection
- Class C (enrichment) — if address/phone fields present in detail

"""

with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write(md)
print(f"MD saved → {OUTPUT_MD}")
print("\nDone.")
