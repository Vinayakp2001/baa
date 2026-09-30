"""
VR13.1 (v3) — NNI Business Registry — actual search paths probe
Confirmed from HTML nav menu:
  /business/search/community   — Search by Community (has form with community dropdown)
  /business/search/name        — Search by Business Name
  /business/search/suppliers   — Search for Suppliers (goods/services + category)
  /business/search/active      — Search by Active Date
  /business/search/number      — Search by Business Number
  /business/list               — List ALL businesses

Also confirmed:
  /index.php/node/75           — Privacy page (need full body)
  /index.php/documents         — Documents page (need full body for terms)
  robots.txt: Disallow: /search/ — that was Drupal site search, NOT business search

Key insight: GET params on /index.php/business/search differ in byte size but
POST to /search/node returns 10501b (that's the Drupal site search, not business search).
The business search uses its own sub-paths with their own forms.

Goals:
1. Fetch /business/list — the "list all businesses" endpoint (highest value)
2. Fetch /business/search/community with no params — get the community dropdown options
3. Submit community=all (or community=0) to get all Nunavut results
4. Fetch /business/search/name and try a name search
5. Fetch /business/search/suppliers — get goods/services/category dropdowns
6. Fetch /business/search/active — check effective-date range search
7. Fetch full body of /index.php/node/75 (Privacy) for reuse terms
8. Fetch full body of /index.php/documents for NNI Regulations PDF links

Run: python scripts/probe_nni_vr13_3.py
Output: reports/validation_rounds/VR13_1_NNI_V3.json
        reports/validation_rounds/VR13_1_NNI_LIST_PAGE.html
        reports/validation_rounds/VR13_1_NNI_COMMUNITY_PAGE.html
        reports/validation_rounds/VR13_1_NNI_SUPPLIER_PAGE.html
        reports/validation_rounds/VR13_1_NNI_PRIVACY_PAGE.html
"""

import json
import time
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone

BASE = "https://nni.gov.nu.ca"
RESULTS = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
    "Referer": "https://nni.gov.nu.ca/business/search",
}


def fetch(path, label=""):
    url = BASE + path if not path.startswith("http") else path
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="replace")
            print(f"  {label or path} → {r.status} ({len(body)}b)")
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  {label or path} → {e.code} ({len(body)}b)")
        return e.code, body
    except Exception as ex:
        print(f"  {label or path} → ERROR: {ex}")
        return 0, str(ex)


def post_form(path, data, label=""):
    url = BASE + path
    payload = urllib.parse.urlencode(data).encode("utf-8")
    hdrs = {**HEADERS, "Content-Type": "application/x-www-form-urlencoded"}
    req = urllib.request.Request(url, data=payload, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="replace")
            print(f"  POST {label or path} → {r.status} ({len(body)}b)")
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  POST {label or path} → {e.code} ({len(body)}b)")
        return e.code, body
    except Exception as ex:
        print(f"  POST {label or path} → ERROR: {ex}")
        return 0, str(ex)


def extract_form_info(html):
    """Extract form action, inputs, selects and their options."""
    actions = re.findall(r'<form[^>]+action=["\']([^"\']+)["\']', html, re.I)
    inputs = re.findall(r'<input[^>]+>', html, re.I)
    input_names = re.findall(r'name=["\']([^"\']+)["\']', " ".join(inputs), re.I)
    input_values = {}
    for inp in inputs:
        n = re.search(r'name=["\']([^"\']+)["\']', inp, re.I)
        v = re.search(r'value=["\']([^"\']*)["\']', inp, re.I)
        if n:
            input_values[n.group(1)] = v.group(1) if v else ""

    selects = {}
    for m in re.finditer(r'<select[^>]+name=["\']([^"\']+)["\'][^>]*>(.*?)</select>',
                         html, re.I | re.DOTALL):
        sel_name = m.group(1)
        opts = re.findall(r'<option[^>]*value=["\']([^"\']*)["\'][^>]*>\s*([^<]*)\s*</option>',
                          m.group(2), re.I)
        selects[sel_name] = opts
    return {
        "form_actions": actions,
        "input_names": list(set(input_names)),
        "input_values": input_values,
        "selects": selects,
        "select_option_counts": {k: len(v) for k, v in selects.items()},
    }


def count_records(html):
    """Rough record count from table rows and list items."""
    trs = len(re.findall(r'<tr[^>]*>', html, re.I))
    # Look for result count text patterns
    count_match = re.search(
        r'(\d+)\s+(?:result|record|business|compan)',
        html, re.I)
    text_count = int(count_match.group(1)) if count_match else None
    # Extract business links (paths like /business/view/NNN or /business/NNN)
    biz_links = re.findall(r'href=["\']([^"\']*business[^"\']+)["\']', html, re.I)
    # Pagination
    pager = re.findall(r'page=(\d+)', html)
    return {
        "tr_count": trs,
        "text_count": text_count,
        "business_link_count": len(biz_links),
        "unique_business_links": list(set(biz_links))[:20],
        "pager_pages_mentioned": sorted(set(int(p) for p in pager)),
    }


def save_html(path, body, label):
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"  Saved {label} → {path}")


# ---------------------------------------------------------------------------
# 1. /business/list — list ALL businesses
# ---------------------------------------------------------------------------
print("\n[1] /business/list — list all businesses")
s, body = fetch("/business/list", "list all")
RESULTS["list_all"] = {"status": s, "bytes": len(body)}
RESULTS["list_all"].update(extract_form_info(body))
RESULTS["list_all"].update(count_records(body))
RESULTS["list_all"]["snippet"] = body[body.find("<main"):body.find("<main")+4000] if "<main" in body else body[:4000]
save_html("reports/validation_rounds/VR13_1_NNI_LIST_PAGE.html", body, "business/list")
time.sleep(1)

# ---------------------------------------------------------------------------
# 2. /business/search/community — get the form (community dropdown)
# ---------------------------------------------------------------------------
print("\n[2] /business/search/community — community search form")
s, body = fetch("/business/search/community", "community form")
RESULTS["community_form"] = {"status": s, "bytes": len(body)}
RESULTS["community_form"].update(extract_form_info(body))
RESULTS["community_form"].update(count_records(body))
RESULTS["community_form"]["snippet"] = body[body.find("<main"):body.find("<main")+4000] if "<main" in body else body[:4000]
save_html("reports/validation_rounds/VR13_1_NNI_COMMUNITY_PAGE.html", body, "community form")

# Extract the community select options for use in next step
community_select = RESULTS["community_form"]["selects"]
print(f"  Select fields: { {k: len(v) for k,v in community_select.items()} }")
time.sleep(1)

# ---------------------------------------------------------------------------
# 3. Submit community search — try community=0 (all) and community=Iqaluit value
# ---------------------------------------------------------------------------
print("\n[3] Submitting community search (all Nunavut)")

# Identify form action and hidden fields
form_action = RESULTS["community_form"]["form_actions"][0] if RESULTS["community_form"]["form_actions"] else "/business/search/community"
hidden_vals = {k: v for k, v in RESULTS["community_form"]["input_values"].items()
               if k not in ("op",)}

# Try the Directory Summary link from the page which had:
# /business/search/community?sort=asc&order=Name&l=&edit%5Bcommunity%5D=0&op=Search
print("  Trying directory summary URL (community=0 = all Nunavut)")
s, body = fetch("/business/search/community?sort=asc&order=Name&l=&edit%5Bcommunity%5D=0&op=Search")
RESULTS["community_all_get"] = {"status": s, "bytes": len(body)}
RESULTS["community_all_get"].update(count_records(body))
RESULTS["community_all_get"]["snippet"] = body[body.find("<main"):body.find("<main")+5000] if "<main" in body else body[:5000]
time.sleep(1)

# Also try with Iqaluit (typical value might be the community name or a number)
# Find Iqaluit value from dropdown options
iqaluit_val = "Iqaluit"
for sel_name, opts in community_select.items():
    for val, label in opts:
        if "iqaluit" in label.lower():
            iqaluit_val = val
            break

print(f"  Trying community=Iqaluit (value={iqaluit_val!r})")
s, body2 = fetch(f"/business/search/community?sort=asc&order=Name&l=&edit%5Bcommunity%5D={urllib.parse.quote(iqaluit_val)}&op=Search")
RESULTS["community_iqaluit_get"] = {"status": s, "bytes": len(body2)}
RESULTS["community_iqaluit_get"].update(count_records(body2))
RESULTS["community_iqaluit_get"]["snippet"] = body2[body2.find("<main"):body2.find("<main")+3000] if "<main" in body2 else body2[:3000]
time.sleep(1)

# ---------------------------------------------------------------------------
# 4. /business/search/name — name search
# ---------------------------------------------------------------------------
print("\n[4] /business/search/name — form then submit")
s, body = fetch("/business/search/name", "name form")
RESULTS["name_form"] = {"status": s, "bytes": len(body)}
RESULTS["name_form"].update(extract_form_info(body))
RESULTS["name_form"]["snippet"] = body[body.find("<main"):body.find("<main")+3000] if "<main" in body else body[:3000]
time.sleep(1)

# Submit name search
print("  Submitting name=Arctic")
s, body = fetch("/business/search/name?edit%5Bname%5D=Arctic&op=Search")
RESULTS["name_search_arctic"] = {"status": s, "bytes": len(body)}
RESULTS["name_search_arctic"].update(count_records(body))
RESULTS["name_search_arctic"]["snippet"] = body[body.find("<main"):body.find("<main")+3000] if "<main" in body else body[:3000]
time.sleep(1)

# ---------------------------------------------------------------------------
# 5. /business/search/suppliers — supplier search (goods/services + categories)
# ---------------------------------------------------------------------------
print("\n[5] /business/search/suppliers — supplier form")
s, body = fetch("/business/search/suppliers", "supplier form")
RESULTS["supplier_form"] = {"status": s, "bytes": len(body)}
RESULTS["supplier_form"].update(extract_form_info(body))
RESULTS["supplier_form"].update(count_records(body))
RESULTS["supplier_form"]["snippet"] = body[body.find("<main"):body.find("<main")+4000] if "<main" in body else body[:4000]
save_html("reports/validation_rounds/VR13_1_NNI_SUPPLIER_PAGE.html", body, "supplier form")
print(f"  Select fields: { {k: len(v) for k,v in RESULTS['supplier_form']['selects'].items()} }")
time.sleep(1)

# ---------------------------------------------------------------------------
# 6. /business/search/active — active date search
# ---------------------------------------------------------------------------
print("\n[6] /business/search/active — active date form")
s, body = fetch("/business/search/active", "active date form")
RESULTS["active_form"] = {"status": s, "bytes": len(body)}
RESULTS["active_form"].update(extract_form_info(body))
RESULTS["active_form"]["snippet"] = body[body.find("<main"):body.find("<main")+3000] if "<main" in body else body[:3000]
time.sleep(1)

# ---------------------------------------------------------------------------
# 7. Privacy page — full body for reuse/automation terms
# ---------------------------------------------------------------------------
print("\n[7] /index.php/node/75 — Privacy page (full body)")
s, body = fetch("/index.php/node/75", "privacy")
RESULTS["privacy_page"] = {
    "status": s, "bytes": len(body),
    "full_body": body,  # keep full for terms analysis
}
save_html("reports/validation_rounds/VR13_1_NNI_PRIVACY_PAGE.html", body, "privacy")
time.sleep(0.5)

# ---------------------------------------------------------------------------
# 8. Documents page — full body (NNI Regulations PDF links)
# ---------------------------------------------------------------------------
print("\n[8] /index.php/documents — Documents listing (full body)")
s, body = fetch("/index.php/documents", "documents")
# Extract all PDF links
pdf_links = re.findall(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', body, re.I)
RESULTS["documents_page"] = {
    "status": s, "bytes": len(body),
    "pdf_links": pdf_links,
    "snippet": body[body.find("<main"):body.find("<main")+5000] if "<main" in body else body[:5000],
}
print(f"  PDF links found: {len(pdf_links)}")
for p in pdf_links[:10]:
    print(f"    {p}")
time.sleep(0.5)

# ---------------------------------------------------------------------------
# SAVE JSON (strip very long full_body before saving to keep it readable)
# ---------------------------------------------------------------------------
save_data = {k: v for k, v in RESULTS.items()}
# Truncate full privacy body in JSON (keep first 3000 chars)
if "privacy_page" in save_data and "full_body" in save_data["privacy_page"]:
    save_data["privacy_page"] = {
        **save_data["privacy_page"],
        "full_body": save_data["privacy_page"]["full_body"][:3000]
    }

save_data["generated"] = datetime.now(timezone.utc).isoformat()

with open("reports/validation_rounds/VR13_1_NNI_V3.json", "w", encoding="utf-8") as f:
    json.dump(save_data, f, indent=2, ensure_ascii=False)
print("\nJSON saved → reports/validation_rounds/VR13_1_NNI_V3.json")

# ---------------------------------------------------------------------------
# PRINT SUMMARY
# ---------------------------------------------------------------------------
print("\n=== SUMMARY ===")
print(f"business/list        : status={RESULTS['list_all']['status']} "
      f"bytes={RESULTS['list_all']['bytes']} "
      f"tr={RESULTS['list_all']['tr_count']} "
      f"biz_links={RESULTS['list_all']['business_link_count']}")
print(f"community form       : status={RESULTS['community_form']['status']} "
      f"selects={ {k:len(v) for k,v in RESULTS['community_form']['selects'].items()} }")
print(f"community all GET    : status={RESULTS['community_all_get']['status']} "
      f"bytes={RESULTS['community_all_get']['bytes']} "
      f"tr={RESULTS['community_all_get']['tr_count']} "
      f"biz_links={RESULTS['community_all_get']['business_link_count']} "
      f"text_count={RESULTS['community_all_get']['text_count']}")
print(f"community Iqaluit GET: status={RESULTS['community_iqaluit_get']['status']} "
      f"bytes={RESULTS['community_iqaluit_get']['bytes']} "
      f"tr={RESULTS['community_iqaluit_get']['tr_count']} "
      f"biz_links={RESULTS['community_iqaluit_get']['business_link_count']}")
print(f"name search Arctic   : status={RESULTS['name_search_arctic']['status']} "
      f"tr={RESULTS['name_search_arctic']['tr_count']} "
      f"biz_links={RESULTS['name_search_arctic']['business_link_count']}")
print(f"supplier form        : selects={ {k:len(v) for k,v in RESULTS['supplier_form']['selects'].items()} }")
print(f"active date form     : selects={ {k:len(v) for k,v in RESULTS['active_form']['selects'].items()} }")
print(f"privacy page         : {RESULTS['privacy_page']['bytes']}b")
print(f"PDF links found      : {len(RESULTS['documents_page']['pdf_links'])}")
print("\nDone.")
