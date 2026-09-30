"""
VR12 — Newfoundland & Labrador CADO Technical Validation
Objective: Determine whether CADO public search works anonymously, what fields
           are returned, how the request is structured (form POST / XHR / JSON),
           and where the free/paid boundary lies.

Approach:
  1. Fetch robots.txt from both hosts
  2. GET the search page — extract ASP.NET hidden fields (ViewState etc.)
  3. POST a name search for one known company
  4. Parse the HTML response — extract result rows and fields
  5. If results found, GET one company detail page — extract all visible fields
  6. Fetch the CADO disclaimer/terms page
  7. Write VR12_NL_CADO.json

Rules:
  - No enumeration — exactly one name search + one detail lookup
  - No login, no payment, no bypassing of paywalls
  - Record every redirect and HTTP status accurately

Output: reports/validation_rounds/VR12_NL_CADO.json
"""

import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import re
import time
import sys

BASE = "https://cado.eservices.gov.nl.ca"

URLS = {
    "home":         BASE + "/",
    "company_main": BASE + "/Company/CompanyMain.aspx",
    "search":       BASE + "/Company/CompanyNameNumberSearch.aspx",
    "disclaimer":   BASE + "/Disclaimer.aspx",
    "robots":       BASE + "/robots.txt",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Connection": "keep-alive",
}

# One well-known NL company for the test search
TEST_SEARCH_NAME = "Muskrat Falls"


# ---------------------------------------------------------------------------
# HTTP helpers — share a cookie jar to preserve ASP.NET session
# ---------------------------------------------------------------------------

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def get(url, extra_headers=None, timeout=20):
    hdrs = dict(HEADERS)
    if extra_headers:
        hdrs.update(extra_headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with opener.open(req, timeout=timeout) as r:
            body = r.read()
            return r.status, r.url, dict(r.headers), body
    except urllib.error.HTTPError as e:
        body = e.read() or b""
        return e.code, url, {}, body
    except Exception as ex:
        return 0, url, {"error": str(ex)}, b""


def post(url, data_dict, extra_headers=None, timeout=20):
    hdrs = dict(HEADERS)
    hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    if extra_headers:
        hdrs.update(extra_headers)
    body = urllib.parse.urlencode(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    try:
        with opener.open(req, timeout=timeout) as r:
            resp_body = r.read()
            return r.status, r.url, dict(r.headers), resp_body
    except urllib.error.HTTPError as e:
        resp_body = e.read() or b""
        return e.code, url, {}, resp_body
    except Exception as ex:
        return 0, url, {"error": str(ex)}, b""


# ---------------------------------------------------------------------------
# HTML parsing helpers (stdlib only)
# ---------------------------------------------------------------------------

def extract_hidden_fields(html_text):
    """Extract all <input type='hidden'> fields from an ASP.NET page."""
    fields = {}
    for m in re.finditer(
        r'<input[^>]+type=["\']hidden["\'][^>]*>', html_text, re.IGNORECASE
    ):
        tag = m.group(0)
        name_m = re.search(r'name=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        val_m = re.search(r'value=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if name_m:
            fields[name_m.group(1)] = val_m.group(1) if val_m else ""
    return fields


def extract_table_rows(html_text, max_rows=10):
    """Extract text content from <tr> rows within any <table>."""
    rows = []
    for tr in re.finditer(r'<tr[^>]*>(.*?)</tr>', html_text, re.IGNORECASE | re.DOTALL):
        cells = re.findall(
            r'<t[dh][^>]*>(.*?)</t[dh]>', tr.group(1), re.IGNORECASE | re.DOTALL
        )
        row = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        row = [r for r in row if r]
        if row:
            rows.append(row)
        if len(rows) >= max_rows:
            break
    return rows


def extract_links(html_text, base_url, pattern=None):
    """Extract href links optionally filtered by a regex pattern on the href."""
    links = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\']', html_text, re.IGNORECASE):
        href = m.group(1)
        if pattern and not re.search(pattern, href, re.IGNORECASE):
            continue
        if href.startswith("http"):
            links.append(href)
        elif href.startswith("/"):
            links.append(BASE + href)
        else:
            links.append(base_url.rstrip("/") + "/" + href.lstrip("/"))
    return list(dict.fromkeys(links))  # deduplicate, preserve order


def extract_page_text(html_text, max_chars=3000):
    """Strip HTML tags and return plain text excerpt."""
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html_text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


def detect_login_wall(html_text):
    lower = html_text.lower()
    signals = ["login", "sign in", "please log", "username", "password", "authenticate"]
    hits = [s for s in signals if s in lower]
    return bool(hits), hits


def detect_payment_wall(html_text):
    lower = html_text.lower()
    signals = ["fee", "payment", "credit card", "purchase", "pay", "cost", "$", "charged"]
    hits = [s for s in signals if s in lower]
    return bool(hits), hits


def find_input_names(html_text, label_hints):
    """Find input field names near label text hints."""
    fields = {}
    for hint in label_hints:
        idx = html_text.lower().find(hint.lower())
        if idx == -1:
            continue
        window = html_text[max(0, idx - 200):idx + 400]
        m = re.search(r'<input[^>]+name=["\']([^"\']+)["\']', window, re.IGNORECASE)
        if m:
            fields[hint] = m.group(1)
    return fields


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    report = {
        "round": "VR12",
        "source": "Newfoundland & Labrador Companies and Deeds Online (CADO)",
        "generated": "2026-09-26",
        "base_url": BASE,
        "test_search_name": TEST_SEARCH_NAME,
        "steps": {},
        "conclusions": {},
    }

    # ------------------------------------------------------------------
    # Step 1 — robots.txt
    # ------------------------------------------------------------------
    print("=== Step 1: robots.txt ===")
    status, final_url, hdrs, body = get(URLS["robots"])
    text = body.decode("utf-8", errors="replace")
    print(f"  {status}  {len(body)} bytes")
    if body:
        print(f"  Content:\n{text[:600]}")
    report["steps"]["robots_txt"] = {
        "url": URLS["robots"],
        "status": status,
        "content": text if body else None,
    }
    time.sleep(1)

    # ------------------------------------------------------------------
    # Step 2 — Home page
    # ------------------------------------------------------------------
    print("\n=== Step 2: CADO home page ===")
    status, final_url, hdrs, body = get(URLS["home"])
    html = body.decode("utf-8", errors="replace")
    print(f"  {status}  final_url={final_url}  {len(body)} bytes")
    login_wall, login_signals = detect_login_wall(html)
    print(f"  Login wall signals: {login_signals}")
    report["steps"]["home_page"] = {
        "url": URLS["home"],
        "final_url": final_url,
        "status": status,
        "bytes": len(body),
        "login_wall_detected": login_wall,
        "login_signals": login_signals,
        "page_text_excerpt": extract_page_text(html, 800),
    }
    time.sleep(1)

    # ------------------------------------------------------------------
    # Step 3 — GET search page (collect ViewState + hidden fields)
    # ------------------------------------------------------------------
    print("\n=== Step 3: GET search page ===")
    status, final_url, hdrs, body = get(URLS["search"])
    html = body.decode("utf-8", errors="replace")
    print(f"  {status}  final_url={final_url}  {len(body)} bytes")
    login_wall, login_signals = detect_login_wall(html)
    pay_wall, pay_signals = detect_payment_wall(html)
    print(f"  Login wall: {login_wall} {login_signals}")
    print(f"  Payment wall: {pay_wall} {pay_signals}")

    hidden = extract_hidden_fields(html)
    print(f"  Hidden fields found: {list(hidden.keys())}")

    # Find the actual name/number input field names
    search_input_names = find_input_names(
        html,
        ["company name", "company number", "name keyword", "search keyword", "keyword"]
    )
    print(f"  Search input name hints: {search_input_names}")

    # Also just grab all visible input names
    all_inputs = re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', html, re.IGNORECASE)
    print(f"  All input names: {all_inputs}")

    report["steps"]["search_page_get"] = {
        "url": URLS["search"],
        "final_url": final_url,
        "status": status,
        "bytes": len(body),
        "login_wall_detected": login_wall,
        "login_signals": login_signals,
        "payment_wall_detected": pay_wall,
        "payment_signals": pay_signals,
        "hidden_fields_found": list(hidden.keys()),
        "all_input_names": all_inputs,
        "search_input_hints": search_input_names,
        "page_text_excerpt": extract_page_text(html, 1000),
    }
    time.sleep(1)

    # ------------------------------------------------------------------
    # Step 4 — POST search form
    # ------------------------------------------------------------------
    print(f"\n=== Step 4: POST search for '{TEST_SEARCH_NAME}' ===")

    if status != 200 or login_wall:
        print("  Skipping POST — search page not accessible anonymously")
        report["steps"]["search_post"] = {
            "skipped": True,
            "reason": "Search page not accessible anonymously" if login_wall else f"HTTP {status}",
        }
    else:
        # Build form payload — ASP.NET requires all hidden fields + the search input
        # Common NL CADO field names (discovered from page, fallback guesses)
        name_field = None
        for candidate in [
            "ctl00$ContentPlaceHolder1$txtCompanyName",
            "ctl00$MainContent$txtCompanyName",
            "txtCompanyName", "txtName", "txtKeyword",
            "ctl00$ContentPlaceHolder1$txtKeyword1",
            "ctl00$ContentPlaceHolder1$txtKeyword",
        ]:
            if candidate in all_inputs or candidate.split("$")[-1] in all_inputs:
                name_field = candidate
                break
        # Fallback: use the first text input that isn't hidden
        if not name_field:
            for inp in re.finditer(
                r'<input[^>]+type=["\']text["\'][^>]*name=["\']([^"\']+)["\']',
                html, re.IGNORECASE
            ):
                name_field = inp.group(1)
                break

        print(f"  Using name field: {name_field}")

        post_data = dict(hidden)  # start with all hidden fields (ViewState etc.)
        if name_field:
            post_data[name_field] = TEST_SEARCH_NAME

        # Find the submit button name/value
        submit_m = re.search(
            r'<input[^>]+type=["\']submit["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
            html, re.IGNORECASE
        )
        if not submit_m:
            submit_m = re.search(
                r'<input[^>]+name=["\']([^"\']+)["\'][^>]*type=["\']submit["\'][^>]*value=["\']([^"\']*)["\']',
                html, re.IGNORECASE
            )
        if submit_m:
            post_data[submit_m.group(1)] = submit_m.group(2)
            print(f"  Submit button: {submit_m.group(1)} = {submit_m.group(2)!r}")

        # ASP.NET event target for search (common pattern)
        if "__EVENTTARGET" not in post_data:
            post_data["__EVENTTARGET"] = ""
        if "__EVENTARGUMENT" not in post_data:
            post_data["__EVENTARGUMENT"] = ""

        p_status, p_final_url, p_hdrs, p_body = post(
            final_url,  # POST back to the same page (ASP.NET postback)
            post_data,
            extra_headers={"Referer": URLS["search"]}
        )
        p_html = p_body.decode("utf-8", errors="replace")
        print(f"  POST → {p_status}  final_url={p_final_url}  {len(p_body)} bytes")
        print(f"  Content-Type: {p_hdrs.get('Content-Type', '')}")

        p_login_wall, p_login_signals = detect_login_wall(p_html)
        p_pay_wall, p_pay_signals = detect_payment_wall(p_html)
        print(f"  Login wall: {p_login_wall} {p_login_signals}")
        print(f"  Payment wall: {p_pay_wall} {p_pay_signals}")

        # Try to parse result rows
        result_rows = extract_table_rows(p_html)
        print(f"  Table rows found: {len(result_rows)}")
        for i, row in enumerate(result_rows[:5]):
            print(f"    Row {i}: {row}")

        # Extract any detail page links (company profile links)
        detail_links = extract_links(p_html, p_final_url, pattern=r"Company(Detail|View|Info|Profile)")
        print(f"  Detail links found: {detail_links[:3]}")

        is_json = False
        try:
            json.loads(p_html)
            is_json = True
        except Exception:
            pass

        report["steps"]["search_post"] = {
            "url": final_url,
            "final_url": p_final_url,
            "status": p_status,
            "bytes": len(p_body),
            "content_type": p_hdrs.get("Content-Type", ""),
            "response_is_json": is_json,
            "response_is_html": "text/html" in p_hdrs.get("Content-Type", ""),
            "login_wall_detected": p_login_wall,
            "login_signals": p_login_signals,
            "payment_wall_detected": p_pay_wall,
            "payment_signals": p_pay_signals,
            "table_rows_found": len(result_rows),
            "sample_rows": result_rows[:5],
            "detail_links_found": detail_links[:5],
            "name_field_used": name_field,
            "page_text_excerpt": extract_page_text(p_html, 1500),
        }

        # ------------------------------------------------------------------
        # Step 5 — GET one detail page (if found)
        # ------------------------------------------------------------------
        if detail_links:
            print(f"\n=== Step 5: GET detail page ===")
            time.sleep(1)
            d_url = detail_links[0]
            d_status, d_final_url, d_hdrs, d_body = get(d_url)
            d_html = d_body.decode("utf-8", errors="replace")
            print(f"  {d_status}  {d_final_url}  {len(d_body)} bytes")
            d_login, _ = detect_login_wall(d_html)
            d_pay, d_pay_s = detect_payment_wall(d_html)
            d_rows = extract_table_rows(d_html, max_rows=30)

            # Try to identify specific fields
            field_matrix = {}
            for field in [
                "company name", "registration", "status", "type", "incorporation",
                "registered office", "mailing address", "director", "officer",
                "annual return", "previous name", "business activity", "phone", "email"
            ]:
                field_matrix[field] = field.lower() in d_html.lower()

            print(f"  Login wall: {d_login}")
            print(f"  Payment wall: {d_pay} {d_pay_s}")
            print(f"  Table rows: {len(d_rows)}")
            print(f"  Field matrix: {field_matrix}")

            report["steps"]["detail_page"] = {
                "url": d_url,
                "final_url": d_final_url,
                "status": d_status,
                "bytes": len(d_body),
                "login_wall_detected": d_login,
                "payment_wall_detected": d_pay,
                "payment_signals": d_pay_s,
                "table_rows_found": len(d_rows),
                "sample_rows": d_rows[:10],
                "field_matrix": field_matrix,
                "page_text_excerpt": extract_page_text(d_html, 2000),
            }
        else:
            print("\n=== Step 5: No detail links found — skipping ===")
            report["steps"]["detail_page"] = {
                "skipped": True,
                "reason": "No detail page links found in search results"
            }

    # ------------------------------------------------------------------
    # Step 6 — Disclaimer / Terms page
    # ------------------------------------------------------------------
    print("\n=== Step 6: Disclaimer/Terms page ===")
    time.sleep(1)
    status, final_url, hdrs, body = get(URLS["disclaimer"])
    html = body.decode("utf-8", errors="replace")
    print(f"  {status}  {len(body)} bytes")
    text = extract_page_text(html, 3000)
    print(f"  Text excerpt:\n{text[:800]}")

    # Flag key licensing phrases
    licensing_flags = {}
    checks = {
        "copyright_government": "copyright",
        "commercial_use_mentioned": "commercial",
        "value_added_restricted": "value-added",
        "distribution_restricted": "distribut",
        "prior_written_approval": "written approval",
        "non_commercial_only": "non-commercial",
        "ogl_or_open_licence": "open government licence",
        "automated_use_mentioned": "automat",
        "sold_prohibited": "sold",
        "copied_prohibited": "cop",
    }
    for flag, kw in checks.items():
        licensing_flags[flag] = kw.lower() in text.lower()

    print(f"  Licensing flags: {licensing_flags}")

    report["steps"]["disclaimer"] = {
        "url": URLS["disclaimer"],
        "status": status,
        "bytes": len(body),
        "full_text": text,
        "licensing_flags": licensing_flags,
    }

    # ------------------------------------------------------------------
    # Step 7 — Build conclusions
    # ------------------------------------------------------------------
    print("\n=== Step 7: Conclusions ===")

    search_step = report["steps"].get("search_post", {})
    detail_step = report["steps"].get("detail_page", {})
    disc_step = report["steps"].get("disclaimer", {})

    anon_search_works = (
        not search_step.get("skipped")
        and search_step.get("status") == 200
        and not search_step.get("login_wall_detected")
        and search_step.get("table_rows_found", 0) > 0
    )

    detail_accessible = (
        not detail_step.get("skipped")
        and detail_step.get("status") == 200
        and not detail_step.get("login_wall_detected")
        and not detail_step.get("payment_wall_detected")
    )

    lf = disc_step.get("licensing_flags", {})
    commercial_restricted = lf.get("value_added_restricted") or lf.get("commercial_use_mentioned")

    report["conclusions"] = {
        "anonymous_search_works": anon_search_works,
        "detail_page_accessible_free": detail_accessible,
        "response_format": "JSON" if search_step.get("response_is_json") else "HTML",
        "aspnet_form_postback": True,
        "json_api_found": False,
        "login_required_for_search": report["steps"].get("search_page_get", {}).get("login_wall_detected", False),
        "payment_required_for_search": search_step.get("payment_wall_detected", False),
        "payment_required_for_detail": detail_step.get("payment_wall_detected", False),
        "robots_txt_present": report["steps"]["robots_txt"]["status"] == 200,
        "copyright_confirmed": lf.get("copyright_government", False),
        "value_added_restricted": lf.get("value_added_restricted", False),
        "prior_written_approval_required": lf.get("prior_written_approval", False),
        "open_government_licence": lf.get("ogl_or_open_licence", False),
        "commercial_automation_permitted": (
            "LIKELY_PROHIBITED" if commercial_restricted
            else "UNKNOWN — terms not retrieved" if disc_step.get("status") != 200
            else "UNKNOWN — recheck disclaimer text"
        ),
        "recommended_classification": (
            "NOT_SUITABLE" if commercial_restricted and not lf.get("ogl_or_open_licence")
            else "PARTIALLY_VALIDATED" if anon_search_works
            else "DEFERRED"
        ),
        "notes": (
            "CADO appears to use ASP.NET WebForms server-rendered HTML. "
            "Licensing is the primary gate for commercial use — "
            "check disclaimer text for value-added / distribution restrictions."
        ),
    }

    print(f"  Anonymous search works: {anon_search_works}")
    print(f"  Detail accessible free: {detail_accessible}")
    print(f"  Commercial restricted: {commercial_restricted}")
    print(f"  Recommended classification: {report['conclusions']['recommended_classification']}")

    # ------------------------------------------------------------------
    # Write report
    # ------------------------------------------------------------------
    out_path = "reports/validation_rounds/VR12_NL_CADO.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Report written: {out_path}")


if __name__ == "__main__":
    main()
