"""
VR05 — Statistics Canada Business Counts Validation

Downloads and profiles two StatsCan tables:
  VR05-A: Table 33-10-1174-01 — Canadian Business Counts, with employees (June 2026)
  VR05-B: Table 33-10-0722-01 — Business Openings and Closures (monthly, experimental)

Key question: Do the StatsCan employment-size labels map cleanly to the
assignment's required buckets: 1-4, 5-9, 10-19, 20-49, 50-99, 100-199,
200-499, 500-999, 1000+?

Output:
  data/raw/statcan_33101174.zip
  data/raw/statcan_33100722.zip
  reports/validation_rounds/VR05_STATSCAN_BUSINESS_COUNTS.md
"""
from __future__ import annotations

import csv
import io
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports" / "validation_rounds"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = REPORTS_DIR / "VR05_STATSCAN_BUSINESS_COUNTS.md"

HEADERS = {
    "User-Agent": "CanadaBusinessDataAutomation/0.1 (research/validation)",
    "Accept": "*/*",
}

# StatsCan standard bulk CSV ZIP URL pattern
# https://www150.statcan.gc.ca/n1/tbl/csv/{table_id_nodash}-eng.zip
STATSCAN_ZIP_BASE = "https://www150.statcan.gc.ca/n1/tbl/csv"

TABLES = [
    {
        "id": "33-10-1174-01",
        "id_nodash": "33101174",
        "label": "Canadian Business Counts, with employees",
        "key": "A",
        "zip_file": RAW_DIR / "statcan_33101174.zip",
        "current_release": "June 2026",
        "frequency": "Semi-annual",
        "role": "Class D — employment-size + NAICS + geography benchmark",
    },
    {
        "id": "33-10-0722-01",
        "id_nodash": "33100722",
        "label": "Canadian Business Openings and Closures",
        "key": "B",
        "zip_file": RAW_DIR / "statcan_33100722.zip",
        "current_release": "2026 (monthly, back to Jan 2015)",
        "frequency": "Monthly",
        "role": "Class D — new-business/closure benchmark (experimental estimates)",
    },
]

# Assignment's required employment-size buckets for comparison
REQUIRED_BUCKETS = [
    "1-4", "5-9", "10-19", "20-49", "50-99",
    "100-199", "200-499", "500-999", "1000+",
]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_zip(url: str, dest: Path) -> tuple[bool, str]:
    """Download a ZIP to dest. Returns (success, message)."""
    print(f"Downloading: {url}")
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=120) as resp:
            content = resp.read()
        dest.write_bytes(content)
        print(f"  → {len(content):,} bytes saved to {dest.name}")
        return True, f"{len(content):,} bytes"
    except HTTPError as e:
        msg = f"HTTP {e.code}"
        print(f"  → {msg}")
        return False, msg
    except URLError as e:
        msg = f"URLError: {e}"
        print(f"  → {msg}")
        return False, msg


def ensure_downloaded(table: dict) -> bool:
    """Download the ZIP if not already present."""
    dest: Path = table["zip_file"]

    if dest.exists():
        print(f"Using existing file: {dest.name} ({dest.stat().st_size:,} bytes)")
        return True

    url = f"{STATSCAN_ZIP_BASE}/{table['id_nodash']}-eng.zip"
    ok, _ = download_zip(url, dest)
    return ok


# ---------------------------------------------------------------------------
# ZIP inspection
# ---------------------------------------------------------------------------

def list_zip_contents(zip_path: Path) -> list[str]:
    """Return list of filenames inside the ZIP."""
    with zipfile.ZipFile(zip_path) as zf:
        return zf.namelist()


def read_csv_from_zip(zip_path: Path, filename: str) -> list[dict]:
    """Read a CSV file from inside a ZIP. Returns list of row dicts."""
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(filename) as f:
            text = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")
            reader = csv.DictReader(text)
            return list(reader)


# ---------------------------------------------------------------------------
# Profile helpers
# ---------------------------------------------------------------------------

def get_unique_values(rows: list[dict], field: str) -> list[str]:
    """Return sorted unique values for a field."""
    return sorted({row.get(field, "") for row in rows if row.get(field, "")})


def get_column_names(rows: list[dict]) -> list[str]:
    """Return column names from first row."""
    if not rows:
        return []
    return list(rows[0].keys())


def find_employment_size_column(columns: list[str]) -> str | None:
    """Heuristically identify the employment-size dimension column."""
    candidates = [
        c for c in columns
        if any(kw in c.lower() for kw in [
            "employ", "size", "class", "worker", "staff", "headcount"
        ])
    ]
    return candidates[0] if candidates else None


def find_geography_column(columns: list[str]) -> str | None:
    candidates = [
        c for c in columns
        if any(kw in c.lower() for kw in [
            "geo", "province", "region", "geography", "location"
        ])
    ]
    return candidates[0] if candidates else None


def find_naics_column(columns: list[str]) -> str | None:
    candidates = [
        c for c in columns
        if any(kw in c.lower() for kw in ["naics", "industry", "sector"])
    ]
    return candidates[0] if candidates else None


def find_date_column(columns: list[str]) -> str | None:
    candidates = [
        c for c in columns
        if any(kw in c.lower() for kw in ["ref_date", "date", "period", "month", "year"])
    ]
    return candidates[0] if candidates else None


def find_value_column(columns: list[str]) -> str | None:
    candidates = [
        c for c in columns
        if any(kw in c.lower() for kw in ["value", "count", "number", "val"])
    ]
    return candidates[0] if candidates else None


def find_symbol_column(columns: list[str]) -> str | None:
    """Find suppression/symbol column."""
    candidates = [
        c for c in columns
        if any(kw in c.lower() for kw in ["symbol", "suppressed", "flag", "status"])
    ]
    return candidates[0] if candidates else None


def map_to_required_buckets(observed: list[str]) -> dict:
    """
    Attempt to map observed employment-size labels to the 9 required buckets.
    Returns dict of required_bucket -> list of matching observed labels.
    """
    mapping = {b: [] for b in REQUIRED_BUCKETS}
    unmatched = []

    for label in observed:
        label_norm = label.lower().replace(" ", "").replace(",", "").replace("–", "-").replace("—", "-")
        matched = False
        for bucket in REQUIRED_BUCKETS:
            bucket_norm = bucket.lower().replace(" ", "")
            if bucket_norm in label_norm or label_norm in bucket_norm:
                mapping[bucket].append(label)
                matched = True
                break
        if not matched:
            # Try numeric range matching
            import re
            nums = re.findall(r"\d+", label_norm)
            if nums:
                first = int(nums[0])
                if first >= 1000 or "1000" in label_norm or "1,000" in label.lower():
                    mapping["1000+"].append(label)
                    matched = True
                elif first >= 500:
                    mapping["500-999"].append(label)
                    matched = True
                elif first >= 200:
                    mapping["200-499"].append(label)
                    matched = True
                elif first >= 100:
                    mapping["100-199"].append(label)
                    matched = True
                elif first >= 50:
                    mapping["50-99"].append(label)
                    matched = True
                elif first >= 20:
                    mapping["20-49"].append(label)
                    matched = True
                elif first >= 10:
                    mapping["10-19"].append(label)
                    matched = True
                elif first >= 5:
                    mapping["5-9"].append(label)
                    matched = True
                elif first >= 1:
                    mapping["1-4"].append(label)
                    matched = True
            if not matched:
                unmatched.append(label)

    return {"mapping": mapping, "unmatched": unmatched}


# ---------------------------------------------------------------------------
# Profile table A — Business Counts with employees
# ---------------------------------------------------------------------------

def profile_table_a(zip_path: Path) -> dict:
    print("\nProfiling Table A — 33-10-1174-01")
    print("-" * 40)

    contents = list_zip_contents(zip_path)
    print(f"ZIP contents: {contents}")

    # Find the main data CSV (not the metadata CSV)
    data_file = next(
        (f for f in contents if f.endswith(".csv") and "MetaData" not in f),
        contents[0] if contents else None,
    )
    meta_file = next(
        (f for f in contents if "MetaData" in f),
        None,
    )

    print(f"Data file: {data_file}")
    print(f"Meta file: {meta_file}")

    rows = read_csv_from_zip(zip_path, data_file)
    columns = get_column_names(rows)

    print(f"Rows: {len(rows):,}")
    print(f"Columns: {columns}")

    emp_col = find_employment_size_column(columns)
    geo_col = find_geography_column(columns)
    naics_col = find_naics_column(columns)
    date_col = find_date_column(columns)
    val_col = find_value_column(columns)
    sym_col = find_symbol_column(columns)

    print(f"Employment col: {emp_col}")
    print(f"Geography col:  {geo_col}")
    print(f"NAICS col:      {naics_col}")
    print(f"Date col:       {date_col}")
    print(f"Value col:      {val_col}")
    print(f"Symbol col:     {sym_col}")

    emp_labels = get_unique_values(rows, emp_col) if emp_col else []
    geo_labels = get_unique_values(rows, geo_col) if geo_col else []
    naics_labels = get_unique_values(rows, naics_col) if naics_col else []
    date_labels = get_unique_values(rows, date_col) if date_col else []

    print(f"\nEmployment-size labels ({len(emp_labels)}):")
    for label in emp_labels:
        print(f"  {label!r}")

    print(f"\nGeography values ({len(geo_labels)}): {geo_labels[:10]}{'...' if len(geo_labels) > 10 else ''}")
    print(f"NAICS values ({len(naics_labels)}): showing first 5: {naics_labels[:5]}")
    print(f"Date range: {date_labels[:1]} → {date_labels[-1:]}")

    # Suppression
    sym_counts: Counter = Counter()
    if sym_col:
        for row in rows:
            sym_counts[row.get(sym_col, "")] += 1

    # Bucket mapping
    bucket_map = map_to_required_buckets(emp_labels)
    print(f"\nBucket mapping:")
    for bucket, matches in bucket_map["mapping"].items():
        status = "✅" if matches else "❌"
        print(f"  {status} {bucket}: {matches}")
    if bucket_map["unmatched"]:
        print(f"  Unmatched: {bucket_map['unmatched']}")

    return {
        "data_file": data_file,
        "meta_file": meta_file,
        "row_count": len(rows),
        "columns": columns,
        "emp_col": emp_col,
        "geo_col": geo_col,
        "naics_col": naics_col,
        "date_col": date_col,
        "val_col": val_col,
        "sym_col": sym_col,
        "emp_labels": emp_labels,
        "geo_labels": geo_labels,
        "naics_labels": naics_labels,
        "date_labels": date_labels,
        "sym_counts": sym_counts,
        "bucket_map": bucket_map,
    }


# ---------------------------------------------------------------------------
# Profile table B — Business Openings and Closures
# ---------------------------------------------------------------------------

def profile_table_b(zip_path: Path) -> dict:
    print("\nProfiling Table B — 33-10-0722-01")
    print("-" * 40)

    contents = list_zip_contents(zip_path)
    print(f"ZIP contents: {contents}")

    data_file = next(
        (f for f in contents if f.endswith(".csv") and "MetaData" not in f),
        contents[0] if contents else None,
    )
    meta_file = next(
        (f for f in contents if "MetaData" in f),
        None,
    )

    print(f"Data file: {data_file}")
    print(f"Meta file: {meta_file}")

    rows = read_csv_from_zip(zip_path, data_file)
    columns = get_column_names(rows)

    print(f"Rows: {len(rows):,}")
    print(f"Columns: {columns}")

    emp_col = find_employment_size_column(columns)
    geo_col = find_geography_column(columns)
    naics_col = find_naics_column(columns)
    date_col = find_date_column(columns)
    val_col = find_value_column(columns)
    sym_col = find_symbol_column(columns)

    print(f"Employment col: {emp_col}")
    print(f"Geography col:  {geo_col}")
    print(f"NAICS col:      {naics_col}")
    print(f"Date col:       {date_col}")
    print(f"Value col:      {val_col}")
    print(f"Symbol col:     {sym_col}")

    emp_labels = get_unique_values(rows, emp_col) if emp_col else []
    geo_labels = get_unique_values(rows, geo_col) if geo_col else []
    naics_labels = get_unique_values(rows, naics_col) if naics_col else []
    date_labels = get_unique_values(rows, date_col) if date_col else []
    sym_counts: Counter = Counter()
    if sym_col:
        for row in rows:
            sym_counts[row.get(sym_col, "")] += 1

    # Find "type" dimension — openings / closures / continuing
    type_col = next(
        (c for c in columns if any(kw in c.lower() for kw in [
            "type", "status", "category", "business type", "opening", "closure"
        ])),
        None,
    )
    type_labels = get_unique_values(rows, type_col) if type_col else []

    # Seasonal adjustment
    seasonal_col = next(
        (c for c in columns if any(kw in c.lower() for kw in [
            "season", "adjust", "unadjust"
        ])),
        None,
    )
    seasonal_labels = get_unique_values(rows, seasonal_col) if seasonal_col else []

    print(f"\nEmployment-size labels ({len(emp_labels)}): {emp_labels}")
    print(f"Type/category labels ({len(type_labels)}): {type_labels}")
    print(f"Seasonal adjustment values: {seasonal_labels}")
    print(f"Date range: {date_labels[:1]} → {date_labels[-1:]}")
    print(f"Geography ({len(geo_labels)}): {geo_labels[:8]}{'...' if len(geo_labels) > 8 else ''}")
    print(f"NAICS ({len(naics_labels)}): first 5: {naics_labels[:5]}")

    bucket_map = map_to_required_buckets(emp_labels)

    return {
        "data_file": data_file,
        "meta_file": meta_file,
        "row_count": len(rows),
        "columns": columns,
        "emp_col": emp_col,
        "geo_col": geo_col,
        "naics_col": naics_col,
        "date_col": date_col,
        "val_col": val_col,
        "sym_col": sym_col,
        "type_col": type_col,
        "seasonal_col": seasonal_col,
        "emp_labels": emp_labels,
        "geo_labels": geo_labels,
        "naics_labels": naics_labels,
        "date_labels": date_labels,
        "type_labels": type_labels,
        "seasonal_labels": seasonal_labels,
        "sym_counts": sym_counts,
        "bucket_map": bucket_map,
    }


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(results: dict) -> None:
    a = results.get("a", {})
    b = results.get("b", {})

    lines = [
        "# VR05 — Statistics Canada Business Counts",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Sources",
        "",
        "| Table | ID | Label | Release | Role |",
        "|---|---|---|---|---|",
        "| A | `33-10-1174-01` | Canadian Business Counts, with employees | June 2026 | Class D benchmark |",
        "| B | `33-10-0722-01` | Business Openings and Closures | Monthly (Jan 2015–) | Class D benchmark (experimental) |",
        "",
        "Both tables downloaded as full bulk CSV ZIP from:",
        "`https://www150.statcan.gc.ca/n1/tbl/csv/{table_id}-eng.zip`",
        "",
        "---",
        "",
        "## Table A — Canadian Business Counts, with employees (33-10-1174-01)",
        "",
    ]

    if a:
        lines += [
            f"- Data file: `{a.get('data_file')}`",
            f"- Rows: `{a.get('row_count', 0):,}`",
            f"- Columns: `{len(a.get('columns', []))}`",
            "",
            "### A.1 Column names",
            "",
        ]
        for col in a.get("columns", []):
            lines.append(f"- `{col}`")

        lines += [
            "",
            "### A.2 Key dimension columns identified",
            "",
            f"| Dimension | Column name |",
            f"|---|---|",
            f"| Employment size | `{a.get('emp_col')}` |",
            f"| Geography | `{a.get('geo_col')}` |",
            f"| NAICS | `{a.get('naics_col')}` |",
            f"| Reference date | `{a.get('date_col')}` |",
            f"| Value | `{a.get('val_col')}` |",
            f"| Symbol/suppression | `{a.get('sym_col')}` |",
            "",
            "### A.3 Employment-size labels (actual values in data)",
            "",
            "| # | Label as it appears in data |",
            "|---|---|",
        ]
        for i, label in enumerate(a.get("emp_labels", []), 1):
            lines.append(f"| {i} | `{label}` |")

        lines += [
            "",
            "### A.4 Employment-size → required bucket mapping",
            "",
            "Required buckets: `1-4, 5-9, 10-19, 20-49, 50-99, 100-199, 200-499, 500-999, 1000+`",
            "",
            "| Required bucket | Matching StatsCan label(s) | Mappable? |",
            "|---|---|---|",
        ]
        bmap = a.get("bucket_map", {}).get("mapping", {})
        for bucket in REQUIRED_BUCKETS:
            matches = bmap.get(bucket, [])
            mappable = "✅" if matches else "❌ GAP"
            lines.append(f"| `{bucket}` | {', '.join(f'`{m}`' for m in matches) or '—'} | {mappable} |")

        unmatched = a.get("bucket_map", {}).get("unmatched", [])
        if unmatched:
            lines += [
                "",
                "**Unmatched StatsCan labels (do not map to any required bucket):**",
                "",
            ]
            for u in unmatched:
                lines.append(f"- `{u}`")

        lines += [
            "",
            "### A.5 Geography values",
            "",
            f"Total: {len(a.get('geo_labels', []))}",
            "",
        ]
        for g in a.get("geo_labels", []):
            lines.append(f"- `{g}`")

        lines += [
            "",
            "### A.6 NAICS dimension",
            "",
            f"Unique NAICS values: `{len(a.get('naics_labels', []))}`",
            "",
            "First 10:",
        ]
        for n in a.get("naics_labels", [])[:10]:
            lines.append(f"- `{n}`")

        lines += [
            "",
            "### A.7 Reference dates",
            "",
            f"- Earliest: `{a.get('date_labels', ['?'])[0]}`",
            f"- Latest: `{a.get('date_labels', ['?'])[-1]}`",
            f"- Total periods: `{len(a.get('date_labels', []))}`",
            "",
            "### A.8 Suppression / symbols",
            "",
        ]
        sym_counts = a.get("sym_counts", {})
        if sym_counts:
            lines += ["| Symbol | Count |", "|---|---:|"]
            for sym, cnt in sorted(sym_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| `{sym!r}` | {cnt:,} |")
        else:
            lines.append("No symbol column identified.")

    else:
        lines.append("**Download failed — no data profiled.**")

    lines += [
        "",
        "---",
        "",
        "## Table B — Business Openings and Closures (33-10-0722-01)",
        "",
    ]

    if b:
        lines += [
            f"- Data file: `{b.get('data_file')}`",
            f"- Rows: `{b.get('row_count', 0):,}`",
            f"- Columns: `{len(b.get('columns', []))}`",
            "",
            "### B.1 Column names",
            "",
        ]
        for col in b.get("columns", []):
            lines.append(f"- `{col}`")

        lines += [
            "",
            "### B.2 Key dimension columns identified",
            "",
            "| Dimension | Column name |",
            "|---|---|",
            f"| Employment size | `{b.get('emp_col')}` |",
            f"| Geography | `{b.get('geo_col')}` |",
            f"| NAICS | `{b.get('naics_col')}` |",
            f"| Reference date | `{b.get('date_col')}` |",
            f"| Value | `{b.get('val_col')}` |",
            f"| Opening/closure type | `{b.get('type_col')}` |",
            f"| Seasonal adjustment | `{b.get('seasonal_col')}` |",
            f"| Symbol/suppression | `{b.get('sym_col')}` |",
            "",
            "### B.3 Opening/closure type categories",
            "",
        ]
        for t in b.get("type_labels", []):
            lines.append(f"- `{t}`")

        lines += [
            "",
            "### B.4 Employment-size labels",
            "",
            "| # | Label as it appears in data |",
            "|---|---|",
        ]
        for i, label in enumerate(b.get("emp_labels", []), 1):
            lines.append(f"| {i} | `{label}` |")

        lines += [
            "",
            "### B.5 Employment-size → required bucket mapping",
            "",
            "| Required bucket | Matching StatsCan label(s) | Mappable? |",
            "|---|---|---|",
        ]
        bmap = b.get("bucket_map", {}).get("mapping", {})
        for bucket in REQUIRED_BUCKETS:
            matches = bmap.get(bucket, [])
            mappable = "✅" if matches else "❌ GAP"
            lines.append(f"| `{bucket}` | {', '.join(f'`{m}`' for m in matches) or '—'} | {mappable} |")

        lines += [
            "",
            "### B.6 Seasonal adjustment values",
            "",
        ]
        for s in b.get("seasonal_labels", []):
            lines.append(f"- `{s}`")

        lines += [
            "",
            "### B.7 Date range",
            "",
            f"- Earliest: `{b.get('date_labels', ['?'])[0]}`",
            f"- Latest: `{b.get('date_labels', ['?'])[-1]}`",
            f"- Total periods: `{len(b.get('date_labels', []))}`",
            "",
            "### B.8 Geography values",
            "",
            f"Total: {len(b.get('geo_labels', []))}",
            "",
        ]
        for g in b.get("geo_labels", []):
            lines.append(f"- `{g}`")

        lines += [
            "",
            "### B.9 Suppression / symbols",
            "",
        ]
        sym_counts = b.get("sym_counts", {})
        if sym_counts:
            lines += ["| Symbol | Count |", "|---|---:|"]
            for sym, cnt in sorted(sym_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| `{sym!r}` | {cnt:,} |")
        else:
            lines.append("No symbol column identified.")

    else:
        lines.append("**Download failed — no data profiled.**")

    lines += [
        "",
        "---",
        "",
        "## Cross-table comparison",
        "",
        "### Employment-size label consistency",
        "",
    ]

    if a and b:
        emp_a = set(a.get("emp_labels", []))
        emp_b = set(b.get("emp_labels", []))
        shared = sorted(emp_a & emp_b)
        only_a = sorted(emp_a - emp_b)
        only_b = sorted(emp_b - emp_a)

        lines += [
            f"- Labels in both tables: `{len(shared)}`",
            f"- Only in Table A: `{len(only_a)}`",
            f"- Only in Table B: `{len(only_b)}`",
            "",
            "Shared labels:",
        ]
        for s in shared:
            lines.append(f"- `{s}`")
        if only_a:
            lines += ["", "Only in A:"]
            for s in only_a:
                lines.append(f"- `{s}`")
        if only_b:
            lines += ["", "Only in B:"]
            for s in only_b:
                lines.append(f"- `{s}`")

    lines += [
        "",
        "---",
        "",
        "## Role assessment",
        "",
        "### Table A",
        "",
        (
            "Canadian Business Counts (with employees) is a Class D validation/benchmark dataset. "
            "It contains aggregate counts of employer businesses by province/territory, NAICS, "
            "and employment-size range. It does NOT contain individual business records and "
            "cannot be used as a lead source."
        ),
        "",
        (
            "Its value in this system: benchmark pipeline coverage "
            "(how many businesses does our pipeline identify vs the StatsCan total, "
            "by province × NAICS × employment-size bucket)."
        ),
        "",
        "### Table B",
        "",
        (
            "Business Openings and Closures is a Class D validation/benchmark dataset. "
            "It contains aggregate monthly counts of employer business openings, closures, "
            "continuing businesses, re-openings, and entrants. "
            "These are EXPERIMENTAL ESTIMATES subject to monthly revision."
        ),
        "",
        (
            "Opening definition (StatsCan): employees this month, no employees last month. "
            "This is fundamentally different from: incorporation date, licence issue date, "
            "website launch date, or business-name registration. "
            "The system must NOT conflate these events."
        ),
        "",
        (
            "Its value: benchmark scale/distribution of new employer businesses per month "
            "per province × NAICS × employment size. "
            "Validates whether our event-detection layer is producing plausible volumes."
        ),
        "",
        "### What StatsCan cannot provide",
        "",
        "- Individual business names, addresses, or identifiers",
        "- Phone, email, website, or contact information",
        "- Director or decision-maker names",
        "- Real-time or daily new-business signals",
        "",
        "---",
        "",
        "## Open questions",
        "",
        "- [ ] Do the StatsCan employment-size labels map cleanly to all 9 required buckets? (see tables A.4 and B.5)",
        "- [ ] Are suppressed values (`..`) concentrated in specific province × NAICS combinations?",
        "- [ ] Does Table B cover all provinces/territories or only national/major-CMA level?",
        "- [ ] Are Table B opening counts stable enough month-over-month to use as a benchmark?",
        "- [ ] Does Table A include a 'without employees' category or only employer businesses?",
        "",
    ]

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written: {REPORT_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("VR05 — STATISTICS CANADA BUSINESS COUNTS")
    print("=" * 80)
    print()

    results = {}

    for table in TABLES:
        print(f"\n{'=' * 80}")
        print(f"TABLE {table['key']}: {table['id']} — {table['label']}")
        print("=" * 80)

        ok = ensure_downloaded(table)
        if not ok:
            print(f"SKIPPING {table['id']} — download failed")
            continue

        if table["key"] == "A":
            results["a"] = profile_table_a(table["zip_file"])
        else:
            results["b"] = profile_table_b(table["zip_file"])

    print("\n" + "=" * 80)
    print("WRITING REPORT")
    print("=" * 80)
    write_report(results)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if "a" in results:
        a = results["a"]
        print(f"Table A rows:          {a.get('row_count', 0):,}")
        print(f"Table A emp labels:    {len(a.get('emp_labels', []))}")
        bmap = a.get("bucket_map", {}).get("mapping", {})
        covered = sum(1 for v in bmap.values() if v)
        print(f"Table A buckets mapped: {covered}/9")
    if "b" in results:
        b = results["b"]
        print(f"Table B rows:          {b.get('row_count', 0):,}")
        print(f"Table B date range:    {b.get('date_labels', ['?'])[0]} → {b.get('date_labels', ['?'])[-1]}")
        print(f"Table B type labels:   {b.get('type_labels', [])}")
    print()


if __name__ == "__main__":
    main()
