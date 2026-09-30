from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "corporations-active-cbca-en.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "validation_rounds"
    / "VR02a_CORPS_CANADA_PROVINCE_DISTRIBUTION.md"
)


def main():
    print("=" * 80)
    print("CORPORATIONS CANADA — PROVINCE DISTRIBUTION")
    print("=" * 80)
    print()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    counts = Counter()
    total = 0
    missing = 0

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        print("Detected columns:")
        print(reader.fieldnames)
        print()

        # Case-insensitive column lookup.
        province_column = next(
            (
                column
                for column in reader.fieldnames or []
                if column.strip().lower()
                == "province/territory"
            ),
            None,
        )

        if province_column is None:
            raise RuntimeError(
                "Could not find Province/territory column."
            )

        print(f"Using column: {province_column}")
        print()

        for row in reader:
            total += 1

            province = (
                row.get(province_column) or ""
            ).strip()

            if not province:
                province = "<MISSING>"
                missing += 1

            counts[province] += 1

            if total % 100_000 == 0:
                print(f"Processed {total:,} rows...")

    print()
    print("Province distribution:")
    print()

    for province, count in counts.most_common():
        percentage = count / total * 100

        print(
            f"{province:5} "
            f"{count:>10,} "
            f"{percentage:>7.2f}%"
        )

    lines = [
        "# Corporations Canada — Province/Territory Distribution",
        "",
        f"- Input: `{INPUT_FILE}`",
        f"- Total active CBCA corporations: `{total:,}`",
        f"- Missing province: `{missing:,}`",
        "",
        "## Distribution",
        "",
        "| Province/Territory | Corporations | Percentage |",
        "|---|---:|---:|",
    ]

    for province, count in counts.most_common():
        percentage = count / total * 100

        lines.append(
            f"| `{province}` | {count:,} | {percentage:.2f}% |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        (
            "This is the geographic distribution of active federal "
            "CBCA corporations only. It is not a distribution of all "
            "Canadian businesses."
        ),
        "",
    ])

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print(f"Report written to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
