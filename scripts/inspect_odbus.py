from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def find_zip_file(raw_dir: Path) -> Path:
    """Find the ODBus ZIP automatically if --zip was not supplied."""
    zips = sorted(raw_dir.glob("*.zip"))

    if not zips:
        raise FileNotFoundError(
            f"No ZIP file found in {raw_dir}. "
            "Place ODBus_2023.zip in data/raw or provide --zip."
        )

    if len(zips) == 1:
        return zips[0]

    # Prefer ODBus-looking names.
    odbus_zips = [
        z for z in zips
        if "odbus" in z.name.lower()
    ]

    if len(odbus_zips) == 1:
        return odbus_zips[0]

    raise RuntimeError(
        "Multiple ZIP files found. Please specify one with --zip:\n"
        + "\n".join(f"  {z}" for z in zips)
    )


def is_tabular_file(name: str) -> bool:
    suffix = Path(name).suffix.lower()
    return suffix in {".csv", ".tsv", ".txt"}


def detect_delimiter(sample_text: str) -> str:
    """Detect delimiter using csv.Sniffer, with sensible fallbacks."""
    try:
        dialect = csv.Sniffer().sniff(
            sample_text,
            delimiters=",\t;|"
        )
        return dialect.delimiter
    except csv.Error:
        # ODBus files are expected to be CSV/TSV.
        counts = {
            ",": sample_text.count(","),
            "\t": sample_text.count("\t"),
            ";": sample_text.count(";"),
            "|": sample_text.count("|"),
        }

        return max(counts, key=counts.get)


def decode_bytes(raw: bytes) -> tuple[str, str]:
    """
    Decode bytes using common encodings found in government/open-data files.

    Returns:
        (decoded_text, encoding_used)
    """
    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    ]

    for encoding in encodings:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    # latin-1 should technically always work, but keep a final fallback.
    return raw.decode("latin-1", errors="replace"), "latin-1-replace"


def read_csv_from_zip(
    zf: zipfile.ZipFile,
    member: str,
    nrows: Optional[int] = None,
) -> tuple[pd.DataFrame, str, str]:
    """
    Read a CSV/TSV member from a ZIP while automatically detecting encoding
    and delimiter.

    Returns:
        dataframe, encoding, delimiter
    """
    with zf.open(member) as f:
        raw = f.read()

    text, encoding = decode_bytes(raw)

    # Use a sample for delimiter detection.
    sample = text[:100_000]
    delimiter = detect_delimiter(sample)

    df = pd.read_csv(
        io.StringIO(text),
        sep=delimiter,
        nrows=nrows,
        low_memory=False,
    )

    return df, encoding, delimiter


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def markdown_table(
    rows: list[list],
    headers: list[str],
) -> str:
    if not rows:
        return "_No data_"

    def clean(value) -> str:
        if value is None:
            return ""

        value = str(value)
        value = value.replace("|", "\\|")
        value = value.replace("\n", " ")
        return value

    output = []

    output.append(
        "| " + " | ".join(clean(h) for h in headers) + " |"
    )
    output.append(
        "| " + " | ".join("---" for _ in headers) + " |"
    )

    for row in rows:
        output.append(
            "| " + " | ".join(clean(v) for v in row) + " |"
        )

    return "\n".join(output)


def format_number(value) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return str(value)


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------

def find_column(
    columns,
    patterns: list[str],
) -> Optional[str]:
    """
    Find a column using case-insensitive substring matching.
    """
    normalized = {
        str(c).strip().lower(): c
        for c in columns
    }

    # Exact match first.
    for pattern in patterns:
        pattern_lower = pattern.lower()

        if pattern_lower in normalized:
            return normalized[pattern_lower]

    # Substring match.
    for column_lower, original in normalized.items():
        for pattern in patterns:
            if pattern.lower() in column_lower:
                return original

    return None


def find_columns(
    columns,
    patterns: list[str],
) -> list[str]:
    matches = []

    for column in columns:
        column_lower = str(column).lower()

        if any(pattern.lower() in column_lower for pattern in patterns):
            matches.append(column)

    return matches


# ---------------------------------------------------------------------------
# File inspection
# ---------------------------------------------------------------------------

def inspect_file(
    zf: zipfile.ZipFile,
    member: str,
) -> dict:
    print(f"\nInspecting: {member}")

    # Read everything because the ODBus metadata files are small and the main
    # ODBus dataset is manageable (~hundreds of thousands of rows).
    df, encoding, delimiter = read_csv_from_zip(zf, member)

    print(f"  Encoding : {encoding}")
    print(f"  Delimiter: {repr(delimiter)}")
    print(f"  Rows     : {len(df):,}")
    print(f"  Columns  : {len(df.columns):,}")

    return {
        "member": member,
        "encoding": encoding,
        "delimiter": delimiter,
        "rows": len(df),
        "columns": list(df.columns),
        "dataframe": df,
    }


# ---------------------------------------------------------------------------
# ODBus dataset analysis
# ---------------------------------------------------------------------------

def analyze_main_dataset(df: pd.DataFrame) -> dict:
    result = {}

    result["row_count"] = len(df)
    result["column_count"] = len(df.columns)
    result["columns"] = [str(c) for c in df.columns]

    # -----------------------------------------------------------------------
    # Missingness
    # -----------------------------------------------------------------------

    missing_rows = []

    for column in df.columns:
        missing = int(df[column].isna().sum())

        # Also treat blank strings as missing.
        try:
            blank = int(
                df[column]
                .astype("string")
                .str.strip()
                .eq("")
                .sum()
            )
        except Exception:
            blank = 0

        total_missing = max(missing, blank)

        percentage = (
            total_missing / len(df) * 100
            if len(df)
            else 0
        )

        missing_rows.append(
            [
                str(column),
                total_missing,
                round(percentage, 2),
            ]
        )

    missing_rows.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    result["missingness"] = missing_rows

    # -----------------------------------------------------------------------
    # Likely important fields
    # -----------------------------------------------------------------------

    field_patterns = {
        "business_name": [
            "business_name",
            "business name",
            "company_name",
            "company name",
            "name",
        ],
        "business_id": [
            "business_id",
            "business id",
            "businessid",
            "enterprise_id",
            "enterprise id",
            "id",
        ],
        "province": [
            "province",
            "prov",
        ],
        "municipality": [
            "municipality",
            "city",
            "town",
            "locality",
        ],
        "postal_code": [
            "postal",
            "postcode",
            "zip",
        ],
        "address": [
            "address",
            "street",
        ],
        "naics": [
            "naics",
        ],
        "employee": [
            "employee",
            "employment",
            "employees",
        ],
        "status": [
            "status",
        ],
        "licence": [
            "licence",
            "license",
        ],
        "latitude": [
            "latitude",
            "lat",
        ],
        "longitude": [
            "longitude",
            "lon",
            "lng",
        ],
    }

    detected_fields = {}

    for field, patterns in field_patterns.items():
        detected_fields[field] = find_columns(
            df.columns,
            patterns,
        )

    result["detected_fields"] = detected_fields

    # -----------------------------------------------------------------------
    # Province distribution
    # -----------------------------------------------------------------------

    province_col = find_column(
        df.columns,
        ["province", "prov"],
    )

    if province_col:
        counts = (
            df[province_col]
            .fillna("<MISSING>")
            .astype(str)
            .str.strip()
            .value_counts()
            .head(30)
        )

        result["province_distribution"] = [
            [str(index), int(value)]
            for index, value in counts.items()
        ]
    else:
        result["province_distribution"] = []

    # -----------------------------------------------------------------------
    # Employee-related distributions
    # -----------------------------------------------------------------------

    employee_cols = find_columns(
        df.columns,
        [
            "employee",
            "employment",
        ],
    )

    employee_distributions = {}

    for column in employee_cols:
        counts = (
            df[column]
            .fillna("<MISSING>")
            .astype(str)
            .str.strip()
            .value_counts()
            .head(50)
        )

        employee_distributions[str(column)] = [
            [str(index), int(value)]
            for index, value in counts.items()
        ]

    result["employee_distributions"] = employee_distributions

    # -----------------------------------------------------------------------
    # NAICS distribution
    # -----------------------------------------------------------------------

    naics_col = find_column(
        df.columns,
        ["naics"],
    )

    if naics_col:
        counts = (
            df[naics_col]
            .fillna("<MISSING>")
            .astype(str)
            .str.strip()
            .value_counts()
            .head(50)
        )

        result["naics_distribution"] = [
            [str(index), int(value)]
            for index, value in counts.items()
        ]
    else:
        result["naics_distribution"] = []

    # -----------------------------------------------------------------------
    # Status distribution
    # -----------------------------------------------------------------------

    status_col = find_column(
        df.columns,
        ["status"],
    )

    if status_col:
        counts = (
            df[status_col]
            .fillna("<MISSING>")
            .astype(str)
            .str.strip()
            .value_counts()
            .head(50)
        )

        result["status_distribution"] = [
            [str(index), int(value)]
            for index, value in counts.items()
        ]
    else:
        result["status_distribution"] = []

    # -----------------------------------------------------------------------
    # Possible duplicate IDs
    # -----------------------------------------------------------------------

    id_col = find_column(
        df.columns,
        [
            "business_id",
            "business id",
            "businessid",
            "enterprise_id",
            "enterprise id",
        ],
    )

    if id_col:
        non_null = df[id_col].dropna()

        duplicate_count = int(
            non_null.duplicated(keep=False).sum()
        )

        result["duplicate_id_rows"] = duplicate_count

        result["id_column"] = str(id_col)
    else:
        result["duplicate_id_rows"] = None
        result["id_column"] = None

    # -----------------------------------------------------------------------
    # Potential duplicate business names
    # -----------------------------------------------------------------------

    name_col = find_column(
        df.columns,
        [
            "business_name",
            "business name",
            "company_name",
            "company name",
        ],
    )

    if name_col:
        normalized_names = (
            df[name_col]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )

        duplicated_name_rows = int(
            normalized_names[
                normalized_names.duplicated(keep=False)
            ]
            .ne("")
            .sum()
        )

        result["duplicate_name_rows"] = duplicated_name_rows
        result["name_column"] = str(name_col)
    else:
        result["duplicate_name_rows"] = None
        result["name_column"] = None

    # -----------------------------------------------------------------------
    # Sample rows
    # -----------------------------------------------------------------------

    sample = df.head(10).copy()

    result["sample_columns"] = [
        str(c) for c in sample.columns
    ]

    result["sample_rows"] = (
        sample.fillna("")
        .astype(str)
        .values
        .tolist()
    )

    # -----------------------------------------------------------------------
    # Data types
    # -----------------------------------------------------------------------

    result["dtypes"] = [
        [str(column), str(dtype)]
        for column, dtype in df.dtypes.items()
    ]

    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_report(
    zip_path: Path,
    archive_members: list[str],
    file_reports: list[dict],
    main_analysis: Optional[dict],
) -> str:

    lines = []

    lines.append("# ODBus Inspection Report")
    lines.append("")
    lines.append(
        f"Generated from `{zip_path.name}`."
    )
    lines.append("")

    lines.append("## Archive")
    lines.append("")
    lines.append(f"- ZIP: `{zip_path}`")
    lines.append(f"- Archive members: {len(archive_members):,}")
    lines.append("")

    lines.append("### Files in archive")
    lines.append("")

    for member in archive_members:
        lines.append(f"- `{member}`")

    lines.append("")

    lines.append("## Tabular file inspection")
    lines.append("")

    rows = []

    for report in file_reports:
        rows.append(
            [
                report["member"],
                report["encoding"],
                repr(report["delimiter"]),
                format_number(report["rows"]),
                format_number(report["columns_count"]),
            ]
        )

    lines.append(
        markdown_table(
            rows,
            [
                "File",
                "Encoding",
                "Delimiter",
                "Rows",
                "Columns",
            ],
        )
    )

    lines.append("")

    if not main_analysis:
        lines.append(
            "> Main ODBus dataset could not be identified."
        )
        return "\n".join(lines)

    # -----------------------------------------------------------------------
    # Main dataset
    # -----------------------------------------------------------------------

    lines.append("## Main ODBus dataset")
    lines.append("")

    lines.append(
        f"- Rows: **{main_analysis['row_count']:,}**"
    )
    lines.append(
        f"- Columns: **{main_analysis['column_count']:,}**"
    )

    if main_analysis.get("id_column"):
        lines.append(
            f"- Detected ID column: `{main_analysis['id_column']}`"
        )

    if main_analysis.get("name_column"):
        lines.append(
            f"- Detected business-name column: "
            f"`{main_analysis['name_column']}`"
        )

    lines.append("")

    lines.append("### Columns")
    lines.append("")

    for column in main_analysis["columns"]:
        lines.append(f"- `{column}`")

    lines.append("")

    # -----------------------------------------------------------------------
    # Detected fields
    # -----------------------------------------------------------------------

    lines.append("### Detected business-data fields")
    lines.append("")

    detected_rows = []

    for field, columns in main_analysis["detected_fields"].items():
        detected_rows.append(
            [
                field,
                ", ".join(f"`{c}`" for c in columns)
                if columns
                else "Not detected",
            ]
        )

    lines.append(
        markdown_table(
            detected_rows,
            ["Logical field", "Detected columns"],
        )
    )

    lines.append("")

    # -----------------------------------------------------------------------
    # Missingness
    # -----------------------------------------------------------------------

    lines.append("### Missingness")
    lines.append("")

    lines.append(
        markdown_table(
            main_analysis["missingness"][:50],
            [
                "Column",
                "Missing/blank rows",
                "Missing %",
            ],
        )
    )

    lines.append("")

    # -----------------------------------------------------------------------
    # Province
    # -----------------------------------------------------------------------

    if main_analysis["province_distribution"]:
        lines.append("### Province distribution")
        lines.append("")

        lines.append(
            markdown_table(
                main_analysis["province_distribution"],
                ["Province", "Rows"],
            )
        )

        lines.append("")

    # -----------------------------------------------------------------------
    # Employee
    # -----------------------------------------------------------------------

    if main_analysis["employee_distributions"]:
        lines.append("### Employee-related distributions")
        lines.append("")

        for column, rows in main_analysis[
            "employee_distributions"
        ].items():

            lines.append(f"#### `{column}`")
            lines.append("")

            lines.append(
                markdown_table(
                    rows,
                    ["Value", "Rows"],
                )
            )

            lines.append("")

    # -----------------------------------------------------------------------
    # NAICS
    # -----------------------------------------------------------------------

    if main_analysis["naics_distribution"]:
        lines.append("### NAICS distribution")
        lines.append("")

        lines.append(
            markdown_table(
                main_analysis["naics_distribution"],
                ["NAICS value", "Rows"],
            )
        )

        lines.append("")

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------

    if main_analysis["status_distribution"]:
        lines.append("### Status distribution")
        lines.append("")

        lines.append(
            markdown_table(
                main_analysis["status_distribution"],
                ["Status", "Rows"],
            )
        )

        lines.append("")

    # -----------------------------------------------------------------------
    # Duplicate analysis
    # -----------------------------------------------------------------------

    lines.append("## Duplicate indicators")
    lines.append("")

    if main_analysis["duplicate_id_rows"] is not None:
        lines.append(
            f"- Rows involved in duplicate IDs: "
            f"**{main_analysis['duplicate_id_rows']:,}**"
        )
    else:
        lines.append("- No obvious business ID column detected.")

    if main_analysis["duplicate_name_rows"] is not None:
        lines.append(
            f"- Rows involved in repeated normalized business names: "
            f"**{main_analysis['duplicate_name_rows']:,}**"
        )
    else:
        lines.append(
            "- No obvious business-name column detected."
        )

    lines.append("")
    lines.append(
        "> Repeated names are not automatically duplicates. "
        "Address, postal code, phone, corporation number, "
        "and other identifiers must be considered before entity merging."
    )
    lines.append("")

    # -----------------------------------------------------------------------
    # Sample
    # -----------------------------------------------------------------------

    lines.append("## Sample records")
    lines.append("")

    sample_rows = main_analysis["sample_rows"]

    if sample_rows:
        lines.append(
            markdown_table(
                sample_rows,
                main_analysis["sample_columns"],
            )
        )
    else:
        lines.append("_No sample rows available._")

    lines.append("")

    # -----------------------------------------------------------------------
    # Data types
    # -----------------------------------------------------------------------

    lines.append("## Data types")
    lines.append("")

    lines.append(
        markdown_table(
            main_analysis["dtypes"],
            ["Column", "Pandas dtype"],
        )
    )

    lines.append("")

    # -----------------------------------------------------------------------
    # Initial interpretation
    # -----------------------------------------------------------------------

    lines.append("## Initial interpretation")
    lines.append("")

    lines.append(
        "This report is an inspection artifact, not a final data-quality "
        "assessment. Before using ODBus in the production pipeline, verify:"
    )
    lines.append("")
    lines.append(
        "1. Actual field semantics against the supplied ODBus metadata."
    )
    lines.append(
        "2. Geographic coverage across Canada."
    )
    lines.append(
        "3. Whether employee information is suitable for the required "
        "employee-size buckets."
    )
    lines.append(
        "4. Whether business status and licence information can support "
        "new-business/change detection."
    )
    lines.append(
        "5. Whether records can be safely linked to other sources."
    )
    lines.append(
        "6. The licensing terms and permitted commercial use."
    )
    lines.append(
        "7. Whether ODBus is current enough for the intended lead-generation "
        "use case."
    )
    lines.append("")

    lines.append(
        "The production system should treat ODBus as one source among "
        "multiple sources and preserve source provenance rather than "
        "overwriting conflicting observations."
    )

    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Inspect the Statistics Canada ODBus ZIP."
    )

    parser.add_argument(
        "--zip",
        dest="zip_path",
        type=Path,
        default=None,
        help="Path to ODBus ZIP. Defaults to automatic discovery in data/raw.",
    )

    parser.add_argument(
        "--report",
        dest="report_path",
        type=Path,
        default=None,
        help="Output Markdown report path.",
    )

    args = parser.parse_args()

    zip_path = (
        args.zip_path
        if args.zip_path
        else find_zip_file(DEFAULT_RAW_DIR)
    )

    if not zip_path.exists():
        raise FileNotFoundError(
            f"ZIP file does not exist: {zip_path}"
        )

    report_path = (
        args.report_path
        if args.report_path
        else DEFAULT_REPORT_DIR / "ODBUS_INSPECTION_REPORT.md"
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("ODBus Inspection")
    print("=" * 70)

    print(f"\nOpening: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:

        archive_members = zf.namelist()

        print("\nFiles in archive:")

        for member in archive_members:
            print(f"  - {member}")

        tabular_members = [
            member
            for member in archive_members
            if is_tabular_file(member)
        ]

        print("\nTabular files:")

        for member in tabular_members:
            print(f"  - {member}")

        file_reports = []
        main_analysis = None

        for member in tabular_members:

            try:
                inspection = inspect_file(
                    zf,
                    member,
                )

                file_reports.append(
                    {
                        "member": inspection["member"],
                        "encoding": inspection["encoding"],
                        "delimiter": inspection["delimiter"],
                        "rows": inspection["rows"],
                        "columns_count": len(
                            inspection["columns"]
                        ),
                    }
                )

                # The main dataset is expected to contain ODBus_v1
                # in its filename and should be much larger than metadata.
                member_lower = member.lower()

                if (
                    member_lower.endswith("odbus_v1.csv")
                    or (
                        "odbus" in member_lower
                        and inspection["rows"] > 10_000
                    )
                ):
                    print(
                        "\nIdentified main ODBus dataset:"
                    )
                    print(f"  {member}")

                    main_analysis = analyze_main_dataset(
                        inspection["dataframe"]
                    )

            except Exception as exc:
                print(
                    f"\nERROR inspecting {member}: "
                    f"{type(exc).__name__}: {exc}"
                )

                file_reports.append(
                    {
                        "member": member,
                        "encoding": "ERROR",
                        "delimiter": "ERROR",
                        "rows": "ERROR",
                        "columns_count": "ERROR",
                    }
                )

        report = build_report(
            zip_path=zip_path,
            archive_members=archive_members,
            file_reports=file_reports,
            main_analysis=main_analysis,
        )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    print("\n" + "=" * 70)
    print("Inspection complete")
    print("=" * 70)

    print(f"\nReport written to:")
    print(f"  {report_path}")

    if main_analysis:
        print(
            f"\nMain dataset rows: "
            f"{main_analysis['row_count']:,}"
        )

        print(
            f"Main dataset columns: "
            f"{main_analysis['column_count']:,}"
        )

    print("\nNext step:")
    print(
        "Open reports\\ODBUS_INSPECTION_REPORT.md "
        "and review the actual fields and distributions."
    )


if __name__ == "__main__":
    main()