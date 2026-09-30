"""
VR14.4 — ODBus 2022 vs Current-Source Comparison
Compares Calgary, Edmonton, Vancouver, Winnipeg current municipal licence datasets
against the ODBus 2022 snapshot for the same cities.
Also profiles Vancouver's numberofemployees field in detail.

Outputs:
  reports/validation_rounds/VR14_4_ODBUS_VS_CURRENT.json
  reports/validation_rounds/VR14_4_ODBUS_VS_CURRENT.md
"""

import urllib.request
import csv
import json
import io
import os
import re
from datetime import datetime, timezone

OUT_JSON = "reports/validation_rounds/VR14_4_ODBUS_VS_CURRENT.json"
OUT_MD   = "reports/validation_rounds/VR14_4_ODBUS_VS_CURRENT.md"
ODBUS_CSV = "data/raw/ODBus_Sources.csv"  # may not exist — handled gracefully

SOURCES = {
    "calgary": {
        "label": "Calgary Business Licences",
        "province": "AB",
        "portal": "data.calgary.ca (Socrata)",
        "url": "https://data.calgary.ca/api/views/vdjc-pybd/rows.csv?accessType=DOWNLOAD",
        "odbus_city": "Calgary",
        # All col names are lowercase to match normalised DictReader keys
        "name_col": "tradename",
        "address_col": "address",
        "postal_col": None,
        "phone_col": None,
        "email_col": None,
        "naics_col": None,
        "status_col": "jobstatusdesc",
        "licence_col": "getbusid",
        "new_biz_col": "first_iss_dt",
        "employee_col": None,
    },
    "edmonton": {
        "label": "Edmonton Business Licences",
        "province": "AB",
        "portal": "data.edmonton.ca (Socrata)",
        "url": "https://data.edmonton.ca/api/views/qhi4-bdpu/rows.csv?accessType=DOWNLOAD",
        "odbus_city": "Edmonton",
        # Edmonton headers: "Business Name", "Business Address", "Original Issue Date", "Licence Number"
        "name_col": "business name",
        "address_col": "business address",
        "postal_col": None,
        "phone_col": None,
        "email_col": None,
        "naics_col": None,
        "status_col": None,
        "licence_col": "licence number",
        "new_biz_col": "original issue date",
        "employee_col": None,
    },
    "vancouver": {
        "label": "Vancouver Business Licences",
        "province": "BC",
        "portal": "opendata.vancouver.ca (OpenDataSoft)",
        # OpenDataSoft export — semicolon delimited, handled by fetch_csv_ods()
        "url": "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/business-licences/exports/csv?limit=-1&timezone=UTC&use_labels=false&epsg=4326&delimiter=%3B",
        "odbus_city": "Vancouver",
        "name_col": "businessname",
        "address_col": "street",
        "postal_col": "postalcode",
        "phone_col": None,
        "email_col": None,
        "naics_col": None,
        "status_col": "status",
        "licence_col": "licencenumber",
        "new_biz_col": "issueddate",
        "employee_col": "numberofemployees",
    },
    "winnipeg": {
        "label": "Winnipeg Business Licences",
        "province": "MB",
        "portal": "data.winnipeg.ca (Socrata)",
        "url": "https://data.winnipeg.ca/api/views/d5k3-sfzx/rows.csv?accessType=DOWNLOAD",
        "odbus_city": "Winnipeg",
        # Winnipeg headers: "Trade Name", "Address", "Issue Date", "Status"
        "name_col": "trade name",
        "address_col": "address",
        "postal_col": None,
        "phone_col": None,
        "email_col": None,
        "naics_col": None,
        "status_col": "status",
        "licence_col": None,
        "new_biz_col": "issue date",
        "employee_col": None,
    },
}

# Required employee buckets from the assignment
EMPLOYEE_BUCKETS = [
    (1, 4), (5, 9), (10, 19), (20, 49), (50, 99),
    (100, 199), (200, 499), (500, 999), (1000, None)
]


def fetch_csv(url, max_bytes=60 * 1024 * 1024):
    """Download up to max_bytes of CSV. Returns (rows_list, columns, truncated, error).
    Auto-detects delimiter (comma or semicolon) from first line.
    Rows are normalised so every key is lowercase-stripped for consistent access."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research)"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read(max_bytes)
            truncated = len(raw) == max_bytes
        text = raw.decode("utf-8", errors="replace")
        # Auto-detect delimiter: if first line has more semicolons than commas, use semicolon
        first_line = text.split("\n", 1)[0]
        delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        raw_rows = list(reader)
        raw_columns = reader.fieldnames or []
        # Normalise: lowercase + strip all keys, strip BOM from first column
        columns = [c.strip().lstrip("\ufeff") for c in raw_columns if c is not None]
        rows = [
            {k.strip().lstrip("\ufeff").lower(): (v or "") for k, v in row.items() if k is not None}
            for row in raw_rows
        ]
        return rows, columns, truncated, None
    except Exception as e:
        return [], [], False, str(e)


def profile_field(rows, col):
    """Return basic presence/uniqueness stats for a column."""
    if col is None:
        return {"present_in_schema": False}
    vals = [r.get(col) or "" for r in rows]
    non_empty = [v for v in vals if v and v.strip() not in ("", "N/A", "NULL", "null", "None")]
    unique = set(non_empty)
    return {
        "present_in_schema": True,
        "total_rows": len(vals),
        "non_empty": len(non_empty),
        "pct_filled": round(len(non_empty) / len(vals) * 100, 1) if vals else 0,
        "unique_values": len(unique),
    }


def profile_dates(rows, col):
    """Sample earliest and latest dates from a date column."""
    if col is None:
        return {"present_in_schema": False}
    vals = [(r.get(col) or "").strip() for r in rows if (r.get(col) or "").strip()]
    if not vals:
        return {"present_in_schema": True, "non_empty": 0}
    # Grab sample of 5 earliest-looking and 5 latest-looking by sort
    sorted_vals = sorted(vals)
    return {
        "present_in_schema": True,
        "non_empty": len(vals),
        "sample_earliest_5": sorted_vals[:5],
        "sample_latest_5": sorted_vals[-5:],
    }


def profile_employee_count(rows, col):
    """
    Detailed profile of Vancouver's numberofemployees.
    Detects: integer vs bucket string, nulls, distribution across required buckets.
    """
    if col is None:
        return None
    raw_vals = [r.get(col, "") or "" for r in rows]
    empty = sum(1 for v in raw_vals if not v.strip() or v.strip() in ("NULL", "null", "N/A"))
    non_empty_vals = [v.strip() for v in raw_vals if v.strip() and v.strip() not in ("NULL", "null", "N/A")]

    # Classify: integer, range-string, or other
    integers = []
    ranges = []
    others = []
    for v in non_empty_vals:
        if re.match(r"^\d+$", v):
            integers.append(int(v))
        elif re.match(r"^\d+[\-–]\d+$", v):
            ranges.append(v)
        else:
            others.append(v)

    result = {
        "column": col,
        "total_rows": len(raw_vals),
        "empty_or_null": empty,
        "non_empty": len(non_empty_vals),
        "pct_non_empty": round(len(non_empty_vals) / len(raw_vals) * 100, 1) if raw_vals else 0,
        "value_type": "integer" if integers and not ranges else ("range_string" if ranges else "mixed"),
        "integer_count": len(integers),
        "range_string_count": len(ranges),
        "other_count": len(others),
        "other_samples": list(set(others))[:10],
    }

    if integers:
        result["min"] = min(integers)
        result["max"] = max(integers)
        result["zero_count"] = sum(1 for i in integers if i == 0)
        # Distribution across required buckets
        bucket_dist = {}
        for lo, hi in EMPLOYEE_BUCKETS:
            label = f"{lo}-{hi}" if hi else f"{lo}+"
            if hi:
                count = sum(1 for i in integers if lo <= i <= hi)
            else:
                count = sum(1 for i in integers if i >= lo)
            bucket_dist[label] = count
        result["bucket_distribution"] = bucket_dist
        # Sample values
        from collections import Counter
        top = Counter(integers).most_common(10)
        result["most_common_values"] = [{"value": v, "count": c} for v, c in top]

    if ranges:
        from collections import Counter
        result["range_samples"] = list(set(ranges))[:10]

    return result


def load_odbus_for_city(city_name):
    """Load ODBus rows matching a city name. Returns dict or None if file absent."""
    if not os.path.exists(ODBUS_CSV):
        return None
    try:
        with open(ODBUS_CSV, encoding="cp1252", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = [r for r in reader if city_name.lower() in (r.get("City", "") or "").lower()]
        return {
            "odbus_rows_for_city": len(rows),
            "odbus_columns": list(rows[0].keys()) if rows else [],
            "note": f"ODBus snapshot rows where City contains '{city_name}'"
        }
    except Exception as e:
        return {"error": str(e)}


def compare_source(key, cfg):
    print(f"\n--- {cfg['label']} ---")
    rows, columns, truncated, err = fetch_csv(cfg["url"])

    result = {
        "source": cfg["label"],
        "city": key.capitalize(),
        "province": cfg["province"],
        "portal": cfg["portal"],
        "url": cfg["url"],
        "fetch_error": err,
        "row_count_fetched": len(rows),
        "truncated": truncated,
        "columns": columns,
    }

    if err:
        print(f"  ERROR: {err}")
        result["odbus_comparison"] = load_odbus_for_city(cfg["odbus_city"])
        return result

    print(f"  Rows fetched: {len(rows)} {'(truncated)' if truncated else ''}")
    print(f"  Columns ({len(columns)}): {columns}")
    if rows:
        print(f"  Normalised keys (first row sample): {list(rows[0].keys())[:8]}")

    # Field presence profiling
    result["field_profiles"] = {
        "name":    profile_field(rows, cfg["name_col"]),
        "address": profile_field(rows, cfg["address_col"]),
        "postal":  profile_field(rows, cfg["postal_col"]),
        "phone":   profile_field(rows, cfg["phone_col"]),
        "email":   profile_field(rows, cfg["email_col"]),
        "naics":   profile_field(rows, cfg["naics_col"]),
        "status":  profile_field(rows, cfg["status_col"]),
        "licence": profile_field(rows, cfg["licence_col"]),
        "new_biz_date": profile_field(rows, cfg["new_biz_col"]),
    }

    # Date range
    result["date_range"] = profile_dates(rows, cfg["new_biz_col"])

    # Status distribution
    if cfg["status_col"] and cfg["status_col"] in (columns or []):
        from collections import Counter
        status_counts = Counter(r.get(cfg["status_col"], "").strip() for r in rows)
        result["status_distribution"] = dict(status_counts.most_common(15))

    # Employee profiling (Vancouver only)
    if cfg["employee_col"]:
        result["employee_profile"] = profile_employee_count(rows, cfg["employee_col"])

    # ODBus comparison
    result["odbus_comparison"] = load_odbus_for_city(cfg["odbus_city"])

    # Summary booleans for comparison table
    fp = result["field_profiles"]
    result["field_matrix"] = {
        "name":         fp["name"].get("pct_filled", 0) > 50,
        "address":      fp["address"].get("pct_filled", 0) > 50,
        "postal_code":  fp["postal"].get("present_in_schema", False),
        "phone":        fp["phone"].get("present_in_schema", False),
        "email":        fp["email"].get("present_in_schema", False),
        "naics":        fp["naics"].get("present_in_schema", False),
        "status":       fp["status"].get("present_in_schema", False),
        "licence_id":   fp["licence"].get("present_in_schema", False),
        "new_biz_date": fp["new_biz_date"].get("present_in_schema", False),
        "employee_count": cfg["employee_col"] is not None,
    }

    return result


def main():
    os.makedirs("reports/validation_rounds", exist_ok=True)
    results = {}
    for key, cfg in SOURCES.items():
        results[key] = compare_source(key, cfg)

    # Assemble JSON output
    output = {
        "vr": "VR14.4",
        "title": "ODBus 2022 vs Current-Source Comparison",
        "generated": datetime.now(timezone.utc).isoformat(),
        "scope": "Calgary, Edmonton, Vancouver, Winnipeg — ODBus snapshot vs 2026 live sources",
        "sources": results,
        "summary": build_summary(results),
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nJSON written: {OUT_JSON}")

    write_md(output)
    print(f"MD written:   {OUT_MD}")


def build_summary(results):
    rows = []
    for key, r in results.items():
        if r.get("fetch_error"):
            rows.append({"city": key, "status": "ERROR", "error": r["fetch_error"]})
            continue
        fm = r.get("field_matrix", {})
        rows.append({
            "city": key.capitalize(),
            "province": r.get("province"),
            "rows_fetched": r.get("row_count_fetched"),
            "truncated": r.get("truncated"),
            "field_matrix": fm,
        })
    return rows


def write_md(data):
    lines = []
    lines.append(f"# VR14.4 — ODBus 2022 vs Current-Source Comparison\n")
    lines.append(f"Generated: `{data['generated']}`  ")
    lines.append(f"Script: `scripts/probe_odbus_vr14_4.py`  ")
    lines.append(f"JSON: `reports/validation_rounds/VR14_4_ODBUS_VS_CURRENT.json`\n")
    lines.append("---\n")
    lines.append("## Objective\n")
    lines.append(
        "Quantify the freshness and field gain from ingesting current municipal licence "
        "sources directly vs relying on the ODBus 2022 snapshot. "
        "Profile Vancouver `numberofemployees` in detail against the 9 required size buckets.\n"
    )
    lines.append("---\n")
    lines.append("## Field Matrix Summary\n")
    lines.append("| City | Prov | Rows | Name | Address | Postal | Phone | Email | NAICS | Status | Licence ID | New-Biz Date | Employee Count |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    check = lambda b: "✅" if b else "❌"
    for s in data["summary"]:
        if "error" in s:
            lines.append(f"| {s['city']} | — | ERROR | — | — | — | — | — | — | — | — | — | — |")
            continue
        fm = s.get("field_matrix", {})
        trunc = " *(trunc)*" if s.get("truncated") else ""
        lines.append(
            f"| {s['city']} | {s['province']} | {s['rows_fetched']}{trunc} "
            f"| {check(fm.get('name'))} | {check(fm.get('address'))} "
            f"| {check(fm.get('postal_code'))} | {check(fm.get('phone'))} "
            f"| {check(fm.get('email'))} | {check(fm.get('naics'))} "
            f"| {check(fm.get('status'))} | {check(fm.get('licence_id'))} "
            f"| {check(fm.get('new_biz_date'))} | {check(fm.get('employee_count'))} |"
        )
    lines.append("")

    for key, r in data["sources"].items():
        lines.append(f"---\n")
        lines.append(f"## {r.get('label', key.capitalize())}\n")
        if r.get("fetch_error"):
            lines.append(f"**FETCH ERROR:** `{r['fetch_error']}`\n")
            if r.get("odbus_comparison"):
                lines.append(f"ODBus rows for this city: {r['odbus_comparison']}\n")
            continue

        lines.append(f"- Portal: {r.get('portal')}")
        lines.append(f"- Rows fetched: {r.get('row_count_fetched')} {'*(truncated at 12MB)*' if r.get('truncated') else ''}")
        lines.append(f"- Columns ({len(r.get('columns', []))}): `{', '.join(r.get('columns', []))}`\n")

        # Field profiles table
        lines.append("### Field Profiles\n")
        lines.append("| Field | In Schema | % Filled | Unique Values |")
        lines.append("|---|---|---|---|")
        for fname, fp in r.get("field_profiles", {}).items():
            in_schema = "✅" if fp.get("present_in_schema") else "❌"
            pct = f"{fp.get('pct_filled', '—')}%" if fp.get("present_in_schema") else "—"
            uniq = fp.get("unique_values", "—") if fp.get("present_in_schema") else "—"
            lines.append(f"| {fname} | {in_schema} | {pct} | {uniq} |")
        lines.append("")

        # Date range
        dr = r.get("date_range", {})
        if dr.get("non_empty"):
            lines.append(f"### New-Business Date Range")
            lines.append(f"- Non-empty: {dr['non_empty']}")
            lines.append(f"- Earliest sample: {dr.get('sample_earliest_5', [])}")
            lines.append(f"- Latest sample: {dr.get('sample_latest_5', [])}\n")

        # Status distribution
        if r.get("status_distribution"):
            lines.append("### Status Distribution\n")
            lines.append("| Status | Count |")
            lines.append("|---|---|")
            for s, c in r["status_distribution"].items():
                lines.append(f"| {s or '(blank)'} | {c} |")
            lines.append("")

        # Employee profile (Vancouver)
        ep = r.get("employee_profile")
        if ep:
            lines.append("### Employee Count Profile (`numberofemployees`)\n")
            lines.append(f"- Total rows: {ep.get('total_rows')}")
            lines.append(f"- Empty/null: {ep.get('empty_or_null')} ({100 - ep.get('pct_non_empty', 0):.1f}%)")
            lines.append(f"- Non-empty: {ep.get('non_empty')} ({ep.get('pct_non_empty')}%)")
            lines.append(f"- Value type: `{ep.get('value_type')}`")
            if ep.get("min") is not None:
                lines.append(f"- Min: {ep['min']}, Max: {ep['max']}, Zero count: {ep.get('zero_count')}")
            if ep.get("bucket_distribution"):
                lines.append("\n#### Distribution Across Required Buckets\n")
                lines.append("| Bucket | Count |")
                lines.append("|---|---|")
                for bucket, count in ep["bucket_distribution"].items():
                    lines.append(f"| {bucket} | {count} |")
            if ep.get("most_common_values"):
                lines.append("\n#### Top 10 Most Common Values\n")
                lines.append("| Value | Count |")
                lines.append("|---|---|")
                for entry in ep["most_common_values"]:
                    lines.append(f"| {entry['value']} | {entry['count']} |")
            lines.append("")

        # ODBus comparison
        odc = r.get("odbus_comparison")
        if odc:
            lines.append("### ODBus 2022 Comparison\n")
            if odc.get("error"):
                lines.append(f"ODBus CSV not found or error: `{odc['error']}`\n")
            else:
                lines.append(f"- ODBus rows for this city: {odc.get('odbus_rows_for_city', 'N/A')}")
                lines.append(f"- ODBus columns: `{', '.join(odc.get('odbus_columns', []))}`")
                lines.append(f"- Note: {odc.get('note', '')}\n")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
