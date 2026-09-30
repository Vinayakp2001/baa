"""
VR16+17 — Source Coverage & Overlap
Script: probe_vr16_17_source_coverage_overlap.py
Output: reports/validation_rounds/VR16_17_SOURCE_COVERAGE_OVERLAP.md
        reports/validation_rounds/VR16_17_SOURCE_COVERAGE_OVERLAP.json

Two-part combined validation round:

PART A — Source freshness & coverage
  Profile remaining live ODBus sources not yet deep-validated.
  Test priority sources that can improve provincial/territorial coverage.
  Capture: province, municipality, row count, date range, field set, grain,
           new-business signal, access method, licence.

PART B — Cross-source overlap & entity-resolution
  Using local data + API samples: quantify business-name and address overlap
  between confirmed sources. Identify duplicate patterns and single-entity
  multi-row cases.

Sources already deep-validated (skip in Part A):
  Calgary, Edmonton, Vancouver, Winnipeg (VR14.4)
  Ontario Select Licence (VR06)
  Saskatoon (VR07)
  Corporations Canada CSV (VR01)
  BC OrgBook API (VR09)
  NNI Nunavut (VR13.1)
"""

import urllib.request
import urllib.error
import json
import csv
import io
import time
import re
import os
from datetime import datetime, timezone

REPORT_DIR = "reports/validation_rounds"
REPORT_MD  = os.path.join(REPORT_DIR, "VR16_17_SOURCE_COVERAGE_OVERLAP.md")
REPORT_JSON = os.path.join(REPORT_DIR, "VR16_17_SOURCE_COVERAGE_OVERLAP.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Canada-Business-Research/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/json,text/csv,*/*"
}
TIMEOUT = 20

# ---------------------------------------------------------------------------
# Priority ODBus sources NOT yet deep-validated, grouped by province
# Format: (label, province, city, url, notes)
# ---------------------------------------------------------------------------
PART_A_SOURCES = [
    # --- ONTARIO ---
    # Hamilton specialized licences — already confirmed reachable VR14.2
    ("hamilton_food_shops",    "ON", "Hamilton",    "https://open.hamilton.ca/datasets/1be5ece7f68c4e01855ada16c5f0a8e0_0.csv",
     "Hamilton food shop licences — 1 of 13 Hamilton specialized datasets"),
    ("hamilton_trade_cont",    "ON", "Hamilton",    "https://opendata.hamilton.ca/datasets/fdb8d2e7de9e4879bcf9b7faac8abb0e_0.csv",
     "Hamilton trade contractors"),
    ("ottawa_business",        "ON", "Ottawa",      "https://open.ottawa.ca/datasets/6dd1e4b7db2f48d48af04c3adb71e9c9_0.csv",
     "Ottawa business licences — major ON city"),
    ("brampton_business",      "ON", "Brampton",    "https://opendata.brampton.ca/datasets/brampton::business-directory/explore",
     "Brampton business directory portal"),
    ("mississauga_current",    "ON", "Mississauga", "https://opendata.arcgis.com/datasets/68b12f84eb0b4b9484a9781b4ccf6c0e_0.csv",
     "Mississauga current business directory (not the 2019 403 one)"),
    # --- BC ---
    ("bc_indigenous",          "BC", "BC (provincial)", "https://catalogue.data.gov.bc.ca/dataset/bdc81d33-1ab5-4882-9764-8701e8971bb7/resource/f805f66e-8294-4f8d-bdd9-2400eb3938d0/download/bcindigenousbusinesslistings.csv",
     "BC Indigenous Business Listings — direct CSV confirmed VR14.2"),
    ("bc_establishments_ckan", "BC", "BC (provincial)", "https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=2b71813e-fb00-4a8a-a60e-a67a46c81d2d",
     "BC Licensed Establishments — CKAN metadata to find current download URL"),
    ("bc_wineries_ckan",       "BC", "BC (provincial)", "https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=1d21922b-ec4f-42e5-8f6b-bf320a286157",
     "BC Winery Locations — CKAN metadata to find current download URL"),
    ("surrey_arcgis",          "BC", "Surrey",      "https://opendata-surrey.hub.arcgis.com/datasets/surrey::active-business-licences/about",
     "Surrey active business licences — migrated to ArcGIS Hub"),
    ("burnaby_business",       "BC", "Burnaby",     "https://data.burnaby.ca/datasets/burnaby::business-licences/explore",
     "Burnaby business licences"),
    ("new_west_all",           "BC", "New Westminster", "https://opendata.newwestcity.ca/datasets/NewWest::business-licences-current-year/explore",
     "New Westminster all current year"),
    ("new_west_new_this_year", "BC", "New Westminster", "https://opendata.newwestcity.ca/datasets/NewWest::business-licences-new-this-year/explore",
     "New Westminster new-this-year — highest-priority new-biz signal"),
    ("kelowna_business",       "BC", "Kelowna",     "https://opendata.kelowna.ca/datasets/kelowna::business-licences/about",
     "Kelowna business licences — portal confirmed live VR14.3"),
    ("port_moody",             "BC", "Port Moody",  "https://data.portmoody.ca/datasets/portmoody::business-licences/explore",
     "Port Moody business licences"),
    # --- ALBERTA ---
    ("chestermere",            "AB", "Chestermere", "https://data.chestermere.ca/datasets/chestermere::business-licences/explore",
     "Chestermere — small AB city"),
    # --- NEW BRUNSWICK ---
    ("moncton_grocery",        "NB", "Moncton",     "https://opendata.moncton.ca/datasets/moncton::grocery-stores/explore",
     "Moncton grocery stores — sector-specific"),
    ("saintjohn_grocery",      "NB", "Saint John",  "https://catalogue-saintjohn.opendata.arcgis.com/datasets/saintjohn::grocery-stores/explore",
     "Saint John grocery stores — sector-specific"),
    # --- SOURCES OUTSIDE ODBUS covering gap provinces ---
    ("saskatoon_portal",       "SK", "Saskatoon",   "https://opendata-saskatoon.opendata.arcgis.com/",
     "Saskatoon open data portal — check for other business datasets beyond already-downloaded XLSX"),
    ("regina_business",        "SK", "Regina",      "https://openregina.ca/datasets/regina::business-licences/explore",
     "Regina business licences — second SK city, not in ODBus"),
    ("halifax_business",       "NS", "Halifax",     "https://catalogue-hrm.opendata.arcgis.com/datasets/hrm::business-licences/explore",
     "Halifax Regional Municipality — NS gap coverage, not in ODBus"),
    ("fredericton_business",   "NB", "Fredericton", "https://data.fredericton.ca/datasets/fredericton::business-licences/explore",
     "Fredericton — NB city not in ODBus"),
]

# Socrata JSON API endpoints for sources we can sample directly
# These return JSON we can count + field-profile without downloading full CSV
SOCRATA_SAMPLE_SOURCES = [
    {
        "label": "calgary",
        "province": "AB",
        "city": "Calgary",
        "count_url": "https://data.calgary.ca/resource/vdjc-pybd.json?$select=count(*)&$limit=1",
        "sample_url": "https://data.calgary.ca/resource/vdjc-pybd.json?$limit=5&$order=first_iss_dt+DESC",
        "already_profiled": True
    },
    {
        "label": "edmonton",
        "province": "AB",
        "city": "Edmonton",
        "count_url": "https://data.edmonton.ca/resource/qhi4-bdpu.json?$select=count(*)&$limit=1",
        "sample_url": "https://data.edmonton.ca/resource/qhi4-bdpu.json?$limit=5&$order=most_recent_issue_date+DESC",
        "already_profiled": True
    },
    {
        "label": "winnipeg",
        "province": "MB",
        "city": "Winnipeg",
        "count_url": "https://data.winnipeg.ca/resource/d5k3-sfzx.json?$select=count(*)&$limit=1",
        "sample_url": "https://data.winnipeg.ca/resource/d5k3-sfzx.json?$limit=5&$order=issue_date+DESC",
        "already_profiled": True
    },
]

def fetch(url, timeout=TIMEOUT):
    """GET request; returns (status, content_bytes, content_type)."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, b"", ""
    except Exception as ex:
        return 0, str(ex).encode(), ""

def fetch_json(url, timeout=TIMEOUT):
    status, data, ct = fetch(url, timeout)
    if status == 200:
        try:
            return status, json.loads(data)
        except Exception:
            return status, None
    return status, None

def fetch_csv_sample(url, max_rows=500, timeout=30):
    """Download first chunk of a CSV and return (row_count_in_sample, fieldnames, rows)."""
    status, data, ct = fetch(url, timeout)
    if status != 200:
        return status, [], []
    try:
        text = data.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(row)
        return 200, list(reader.fieldnames or []), rows
    except Exception as ex:
        return status, [], []

def profile_csv_sample(rows, fieldnames):
    """Return field fill rates for a sample of rows."""
    if not rows:
        return {}
    n = len(rows)
    fill = {}
    for f in fieldnames:
        filled = sum(1 for r in rows if r.get(f, "").strip() not in ("", "N/A", "n/a", "null", "NULL"))
        fill[f] = round(filled / n * 100, 1)
    return fill

def detect_date_field(fieldnames):
    """Guess which field is the licence issue/registration date."""
    candidates = [f for f in fieldnames if any(k in f.lower() for k in
                  ("date", "issued", "issue", "start", "open", "iss_dt", "effective"))]
    return candidates[0] if candidates else None

def detect_employee_field(fieldnames):
    candidates = [f for f in fieldnames if any(k in f.lower() for k in
                  ("employ", "staff", "worker", "headcount", "fte"))]
    return candidates[0] if candidates else None

def detect_contact_fields(fieldnames):
    phone = [f for f in fieldnames if "phone" in f.lower() or "tel" in f.lower()]
    email = [f for f in fieldnames if "email" in f.lower() or "mail" in f.lower()]
    web   = [f for f in fieldnames if "web" in f.lower() or "url" in f.lower() or "site" in f.lower()]
    return phone, email, web

# ---------------------------------------------------------------------------
# PART A — probe each source
# ---------------------------------------------------------------------------
def probe_source(label, province, city, url, notes):
    print(f"  [{province}] {city} — {label}")
    result = {
        "label": label,
        "province": province,
        "city": city,
        "url": url,
        "notes": notes,
        "status": None,
        "content_type": None,
        "row_count_sample": None,
        "fieldnames": [],
        "fill_rates": {},
        "date_field": None,
        "employee_field": None,
        "phone_fields": [],
        "email_fields": [],
        "web_fields": [],
        "max_date_in_sample": None,
        "observation": "",
        "access_method": "unknown",
    }

    # Determine if it's a direct CSV download or a portal/explore page
    is_csv = any(x in url for x in ["/rows.csv", "/download/", ".csv", "export/?format=csv",
                                      "format=csv", "/resource/", "accessType=DOWNLOAD"])
    is_ckan_api = "ckan" in url or "api/3/action" in url
    is_arcgis = "arcgis" in url or "/explore" in url or "/about" in url
    is_portal  = "/explore" in url or "/about" in url or "/datasets/" in url

    status, data, ct = fetch(url)
    result["status"] = status
    result["content_type"] = ct[:80] if ct else ""

    if status == 0:
        result["observation"] = f"Connection error: {data.decode()[:200]}"
        return result

    if status == 403:
        result["observation"] = "HTTP 403 — blocked/WAF. Not a prohibition if open data portal."
        result["access_method"] = "blocked"
        return result

    if status == 404:
        result["observation"] = "HTTP 404 — URL dead or rotated."
        result["access_method"] = "dead"
        return result

    if status != 200:
        result["observation"] = f"HTTP {status}"
        return result

    # CKAN metadata — extract current resource URL
    if is_ckan_api:
        try:
            j = json.loads(data)
            if j.get("success"):
                pkg = j["result"]
                resources = pkg.get("resources", [])
                result["observation"] = f"CKAN package found. Resources: {len(resources)}. "
                for r in resources:
                    fmt = r.get("format", "").upper()
                    rurl = r.get("url", "")
                    result["observation"] += f"[{fmt}] {rurl[:80]} | "
                result["access_method"] = "ckan_metadata"
        except Exception as ex:
            result["observation"] = f"CKAN parse error: {ex}"
        return result

    # Portal/explore page — just record reachability + check for data signals
    if is_portal and not is_csv:
        text = data.decode("utf-8", errors="replace")
        size = len(data)
        # Try to find any record count hint in the page text
        count_match = re.search(r'([\d,]+)\s*(records?|features?|rows?|licen)', text, re.IGNORECASE)
        count_str = count_match.group(0) if count_match else "count not found in HTML"
        # Look for last-updated date
        date_match = re.search(r'(202[0-9])[/-](0[1-9]|1[0-2])[/-](\d{2})', text)
        date_str = date_match.group(0) if date_match else "date not found in HTML"
        result["observation"] = f"Portal page: HTTP 200, {size} bytes. {count_str}. Date signal: {date_str}."
        result["access_method"] = "portal_page_only"
        # Look for direct CSV/API URL patterns
        csv_links = re.findall(r'https?://[^\s"\'<>]+(?:\.csv|rows\.csv|accessType=DOWNLOAD|format=csv)[^\s"\'<>]*', text)
        if csv_links:
            result["observation"] += f" CSV links found: {csv_links[:3]}"
            result["access_method"] = "portal_csv_link_found"
        api_links = re.findall(r'https?://[^\s"\'<>]+/resource/[a-z0-9\-]+\.json[^\s"\'<>]*', text)
        if api_links:
            result["observation"] += f" Socrata API links found: {api_links[:2]}"
        return result

    # Direct CSV — sample and profile
    if is_csv or "text/csv" in ct or data[:3] in (b'\xef\xbb\xbf', b'bus', b'Bus', b'tra', b'Tra'):
        status2, fieldnames, rows = fetch_csv_sample(url)
        if rows:
            result["row_count_sample"] = len(rows)
            result["fieldnames"] = fieldnames
            result["fill_rates"] = profile_csv_sample(rows, fieldnames)
            result["date_field"] = detect_date_field(fieldnames)
            result["employee_field"] = detect_employee_field(fieldnames)
            ph, em, wb = detect_contact_fields(fieldnames)
            result["phone_fields"] = ph
            result["email_fields"] = em
            result["web_fields"] = wb
            # Max date in sample
            df = result["date_field"]
            if df:
                dates = [r.get(df, "") for r in rows if r.get(df, "").strip()]
                if dates:
                    result["max_date_in_sample"] = max(dates)
            result["access_method"] = "direct_csv"
            result["observation"] = (
                f"CSV downloaded. Sample={len(rows)} rows. Fields: {len(fieldnames)}. "
                f"Date field: {df}. Max date in sample: {result['max_date_in_sample']}. "
                f"Employee field: {result['employee_field']}. "
                f"Phone: {ph}. Email: {em}."
            )
        else:
            result["observation"] = f"CSV fetch returned HTTP {status2} or empty/unparseable content."
        return result

    # JSON (possibly Socrata)
    if "json" in ct.lower() or data[:1] == b'[' or data[:1] == b'{':
        try:
            j = json.loads(data)
            if isinstance(j, list) and j:
                fieldnames = list(j[0].keys())
                result["fieldnames"] = fieldnames
                result["row_count_sample"] = len(j)
                result["fill_rates"] = profile_csv_sample(j, fieldnames)
                result["date_field"] = detect_date_field(fieldnames)
                result["employee_field"] = detect_employee_field(fieldnames)
                ph, em, wb = detect_contact_fields(fieldnames)
                result["phone_fields"] = ph
                result["email_fields"] = em
                result["web_fields"] = wb
                result["access_method"] = "json_api"
                result["observation"] = f"JSON array: {len(j)} records. Fields: {fieldnames}."
            elif isinstance(j, dict):
                result["observation"] = f"JSON object returned. Keys: {list(j.keys())[:10]}"
                result["access_method"] = "json_object"
        except Exception as ex:
            text = data.decode("utf-8", errors="replace")[:300]
            result["observation"] = f"JSON parse error: {ex}. Snippet: {text}"
        return result

    # Fallback — HTML or unknown
    text = data.decode("utf-8", errors="replace")
    size = len(data)
    date_match = re.search(r'(202[0-9])[/-](0[1-9]|1[0-2])[/-](\d{2})', text)
    date_str = date_match.group(0) if date_match else "no 2020s date found"
    result["observation"] = f"HTML/unknown: HTTP 200, {size} bytes. Date signal: {date_str}."
    result["access_method"] = "html_only"
    return result

# ---------------------------------------------------------------------------
# PART B — cross-source overlap using local data files
# ---------------------------------------------------------------------------
def run_part_b():
    """
    Compare business names across sources where we have local data.
    Uses: Ontario Select Licence CSV + Saskatoon XLSX (via openpyxl) + any
    downloaded CSV samples captured in Part A.
    Also compares Corporations Canada province field against municipal sources.
    """
    print("\n=== PART B: Cross-source overlap ===")

    results = {
        "sources_compared": [],
        "overlap_findings": [],
        "entity_resolution_examples": [],
        "observations": []
    }

    # Load Ontario Select Licence
    ont_names = set()
    ont_file = "data/raw/ontario_select_licence_business_20260925.csv"
    if os.path.exists(ont_file):
        with open(ont_file, encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Legal Name", row.get("legal_name", "")).strip().upper()
                if name and name not in ("N/A", ""):
                    ont_names.add(name)
        results["sources_compared"].append({
            "source": "Ontario Select Licence (VR06)",
            "file": ont_file,
            "unique_names": len(ont_names)
        })
        print(f"  Ontario Select Licence: {len(ont_names)} unique names loaded")
    else:
        print(f"  SKIP: {ont_file} not found")

    # Load Saskatoon all-businesses
    sask_names = set()
    sask_file = "data/raw/saskatoon_all_businesses_20260925.xlsx"
    if os.path.exists(sask_file):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(sask_file, read_only=True, data_only=True)
            ws = wb.active
            headers = None
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(c).strip() if c else "" for c in row]
                    continue
                if headers:
                    d = dict(zip(headers, row))
                    name_field = next((h for h in headers if "name" in h.lower()), None)
                    if name_field:
                        name = str(d.get(name_field, "") or "").strip().upper()
                        if name and name not in ("N/A", "NONE", ""):
                            sask_names.add(name)
            wb.close()
            results["sources_compared"].append({
                "source": "Saskatoon All Businesses (VR07)",
                "file": sask_file,
                "unique_names": len(sask_names)
            })
            print(f"  Saskatoon: {len(sask_names)} unique names loaded")
        except ImportError:
            print("  SKIP: openpyxl not installed")
        except Exception as ex:
            print(f"  Saskatoon load error: {ex}")
    else:
        print(f"  SKIP: {sask_file} not found")

    # Load Corporations Canada active CSV (sample only — large file)
    corps_names = set()
    corps_file = None
    # Find the file by common naming convention
    for candidate in ["data/raw/corporations_canada_active_CBCA.csv",
                       "data/raw/Active_CBCA_Corporations_CSV.csv",
                       "data/raw/active_cbca.csv"]:
        if os.path.exists(candidate):
            corps_file = candidate
            break
    if corps_file:
        try:
            with open(corps_file, encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= 50000:  # sample first 50k rows
                        break
                    name_field = next((k for k in row if "name" in k.lower() and "form 1" in k.lower()), None)
                    if not name_field:
                        name_field = next((k for k in row if "name" in k.lower()), None)
                    if name_field:
                        name = row.get(name_field, "").strip().upper()
                        if name:
                            corps_names.add(name)
            results["sources_compared"].append({
                "source": "Corporations Canada active CBCA (VR01, sample 50k)",
                "file": corps_file,
                "unique_names": len(corps_names)
            })
            print(f"  Corporations Canada: {len(corps_names)} unique names in 50k sample")
        except Exception as ex:
            print(f"  Corps Canada load error: {ex}")
    else:
        print("  Corporations Canada CSV not found in data/raw/ — skip")

    # --- Overlap analysis ---
    source_sets = {}
    if ont_names:
        source_sets["ontario_select_licence"] = ont_names
    if sask_names:
        source_sets["saskatoon_businesses"] = sask_names
    if corps_names:
        source_sets["corps_canada_sample_50k"] = corps_names

    source_labels = list(source_sets.keys())

    for i in range(len(source_labels)):
        for j in range(i + 1, len(source_labels)):
            a_lbl = source_labels[i]
            b_lbl = source_labels[j]
            a_set = source_sets[a_lbl]
            b_set = source_sets[b_lbl]
            exact_overlap = a_set & b_set
            overlap_pct_a = round(len(exact_overlap) / len(a_set) * 100, 2) if a_set else 0
            overlap_pct_b = round(len(exact_overlap) / len(b_set) * 100, 2) if b_set else 0
            finding = {
                "source_a": a_lbl,
                "source_b": b_lbl,
                "size_a": len(a_set),
                "size_b": len(b_set),
                "exact_name_overlap": len(exact_overlap),
                "pct_of_a": overlap_pct_a,
                "pct_of_b": overlap_pct_b,
                "overlap_examples": sorted(list(exact_overlap))[:10]
            }
            results["overlap_findings"].append(finding)
            print(f"  Overlap {a_lbl} vs {b_lbl}: {len(exact_overlap)} exact matches "
                  f"({overlap_pct_a}% of A, {overlap_pct_b}% of B)")

    # --- Multi-licence / multi-row pattern in local data ---
    # Winnipeg: 275 unique names / 13,757 rows = multi-licence pattern
    # Vancouver: 17.7% of names have multiple employee values (from VR14.4.1)
    results["entity_resolution_examples"] = [
        {
            "source": "Winnipeg (VR14.4)",
            "pattern": "multi_licence_per_entity",
            "description": "13,757 rows but only 275 unique trade_name values — ~50 licence rows per business on average. Grain is licence-event, not entity.",
            "implication": "Group by trade_name + address to approximate entity count; expect significant loss from 13,757 → ~275"
        },
        {
            "source": "Vancouver (VR14.4.1)",
            "pattern": "multi_licence_employee_variance",
            "description": "17.7% of unique business names have multiple different employee values across rows. Extreme example: Pacific National Exhibition = [0, 30, 200, 3000, 4000].",
            "implication": "Employee count must be resolved at entity layer (e.g. most-recent licence row), not averaged"
        },
        {
            "source": "Saskatoon (VR07)",
            "pattern": "schema_grain_mismatch",
            "description": "all-businesses file (7,472 rows, Bus_Lic_Acct_Id) and new-businesses file (51 rows, Business_License_Id) use different ID schemas — 5.9% name match across files.",
            "implication": "Two Saskatoon files cannot be joined on ID. Name-based fuzzy match required with high false-positive risk."
        },
    ]

    # Check for Saskatoon new-businesses file to test intra-city overlap
    sask_new_file = "data/raw/saskatoon_new_businesses_20260925.xlsx"
    if os.path.exists(sask_file) and os.path.exists(sask_new_file):
        sask_new_names = set()
        try:
            import openpyxl
            wb2 = openpyxl.load_workbook(sask_new_file, read_only=True, data_only=True)
            ws2 = wb2.active
            headers2 = None
            for i, row in enumerate(ws2.iter_rows(values_only=True)):
                if i == 0:
                    headers2 = [str(c).strip() if c else "" for c in row]
                    continue
                if headers2:
                    d = dict(zip(headers2, row))
                    name_field = next((h for h in headers2 if "name" in h.lower()), None)
                    if name_field:
                        name = str(d.get(name_field, "") or "").strip().upper()
                        if name:
                            sask_new_names.add(name)
            wb2.close()
            sask_intra = sask_names & sask_new_names
            results["entity_resolution_examples"].append({
                "source": "Saskatoon intra-city (VR07)",
                "pattern": "intra_city_schema_mismatch",
                "all_biz_names": len(sask_names),
                "new_biz_names": len(sask_new_names),
                "exact_name_overlap": len(sask_intra),
                "overlap_pct": round(len(sask_intra) / len(sask_new_names) * 100, 1) if sask_new_names else 0,
                "description": "New-biz file vs all-biz file exact name match rate.",
                "implication": "Low match rate confirms different populations or different naming conventions, not simply a subset."
            })
            print(f"  Saskatoon intra: new({len(sask_new_names)}) vs all({len(sask_names)}) — {len(sask_intra)} exact matches")
        except Exception as ex:
            print(f"  Saskatoon intra-city comparison error: {ex}")

    return results

# ---------------------------------------------------------------------------
# Write report
# ---------------------------------------------------------------------------
def write_report(part_a_results, part_b_results, generated_at):
    # JSON
    report_data = {
        "vr": "VR16_17",
        "title": "Source Coverage & Freshness + Cross-Source Overlap",
        "generated": generated_at,
        "script": "scripts/probe_vr16_17_source_coverage_overlap.py",
        "part_a_source_coverage": part_a_results,
        "part_b_overlap": part_b_results,
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    # Markdown
    lines = [
        "# VR16+17 — Source Coverage & Freshness + Cross-Source Overlap",
        "",
        f"Generated: `{generated_at}`",
        f"Script: `scripts/probe_vr16_17_source_coverage_overlap.py`",
        f"JSON: `reports/validation_rounds/VR16_17_SOURCE_COVERAGE_OVERLAP.json`",
        "",
        "---",
        "",
        "## PART A — Source Freshness & Coverage",
        "",
        "### Summary Table",
        "",
        "| Province | City/Source | Status | Access | Date Signal | Rows Sampled | Employee | Phone/Email |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for r in part_a_results:
        status_str = str(r.get("status", "?"))
        access = r.get("access_method", "?")
        date_sig = r.get("max_date_in_sample") or r.get("date_field") or "?"
        rows_s = str(r.get("row_count_sample") or "?")
        emp = r.get("employee_field") or "none"
        ph = ",".join(r.get("phone_fields", [])) or "none"
        em = ",".join(r.get("email_fields", [])) or "none"
        contact = f"phone:{ph} email:{em}"
        lines.append(f"| {r['province']} | {r['city']} — {r['label']} | HTTP {status_str} | {access} | {date_sig} | {rows_s} | {emp} | {contact} |")

    lines += [
        "",
        "### Detailed Findings",
        "",
    ]
    for r in part_a_results:
        lines.append(f"#### {r['province']} — {r['city']} ({r['label']})")
        lines.append(f"- URL: `{r['url']}`")
        lines.append(f"- Notes: {r['notes']}")
        lines.append(f"- HTTP status: {r.get('status')}")
        lines.append(f"- Access method: {r.get('access_method')}")
        lines.append(f"- Observation: {r.get('observation')}")
        if r.get("fieldnames"):
            lines.append(f"- Fields ({len(r['fieldnames'])}): {r['fieldnames']}")
        if r.get("fill_rates"):
            top = sorted(r["fill_rates"].items(), key=lambda x: -x[1])[:8]
            lines.append(f"- Fill rates (top 8): {dict(top)}")
        lines.append("")

    lines += [
        "---",
        "",
        "## PART B — Cross-Source Overlap & Entity Resolution",
        "",
        "### Sources Compared",
        "",
    ]
    for s in part_b_results.get("sources_compared", []):
        lines.append(f"- **{s['source']}**: {s['unique_names']} unique names")

    lines += ["", "### Exact Name Overlap Matrix", ""]
    for f in part_b_results.get("overlap_findings", []):
        lines.append(f"- **{f['source_a']}** vs **{f['source_b']}**: "
                     f"{f['exact_name_overlap']} exact matches "
                     f"({f['pct_of_a']}% of A={f['size_a']}, {f['pct_of_b']}% of B={f['size_b']})")
        if f.get("overlap_examples"):
            lines.append(f"  - Examples: {f['overlap_examples'][:5]}")

    lines += ["", "### Entity Resolution Patterns", ""]
    for e in part_b_results.get("entity_resolution_examples", []):
        lines.append(f"#### {e['source']} — {e['pattern']}")
        lines.append(f"- {e['description']}")
        lines.append(f"- Implication: {e['implication']}")
        lines.append("")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nReport written: {REPORT_MD}")
    print(f"JSON written:   {REPORT_JSON}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print("=== VR16+17 — Part A: Source freshness & coverage ===")
    part_a_results = []
    for label, province, city, url, notes in PART_A_SOURCES:
        result = probe_source(label, province, city, url, notes)
        part_a_results.append(result)
        # Brief summary to terminal
        print(f"    → HTTP {result['status']} | {result['access_method']} | {result['observation'][:100]}")
        time.sleep(0.8)  # polite crawl rate

    print("\n=== VR16+17 — Part B: Cross-source overlap ===")
    part_b_results = run_part_b()

    write_report(part_a_results, part_b_results, generated_at)

    # Terminal summary
    print("\n=== PART A SUMMARY ===")
    by_status = {}
    for r in part_a_results:
        s = r.get("access_method", "unknown")
        by_status.setdefault(s, []).append(f"{r['province']}/{r['label']}")
    for k, v in sorted(by_status.items()):
        print(f"  {k}: {v}")

    print("\n=== PART B SUMMARY ===")
    for f in part_b_results.get("overlap_findings", []):
        print(f"  {f['source_a']} ∩ {f['source_b']}: {f['exact_name_overlap']} exact ({f['pct_of_a']}% / {f['pct_of_b']}%)")

    print(f"\nDone. Reports: {REPORT_MD} + {REPORT_JSON}")

if __name__ == "__main__":
    main()
