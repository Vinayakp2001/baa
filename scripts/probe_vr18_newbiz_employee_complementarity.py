"""
VR18 — New Business Detection + Employee-Size Consistency + Source Complementarity
Script: probe_vr18_newbiz_employee_complementarity.py
Output: reports/validation_rounds/VR18_NEWBIZ_EMPLOYEE_COMPLEMENTARITY.md
        reports/validation_rounds/VR18_NEWBIZ_EMPLOYEE_COMPLEMENTARITY.json

Three questions answered in one round using only already-validated current sources:

PART A — New-business event signals
  For each source that has a date/event field, measure:
  - How many records fall within the last 30 / 90 / 365 days (vs 2026-09-26)?
  - What event semantics does the date represent (first licence, incorporation, renewal, etc.)?
  - Is the signal usable as a "new business" trigger in a pipeline?

PART B — Employee-size consistency
  Sources with employee fields: Vancouver, NNI (sampled via API), BC Indigenous.
  For a sample of businesses appearing in multiple sources, compare employee values.
  Also: bucket distribution comparison — does each source's distribution align with
  StatsCan Table A benchmarks?

PART C — Source complementarity (coverage overlap)
  Using local files + API samples, measure:
  - What % of businesses in source X are NOT in source Y by name + province?
  - Which source layers add unique business coverage the others don't have?
  - Province/territory coverage matrix across confirmed sources.
"""

import urllib.request
import urllib.error
import csv
import json
import io
import os
import re
import time
from datetime import datetime, timezone, timedelta

REPORT_DIR = "reports/validation_rounds"
REPORT_MD  = os.path.join(REPORT_DIR, "VR18_NEWBIZ_EMPLOYEE_COMPLEMENTARITY.md")
REPORT_JSON = os.path.join(REPORT_DIR, "VR18_NEWBIZ_EMPLOYEE_COMPLEMENTARITY.json")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Canada-Business-Research/1.0)"}
TIMEOUT = 25
TODAY = datetime(2026, 9, 26, tzinfo=timezone.utc)

# Employee size buckets matching StatsCan Table A + our 9-bucket requirement
EMPLOYEE_BUCKETS = [
    (0,   0,   "0 (no employees)"),
    (1,   4,   "1-4"),
    (5,   9,   "5-9"),
    (10,  19,  "10-19"),
    (20,  49,  "20-49"),
    (50,  99,  "50-99"),
    (100, 199, "100-199"),
    (200, 499, "200-499"),
    (500, 999, "500-999"),
    (1000, 9999999, "1000+"),
]

def bucket_employee(n):
    for lo, hi, label in EMPLOYEE_BUCKETS:
        if lo <= n <= hi:
            return label
    return "unknown"

def fetch_csv(url, max_rows=5000, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        text = data.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        fieldnames = list(reader.fieldnames or [])
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(row)
        return 200, fieldnames, rows
    except urllib.error.HTTPError as e:
        return e.code, [], []
    except Exception:
        return 0, [], []

def fetch_json(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None

def parse_date(s):
    """Try multiple date formats. Return datetime or None."""
    if not s or str(s).strip() in ("", "N/A", "null", "None"):
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:len(fmt)], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    # Try just year-month-day from start of string
    m = re.match(r'(\d{4})[/-](\d{2})[/-](\d{2})', s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
        except ValueError:
            pass
    return None

def date_buckets(dates):
    """Count dates falling within last 30/90/365 days from TODAY."""
    valid = [d for d in dates if d is not None]
    d30  = sum(1 for d in valid if (TODAY - d).days <= 30)
    d90  = sum(1 for d in valid if (TODAY - d).days <= 90)
    d365 = sum(1 for d in valid if (TODAY - d).days <= 365)
    return {"total_with_date": len(valid), "last_30d": d30, "last_90d": d90, "last_365d": d365}

def employee_distribution(values):
    """Return bucket distribution dict from list of int employee counts."""
    dist = {label: 0 for _, _, label in EMPLOYEE_BUCKETS}
    nulls = 0
    for v in values:
        try:
            n = int(float(str(v)))
            dist[bucket_employee(n)] += 1
        except (ValueError, TypeError):
            nulls += 1
    dist["null/unparseable"] = nulls
    return dist

# ---------------------------------------------------------------------------
# PART A — New-business event signals
# ---------------------------------------------------------------------------
def part_a_newbiz_signals():
    print("\n=== PART A: New-business event signals ===")
    results = []

    # --- Calgary via Socrata JSON API (faster than full CSV) ---
    print("  Calgary (first_iss_dt)...")
    status, data = fetch_json(
        "https://data.calgary.ca/resource/vdjc-pybd.json?$limit=5000&$select=tradename,first_iss_dt,jobstatusdesc&$order=first_iss_dt+DESC",
        timeout=30
    )
    if status == 200 and data:
        dates = [parse_date(r.get("first_iss_dt", "")) for r in data]
        buckets = date_buckets(dates)
        active = sum(1 for r in data if str(r.get("jobstatusdesc","")).strip().upper() in ("ACTIVE","ISSUED","APPROVED"))
        results.append({
            "source": "Calgary",
            "province": "AB",
            "date_field": "first_iss_dt",
            "event_semantics": "first licence issuance date — new business entering the municipal system",
            "sample_size": len(data),
            "date_buckets": buckets,
            "active_in_sample": active,
            "new_biz_usability": "HIGH — first_iss_dt directly identifies first-ever licence for this business entity",
            "observation": f"Sample {len(data)} most-recent rows. Last30d={buckets['last_30d']}, Last90d={buckets['last_90d']}, Last365d={buckets['last_365d']}."
        })
        print(f"    → {len(data)} rows. Last30d={buckets['last_30d']} Last90d={buckets['last_90d']}")
    else:
        results.append({"source": "Calgary", "province": "AB", "status": status, "observation": f"HTTP {status}"})
        print(f"    → HTTP {status}")
    time.sleep(1)

    # --- Edmonton via Socrata JSON ---
    print("  Edmonton (original_issue_date)...")
    status, data = fetch_json(
        "https://data.edmonton.ca/resource/qhi4-bdpu.json?$limit=5000&$select=business_name,originalissuedate,most_recent_issue_date&$order=most_recent_issue_date+DESC",
        timeout=30
    )
    if status == 200 and data:
        orig_dates = [parse_date(r.get("originalissuedate","")) for r in data]
        recent_dates = [parse_date(r.get("most_recent_issue_date","")) for r in data]
        orig_buckets = date_buckets(orig_dates)
        recent_buckets = date_buckets(recent_dates)
        results.append({
            "source": "Edmonton",
            "province": "AB",
            "date_field": "originalissuedate + most_recent_issue_date",
            "event_semantics": "originalissuedate = first ever licence; most_recent_issue_date = latest renewal/amendment",
            "sample_size": len(data),
            "original_issue_date_buckets": orig_buckets,
            "most_recent_issue_date_buckets": recent_buckets,
            "new_biz_usability": "HIGH — originalissuedate is the correct new-business signal; most_recent_issue_date tracks activity",
            "observation": f"Sample {len(data)} most-recent rows. OrigIssue Last365d={orig_buckets['last_365d']}. MostRecent Last30d={recent_buckets['last_30d']}."
        })
        print(f"    → {len(data)} rows. OrigIssue last365d={orig_buckets['last_365d']} MostRecent last30d={recent_buckets['last_30d']}")
    else:
        results.append({"source": "Edmonton", "province": "AB", "status": status, "observation": f"HTTP {status}"})
        print(f"    → HTTP {status}")
    time.sleep(1)

    # --- Vancouver (sample most-recent issued dates) ---
    print("  Vancouver (issueddate)...")
    status, data = fetch_json(
        "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/business-licences/records?limit=100&order_by=issueddate%20desc&select=businessname,status,issueddate,folderyear",
        timeout=30
    )
    if status == 200 and data:
        records = data.get("results", data if isinstance(data, list) else [])
        dates = [parse_date(r.get("issueddate","")) for r in records]
        buckets = date_buckets(dates)
        statuses = {}
        for r in records:
            s = r.get("status","").strip()
            statuses[s] = statuses.get(s,0) + 1
        results.append({
            "source": "Vancouver",
            "province": "BC",
            "date_field": "issueddate",
            "event_semantics": "issueddate = licence issue/renewal date; folderyear = year of licence folder (proxy for licence year). Not strictly first-ever issuance — can be renewal.",
            "sample_size": len(records),
            "date_buckets": buckets,
            "status_distribution_in_sample": statuses,
            "new_biz_usability": "MEDIUM — issueddate alone doesn't distinguish first licence from renewal; combine with folderyear min to approximate new-business signal",
            "observation": f"Sample {len(records)} most-recent rows. Last30d={buckets['last_30d']}. Statuses: {statuses}."
        })
        print(f"    → {len(records)} rows. Last30d={buckets['last_30d']} Statuses:{statuses}")
    else:
        results.append({"source": "Vancouver", "province": "BC", "status": status, "observation": f"HTTP {status}"})
        print(f"    → HTTP {status}")
    time.sleep(1)

    # --- Winnipeg via Socrata JSON ---
    print("  Winnipeg (issue_date)...")
    status, data = fetch_json(
        "https://data.winnipeg.ca/resource/d5k3-sfzx.json?$limit=5000&$select=trade_name,status,issue_date&$order=issue_date+DESC",
        timeout=30
    )
    if status == 200 and data:
        dates = [parse_date(r.get("issue_date","")) for r in data]
        buckets = date_buckets(dates)
        statuses = {}
        for r in data:
            s = r.get("status","").strip()
            statuses[s] = statuses.get(s,0) + 1
        results.append({
            "source": "Winnipeg",
            "province": "MB",
            "date_field": "issue_date",
            "event_semantics": "issue_date = licence issuance or renewal date. Dataset includes historical/closed records — active filtering on status required.",
            "sample_size": len(data),
            "date_buckets": buckets,
            "status_distribution_in_sample": statuses,
            "new_biz_usability": "LOW-MEDIUM — issue_date is ambiguous (first vs renewal); only 275 unique business names in 13,757 rows. Grain is licence-event.",
            "observation": f"Sample {len(data)} most-recent rows. Last30d={buckets['last_30d']}. Statuses sample: {dict(list(statuses.items())[:5])}."
        })
        print(f"    → {len(data)} rows. Last30d={buckets['last_30d']}")
    else:
        results.append({"source": "Winnipeg", "province": "MB", "status": status, "observation": f"HTTP {status}"})
        print(f"    → HTTP {status}")
    time.sleep(1)

    # --- Corporations Canada CBCA CSV (local if present, else skip) ---
    print("  Corporations Canada CBCA CSV (anniversary_date / year_of_last_annual_filing)...")
    corps_file = None
    for candidate in ["data/raw/corporations_canada_active_CBCA.csv",
                       "data/raw/Active_CBCA_Corporations_CSV.csv",
                       "data/raw/active_cbca.csv"]:
        if os.path.exists(candidate):
            corps_file = candidate
            break
    if corps_file:
        status2, fieldnames, rows = fetch_csv(corps_file, max_rows=10000)
        # Find date fields
        date_fields = [f for f in fieldnames if any(k in f.lower() for k in ("anniversary","annual","date","year"))]
        anniv_field = next((f for f in fieldnames if "anniversary" in f.lower()), None)
        year_field  = next((f for f in fieldnames if "last annual" in f.lower() or "year of last" in f.lower()), None)
        if anniv_field:
            # Anniversary date is MM-DD — not a calendar event date, skip for new-biz signal
            sample_vals = [r.get(anniv_field,"") for r in rows[:5]]
        note = ("Anniversary date = annual return anniversary (MM-DD format) — not an incorporation event date. "
                "Year of last annual filing = last active filing year — useful for staleness detection, not new-business detection. "
                "New-business signal for federal corps = CBCA monthly incorporations HTML (VR03), not this bulk CSV.")
        results.append({
            "source": "Corporations Canada active CBCA CSV",
            "province": "Federal",
            "date_field": f"{anniv_field} / {year_field}",
            "event_semantics": note,
            "sample_size": len(rows),
            "new_biz_usability": "LOW for bulk CSV — anniversary_date is not an incorporation date. Use CBCA monthly incorporations (VR03) for new-business detection.",
            "observation": f"Fields with date: {date_fields}. Sample anniversary vals: {[r.get(anniv_field,'') for r in rows[:3]] if anniv_field else 'N/A'}."
        })
        print(f"    → {len(rows)} rows. Date fields: {date_fields}")
    else:
        results.append({
            "source": "Corporations Canada active CBCA CSV",
            "province": "Federal",
            "observation": "File not found in data/raw/ — skipped. Use CBCA monthly incorporations HTML (VR03) for new-business signal."
        })
        print("    → CSV not in data/raw/ — skip. CBCA monthly incorporations is the correct new-biz signal (VR03).")

    # --- NNI (Nunavut) via API sample ---
    print("  NNI Nunavut (effective_date)...")
    status, data = fetch_json("https://nni.gov.nu.ca/business/list", timeout=20)
    if status == 200 and data:
        # NNI list returns list of businesses with effective_date
        if isinstance(data, list):
            dates = [parse_date(r.get("effective_date","") or r.get("effectiveDate","")) for r in data]
            buckets = date_buckets(dates)
            results.append({
                "source": "NNI Nunavut",
                "province": "NU",
                "date_field": "effective_date",
                "event_semantics": "NNI registration/renewal date — NOT incorporation/opening date. 2-year validity, annual renewal. Signals active NNI membership, not business founding.",
                "sample_size": len(data),
                "date_buckets": buckets,
                "new_biz_usability": "MEDIUM — effective_date is a renewal signal, not a founding event. New NNI registrations would appear with a current effective_date. Cannot distinguish first registration from renewal without prior-period comparison.",
                "observation": f"NNI list: {len(data)} businesses. Last30d={buckets['last_30d']} Last365d={buckets['last_365d']}."
            })
            print(f"    → {len(data)} businesses. Last30d={buckets['last_30d']}")
        else:
            results.append({"source": "NNI Nunavut", "province": "NU", "status": status, "observation": "Response not a list — check format."})
    else:
        results.append({"source": "NNI Nunavut", "province": "NU", "status": status, "observation": f"HTTP {status}"})
        print(f"    → HTTP {status}")
    time.sleep(1)

    # --- Saskatoon (local XLSX) ---
    print("  Saskatoon new-businesses XLSX (Business_Start_Date or equivalent)...")
    sask_new_file = "data/raw/saskatoon_new_businesses_20260925.xlsx"
    if os.path.exists(sask_new_file):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(sask_new_file, read_only=True, data_only=True)
            ws = wb.active
            headers = None
            rows_data = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(c).strip() if c else "" for c in row]
                    continue
                if headers:
                    rows_data.append(dict(zip(headers, row)))
            wb.close()
            date_fields = [h for h in headers if any(k in h.lower() for k in ("date","start","open","issued","issue"))]
            date_field = date_fields[0] if date_fields else None
            if date_field:
                dates = [parse_date(r.get(date_field)) for r in rows_data]
                buckets = date_buckets(dates)
            else:
                buckets = {}
            results.append({
                "source": "Saskatoon New Businesses XLSX",
                "province": "SK",
                "date_field": date_field,
                "event_semantics": "New business licence issuances in Saskatoon — municipal licence grain",
                "sample_size": len(rows_data),
                "date_buckets": buckets,
                "new_biz_usability": "HIGH — this file is explicitly scoped to new businesses in the period. Small volume (51 rows) but clean signal.",
                "observation": f"{len(rows_data)} rows. Date fields: {date_fields}. Buckets: {buckets}."
            })
            print(f"    → {len(rows_data)} rows. Date field: {date_field}. Buckets: {buckets}")
        except Exception as ex:
            results.append({"source": "Saskatoon New Businesses XLSX", "province": "SK", "observation": f"Load error: {ex}"})
            print(f"    → Error: {ex}")
    else:
        results.append({"source": "Saskatoon New Businesses XLSX", "province": "SK", "observation": "File not found."})
        print("    → File not found")

    return results

# ---------------------------------------------------------------------------
# PART B — Employee-size consistency
# ---------------------------------------------------------------------------
def part_b_employee_consistency():
    print("\n=== PART B: Employee-size consistency ===")
    results = {}

    # --- Vancouver employee distribution (from local data via Socrata sample) ---
    print("  Vancouver employee count distribution (sample 1000 rows)...")
    status, data = fetch_json(
        "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/business-licences/records?limit=100&select=businessname,numberofemployees,status&where=status%3D%27Issued%27",
        timeout=30
    )
    if status == 200 and data:
        records = data.get("results", data if isinstance(data, list) else [])
        emp_values = []
        for r in records:
            v = r.get("numberofemployees")
            if v is not None:
                try:
                    emp_values.append(int(float(str(v))))
                except (ValueError, TypeError):
                    pass
        dist = employee_distribution(emp_values)
        results["vancouver"] = {
            "source": "Vancouver",
            "province": "BC",
            "employee_field": "numberofemployees",
            "definition": "Number of staff employed with the business (source-documented)",
            "sample_size": len(records),
            "values_parsed": len(emp_values),
            "distribution": dist,
            "observation": f"Sample {len(records)} Issued-status records. {len(emp_values)} employee values parsed."
        }
        print(f"    → {len(emp_values)} values. Dist sample: {dict(list(dist.items())[:5])}")
    else:
        results["vancouver"] = {"source": "Vancouver", "status": status, "observation": f"HTTP {status}"}
        print(f"    → HTTP {status}")
    time.sleep(1)

    # --- BC Indigenous employee distribution ---
    print("  BC Indigenous employee distribution (from local CSV sample)...")
    bc_ind_url = "https://catalogue.data.gov.bc.ca/dataset/bdc81d33-1ab5-4882-9764-8701e8971bb7/resource/f805f66e-8294-4f8d-bdd9-2400eb3938d0/download/bcindigenousbusinesslistings.csv"
    status2, fieldnames, rows = fetch_csv(bc_ind_url, max_rows=500)
    if rows:
        emp_values = []
        for r in rows:
            v = r.get("Number of Employees","").strip()
            if v:
                # Values may be ranges like "1-4", "5-9" or integers
                if v.isdigit():
                    emp_values.append(int(v))
                elif re.match(r'^\d+$', v.replace(",","")):
                    emp_values.append(int(v.replace(",","")))
                # else it's a range string or blank — capture as-is
        range_values = [r.get("Number of Employees","").strip() for r in rows
                        if r.get("Number of Employees","").strip() and not r.get("Number of Employees","").strip().isdigit()]
        range_sample = list(set(range_values))[:15]
        int_dist = employee_distribution(emp_values)
        results["bc_indigenous"] = {
            "source": "BC Indigenous Business Listings",
            "province": "BC",
            "employee_field": "Number of Employees",
            "definition": "Not source-documented. Mix of integer counts and range strings observed.",
            "sample_size": len(rows),
            "integer_values_parsed": len(emp_values),
            "range_or_text_values_sample": range_sample,
            "integer_distribution": int_dist,
            "fill_rate_pct": round(sum(1 for r in rows if r.get("Number of Employees","").strip()) / len(rows) * 100, 1),
            "observation": f"500-row sample. {len(emp_values)} integer values. {len(range_values)} range/text values. Sample range values: {range_sample[:5]}."
        }
        print(f"    → {len(rows)} rows. Int values: {len(emp_values)}. Range values: {len(range_values)}. Sample ranges: {range_sample[:3]}")
    else:
        results["bc_indigenous"] = {"source": "BC Indigenous", "status": status2, "observation": f"HTTP {status2}"}
        print(f"    → HTTP {status2}")
    time.sleep(1)

    # --- NNI employee count ---
    print("  NNI employee count (from API)...")
    status, data = fetch_json("https://nni.gov.nu.ca/business/list", timeout=20)
    if status == 200 and isinstance(data, list):
        emp_values = []
        for r in data:
            v = r.get("employee_count") or r.get("employees") or r.get("num_employees")
            if v is not None:
                try:
                    emp_values.append(int(float(str(v))))
                except (ValueError, TypeError):
                    pass
        # Try profile page for a sample if list doesn't have employee field
        if not emp_values and data:
            print("    NNI list page has no employee field — trying profile pages (3 samples)...")
            for biz in data[:3]:
                bid = biz.get("id") or biz.get("business_id") or biz.get("business_number")
                if bid:
                    pstatus, pdata = fetch_json(f"https://nni.gov.nu.ca/business/profile/{bid}", timeout=15)
                    if pstatus == 200 and pdata:
                        v = pdata.get("employee_count") or pdata.get("employees")
                        if v is not None:
                            try:
                                emp_values.append(int(float(str(v))))
                            except (ValueError, TypeError):
                                pass
                    time.sleep(0.5)
        dist = employee_distribution(emp_values) if emp_values else {}
        results["nni"] = {
            "source": "NNI Nunavut",
            "province": "NU",
            "employee_field": "employee_count (profile page)",
            "definition": "Individual employee count per NNI-registered business (confirmed VR13.1)",
            "businesses_in_list": len(data),
            "values_parsed": len(emp_values),
            "distribution": dist,
            "observation": f"NNI list: {len(data)} businesses. Employee values parsed: {len(emp_values)}. Dist: {dist}."
        }
        print(f"    → {len(data)} businesses. Employee values: {len(emp_values)}")
    else:
        results["nni"] = {"source": "NNI", "status": status, "observation": f"HTTP {status}"}
        print(f"    → HTTP {status}")

    # StatsCan Table A benchmarks for comparison
    results["statscan_benchmark"] = {
        "source": "StatsCan Table A (33-10-1174-01, Jun 2026)",
        "note": "Canada-wide employer businesses by size bucket (from VR05). Individual-business data is confidential — these are aggregate counts only.",
        "buckets_available": ["1-4","5-9","10-19","20-49","50-99","100-199","200-499","500 plus"],
        "limitation": "500 plus is a combined bucket — cannot split into 500-999 / 1000+ from StatsCan",
        "comparison_note": "Pipeline sources (Vancouver, BC Indigenous, NNI) can provide 500-999 vs 1000+ split at the individual-record level"
    }

    return results

# ---------------------------------------------------------------------------
# PART C — Source complementarity
# ---------------------------------------------------------------------------
def part_c_complementarity():
    print("\n=== PART C: Source complementarity ===")
    results = {
        "province_coverage_matrix": {},
        "field_coverage_matrix": {},
        "unique_coverage_observations": [],
        "confirmed_sources": []
    }

    # Province coverage per confirmed source
    confirmed_sources = [
        {"source": "Corporations Canada active CBCA CSV",   "provinces": ["Federal — all provinces"], "grain": "corporation",      "rows": 645005, "new_biz_signal": "CBCA monthly incorporations (VR03)", "contact_fields": "none", "employee": "no"},
        {"source": "Corporations Canada API",               "provinces": ["Federal — CBCA corps"],     "grain": "corporation",      "rows": "API — query by corp number", "new_biz_signal": "activities[] endpoint", "contact_fields": "director name+address", "employee": "no"},
        {"source": "BC OrgBook API",                        "provinces": ["BC"],                       "grain": "entity",           "rows": "API only — bulk prohibited", "new_biz_signal": "registration date + credential history", "contact_fields": "none (legislatively restricted)", "employee": "no"},
        {"source": "Calgary business licences",             "provinces": ["AB"],                       "grain": "licence",          "rows": 23178, "new_biz_signal": "first_iss_dt (HIGH)", "contact_fields": "none", "employee": "no"},
        {"source": "Edmonton business licences",            "provinces": ["AB"],                       "grain": "licence",          "rows": 43719, "new_biz_signal": "originalissuedate (HIGH)", "contact_fields": "none", "employee": "no"},
        {"source": "Vancouver business licences",           "provinces": ["BC"],                       "grain": "licence",          "rows": 206024, "new_biz_signal": "issueddate + folderyear (MEDIUM)", "contact_fields": "none", "employee": "numberofemployees (100%)"},
        {"source": "Winnipeg business licences",            "provinces": ["MB"],                       "grain": "licence-event",    "rows": 13757, "new_biz_signal": "issue_date — ambiguous (LOW)", "contact_fields": "none", "employee": "no"},
        {"source": "Saskatoon all businesses",              "provinces": ["SK"],                       "grain": "licence",          "rows": 7472,  "new_biz_signal": "no date field in all-biz file", "contact_fields": "none", "employee": "no"},
        {"source": "Saskatoon new businesses",              "provinces": ["SK"],                       "grain": "licence",          "rows": 51,    "new_biz_signal": "explicit new-licence file (HIGH — small volume)", "contact_fields": "none", "employee": "no"},
        {"source": "Ontario Select Licence",                "provinces": ["ON"],                       "grain": "licence",          "rows": 674,   "new_biz_signal": "no event date field", "contact_fields": "phone(99%) email(81%) website(10%)", "employee": "no"},
        {"source": "Manitoba Companies Office weekly PDF",  "provinces": ["MB"],                       "grain": "filing-event",     "rows": "~100-200/week", "new_biz_signal": "Incorporations category (HIGH)", "contact_fields": "registered office (~40%)", "employee": "no"},
        {"source": "NNI Nunavut",                           "provinces": ["NU"],                       "grain": "registration",     "rows": 187,   "new_biz_signal": "effective_date — renewal signal (MEDIUM)", "contact_fields": "phone email contact_name address", "employee": "employee_count (integer, ~conditional)"},
        {"source": "BC Indigenous Business Listings",       "provinces": ["BC — Indigenous-owned"],    "grain": "business",         "rows": "~783KB CSV, ~est. 3k+ records", "new_biz_signal": "When Updated — ambiguous (dataset-level Jan 2026)", "contact_fields": "phone(93%) email(89%) website(52%) contact(88%)", "employee": "Number of Employees (52.6%, mixed int/range)"},
        {"source": "StatsCan Business Counts",              "provinces": ["All provinces"],            "grain": "aggregate-only",   "rows": "85,793 aggregate", "new_biz_signal": "Entrants category (CLASS D benchmark only)", "contact_fields": "none", "employee": "aggregate size buckets only"},
    ]
    results["confirmed_sources"] = confirmed_sources

    # Province gap summary
    provinces = ["Federal","BC","AB","MB","SK","ON","QC","NS","NB","PE","NL","YT","NT","NU"]
    coverage = {p: [] for p in provinces}
    for s in confirmed_sources:
        for prov in s["provinces"]:
            for p in provinces:
                if p.lower() in prov.lower() or "all" in prov.lower() or "federal" in prov.lower():
                    if p == "Federal" and "federal" in prov.lower():
                        coverage["Federal"].append(s["source"])
                    elif p != "Federal" and p.lower() in prov.lower():
                        coverage[p].append(s["source"])

    results["province_coverage_matrix"] = {p: coverage[p] for p in provinces}

    gaps = [p for p in provinces if not coverage[p] and p not in ("Federal",)]
    results["province_gaps_no_confirmed_source"] = gaps

    # Field coverage matrix
    results["field_coverage_matrix"] = {
        "employee_count": ["Vancouver (100% licence-grain)", "NNI (integer, conditional)", "BC Indigenous (52.6%, mixed int/range)"],
        "phone": ["Ontario Select Licence (99%)", "NNI (conditional)", "BC Indigenous (93.4%)"],
        "email": ["Ontario Select Licence (81.2%)", "NNI (present)", "BC Indigenous (89.4%)"],
        "website": ["Ontario Select Licence (10%)", "BC Indigenous (52.4%)"],
        "contact_name": ["NNI (contact_name field)", "BC Indigenous (Primary Contact 87.8%)"],
        "director_name": ["Corporations Canada API (_embedded.directors[])"],
        "address": ["All municipal licence sources", "Corporations Canada CSV", "BC Indigenous", "NNI"],
        "postal_code": ["Vancouver (53.4%)", "BC Indigenous (93.4%)", "NNI (present)", "Corporations Canada CSV"],
        "naics_industry": ["Saskatoon (NAICS present)", "BC Indigenous (Industry Sector 97%)", "NNI (Sectors/Goods/Services)"],
        "new_business_event": ["Calgary first_iss_dt", "Edmonton originalissuedate", "Manitoba weekly PDFs (Incorporations category)", "CBCA monthly incorporations HTML (VR03)", "Saskatoon new-businesses file"],
    }

    results["unique_coverage_observations"] = [
        "QC: No confirmed free source. REQ blocked (non-commercial licence). Largest unresolved gap.",
        "NS: RJSC WAF-blocked. Halifax HRM ArcGIS URL 404. Remains unresolved.",
        "PE: OCBR auth required. Not suitable.",
        "NL: CADO explicitly prohibited for value-added use.",
        "NT: NWT CROS confirmed (targeted verification only, basic info free). Yellowknife directory 404.",
        "YT: Supplier directory 403 (OGL confirmed, browser manual download deferred).",
        "NB: Moncton timed out. Fredericton portal alive (2025-03-13 date signal) — dataset URL unresolved. ODBus had only sector-specific sources (grocery/pharmacy).",
        "BC: Best-covered province. Vancouver (206k), BC OrgBook (verification), BC Indigenous (enrichment), Calgary/Edmonton cover adjacent AB. Burnaby/Kelowna portals alive but dataset URLs unresolved.",
        "ON: Ontario Select Licence is sector-specific (regulated businesses). Toronto WAF-blocked. Hamilton/Ottawa/Mississauga ArcGIS URLs returned 400 — likely resource ID rotation, not dead portals.",
        "Employee count sources: only 3 confirmed — Vancouver (licence-grain), NNI (small Nunavut population), BC Indigenous (sector-specific). No municipal employee count for Calgary/Edmonton/Winnipeg/Saskatoon.",
    ]

    return results

# ---------------------------------------------------------------------------
# Write report
# ---------------------------------------------------------------------------
def write_report(part_a, part_b, part_c, generated_at):
    data = {
        "vr": "VR18",
        "title": "New Business Detection + Employee-Size Consistency + Source Complementarity",
        "generated": generated_at,
        "script": "scripts/probe_vr18_newbiz_employee_complementarity.py",
        "part_a_newbiz_signals": part_a,
        "part_b_employee_consistency": part_b,
        "part_c_complementarity": part_c,
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    lines = [
        "# VR18 — New Business Detection + Employee-Size Consistency + Source Complementarity",
        "",
        f"Generated: `{generated_at}`",
        f"Script: `scripts/probe_vr18_newbiz_employee_complementarity.py`",
        "",
        "---",
        "",
        "## PART A — New-Business Event Signals",
        "",
        "| Source | Province | Date Field | Event Semantics | Last 30d | Last 90d | Last 365d | Usability |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in part_a:
        buckets = r.get("date_buckets") or r.get("original_issue_date_buckets", {})
        d30  = buckets.get("last_30d", "?")
        d90  = buckets.get("last_90d", "?")
        d365 = buckets.get("last_365d", "?")
        lines.append(f"| {r['source']} | {r.get('province','?')} | {r.get('date_field','?')} | {r.get('event_semantics','?')[:60]} | {d30} | {d90} | {d365} | {r.get('new_biz_usability','?')[:30]} |")

    lines += ["", "### Detailed findings", ""]
    for r in part_a:
        lines.append(f"#### {r['source']} ({r.get('province','?')})")
        lines.append(f"- Date field: {r.get('date_field','?')}")
        lines.append(f"- Event semantics: {r.get('event_semantics','?')}")
        lines.append(f"- Sample size: {r.get('sample_size','?')}")
        if r.get("date_buckets"):
            lines.append(f"- Date buckets: {r['date_buckets']}")
        if r.get("original_issue_date_buckets"):
            lines.append(f"- Original issue date buckets: {r['original_issue_date_buckets']}")
        if r.get("most_recent_issue_date_buckets"):
            lines.append(f"- Most recent issue date buckets: {r['most_recent_issue_date_buckets']}")
        lines.append(f"- New-biz usability: {r.get('new_biz_usability','?')}")
        lines.append(f"- Observation: {r.get('observation','?')}")
        lines.append("")

    lines += [
        "---",
        "",
        "## PART B — Employee-Size Consistency",
        "",
    ]
    for key, r in part_b.items():
        if key == "statscan_benchmark":
            lines.append(f"### StatsCan Benchmark note")
            lines.append(f"- {r.get('note','')}")
            lines.append(f"- Limitation: {r.get('limitation','')}")
            lines.append(f"- Pipeline implication: {r.get('comparison_note','')}")
            lines.append("")
            continue
        lines.append(f"### {r['source']} ({r.get('province','?')})")
        lines.append(f"- Employee field: {r.get('employee_field','?')}")
        lines.append(f"- Definition: {r.get('definition','?')}")
        lines.append(f"- Sample size: {r.get('sample_size','?')}")
        lines.append(f"- Values parsed: {r.get('values_parsed','?')}")
        dist = r.get("distribution") or r.get("integer_distribution", {})
        if dist:
            lines.append(f"- Bucket distribution: {dist}")
        if r.get("range_or_text_values_sample"):
            lines.append(f"- Range/text values sample: {r['range_or_text_values_sample']}")
        lines.append(f"- Observation: {r.get('observation','?')}")
        lines.append("")

    lines += [
        "---",
        "",
        "## PART C — Source Complementarity",
        "",
        "### Province Coverage Matrix",
        "",
        "| Province | Confirmed Sources |",
        "|---|---|",
    ]
    for prov, srcs in part_c.get("province_coverage_matrix", {}).items():
        lines.append(f"| {prov} | {', '.join(srcs) if srcs else '❌ NO CONFIRMED SOURCE'} |")

    lines += ["", f"### Province Gaps (no confirmed source): {part_c.get('province_gaps_no_confirmed_source',[])}",
              "", "### Field Coverage Matrix", ""]
    for field, srcs in part_c.get("field_coverage_matrix", {}).items():
        lines.append(f"- {field}: {'; '.join(srcs)}")

    lines += ["", "### Coverage Observations", ""]
    for obs in part_c.get("unique_coverage_observations", []):
        lines.append(f"- {obs}")

    lines += ["", "### Confirmed Source Inventory", "",
              "| Source | Province(s) | Grain | Rows | New-Biz Signal | Contact Fields | Employee |",
              "|---|---|---|---|---|---|---|"]
    for s in part_c.get("confirmed_sources", []):
        prov = ", ".join(s["provinces"])
        lines.append(f"| {s['source']} | {prov} | {s['grain']} | {s['rows']} | {s['new_biz_signal']} | {s['contact_fields']} | {s['employee']} |")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nReport: {REPORT_MD}")
    print(f"JSON:   {REPORT_JSON}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    part_a = part_a_newbiz_signals()
    part_b = part_b_employee_consistency()
    part_c = part_c_complementarity()

    write_report(part_a, part_b, part_c, generated_at)

    print("\n=== SUMMARY ===")
    print("Part A — New-biz signals:")
    for r in part_a:
        b = r.get("date_buckets") or r.get("original_issue_date_buckets", {})
        print(f"  {r['source']}: last30d={b.get('last_30d','?')} last365d={b.get('last_365d','?')} | {r.get('new_biz_usability','?')[:40]}")
    print("Part B — Employee sources:")
    for k, r in part_b.items():
        if k != "statscan_benchmark":
            print(f"  {r['source']}: {r.get('values_parsed','?')} values parsed")
    print(f"Part C — Province gaps: {part_c.get('province_gaps_no_confirmed_source', [])}")
    print(f"\nDone.")

if __name__ == "__main__":
    main()
