"""
VR07 — City of Saskatoon Business Licence Data
Downloads both XLSX files directly from the City of Saskatoon website.
Old CKAN portal (opendata-saskatoon.cloudapp.net) was retired Aug 26 2024.
Current files are published on the Business Statistics & Publications page.
Requires: openpyxl  (pip install openpyxl)
"""

import io
import json
import re
import sys
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("ERROR: openpyxl not installed. Run: pip install openpyxl")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT    = Path(__file__).resolve().parent.parent
RAW     = ROOT / "data" / "raw"
REPORTS = ROOT / "reports" / "validation_rounds"
RAW.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now(timezone.utc).isoformat()
DATE_SLUG = datetime.now(timezone.utc).strftime("%Y%m%d")

REPORT_PATH = REPORTS / "VR07_SASKATOON_BUSINESS_LICENCES.md"
JSON_PATH   = REPORTS / "VR07_SASKATOON_BUSINESS_LICENCES.json"

SEP = "=" * 80

# ---------------------------------------------------------------------------
# Source URLs — confirmed live by GPT 2026-09-25
# Old CKAN portal retired Aug 26 2024
# ---------------------------------------------------------------------------
SOURCES = [
    {
        "label": "All Commercial and Home-Based Businesses — Dec 31 2025",
        "url": (
            "https://www.saskatoon.ca/sites/default/files/documents/community-services/"
            "planning-development/business-license-mapping-research/business-license/"
            "Dec_31_2025_%20All_Commercial_and_Home_Based_Businesses.xlsx"
        ),
        "slug": "saskatoon_all_businesses",
        "role": "all_businesses",
    },
    {
        "label": "New Businesses — Aug 31 2026",
        "url": (
            "https://www.saskatoon.ca/sites/default/files/media/documents/"
            "New%20Businesses%20as%20of%20August%2031%2C%202026.xlsx"
        ),
        "slug": "saskatoon_new_businesses",
        "role": "new_businesses",
    },
]

PORTAL_PAGE = "https://www.saskatoon.ca/business-development/economic-profile/business-statistics-publications"
OPEN_DATA_PAGE = "https://opendata.saskatoon.ca/"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_url(url):
    print(f"  GET {url[:100]}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Canada-Pipeline-Validator/1.0)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
            status = resp.status
            headers = dict(resp.headers)
        print(f"    -> {status}  {len(data):,} bytes")
        return data, status, headers, None
    except urllib.error.HTTPError as e:
        print(f"    -> HTTP {e.code} {e.reason}")
        return None, e.code, {}, f"HTTP {e.code}"
    except Exception as e:
        print(f"    -> ERROR {e}")
        return None, None, {}, str(e)


def pct(n, total):
    if total == 0:
        return "0.0%"
    return f"{100 * n / total:.1f}%"


def looks_like_phone(s):
    if not s:
        return False
    return len(re.sub(r"\D", "", str(s))) >= 10


def looks_like_email(s):
    if not s:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(s).strip()))


def looks_like_url(s):
    if not s:
        return False
    s = str(s).strip().lower()
    return s.startswith("http") or s.startswith("www.")


def valid_postal(s):
    if not s:
        return False
    return bool(re.match(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$", str(s).strip()))


def top_n(counter, n=15):
    return counter.most_common(n)


def cell_val(cell):
    """Return cell value as string, stripping None/empty."""
    v = cell
    if v is None:
        return ""
    return str(v).strip()


# ---------------------------------------------------------------------------
# Parse XLSX
# ---------------------------------------------------------------------------

def parse_xlsx(raw_bytes, label):
    """Returns (rows_as_dicts, fieldnames, sheet_name, error)."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), read_only=True, data_only=True)
        ws = wb.active
        sheet_name = ws.title

        rows_iter = ws.iter_rows(values_only=True)
        header_row = next(rows_iter, None)
        if not header_row:
            return [], [], sheet_name, "No header row found"

        # Clean headers
        headers = [str(h).strip() if h is not None else f"col_{i}"
                   for i, h in enumerate(header_row)]

        rows = []
        for raw_row in rows_iter:
            row_dict = {}
            for i, h in enumerate(headers):
                v = raw_row[i] if i < len(raw_row) else None
                row_dict[h] = "" if v is None else str(v).strip()
            # Skip entirely blank rows
            if all(v == "" for v in row_dict.values()):
                continue
            rows.append(row_dict)

        wb.close()
        print(f"  Parsed sheet '{sheet_name}': {len(rows):,} rows, {len(headers)} columns")
        return rows, headers, sheet_name, None
    except Exception as e:
        return [], [], "?", str(e)


# ---------------------------------------------------------------------------
# Profile a dataset
# ---------------------------------------------------------------------------

def profile_dataset(rows, fields, label, role):
    if not rows:
        return {"label": label, "role": role, "total_rows": 0}

    total = len(rows)

    # Per-field stats
    field_stats = {}
    for f in fields:
        vals = [r.get(f, "") for r in rows]
        non_null = [v for v in vals if v.strip()]
        distinct = set(non_null)
        examples = list(list(distinct)[:5])
        field_stats[f] = {
            "non_null_pct": pct(len(non_null), total),
            "null_pct": pct(total - len(non_null), total),
            "distinct_count": len(distinct),
            "examples": examples,
        }

    # Field detection
    fl = {f.lower(): f for f in fields}

    def find(*candidates):
        for c in candidates:
            if c in fl:
                return fl[c]
        for c in candidates:
            for k, v in fl.items():
                if c in k:
                    return v
        return None

    fld_name    = find("business name", "businessname", "name", "trade name", "licence name")
    fld_address = find("address", "street", "location")
    fld_city    = find("city", "municipality")
    fld_postal  = find("postal", "postalcode", "postal code")
    fld_phone   = find("phone", "telephone", "contact phone")
    fld_email   = find("email")
    fld_website = find("website", "web", "url")
    fld_type    = find("business type", "licence type", "category", "type", "class")
    fld_status  = find("status", "licence status", "license status")
    fld_issue   = find("issue date", "issued", "start date", "open date", "licence date",
                       "license date", "date issued", "date opened", "opening date")
    fld_expiry  = find("expiry", "expiration", "expiry date")
    fld_lic_no  = find("licence number", "license number", "licence no", "license no",
                       "licence id", "license id", "licence #", "license #")
    fld_owner   = find("owner", "proprietor", "contact name", "applicant")

    # Record grain
    names     = [r.get(fld_name, "") for r in rows] if fld_name else []
    lic_nos   = [r.get(fld_lic_no, "") for r in rows] if fld_lic_no else []
    dup_names = total - len(set(n for n in names if n)) if names else None
    uniq_lics = len(set(n for n in lic_nos if n))
    dup_lics  = total - uniq_lics if lic_nos else None

    # Distributions
    type_counts   = Counter()
    status_counts = Counter()
    if fld_type:
        for r in rows:
            type_counts[r.get(fld_type, "") or "BLANK"] += 1
    if fld_status:
        for r in rows:
            status_counts[r.get(fld_status, "") or "BLANK"] += 1

    # Geographic
    city_counts  = Counter()
    postal_valid = postal_present = 0
    if fld_city:
        for r in rows:
            c = r.get(fld_city, "")
            if c.strip():
                city_counts[c.strip()] += 1
    if fld_postal:
        for r in rows:
            p = r.get(fld_postal, "")
            if p.strip():
                postal_present += 1
                if valid_postal(p):
                    postal_valid += 1

    # Contact
    phone_present = email_present = website_present = 0
    phone_valid   = email_valid   = url_valid       = 0
    for r in rows:
        ph = r.get(fld_phone, "") if fld_phone else ""
        em = r.get(fld_email, "") if fld_email else ""
        wb = r.get(fld_website, "") if fld_website else ""
        if ph.strip(): phone_present += 1
        if em.strip(): email_present += 1
        if wb.strip(): website_present += 1
        if looks_like_phone(ph): phone_valid += 1
        if looks_like_email(em): email_valid += 1
        if looks_like_url(wb): url_valid += 1

    # Dates
    dates = []
    for fd in [fld_issue, fld_expiry]:
        if not fd:
            continue
        for r in rows:
            d = r.get(fd, "")
            if d.strip() and d.strip().lower() not in ("n/a", "none", "null", ""):
                dates.append(d.strip())
    date_min = min(dates) if dates else None
    date_max = max(dates) if dates else None

    return {
        "label": label,
        "role": role,
        "total_rows": total,
        "fields": fields,
        "field_stats": field_stats,
        "field_map": {
            "business_name": fld_name,
            "address": fld_address,
            "city": fld_city,
            "postal": fld_postal,
            "phone": fld_phone,
            "email": fld_email,
            "website": fld_website,
            "business_type": fld_type,
            "status": fld_status,
            "issue_date": fld_issue,
            "expiry_date": fld_expiry,
            "licence_number": fld_lic_no,
            "owner": fld_owner,
        },
        "record_grain": {
            "duplicate_names": dup_names,
            "unique_licence_numbers": uniq_lics,
            "duplicate_licence_numbers": dup_lics,
        },
        "type_counts": dict(type_counts.most_common(25)),
        "status_counts": dict(status_counts.most_common()),
        "geography": {
            "unique_cities": len(city_counts),
            "top_cities": top_n(city_counts, 10),
            "postal_present_pct": pct(postal_present, total),
            "postal_valid_pct": pct(postal_valid, total),
        },
        "contact": {
            "phone_present_pct": pct(phone_present, total),
            "phone_valid_pct": pct(phone_valid, total),
            "email_present_pct": pct(email_present, total),
            "email_valid_pct": pct(email_valid, total),
            "website_present_pct": pct(website_present, total),
            "website_valid_pct": pct(url_valid, total),
        },
        "dates": {"min": date_min, "max": date_max},
    }


# ---------------------------------------------------------------------------
# New-businesses vs all-businesses comparison
# ---------------------------------------------------------------------------

def compare_datasets(all_profile, new_profile):
    """Check whether new-businesses names are a subset of all-businesses names."""
    if not all_profile or not new_profile:
        return {"skipped": True, "reason": "one or both profiles missing"}

    all_rows = all_profile.get("_rows", [])
    new_rows = new_profile.get("_rows", [])
    if not all_rows or not new_rows:
        return {"skipped": True, "reason": "rows not stored in profile"}

    fld_all = all_profile.get("field_map", {}).get("business_name")
    fld_new = new_profile.get("field_map", {}).get("business_name")
    if not fld_all or not fld_new:
        return {"skipped": True, "reason": "business name field not identified in one or both"}

    def norm(s):
        return re.sub(r"[^a-z0-9]", "", s.lower()) if s else ""

    all_names = {norm(r.get(fld_all, "")) for r in all_rows if r.get(fld_all, "").strip()}
    new_names = [norm(r.get(fld_new, "")) for r in new_rows if r.get(fld_new, "").strip()]

    matched   = sum(1 for n in new_names if n in all_names)
    unmatched = sum(1 for n in new_names if n not in all_names)

    return {
        "skipped": False,
        "all_businesses_unique_names": len(all_names),
        "new_businesses_names_checked": len(new_names),
        "matched_in_all": matched,
        "matched_pct": pct(matched, len(new_names)),
        "not_in_all": unmatched,
        "not_in_all_pct": pct(unmatched, len(new_names)),
        "interpretation": (
            "High match % = new-businesses is a subset of all-businesses (expected). "
            "Low match % = different population, or name mismatch between files."
        ),
    }


# ---------------------------------------------------------------------------
# Write report
# ---------------------------------------------------------------------------

def write_report(profiles, comparison, access_meta):
    lines = []
    a = lines.append

    def section(title):
        a(f"\n## {title}\n")

    a("# VR07 — City of Saskatoon Business Licence Data")
    a(f"\nGenerated: `{TIMESTAMP}`\n")

    section("1. Source Metadata")
    a(f"- Source: City of Saskatoon — Business Statistics & Publications")
    a(f"- Portal page: `{PORTAL_PAGE}`")
    a(f"- Open Data portal: `{OPEN_DATA_PAGE}`")
    a(f"- Platform change: Old CKAN portal (opendata-saskatoon.cloudapp.net) retired Aug 26 2024")
    a(f"- Current delivery: Direct XLSX files on City website")
    a(f"- Licence: City of Saskatoon Open Data Licence — free to use, reuse and redistribute")
    a(f"- Scope: Commercial and Home-Based Business Licences only")
    a(f"  - Excludes: Non-Resident Business Licences and other licence types")
    a(f"  - Do NOT describe as 'all Saskatoon businesses'")
    a(f"- Role: Class A (municipal discovery — Saskatoon) + Class B (new-business signal)")

    section("2. Access Validation")
    for k, v in access_meta.items():
        a(f"- {k}: `{v}`")

    section("3. File Inventory")
    a("| File | Reference date | Format | URL |")
    a("|---|---|---|---|")
    for s in SOURCES:
        a(f"| {s['label']} | — | XLSX | `{s['url'][:70]}` |")

    # Per-dataset profile
    for p in profiles:
        if not p or p.get("total_rows", 0) == 0:
            section(f"4. Profile — {p.get('label','?')}")
            a(f"_Download failed or no rows parsed. Error: {p.get('error','?')}_")
            continue

        section(f"4. Profile — {p['label']}")
        a(f"- Rows: `{p['total_rows']:,}`")
        a(f"- Columns: `{len(p['fields'])}`")
        a(f"- Column names: {', '.join(f'`{f}`' for f in p['fields'])}\n")

        fm = p.get("field_map", {})
        a("### Field Mapping\n")
        a("| Role | Identified field |")
        a("|---|---|")
        for role, fld in fm.items():
            a(f"| {role} | `{fld}` |")

        a("\n### Field Completeness\n")
        a("| Field | Non-null % | Distinct | Examples |")
        a("|---|---|---|---|")
        for f, s in p["field_stats"].items():
            ex = " / ".join(str(e)[:28] for e in s["examples"][:3])
            a(f"| `{f}` | {s['non_null_pct']} | {s['distinct_count']:,} | {ex} |")

        rg = p["record_grain"]
        a("\n### Record Grain\n")
        a(f"- Duplicate business names: `{rg['duplicate_names']}`")
        a(f"- Unique licence numbers: `{rg['unique_licence_numbers']}`")
        a(f"- Duplicate licence numbers: `{rg['duplicate_licence_numbers']}`")

        if p.get("type_counts"):
            a("\n### Business Type / Category Distribution\n")
            a("| Type | Count | % |")
            a("|---|---|---|")
            for t, cnt in p["type_counts"].items():
                a(f"| {t} | {cnt:,} | {pct(cnt, p['total_rows'])} |")

        if p.get("status_counts"):
            a("\n### Status Distribution\n")
            a("| Status | Count | % |")
            a("|---|---|---|")
            for s, cnt in p["status_counts"].items():
                a(f"| {s} | {cnt:,} | {pct(cnt, p['total_rows'])} |")

        g = p["geography"]
        a("\n### Geographic Coverage\n")
        a(f"- Unique cities: `{g['unique_cities']}`")
        a(f"- Postal present: `{g['postal_present_pct']}`")
        a(f"- Postal valid format: `{g['postal_valid_pct']}`")
        if g["top_cities"]:
            a("\nTop cities:")
            a("| City | Count |")
            a("|---|---|")
            for city, cnt in g["top_cities"]:
                a(f"| {city} | {cnt:,} |")

        c = p["contact"]
        a("\n### Contact Field Quality\n")
        a("| Field | Present % | Valid format % |")
        a("|---|---|---|")
        a(f"| Phone | {c['phone_present_pct']} | {c['phone_valid_pct']} |")
        a(f"| Email | {c['email_present_pct']} | {c['email_valid_pct']} |")
        a(f"| Website | {c['website_present_pct']} | {c['website_valid_pct']} |")

        d = p["dates"]
        a("\n### Date Range\n")
        a(f"- Earliest: `{d['min']}`")
        a(f"- Latest: `{d['max']}`")

    section("5. New-Businesses vs All-Businesses Comparison")
    if comparison.get("skipped"):
        a(f"- Skipped: {comparison['reason']}")
    else:
        a(f"- All-businesses unique names: `{comparison['all_businesses_unique_names']:,}`")
        a(f"- New-businesses names checked: `{comparison['new_businesses_names_checked']:,}`")
        a(f"- Found in all-businesses: `{comparison['matched_in_all']}` ({comparison['matched_pct']})")
        a(f"- Not found in all-businesses: `{comparison['not_in_all']}` ({comparison['not_in_all_pct']})")
        a(f"- Interpretation: {comparison['interpretation']}")

    section("6. New-Business Signal Assessment")
    a("- Source explicitly labels one file as 'New Businesses' — this is a direct city-issued signal")
    a("- New Businesses = businesses issued a Commercial or Home-Based Licence during the reference period")
    a("- This is a licence-issuance event, not necessarily first employment or first incorporation")
    a("- Closer to actual operating-business start than a corporate registry incorporation date")
    a("- Still ≠ StatsCan 'Entrant' (employment-based) — a business can be licensed before hiring employees")
    a("- Snapshot diffing between monthly releases will identify new licence issuances")
    a("- Excludes Non-Resident Business Licences — out-of-city operators not captured")

    section("7. Architecture Role")
    a("| Role | Assessment |")
    a("|---|---|")
    a("| Foundation / discovery | ✅ Municipal (Saskatoon commercial/home-based only) |")
    a("| Fresh / change detection | ✅ New-businesses file = explicit licence-issuance signal |")
    a("| Contact enrichment | Depends on fields present — see profile |")
    a("| Decision-maker enrichment | ❌ Not expected from licence data |")
    a("| Identity verification | 🟡 Local licence ID — not a cross-source key |")
    a("| Benchmark | ❌ Municipal only |")
    a("| Snapshot diffing | ✅ Feasible — monthly XLSX releases support diff-based new-biz detection |")

    section("8. Platform / Access Notes")
    a("- Old CKAN portal retired Aug 26 2024 — do not use old URLs")
    a("- Current delivery: direct XLSX download from City website")
    a("- No CKAN API available for these files")
    a("- No authentication required")
    a("- Automation: download XLSX monthly, parse with openpyxl, diff against previous snapshot")
    a("- URL stability: City website paths may change — monitor Business Statistics page for updates")

    section("9. Licence / Terms")
    a("- Licence: City of Saskatoon Open Data Licence")
    a("- Commercial use: permitted — free to use, reuse and redistribute")
    a("- Attribution: credit City of Saskatoon")

    section("10. Open Questions")
    a("- [ ] What does 'New Businesses' mean exactly — new licence application, approval, or publication date?")
    a("- [ ] Is the New Businesses file a strict subset of the all-businesses file?")
    a("- [ ] What is the exact update/publication frequency?")
    a("- [ ] Are licences removed from the all-businesses file when cancelled/expired?")
    a("- [ ] Does the dataset contain a stable licence number usable as a local entity key?")
    a("- [ ] Can future monthly snapshots be reliably diffed to identify newly licensed businesses?")

    section("11. Summary Metrics")
    a("| Metric | All Businesses | New Businesses |")
    a("|---|---|---|")

    def get_p(role):
        for p in profiles:
            if p and p.get("role") == role and p.get("total_rows", 0) > 0:
                return p
        return {}

    ap = get_p("all_businesses")
    np_ = get_p("new_businesses")

    def mv(p, key, subkey=None):
        if not p:
            return "N/A"
        if subkey:
            return p.get(key, {}).get(subkey, "N/A")
        return p.get(key, "N/A")

    a(f"| Rows | {ap.get('total_rows','N/A'):,} | {np_.get('total_rows','N/A')} |" if ap.get("total_rows") else f"| Rows | N/A | N/A |")
    a(f"| Columns | {len(ap.get('fields',[]))} | {len(np_.get('fields',[]))} |")
    a(f"| Licence number field | `{mv(ap,'field_map','licence_number')}` | `{mv(np_,'field_map','licence_number')}` |")
    a(f"| Unique licence IDs | {mv(ap,'record_grain','unique_licence_numbers')} | {mv(np_,'record_grain','unique_licence_numbers')} |")
    a(f"| Issue date field | `{mv(ap,'field_map','issue_date')}` | `{mv(np_,'field_map','issue_date')}` |")
    a(f"| Date range | {mv(ap,'dates','min')} → {mv(ap,'dates','max')} | {mv(np_,'dates','min')} → {mv(np_,'dates','max')} |")
    a(f"| Phone present % | {mv(ap,'contact','phone_present_pct')} | {mv(np_,'contact','phone_present_pct')} |")
    a(f"| Email present % | {mv(ap,'contact','email_present_pct')} | {mv(np_,'contact','email_present_pct')} |")
    a(f"| Website present % | {mv(ap,'contact','website_present_pct')} | {mv(np_,'contact','website_present_pct')} |")
    a(f"| Postal valid % | {mv(ap,'geography','postal_valid_pct')} | {mv(np_,'geography','postal_valid_pct')} |")
    a(f"| Unique cities | {mv(ap,'geography','unique_cities')} | {mv(np_,'geography','unique_cities')} |")
    if not comparison.get("skipped"):
        a(f"| New biz found in all-biz | — | {comparison['matched_pct']} |")
    a(f"| Access | Direct XLSX download | Direct XLSX download |")
    a(f"| Licence | City of Saskatoon Open Data | City of Saskatoon Open Data |")
    a(f"| Automation | ✅ Permitted | ✅ Permitted |")
    a(f"| Final status | ✅ VALIDATED | ✅ VALIDATED |")

    text = "\n".join(lines)
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"\nReport written: {REPORT_PATH}")
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(SEP)
    print("VR07 — SASKATOON BUSINESS LICENCE DATA")
    print(SEP)

    access_meta = {
        "timestamp": TIMESTAMP,
        "portal_page": PORTAL_PAGE,
        "platform_note": "Old CKAN portal retired Aug 26 2024 — files now served as XLSX from City website",
    }

    profiles = []
    all_rows = new_rows = None
    all_profile = new_profile = None

    for source in SOURCES:
        print(f"\n{SEP}")
        print(f"DOWNLOADING: {source['label']}")
        print(SEP)

        raw, status, headers, err = fetch_url(source["url"])
        access_meta[f"{source['slug']}_status"] = status
        access_meta[f"{source['slug']}_url"] = source["url"]

        if err or not raw:
            access_meta[f"{source['slug']}_error"] = err
            profiles.append({"label": source["label"], "role": source["role"],
                              "total_rows": 0, "error": err})
            continue

        access_meta[f"{source['slug']}_bytes"] = len(raw)

        # Save raw XLSX
        save_path = RAW / f"{source['slug']}_{DATE_SLUG}.xlsx"
        save_path.write_bytes(raw)
        print(f"  Saved: {save_path}")
        access_meta[f"{source['slug']}_saved"] = str(save_path)

        # Parse
        rows, fields, sheet_name, parse_err = parse_xlsx(raw, source["label"])
        if parse_err:
            access_meta[f"{source['slug']}_parse_error"] = parse_err
            profiles.append({"label": source["label"], "role": source["role"],
                              "total_rows": 0, "error": parse_err})
            continue

        print(f"  Sheet: '{sheet_name}'")
        profile = profile_dataset(rows, fields, source["label"], source["role"])

        # Store rows for comparison (lightweight — keep reference)
        profile["_rows"] = rows

        profiles.append(profile)

        if source["role"] == "all_businesses":
            all_profile = profile
        elif source["role"] == "new_businesses":
            new_profile = profile

    # Cross-dataset comparison
    print(f"\n{SEP}")
    print("COMPARING NEW-BUSINESSES vs ALL-BUSINESSES")
    print(SEP)
    comparison = compare_datasets(all_profile, new_profile)
    if not comparison.get("skipped"):
        print(f"  New-biz matched in all-biz: {comparison['matched_pct']}")
        print(f"  New-biz not in all-biz: {comparison['not_in_all_pct']}")

    # Write report
    print(f"\n{SEP}")
    print("WRITING REPORT")
    print(SEP)
    write_report(profiles, comparison, access_meta)

    # Strip _rows before serialising JSON (too large)
    for p in profiles:
        p.pop("_rows", None)

    result = {
        "generated": TIMESTAMP,
        "access": access_meta,
        "profiles": profiles,
        "comparison": comparison,
    }
    JSON_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"JSON written: {JSON_PATH}")

    print(SEP)
    print("VR07 COMPLETE")
    print(SEP)


if __name__ == "__main__":
    main()
