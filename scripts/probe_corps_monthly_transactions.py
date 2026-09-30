from __future__ import annotations

import re
from pathlib import Path
from urllib.request import Request, urlopen


BASE_URL = (
    "https://ised-isde.canada.ca/site/"
    "corporations-canada/en/data-services/"
    "monthly-transactions"
)

INCORPORATION_URL = (
    "https://ised-isde.canada.ca/site/"
    "corporations-canada/en/data-services/"
    "monthly-transactions/"
    "certificates-incorporation-cbca"
)

MONTH_URL = (
    "https://ised-isde.canada.ca/site/"
    "corporations-canada/en/data-services/"
    "monthly-transactions/"
    "monthly-transactions-june-2026"
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports" / "validation_rounds"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def fetch(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "CanadaBusinessDataAutomation/0.1 "
                "(research/validation)"
            )
        },
    )

    with urlopen(request, timeout=30) as response:
        content = response.read()

    return content.decode(
        "utf-8",
        errors="replace",
    )


def extract_links(html: str) -> list[str]:
    links = re.findall(
        r'href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    result = []

    for link in links:
        if link not in result:
            result.append(link)

    return result


def main():
    print("=" * 80)
    print("CORPORATIONS CANADA — MONTHLY TRANSACTIONS PROBE")
    print("=" * 80)
    print()

    pages = {
        "monthly_transactions_index": BASE_URL,
        "cbca_incorporations": INCORPORATION_URL,
        "july_2026_month": MONTH_URL,
    }

    reports = []

    for name, url in pages.items():

        print("-" * 80)
        print(name)
        print(url)
        print()

        try:
            html = fetch(url)

            print(
                f"Downloaded: "
                f"{len(html):,} characters"
            )

            links = extract_links(html)

            print(
                f"Links discovered: "
                f"{len(links):,}"
            )

            # Print links relevant to monthly transactions.
            relevant = [
                link
                for link in links
                if (
                    "monthly" in link.lower()
                    or "certificate" in link.lower()
                    or "transaction" in link.lower()
                )
            ]

            print()
            print("Relevant links:")

            for link in relevant[:100]:
                print(" ", link)

            reports.append({
                "name": name,
                "url": url,
                "characters": len(html),
                "links": relevant,
            })

        except Exception as exc:
            print("ERROR:", exc)

            reports.append({
                "name": name,
                "url": url,
                "error": str(exc),
            })

        print()

    output = []

    output.append(
        "# Corporations Canada Monthly Transactions Probe"
    )
    output.append("")

    for item in reports:

        output.append(
            f"## {item['name']}"
        )
        output.append("")
        output.append(
            f"- URL: `{item['url']}`"
        )

        if "error" in item:
            output.append(
                f"- Error: `{item['error']}`"
            )
        else:
            output.append(
                f"- HTML characters: `{item['characters']:,}`"
            )

            output.append("")
            output.append("### Relevant links")
            output.append("")

            for link in item["links"]:
                output.append(
                    f"- `{link}`"
                )

        output.append("")

    report_path = (
        REPORTS_DIR
        / "VR02b_CORPS_CANADA_MONTHLY_TRANSACTIONS_PROBE.md"
    )

    report_path.write_text(
        "\n".join(output),
        encoding="utf-8",
    )

    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print()
    print(report_path)


if __name__ == "__main__":
    main()
