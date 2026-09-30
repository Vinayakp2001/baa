from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports" / "validation_rounds"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


URL = (
    "https://d4bf66bykfyaf.cloudfront.net/"
    "corporations-active-cbca-en.csv"
)

OUTPUT_FILE = RAW_DIR / "corporations-active-cbca-en.csv"


def download_file(url: str, destination: Path) -> None:
    print("Downloading:")
    print(url)
    print()

    request = Request(
        url,
        headers={
            "User-Agent": (
                "CanadaBusinessDataAutomation/0.1 "
                "(research/validation)"
            )
        },
    )

    with urlopen(request, timeout=120) as response:
        with destination.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)

                if not chunk:
                    break

                output.write(chunk)

                print(
                    f"\rDownloaded: "
                    f"{output.tell() / (1024 * 1024):,.1f} MB",
                    end="",
                    flush=True,
                )

    print()
    print()
    print(f"Saved to: {destination}")


def inspect_csv(path: Path) -> dict:
    print("=" * 80)
    print("CSV PROFILING")
    print("=" * 80)
    print()

    file_size = path.stat().st_size

    print(
        f"File size: "
        f"{file_size / (1024 * 1024):,.2f} MB"
    )

    print()

    with path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        fieldnames = reader.fieldnames or []

        print("Columns:")
        for index, field in enumerate(fieldnames, start=1):
            print(f"{index:>3}. {field}")

        print()
        print(f"Column count: {len(fieldnames)}")
        print()

        row_count = 0

        null_counts = Counter()
        status_counts = Counter()
        province_counts = Counter()
        director_min_counts = Counter()
        director_max_counts = Counter()

        samples = []

        for row in reader:
            row_count += 1

            if len(samples) < 5:
                samples.append(row)

            for field in fieldnames:
                value = (row.get(field) or "").strip()

                if not value:
                    null_counts[field] += 1

            # Try common expected fields.
            status = (row.get("Status") or "").strip()
            if status:
                status_counts[status] += 1

            province = (
                row.get("Province/Territory")
                or row.get("Province")
                or row.get("province")
                or ""
            ).strip()

            if province:
                province_counts[province] += 1

            min_directors = (
                row.get("Minimum Number of Directors")
                or row.get("Minimum number of directors")
                or ""
            ).strip()

            max_directors = (
                row.get("Maximum Number of Directors")
                or row.get("Maximum number of directors")
                or ""
            ).strip()

            if min_directors:
                director_min_counts[min_directors] += 1

            if max_directors:
                director_max_counts[max_directors] += 1

            if row_count % 100_000 == 0:
                print(f"Processed {row_count:,} rows...")

    return {
        "file_size": file_size,
        "row_count": row_count,
        "columns": fieldnames,
        "null_counts": null_counts,
        "status_counts": status_counts,
        "province_counts": province_counts,
        "director_min_counts": director_min_counts,
        "director_max_counts": director_max_counts,
        "samples": samples,
    }


def generate_report(profile: dict) -> str:
    now = datetime.now(timezone.utc).isoformat()

    row_count = profile["row_count"]
    columns = profile["columns"]
    null_counts = profile["null_counts"]

    lines = [
        "# Corporations Canada Active Business Corporations — Profile",
        "",
        f"Generated: `{now}`",
        "",
        "## Source",
        "",
        f"- URL: `{URL}`",
        f"- Local file: `{OUTPUT_FILE}`",
        "- Publisher: Innovation, Science and Economic Development Canada",
        "- Dataset family: Federal Corporations",
        "- Subset: Active Business Corporations",
        "- Legislation: Canada Business Corporations Act (CBCA)",
        "- Licence: Open Government Licence - Canada",
        "",
        "## File",
        "",
        f"- Size: `{profile['file_size'] / (1024 * 1024):,.2f} MB`",
        f"- Rows: `{row_count:,}`",
        f"- Columns: `{len(columns)}`",
        "",
        "## Columns",
        "",
    ]

    for index, column in enumerate(columns, start=1):
        lines.append(f"{index}. `{column}`")

    lines.extend([
        "",
        "## Missingness",
        "",
        "| Field | Missing rows | Missing % |",
        "|---|---:|---:|",
    ])

    for field in columns:
        missing = null_counts[field]
        percentage = (
            (missing / row_count * 100)
            if row_count
            else 0
        )

        lines.append(
            f"| `{field}` | {missing:,} | {percentage:.2f}% |"
        )

    lines.extend([
        "",
        "## Status distribution",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ])

    for value, count in profile["status_counts"].most_common():
        lines.append(f"| `{value}` | {count:,} |")

    lines.extend([
        "",
        "## Province/Territory distribution",
        "",
        "| Province/Territory | Rows |",
        "|---|---:|",
    ])

    for value, count in profile["province_counts"].most_common():
        lines.append(f"| `{value}` | {count:,} |")

    lines.extend([
        "",
        "## Minimum number of directors",
        "",
        "| Value | Rows |",
        "|---|---:|",
    ])

    for value, count in profile["director_min_counts"].most_common():
        lines.append(f"| `{value}` | {count:,} |")

    lines.extend([
        "",
        "## Maximum number of directors",
        "",
        "| Value | Rows |",
        "|---|---:|",
    ])

    for value, count in profile["director_max_counts"].most_common():
        lines.append(f"| `{value}` | {count:,} |")

    lines.extend([
        "",
        "## Sample records",
        "",
        "```text",
    ])

    for sample in profile["samples"]:
        lines.append(str(sample))

    lines.extend([
        "```",
        "",
        "## Initial technical interpretation",
        "",
        "- This source is federal-only.",
        "- It should be treated as a corporate identity/status source.",
        "- It should not be treated as a Canada-wide business master.",
        "- Employee count, website, phone and email must be obtained elsewhere.",
        "- Provincial and territorial corporations require other sources.",
        "- Director fields need separate profiling before deciding how to use them.",
        "- Date fields must be profiled carefully; incorporation, anniversary and filing dates are different concepts.",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    if not OUTPUT_FILE.exists():
        download_file(URL, OUTPUT_FILE)
    else:
        print(f"Using existing file: {OUTPUT_FILE}")
        print()

    profile = inspect_csv(OUTPUT_FILE)

    report = generate_report(profile)

    report_path = (
        REPORTS_DIR /
        "VR01_CORPORATIONS_CANADA_ACTIVE_PROFILE.md"
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    print()
    print("=" * 80)
    print("PROFILE COMPLETE")
    print("=" * 80)
    print()
    print(f"Rows: {profile['row_count']:,}")
    print(f"Columns: {len(profile['columns'])}")
    print()
    print(f"Report: {report_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
