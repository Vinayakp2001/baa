from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports" / "validation_rounds"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_PAGE = (
    "https://open.canada.ca/data/en/dataset/"
    "0032ce54-c5dd-4b66-99a0-320a7b5e99f2"
)

DATA_SERVICES_PAGE = (
    "https://ised-isde.canada.ca/site/corporations-canada/en/data-services"
)

DATASETS = {
    "active_business_corporations": {
        "description": (
            "Federal business corporations created under the "
            "Canada Business Corporations Act (CBCA) that are currently active."
        ),
        "url": (
            "https://d4bf66bykfyaf.cloudfront.net/"
            "corporations-active-cbca-en.csv"
        ),
    },
    "other_active_corporations": {
        "description": (
            "Other active federal corporations including not-for-profits, "
            "cooperatives, boards of trade and special-act corporations."
        ),
        "url": (
            "https://d4bf66bykfyaf.cloudfront.net/"
            "corporations-active-non-cbca-en.csv"
        ),
    },
    "inactive_business_corporations": {
        "description": (
            "Federal business corporations created under the CBCA "
            "that are currently inactive."
        ),
        "url": (
            "https://d4bf66bykfyaf.cloudfront.net/"
            "corporations-inactive-or-dissolved-cbca-en.csv"
        ),
    },
    "other_inactive_corporations": {
        "description": (
            "Other inactive federal corporations."
        ),
        "url": (
            "https://d4bf66bykfyaf.cloudfront.net/"
            "corporations-inactive-or-dissolved-non-cbca-en.csv"
        ),
    },
}


def check_url(url: str) -> dict:
    """
    Perform a lightweight HEAD request.

    Some servers do not support HEAD properly, so fall back to GET
    with a small byte range.
    """

    headers = {
        "User-Agent": (
            "CanadaBusinessDataAutomation/0.1 "
            "(research/validation)"
        )
    }

    try:
        request = Request(
            url,
            headers=headers,
            method="HEAD",
        )

        with urlopen(request, timeout=30) as response:
            return {
                "ok": True,
                "status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "content_length": response.headers.get("Content-Length"),
                "final_url": response.geturl(),
                "method": "HEAD",
            }

    except Exception as head_error:

        try:
            request = Request(
                url,
                headers={
                    **headers,
                    "Range": "bytes=0-1023",
                },
                method="GET",
            )

            with urlopen(request, timeout=30) as response:
                return {
                    "ok": True,
                    "status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": response.headers.get("Content-Length"),
                    "content_range": response.headers.get("Content-Range"),
                    "final_url": response.geturl(),
                    "method": "GET_RANGE",
                    "head_error": str(head_error),
                }

        except HTTPError as error:
            return {
                "ok": False,
                "status": error.code,
                "error": str(error),
                "method": "GET_RANGE",
            }

        except URLError as error:
            return {
                "ok": False,
                "error": str(error),
                "method": "GET_RANGE",
            }

        except Exception as error:
            return {
                "ok": False,
                "error": str(error),
                "method": "GET_RANGE",
            }


def build_report(results: dict) -> str:
    now = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Corporations Canada Dataset Discovery Report",
        "",
        f"Generated: `{now}`",
        "",
        "## Official dataset",
        "",
        f"- Dataset page: {DATASET_PAGE}",
        f"- Corporations Canada data services: {DATA_SERVICES_PAGE}",
        "- Publisher: Innovation, Science and Economic Development Canada",
        "- Dataset: Federal Corporations",
        "- Licence: Open Government Licence - Canada",
        "- Update frequency: typically daily",
        "",
        "## Current dataset structure",
        "",
        (
            "As of April 2026, the Federal Corporations dataset was "
            "split into four subsets, each available in English and French."
        ),
        "",
        "| Dataset | URL status | HTTP | Content-Type |",
        "|---|---:|---:|---|",
    ]

    for name, result in results.items():
        status = "PASS" if result.get("ok") else "FAIL"

        lines.append(
            f"| `{name}` | {status} | "
            f"{result.get('status', '')} | "
            f"{result.get('content_type', '')} |"
        )

    lines.extend([
        "",
        "## Resources",
        "",
    ])

    for name, info in DATASETS.items():
        result = results[name]

        lines.extend([
            f"### {name}",
            "",
            f"- Description: {info['description']}",
            f"- URL: `{info['url']}`",
            f"- Accessible: `{result.get('ok')}`",
            f"- HTTP status: `{result.get('status')}`",
            f"- Content-Type: `{result.get('content_type')}`",
            f"- Content-Length: `{result.get('content_length')}`",
            f"- Final URL: `{result.get('final_url')}`",
            "",
        ])

    lines.extend([
        "## Research conclusion",
        "",
        (
            "The current Federal Corporations source has been identified "
            "from the official Open Government Portal. No guessed URL "
            "is being used."
        ),
        "",
        (
            "The next step is to download and profile the active business "
            "corporations CSV before making any architecture decisions."
        ),
        "",
        "## Important scope limitation",
        "",
        (
            "Federal Corporations covers corporations governed by federal "
            "legislation. It does NOT contain corporations created under "
            "provincial, territorial or other corporate legislation."
        ),
        "",
        (
            "Therefore it must not be treated as a Canada-wide master "
            "business dataset."
        ),
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    print("=" * 80)
    print("CORPORATIONS CANADA - OFFICIAL DATASET DISCOVERY")
    print("=" * 80)
    print()

    print("Official dataset:")
    print(DATASET_PAGE)
    print()

    results = {}

    for name, info in DATASETS.items():
        print("-" * 80)
        print(name)
        print(info["url"])

        result = check_url(info["url"])
        results[name] = result

        if result.get("ok"):
            print("STATUS: PASS")
            print("HTTP:", result.get("status"))
            print("Content-Type:", result.get("content_type"))
            print("Content-Length:", result.get("content_length"))
            print("Final URL:", result.get("final_url"))
        else:
            print("STATUS: FAIL")
            print("HTTP:", result.get("status"))
            print("ERROR:", result.get("error"))

        print()

    report_path = REPORTS_DIR / "VR01_CORPORATIONS_CANADA_DISCOVERY.md"

    report = build_report(results)
    report_path.write_text(report, encoding="utf-8")

    json_path = REPORTS_DIR / "VR01_CORPORATIONS_CANADA_DISCOVERY.json"
    json_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "dataset_page": DATASET_PAGE,
                "data_services_page": DATA_SERVICES_PAGE,
                "datasets": DATASETS,
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 80)
    print("REPORTS")
    print("=" * 80)
    print(report_path)
    print(json_path)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
