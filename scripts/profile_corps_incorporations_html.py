from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports" / "validation_rounds"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

URL = (
    "https://ised-isde.canada.ca/site/"
    "corporations-canada/en/data-services/"
    "monthly-transactions/"
    "certificates-incorporation-cbca"
)

HTML_FILE = RAW_DIR / "corporations-canada-cbca-incorporations.html"
CSV_FILE = RAW_DIR / "corporations-canada-cbca-incorporations.csv"
REPORT_FILE = REPORTS_DIR / "VR03_CORPORATIONS_CANADA_CBCA_INCORPORATIONS.md"


def download_html() -> None:
    print("Downloading:")
    print(URL)
    print()

    request = Request(
        URL,
        headers={
            "User-Agent": (
                "CanadaBusinessDataAutomation/0.1 "
                "(research/validation)"
            )
        },
    )

    with urlopen(request, timeout=60) as response:
        content = response.read()

    HTML_FILE.write_bytes(content)
    print(f"Downloaded: {len(content):,} bytes")
    print(f"Saved: {HTML_FILE}")
    print()


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def parse_table() -> list[dict[str, str]]:
    print("=" * 80)
    print("PARSING CBCA INCORPORATION TABLE")
    print("=" * 80)
    print()

    html = HTML_FILE.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    print(f"Tables found: {len(tables)}")
    print()

    target_table = None
    expected_headers = {
        "corporation number",
        "name of corporation",
        "registered office",
        "effective date",
    }

    for index, table in enumerate(tables):
        rows = table.find_all("tr")
        if not rows:
            continue

        first_cells = rows[0].find_all(["th", "td"])
        headers = {
            normalize(cell.get_text(" ", strip=True)).lower()
            for cell in first_cells
        }

        print(f"Table {index + 1}: {len(rows)} rows, headers={headers}")

        if expected_headers.issubset(headers):
            target_table = table
            print(f"--> Selected table {index + 1}")
            print()
            break

    if target_table is None:
        raise RuntimeError(
            "Could not find the expected incorporation table."
        )

    rows = target_table.find_all("tr")
    headers = [
        normalize(cell.get_text(" ", strip=True))
        for cell in rows[0].find_all(["th", "td"])
    ]

    print("Headers:")
    for header in headers:
        print(f"  {header}")
    print()

    records = []
    for row in rows[1:]:
        cells = [
            normalize(cell.get_text(" ", strip=True))
            for cell in row.find_all(["td", "th"])
        ]

        if not cells:
            continue

        if len(cells) != len(headers):
            print("Skipping malformed row:", cells)
            continue

        records.append(dict(zip(headers, cells)))

    print(f"Parsed records: {len(records):,}")
    print()
    return records


def write_csv(records: list[dict[str, str]]) -> None:
    if not records:
        return

    fieldnames = [
        "Corporation Number",
        "Name of Corporation",
        "Registered Office",
        "Effective Date",
    ]

    with CSV_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({
                field: record.get(field, "")
                for field in fieldnames
            })

    print(f"CSV written: {CSV_FILE}")


def profile(records: list[dict[str, str]]) -> dict:
    province_counts: Counter = Counter()
    date_counts: Counter = Counter()
    corporation_counts: Counter = Counter()
    malformed_dates: list[str] = []
    missing_fields: Counter = Counter()
    parsed_dates = []

    required_fields = [
        "Corporation Number",
        "Name of Corporation",
        "Registered Office",
        "Effective Date",
    ]

    for record in records:
        for field in required_fields:
            if not record.get(field):
                missing_fields[field] += 1

        corp_num = record.get("Corporation Number", "")
        if corp_num:
            corporation_counts[corp_num] += 1

        office = record.get("Registered Office", "")
        if office:
            province = office.split("(", 1)[0].strip()
            if province:
                province_counts[province] += 1

        date_value = record.get("Effective Date", "")
        if date_value:
            try:
                parsed = datetime.strptime(date_value, "%Y-%m-%d").date()
                parsed_dates.append(parsed)
                date_counts[date_value] += 1
            except ValueError:
                malformed_dates.append(date_value)

    duplicate_ids = {
        k: v for k, v in corporation_counts.items() if v > 1
    }

    return {
        "records": len(records),
        "province_counts": province_counts,
        "date_counts": date_counts,
        "missing_fields": missing_fields,
        "malformed_dates": malformed_dates,
        "duplicate_ids": duplicate_ids,
        "min_date": min(parsed_dates) if parsed_dates else None,
        "max_date": max(parsed_dates) if parsed_dates else None,
    }


def write_report(result: dict) -> None:
    lines = [
        "# VR03 — Corporations Canada CBCA Incorporations",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Source",
        "",
        f"- URL: `{URL}`",
        "- Publisher: Innovation, Science and Economic Development Canada",
        "- Dataset: Monthly Transactions — Certificates of Incorporation (CBCA)",
        "- Format: HTML table",
        "",
        "## Record count",
        "",
        f"- Parsed records: `{result['records']:,}`",
        "",
        "## Fields",
        "",
        "| Field | Missing |",
        "|---|---:|",
    ]

    for field, count in result["missing_fields"].items():
        lines.append(f"| `{field}` | {count:,} |")

    if not result["missing_fields"]:
        lines.append("| *(none missing)* | 0 |")

    lines.extend([
        "",
        "## Effective-date range",
        "",
        f"- Minimum: `{result['min_date']}`",
        f"- Maximum: `{result['max_date']}`",
        "",
        "## Province distribution",
        "",
        "| Registered office | Records |",
        "|---|---:|",
    ])

    for province, count in result["province_counts"].most_common():
        lines.append(f"| `{province}` | {count:,} |")

    lines.extend([
        "",
        "## Duplicate corporation numbers",
        "",
        f"- Duplicate IDs: `{len(result['duplicate_ids']):,}`",
        "",
    ])

    if result["duplicate_ids"]:
        lines.extend([
            "| Corporation number | Occurrences |",
            "|---|---:|",
        ])
        for corp_num, count in list(result["duplicate_ids"].items())[:100]:
            lines.append(f"| `{corp_num}` | {count:,} |")

    lines.extend([
        "",
        "## Malformed dates",
        "",
        f"- Count: `{len(result['malformed_dates']):,}`",
        "",
    ])

    if result["malformed_dates"]:
        for value in result["malformed_dates"][:100]:
            lines.append(f"- `{value}`")

    lines.extend([
        "",
        "## Transaction type classification (from GPT research)",
        "",
        "| Transaction | Research value |",
        "|---|---|",
        "| Incorporation | New federal registration signal |",
        "| Amalgamation | Entity relationship/change signal |",
        "| Name change | Identity resolution signal |",
        "| Registered-office change | Address refresh signal |",
        "| Other amendment | Potential attribute-change signal |",
        "| Continuance | Entity identity/lifecycle signal |",
        "| Discontinuance | Entity lifecycle/geography signal |",
        "| Revival | Reactivation signal |",
        "| Dissolution | Churn/inactive signal |",
        "| Intent to dissolve | Early lifecycle warning |",
        "| Correction/cancellation | Data-quality/event correction |",
        "| Arrangement | Corporate structural event |",
        "",
        "## Architecture notes",
        "",
        "- Only the latest month is available on the website.",
        "  Older months require contacting Corporations Canada.",
        "  Production job must capture and archive locally on publication.",
        "",
        "- OGL permits commercial reuse with attribution.",
        "  Automation rate/frequency must still respect site terms and robots.txt.",
        "  Do not mark scraping as unconditionally permitted based on OGL alone.",
        "",
        "## Research interpretation",
        "",
        (
            "This source is an official monthly publication of federal "
            "corporation transactions. The CBCA incorporation page exposes "
            "individual incorporation records as an HTML table."
        ),
        "",
        (
            "The effective date must not automatically be interpreted as "
            "the date the business began operating. It represents the "
            "effective date of the incorporation transaction."
        ),
        "",
        (
            "This source represents a federal registration event signal, "
            "not a complete operating-business opening signal. "
            "It must be combined with provincial/territorial registry events, "
            "municipal licensing data, and other operating signals for "
            "Canada-wide new-business detection."
        ),
        "",
        "## Recommended production model",
        "",
        "```",
        "Current active CSV",
        "    → daily current-state refresh",
        "",
        "Monthly transactions (this source)",
        "    → event feed while published",
        "    → capture + archive locally each month",
        "",
        "Corporations Canada API",
        "    → targeted verification/enrichment",
        "```",
        "",
    ])

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written: {REPORT_FILE}")


def main():
    print("=" * 80)
    print("VR03 — CORPORATIONS CANADA CBCA INCORPORATIONS")
    print("=" * 80)
    print()

    if not HTML_FILE.exists():
        download_html()
    else:
        print(f"Using existing HTML: {HTML_FILE}")
        print()

    records = parse_table()
    write_csv(records)
    result = profile(records)

    print()
    print("=" * 80)
    print("PROFILE")
    print("=" * 80)
    print()
    print(f"Records:    {result['records']:,}")
    print(f"Date range: {result['min_date']} -> {result['max_date']}")
    print()
    print("Province distribution:")
    for province, count in result["province_counts"].most_common():
        print(f"  {province:<30} {count:,}")
    print()
    print(f"Duplicate corporation IDs: {len(result['duplicate_ids'])}")
    print(f"Malformed dates:           {len(result['malformed_dates'])}")
    print()

    write_report(result)


if __name__ == "__main__":
    main()
