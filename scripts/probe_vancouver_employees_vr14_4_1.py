"""
VR14.4.1 — Vancouver numberofemployees field profiling
Focused pass on the Vancouver business-licences dataset employee count field.

Checks:
1. Parse all values as numeric (float-string → int)
2. Count unique numeric values
3. min / max / median / most common values
4. Count zeros, negatives, nulls, non-numeric
5. Bucket distribution across the 9 required size bands
6. Sample records with unusually large values (>500)
7. Check employee consistency across repeated business names
8. Note metadata/documentation URL for semantic verification

Output:
  reports/validation_rounds/VR14_4_1_VANCOUVER_EMPLOYEES.json
  reports/validation_rounds/VR14_4_1_VANCOUVER_EMPLOYEES.md
"""

import urllib.request
import csv
import json
import io
import os
import re
from collections import Counter
from datetime import datetime, timezone

URL = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/business-licences/exports/csv?limit=-1&timezone=UTC&use_labels=false&epsg=4326&delimiter=%3B"
OUT_JSON = "reports/validation_rounds/VR14_4_1_VANCOUVER_EMPLOYEES.json"
OUT_MD   = "reports/validation_rounds/VR14_4_1_VANCOUVER_EMPLOYEES.md"
EMPLOYEE_COL = "numberofemployees"
NAME_COL     = "businessname"

# 9 required buckets from the assignment
BUCKETS = [
    (1, 4), (5, 9), (10, 19), (20, 49), (50, 99),
    (100, 199), (200, 499), (500, 999), (1000, None)
]
LARGE_THRESHOLD = 500  # sample records above this


def fetch_vancouver(max_bytes=60 * 1024 * 1024):
    print("Downloading Vancouver business licences...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (research)"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read(max_bytes)
    truncated = len(raw) == max_bytes
    text = raw.decode("utf-8", errors="replace")
    first_line = text.split("\n", 1)[0]
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for row in reader:
        rows.append({k.strip().lstrip("\ufeff").lower(): (v or "") for k, v in row.items() if k is not None})
    print(f"  Rows loaded: {len(rows)} {'(TRUNCATED)' if truncated else ''}")
    return rows, truncated


def parse_employee(val):
    """Parse float-string to int. Returns (int_value, error_type)."""
    v = (val or "").strip()
    if not v or v in ("", "NULL", "null", "N/A", "n/a"):
        return None, "null"
    try:
        f = float(v)
        if f != int(f):
            return int(f), "fractional_truncated"
        return int(f), None
    except ValueError:
        return None, "non_numeric"


def bucket_label(lo, hi):
    return f"{lo}-{hi}" if hi else f"{lo}+"


def main():
    os.makedirs("reports/validation_rounds", exist_ok=True)
    rows, truncated = fetch_vancouver()

    total = len(rows)
    parsed = []
    null_count = 0
    non_numeric_count = 0
    fractional_count = 0
    non_numeric_samples = []

    for r in rows:
        val = r.get(EMPLOYEE_COL, "")
        n, err = parse_employee(val)
        if err == "null":
            null_count += 1
        elif err == "non_numeric":
            non_numeric_count += 1
            if len(non_numeric_samples) < 10:
                non_numeric_samples.append(val)
        elif err == "fractional_truncated":
            fractional_count += 1
        parsed.append(n)

    valid_ints = [v for v in parsed if v is not None]
    zeros = sum(1 for v in valid_ints if v == 0)
    negatives = sum(1 for v in valid_ints if v < 0)
    positives = [v for v in valid_ints if v > 0]

    sorted_vals = sorted(valid_ints)
    median_val = sorted_vals[len(sorted_vals) // 2] if sorted_vals else None

    # Bucket distribution
    bucket_dist = {}
    for lo, hi in BUCKETS:
        label = bucket_label(lo, hi)
        if hi:
            bucket_dist[label] = sum(1 for v in valid_ints if lo <= v <= hi)
        else:
            bucket_dist[label] = sum(1 for v in valid_ints if v >= lo)

    # Top 20 most common values
    top_values = [{"value": v, "count": c} for v, c in Counter(valid_ints).most_common(20)]

    # Sample large-value records
    large_records = []
    for r in rows:
        val = r.get(EMPLOYEE_COL, "")
        n, _ = parse_employee(val)
        if n is not None and n >= LARGE_THRESHOLD:
            large_records.append({
                "businessname": r.get(NAME_COL, ""),
                "businesstype": r.get("businesstype", ""),
                "status": r.get("status", ""),
                "numberofemployees_raw": val,
                "numberofemployees_int": n,
                "issueddate": r.get("issueddate", ""),
                "licencenumber": r.get("licencenumber", ""),
            })
    large_records.sort(key=lambda x: x["numberofemployees_int"], reverse=True)
    large_samples = large_records[:20]

    # Check consistency across repeated business names
    # Group by businessname, collect unique employee values per name
    name_employees = {}
    for r, v in zip(rows, parsed):
        name = (r.get(NAME_COL) or "").strip()
        if name and v is not None:
            name_employees.setdefault(name, set()).add(v)

    # Names with multiple different employee values
    inconsistent = {
        name: sorted(vals)
        for name, vals in name_employees.items()
        if len(vals) > 1
    }
    inconsistent_count = len(inconsistent)
    # Sample 10 inconsistent names
    inconsistent_sample = {k: v for k, v in list(inconsistent.items())[:10]}

    result = {
        "vr": "VR14.4.1",
        "title": "Vancouver numberofemployees Field Profiling",
        "generated": datetime.now(timezone.utc).isoformat(),
        "source": "Vancouver Business Licences — opendata.vancouver.ca",
        "field": EMPLOYEE_COL,
        "total_rows": total,
        "truncated": truncated,
        "parse_summary": {
            "valid_integers_parsed": len(valid_ints),
            "null_or_empty": null_count,
            "non_numeric": non_numeric_count,
            "non_numeric_samples": non_numeric_samples,
            "fractional_truncated": fractional_count,
            "pct_valid": round(len(valid_ints) / total * 100, 1) if total else 0,
        },
        "numeric_summary": {
            "min": min(valid_ints) if valid_ints else None,
            "max": max(valid_ints) if valid_ints else None,
            "median": median_val,
            "zeros": zeros,
            "negatives": negatives,
            "positives": len(positives),
        },
        "bucket_distribution": bucket_dist,
        "top_20_values": top_values,
        "large_value_samples": large_samples,
        "consistency_across_business_names": {
            "business_names_with_employee_data": len(name_employees),
            "names_with_inconsistent_values": inconsistent_count,
            "pct_inconsistent": round(inconsistent_count / len(name_employees) * 100, 1) if name_employees else 0,
            "sample_inconsistent_names": inconsistent_sample,
            "interpretation_note": (
                "If the same businessname has different employee values across rows, "
                "this may indicate: (a) multiple licence records per business location, "
                "(b) records spanning different years with headcount changes, "
                "or (c) the field reflects licence-level data not company-level data."
            ),
        },
        "semantic_note": (
            "Vancouver Open Data documentation should be checked at "
            "https://opendata.vancouver.ca/explore/dataset/business-licences/information/ "
            "to confirm whether numberofemployees represents employees at the licensed location "
            "or total employees of the business entity. "
            "This determination cannot be made from the data values alone."
        ),
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nJSON written: {OUT_JSON}")

    write_md(result)
    print(f"MD written:   {OUT_MD}")

    # Print key stats to terminal
    ps = result["parse_summary"]
    ns = result["numeric_summary"]
    print(f"\n--- Key Stats ---")
    print(f"Total rows:     {total}")
    print(f"Valid integers: {ps['valid_integers_parsed']} ({ps['pct_valid']}%)")
    print(f"Null/empty:     {ps['null_or_empty']}")
    print(f"Non-numeric:    {ps['non_numeric']}")
    print(f"Fractional:     {ps['fractional_truncated']}")
    print(f"Min: {ns['min']}, Max: {ns['max']}, Median: {ns['median']}")
    print(f"Zeros: {ns['zeros']}, Negatives: {ns['negatives']}")
    print(f"\n--- Bucket Distribution ---")
    for label, count in result["bucket_distribution"].items():
        print(f"  {label:>10}: {count}")
    print(f"\n--- Consistency ---")
    cc = result["consistency_across_business_names"]
    print(f"Names with data: {cc['business_names_with_employee_data']}")
    print(f"Inconsistent:    {cc['names_with_inconsistent_values']} ({cc['pct_inconsistent']}%)")


def write_md(data):
    lines = []
    lines.append("# VR14.4.1 — Vancouver `numberofemployees` Field Profiling\n")
    lines.append(f"Generated: `{data['generated']}`  ")
    lines.append(f"Script: `scripts/probe_vancouver_employees_vr14_4_1.py`  ")
    lines.append(f"JSON: `{OUT_JSON}`\n")
    lines.append("---\n")
    lines.append("## Objective\n")
    lines.append(
        "Profile Vancouver's `numberofemployees` field before marking it usable as "
        "an employee-size signal. Determine value type, distribution, consistency, "
        "and flag the semantic question (location-level vs company-level).\n"
    )
    lines.append("---\n")

    ps = data["parse_summary"]
    ns = data["numeric_summary"]

    lines.append("## Parse Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total rows | {data['total_rows']} |")
    lines.append(f"| Valid integers parsed | {ps['valid_integers_parsed']} ({ps['pct_valid']}%) |")
    lines.append(f"| Null / empty | {ps['null_or_empty']} |")
    lines.append(f"| Non-numeric | {ps['non_numeric']} |")
    lines.append(f"| Float-truncated to int | {ps['fractional_truncated']} |")
    lines.append("")

    lines.append("## Numeric Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Min | {ns['min']} |")
    lines.append(f"| Max | {ns['max']} |")
    lines.append(f"| Median | {ns['median']} |")
    lines.append(f"| Zeros | {ns['zeros']} |")
    lines.append(f"| Negatives | {ns['negatives']} |")
    lines.append(f"| Positives | {ns['positives']} |")
    lines.append("")

    lines.append("## Bucket Distribution (Required 9 Bands)\n")
    lines.append("| Bucket | Count |")
    lines.append("|---|---|")
    for label, count in data["bucket_distribution"].items():
        lines.append(f"| {label} | {count} |")
    lines.append("")

    lines.append("## Top 20 Most Common Values\n")
    lines.append("| Employee Count | Occurrences |")
    lines.append("|---|---|")
    for entry in data["top_20_values"]:
        lines.append(f"| {entry['value']} | {entry['count']} |")
    lines.append("")

    lines.append("## Sample Records — Large Values (≥500 employees)\n")
    lines.append("| Business Name | Type | Status | Employees | Issued Date |")
    lines.append("|---|---|---|---|---|")
    for r in data["large_value_samples"]:
        lines.append(
            f"| {r['businessname']} | {r['businesstype']} | {r['status']} "
            f"| {r['numberofemployees_int']} | {r['issueddate'][:10] if r['issueddate'] else '—'} |"
        )
    lines.append("")

    cc = data["consistency_across_business_names"]
    lines.append("## Consistency Across Business Names\n")
    lines.append(f"- Unique business names with employee data: {cc['business_names_with_employee_data']}")
    lines.append(f"- Names with inconsistent values across rows: {cc['names_with_inconsistent_values']} ({cc['pct_inconsistent']}%)")
    lines.append(f"\n{cc['interpretation_note']}\n")
    lines.append("\n### Sample Inconsistent Names\n")
    lines.append("| Business Name | Employee Values Observed |")
    lines.append("|---|---|")
    for name, vals in cc["sample_inconsistent_names"].items():
        lines.append(f"| {name} | {vals} |")
    lines.append("")

    lines.append("## Semantic Note\n")
    lines.append(data["semantic_note"])
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
