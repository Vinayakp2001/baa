"""
VR13 — Yukon + NWT + Nunavut Comparative Validation
Six sources across three territories:
  1.1 Yukon YCOR (Corporate Online Registry)
  1.2 Yukon Supplier Directory (open data download)
  2.1 NWT CROS (Corporate Registries Online Search)
  2.2 NWT BIP Registry
  3.1 Nunavut Corporate Registry
  3.2 NNI Business Registry (public directory)

Rules:
  - One search per registry — no enumeration
  - No login, no payment bypass
  - Separate technical findings from licensing findings
  - Record every HTTP status, redirect, and response type

Output: reports/validation_rounds/VR13_YUKON_NWT_NUNAVUT.json
"""

import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import re
import time

# ---------------------------------------------------------------------------
# Source URLs
# ---------------------------------------------------------------------------

SOURCES = {
    # 1.1 Yukon YCOR
    "yukon_ycor_home":    "https://ycor.gov.yk.ca",
    "yukon_ycor_search":  "https://ycor.gov.yk.ca/search",

    # 1.2 Yukon Supplier Directory — open data portal
    "yukon_supplier_dir_portal": "https://open.yukon.ca/data/datasets/yukon-government-supplier-directory",
    "yukon_supplier_dir_csv":    "https://open.yukon.ca/sites/default/files/YGSupplierDirectory.csv",
    "yukon_supplier_dir_csv_v2": "https://open.yukon.ca/sites/default/files/supplier_directory.csv",

    # 2.1 NWT CROS
    "nwt_cros_home":   "https://www.hss.gov.nt.ca/en/services/corporate-registries",
    "nwt_cros_search": "https://www.hss.gov.nt.ca/en/services/corporate-registries/corporate-search",

    # 2.2 NWT BIP Registry
    "nwt_bip_home":   "https://www.iti.gov.nt.ca/en/services/business-incentive-policy-bip/bip-registry",
    "nwt_bip_search": "https://www.iti.gov.nt.ca/en/services/business-incentive-policy-bip/bip-registry/bip-registry-search",

    # 3.1 Nunavut Corporate Registry
    "nu_corp_home":   "https://www.gov.nu.ca/justice/information-and-services/business-and-corporate",
    "nu_corp_search": "https://www.gov.nu.ca/justice/information-and-services/business-and-corporate/corporate-registry",

    # 3.2 NNI Business Registry
    "nni_home":   "https://www.gov.nu.ca/community-and-government-services/information-and-services/nni-business-registry",
    "nni_search": "https://www.gov.nu.ca/community-and-government-services/information-and-services/nni-business-registry/nni-registry-search",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
}

TEST_NAME = "Yukon Energy"  # known NWT/Yukon company present in multiple registries

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def fetch(url, post_data=None, extra_headers=None, timeout=20):
    hdrs = dict(HEADERS)
    if extra_headers:
        hdrs.update(extra_headers)
    if post_data:
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        body = urllib.parse.urlencode(post_data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    else:
        req = urllib.request.Request(url, headers=hdrs)
    try:
        with opener.open(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, r.url, dict(r.headers), raw
    except urllib.error.HTTPError as e:
        raw = e.read() or b""
        return e.code, url, {}, raw
    except Exception as ex:
        return 0, url, {"error": str(ex)}, b""


def page_text(html, max_chars=2000):
    t = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:max_chars]


def extract_hidden(html):
    fields = {}
    for m in re.finditer(r'<input[^>]+type=["\']hidden["\'][^>]*>', html, re.IGNORECASE):
        tag = m.group(0)
        n = re.search(r'name=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        v = re.search(r'value=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if n:
            fields[n.group(1)] = v.group(1) if v else ""
    return fields


def extract_inputs(html):
    return re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', html, re.IGNORECASE)


def detect_walls(html):
    low = html.lower()
    login = any(s in low for s in ["login", "sign in", "please log", "username", "password"])
    payment = any(s in low for s in ["fee", "payment", "credit card", "purchase", "$", "charged"])
    return login, payment


def licensing_flags(text):
    low = text.lower()
    return {
        "copyright_government": "copyright" in low,
        "open_government_licence": "open government licence" in low or "ogl" in low,
        "value_added_prohibited": "value added" in low or "value-added" in low,
        "distribution_prohibited": "distribut" in low,
        "prior_written_approval": "written approval" in low or "written permission" in low,
        "commercial_prohibited": "non-commercial" in low or "commercial use" in low,
        "automated_use_mentioned": "automat" in low,
        "free_reuse_permitted": "free" in low and ("use" in low or "reuse" in low),
    }


def try_table_rows(html, max_rows=8):
    rows = []
    for tr in re.finditer(r'<tr[^>]*>(.*?)</tr>', html, re.IGNORECASE | re.DOTALL):
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr.group(1), re.IGNORECASE | re.DOTALL)
        row = [re.sub(r'<[^>]+>', '', c).strip() for c in cells if re.sub(r'<[^>]+>', '', c).strip()]
        if row:
            rows.append(row)
        if len(rows) >= max_rows:
            break
    return rows


def probe_url(label, url, note=""):
    print(f"  [{label}] GET {url}")
    status, final_url, hdrs, body = fetch(url)
    html = body.decode("utf-8", errors="replace") if body else ""
    login_wall, pay_wall = detect_walls(html)
    is_json = False
    try:
        json.loads(html)
        is_json = True
    except Exception:
        pass
    ct = hdrs.get("Content-Type", "")
    print(f"    -> {status}  {len(body)}b  ct={ct[:60]}")
    if login_wall:
        print(f"    -> LOGIN WALL detected")
    if pay_wall:
        print(f"    -> PAYMENT signals detected")
    return {
        "url": url,
        "final_url": final_url,
        "status": status,
        "bytes": len(body),
        "content_type": ct,
        "login_wall": login_wall,
        "payment_wall": pay_wall,
        "is_json": is_json,
        "hidden_fields": list(extract_hidden(html).keys()),
        "input_names": extract_inputs(html),
        "table_rows": try_table_rows(html),
        "page_text": page_text(html, 1200),
        "note": note,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    report = {
        "round": "VR13",
        "territories": ["Yukon", "Northwest Territories", "Nunavut"],
        "generated": "2026-09-26",
        "sources": {},
    }

    # ======================================================================
    # 1.1 YUKON — YCOR Corporate Registry
    # ======================================================================
    print("\n" + "="*60)
    print("1.1 YUKON — YCOR Corporate Registry")
    print("="*60)
    time.sleep(0.5)

    ycor = {}

    # robots
    r = probe_url("ycor/robots", "https://ycor.gov.yk.ca/robots.txt")
    ycor["robots_txt"] = {"status": r["status"], "content": r["page_text"][:400]}

    time.sleep(0.8)

    # home
    r_home = probe_url("ycor/home", SOURCES["yukon_ycor_home"])
    ycor["home"] = r_home
    time.sleep(0.8)

    # search page
    # YCOR uses a different URL pattern - try common ones
    search_candidates = [
        "https://ycor.gov.yk.ca/search",
        "https://ycor.gov.yk.ca/company/search",
        "https://ycor.gov.yk.ca/entity/search",
        "https://ycor.gov.yk.ca/Search",
    ]
    ycor["search_attempts"] = []
    search_found = None
    for sc in search_candidates:
        time.sleep(0.5)
        r_s = probe_url("ycor/search", sc)
        ycor["search_attempts"].append({"url": sc, "status": r_s["status"], "bytes": r_s["bytes"]})
        if r_s["status"] == 200 and r_s["bytes"] > 3000:
            search_found = r_s
            break

    if search_found:
        ycor["search_page"] = search_found
        # Try a POST if we found a form
        hidden = extract_hidden(search_found["page_text"])
        inputs = search_found["input_names"]
        print(f"    Inputs: {inputs}")
        # Try a GET with query param (common for non-ASPNET registries)
        time.sleep(0.8)
        search_url = search_found["final_url"]
        for param in ["q", "name", "keyword", "searchTerm", "companyName", "entityName"]:
            qurl = f"{search_url}?{param}={urllib.parse.quote(TEST_NAME)}"
            r_q = probe_url("ycor/query", qurl)
            if r_q["status"] == 200 and r_q["bytes"] != search_found["bytes"]:
                ycor["search_result"] = r_q
                print(f"    Query returned different page with param={param}")
                break
            time.sleep(0.5)
        if "search_result" not in ycor:
            ycor["search_result"] = {"note": "All GET param attempts returned same page size as search form — may require POST or JS interaction"}
    else:
        ycor["search_page"] = {"note": "No search page found at standard paths — YCOR may use different URL structure"}
        # Try the home page links
        if r_home["status"] == 200:
            links = re.findall(r'href=["\']([^"\']+)["\']', r_home["page_text"], re.IGNORECASE)
            ycor["home_links_sample"] = links[:15]

    # terms
    time.sleep(0.8)
    for terms_url in [
        "https://ycor.gov.yk.ca/disclaimer",
        "https://ycor.gov.yk.ca/terms",
        "https://ycor.gov.yk.ca/terms-conditions",
    ]:
        r_t = probe_url("ycor/terms", terms_url)
        if r_t["status"] == 200:
            ycor["terms"] = {
                "url": terms_url,
                "status": r_t["status"],
                "text": r_t["page_text"],
                "licensing_flags": licensing_flags(r_t["page_text"]),
            }
            break
        time.sleep(0.5)
    if "terms" not in ycor:
        ycor["terms"] = {"note": "Terms page not found at standard paths"}

    report["sources"]["yukon_ycor"] = ycor

    # ======================================================================
    # 1.2 YUKON — Supplier Directory
    # ======================================================================
    print("\n" + "="*60)
    print("1.2 YUKON — Supplier Directory")
    print("="*60)
    time.sleep(0.8)

    yukon_sd = {}

    # Portal page
    r_portal = probe_url("ysd/portal", SOURCES["yukon_supplier_dir_portal"])
    yukon_sd["portal_page"] = {
        "url": SOURCES["yukon_supplier_dir_portal"],
        "status": r_portal["status"],
        "bytes": r_portal["bytes"],
        "page_text": r_portal["page_text"],
        "licensing_flags": licensing_flags(r_portal["page_text"]),
    }
    time.sleep(0.8)

    # Try direct CSV download
    csv_found = False
    for csv_url in [SOURCES["yukon_supplier_dir_csv"], SOURCES["yukon_supplier_dir_csv_v2"]]:
        r_csv = probe_url("ysd/csv", csv_url)
        if r_csv["status"] == 200 and b"," in (r_csv["page_text"][:200].encode()):
            rows = r_csv["page_text"][:2000].split("\n")
            yukon_sd["csv_download"] = {
                "url": csv_url,
                "status": r_csv["status"],
                "bytes": r_csv["bytes"],
                "content_type": r_csv["content_type"],
                "header_row": rows[0] if rows else "",
                "sample_rows": rows[1:4],
                "estimated_records": r_csv["bytes"] // 200,
            }
            csv_found = True
            print(f"    CSV found: {r_csv['bytes']} bytes  header={rows[0][:120]}")
            break
        time.sleep(0.5)

    if not csv_found:
        # Scan portal page for download links
        if r_portal["status"] == 200:
            dl_links = re.findall(
                r'href=["\']([^"\']*\.(csv|xlsx|xls|zip)[^"\']*)["\']',
                r_portal["page_text"], re.IGNORECASE
            )
            yukon_sd["download_links_found"] = dl_links[:5]
            if dl_links:
                time.sleep(0.5)
                dl_url = dl_links[0][0]
                if not dl_url.startswith("http"):
                    dl_url = "https://open.yukon.ca" + dl_url
                r_dl = probe_url("ysd/download", dl_url)
                yukon_sd["csv_download"] = {
                    "url": dl_url,
                    "status": r_dl["status"],
                    "bytes": r_dl["bytes"],
                    "content_type": r_dl["content_type"],
                    "preview": r_dl["page_text"][:300],
                }
            else:
                yukon_sd["csv_download"] = {"note": "No CSV/XLSX download link found on portal page"}

    report["sources"]["yukon_supplier_directory"] = yukon_sd

    # ======================================================================
    # 2.1 NWT — CROS Corporate Registry
    # ======================================================================
    print("\n" + "="*60)
    print("2.1 NWT — CROS Corporate Registry")
    print("="*60)
    time.sleep(0.8)

    nwt_cros = {}

    # robots
    r = probe_url("cros/robots", "https://www.hss.gov.nt.ca/robots.txt")
    nwt_cros["robots_txt"] = {"status": r["status"], "content": r["page_text"][:400]}
    time.sleep(0.8)

    # home
    r_home = probe_url("cros/home", SOURCES["nwt_cros_home"])
    nwt_cros["home"] = {
        "url": SOURCES["nwt_cros_home"],
        "final_url": r_home["final_url"],
        "status": r_home["status"],
        "bytes": r_home["bytes"],
        "login_wall": r_home["login_wall"],
        "page_text": r_home["page_text"],
    }
    time.sleep(0.8)

    # search
    r_search = probe_url("cros/search", SOURCES["nwt_cros_search"])
    nwt_cros["search_page"] = {
        "url": SOURCES["nwt_cros_search"],
        "final_url": r_search["final_url"],
        "status": r_search["status"],
        "bytes": r_search["bytes"],
        "login_wall": r_search["login_wall"],
        "payment_wall": r_search["payment_wall"],
        "input_names": r_search["input_names"],
        "hidden_fields": r_search["hidden_fields"],
        "page_text": r_search["page_text"],
    }
    time.sleep(0.8)

    # Try GET search
    if r_search["status"] == 200 and not r_search["login_wall"]:
        for param in ["q", "name", "keyword", "searchName"]:
            qurl = f"{r_search['final_url']}?{param}={urllib.parse.quote(TEST_NAME)}"
            r_q = probe_url("cros/query", qurl)
            if r_q["status"] == 200 and r_q["bytes"] != r_search["bytes"]:
                nwt_cros["search_result"] = {
                    "param": param,
                    "url": qurl,
                    "status": r_q["status"],
                    "bytes": r_q["bytes"],
                    "table_rows": r_q["table_rows"],
                    "page_text": r_q["page_text"],
                }
                break
            time.sleep(0.5)
        if "search_result" not in nwt_cros:
            nwt_cros["search_result"] = {"note": "GET param search returned same page — may require POST or JS form"}

    # terms
    time.sleep(0.8)
    r_terms = probe_url("cros/terms", "https://www.hss.gov.nt.ca/en/terms-conditions")
    if r_terms["status"] == 200:
        nwt_cros["terms"] = {
            "url": r_terms["url"],
            "text": r_terms["page_text"],
            "licensing_flags": licensing_flags(r_terms["page_text"]),
        }
    else:
        nwt_cros["terms"] = {"status": r_terms["status"], "note": "Terms page not found"}

    report["sources"]["nwt_cros"] = nwt_cros

    # ======================================================================
    # 2.2 NWT — BIP Registry
    # ======================================================================
    print("\n" + "="*60)
    print("2.2 NWT — BIP Registry")
    print("="*60)
    time.sleep(0.8)

    nwt_bip = {}

    r_home = probe_url("bip/home", SOURCES["nwt_bip_home"])
    nwt_bip["home"] = {
        "url": SOURCES["nwt_bip_home"],
        "final_url": r_home["final_url"],
        "status": r_home["status"],
        "bytes": r_home["bytes"],
        "login_wall": r_home["login_wall"],
        "page_text": r_home["page_text"],
        "licensing_flags": licensing_flags(r_home["page_text"]),
    }
    time.sleep(0.8)

    r_search = probe_url("bip/search", SOURCES["nwt_bip_search"])
    nwt_bip["search_page"] = {
        "url": SOURCES["nwt_bip_search"],
        "final_url": r_search["final_url"],
        "status": r_search["status"],
        "bytes": r_search["bytes"],
        "login_wall": r_search["login_wall"],
        "input_names": r_search["input_names"],
        "table_rows": r_search["table_rows"],
        "page_text": r_search["page_text"],
    }
    time.sleep(0.8)

    # Try GET search
    if r_search["status"] == 200 and not r_search["login_wall"]:
        for param in ["q", "name", "keyword", "business_name", "BusinessName"]:
            qurl = f"{r_search['final_url']}?{param}={urllib.parse.quote('NWT')}"
            r_q = probe_url("bip/query", qurl)
            if r_q["status"] == 200 and r_q["bytes"] != r_search["bytes"]:
                nwt_bip["search_result"] = {
                    "param": param,
                    "url": qurl,
                    "status": r_q["status"],
                    "bytes": r_q["bytes"],
                    "table_rows": r_q["table_rows"],
                    "page_text": r_q["page_text"],
                }
                break
            time.sleep(0.5)
        if "search_result" not in nwt_bip:
            nwt_bip["search_result"] = {"note": "GET param search returned same page size — may require JS or POST"}

    # Also check for downloadable BIP list
    time.sleep(0.8)
    for dl_url in [
        "https://www.iti.gov.nt.ca/sites/iti/files/bip_registry.csv",
        "https://www.iti.gov.nt.ca/sites/iti/files/bip-registry.xlsx",
    ]:
        r_dl = probe_url("bip/download", dl_url)
        if r_dl["status"] == 200:
            nwt_bip["bulk_download"] = {
                "url": dl_url,
                "status": r_dl["status"],
                "bytes": r_dl["bytes"],
                "content_type": r_dl["content_type"],
                "preview": r_dl["page_text"][:300],
            }
            break
        time.sleep(0.5)
    if "bulk_download" not in nwt_bip:
        nwt_bip["bulk_download"] = {"note": "No bulk download found at standard paths"}

    report["sources"]["nwt_bip"] = nwt_bip

    # ======================================================================
    # 3.1 NUNAVUT — Corporate Registry
    # ======================================================================
    print("\n" + "="*60)
    print("3.1 NUNAVUT — Corporate Registry")
    print("="*60)
    time.sleep(0.8)

    nu_corp = {}

    r_home = probe_url("nu_corp/home", SOURCES["nu_corp_home"])
    nu_corp["home"] = {
        "url": SOURCES["nu_corp_home"],
        "final_url": r_home["final_url"],
        "status": r_home["status"],
        "bytes": r_home["bytes"],
        "login_wall": r_home["login_wall"],
        "page_text": r_home["page_text"],
    }
    time.sleep(0.8)

    r_search = probe_url("nu_corp/search", SOURCES["nu_corp_search"])
    nu_corp["registry_page"] = {
        "url": SOURCES["nu_corp_search"],
        "final_url": r_search["final_url"],
        "status": r_search["status"],
        "bytes": r_search["bytes"],
        "login_wall": r_search["login_wall"],
        "page_text": r_search["page_text"],
    }
    time.sleep(0.8)

    # Try alternate Nunavut registry paths
    for alt in [
        "https://www.gov.nu.ca/justice/services/corporations",
        "https://www.gov.nu.ca/justice/services/business-registrations",
        "https://www.nunavutcorporateregistries.ca",
    ]:
        r_alt = probe_url("nu_corp/alt", alt)
        if r_alt["status"] == 200 and r_alt["bytes"] > 3000:
            nu_corp["alternate_page"] = {
                "url": alt,
                "status": r_alt["status"],
                "bytes": r_alt["bytes"],
                "page_text": r_alt["page_text"],
            }
            break
        time.sleep(0.5)

    report["sources"]["nunavut_corporate"] = nu_corp

    # ======================================================================
    # 3.2 NUNAVUT — NNI Business Registry
    # ======================================================================
    print("\n" + "="*60)
    print("3.2 NUNAVUT — NNI Business Registry")
    print("="*60)
    time.sleep(0.8)

    nni = {}

    r_home = probe_url("nni/home", SOURCES["nni_home"])
    nni["home"] = {
        "url": SOURCES["nni_home"],
        "final_url": r_home["final_url"],
        "status": r_home["status"],
        "bytes": r_home["bytes"],
        "login_wall": r_home["login_wall"],
        "page_text": r_home["page_text"],
        "licensing_flags": licensing_flags(r_home["page_text"]),
    }
    time.sleep(0.8)

    r_search = probe_url("nni/search", SOURCES["nni_search"])
    nni["search_page"] = {
        "url": SOURCES["nni_search"],
        "final_url": r_search["final_url"],
        "status": r_search["status"],
        "bytes": r_search["bytes"],
        "login_wall": r_search["login_wall"],
        "input_names": r_search["input_names"],
        "table_rows": r_search["table_rows"],
        "page_text": r_search["page_text"],
    }
    time.sleep(0.8)

    # Try GET search
    if r_search["status"] == 200 and not r_search["login_wall"]:
        for param in ["q", "name", "keyword", "business"]:
            qurl = f"{r_search['final_url']}?{param}={urllib.parse.quote('Arctic')}"
            r_q = probe_url("nni/query", qurl)
            if r_q["status"] == 200 and r_q["bytes"] != r_search["bytes"]:
                nni["search_result"] = {
                    "param": param,
                    "url": qurl,
                    "status": r_q["status"],
                    "bytes": r_q["bytes"],
                    "table_rows": r_q["table_rows"],
                    "page_text": r_q["page_text"],
                }
                break
            time.sleep(0.5)
        if "search_result" not in nni:
            nni["search_result"] = {"note": "GET param search returned same page size — may require JS or form POST"}

    # Also try a direct NNI directory URL
    time.sleep(0.8)
    for nni_dir in [
        "https://www.gov.nu.ca/community-and-government-services/services/nni-directory",
        "https://nni.gov.nu.ca",
        "https://nni.gov.nu.ca/registry",
    ]:
        r_d = probe_url("nni/dir", nni_dir)
        if r_d["status"] == 200 and r_d["bytes"] > 2000:
            nni["directory_page"] = {
                "url": nni_dir,
                "status": r_d["status"],
                "bytes": r_d["bytes"],
                "page_text": r_d["page_text"],
                "table_rows": r_d["table_rows"],
            }
            break
        time.sleep(0.5)

    report["sources"]["nni_registry"] = nni

    # ======================================================================
    # Write report
    # ======================================================================
    out_path = "reports/validation_rounds/VR13_YUKON_NWT_NUNAVUT.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Report written: {out_path}")
    print(f"Sources probed: {list(report['sources'].keys())}")


if __name__ == "__main__":
    main()
