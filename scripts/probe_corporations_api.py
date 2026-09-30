"""
VR04 — Corporations Canada Federal API Probe

Strategy:
1. Download the official OpenAPI specification
2. Extract all endpoint paths and operations
3. Probe known corporation endpoints with sample corp numbers
4. Profile returned fields for each endpoint family
5. Write structured report to reports/validation_rounds/VR04_CORPORATIONS_CANADA_API.md

Known corporation samples (from VR01 active CSV + VR03 incorporations):
  VR03 (recent incorporations):
    1794852-2  — 17948522 CANADA INC.   AB
    1806189-1  — 18061891 CANADA INC.   AB
  VR01 (active CSV):
    8660115    — MINDANGLER CAPITAL INC.  ON
    821080     — AIRMEC CLIMATISATION LTEE  QC

IMPORTANT: Do not put any API key in this file or any report.
If an API key is required and not available, record that as a finding
(auth_required = True, unauthenticated_status = 401/403) and continue.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports" / "validation_rounds"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Official OpenAPI spec URL (from ISED API documentation)
OPENAPI_URL = (
    "https://api-testcase.ic.gc.ca/corporations-canada/v1/openapi.json"
)
OPENAPI_FALLBACK_URLS = [
    "https://api.ic.gc.ca/corporations-canada/v1/openapi.json",
    "https://api.ic.gc.ca/corporations/v1/openapi.json",
    "https://ised-isde.canada.ca/api/corporations-canada/openapi.json",
]

# Base API URL candidates — will be extracted from OpenAPI spec if found
API_BASE_CANDIDATES = [
    "https://api.ic.gc.ca/corporations-canada/v1",
    "https://api.ic.gc.ca/corporations/v1",
    "https://ised-isde.canada.ca/api/corporations-canada/v1",
]

OPENAPI_FILE = RAW_DIR / "corporations-canada-openapi.json"
REPORT_FILE = REPORTS_DIR / "VR04_CORPORATIONS_CANADA_API.md"

HEADERS = {
    "User-Agent": "CanadaBusinessDataAutomation/0.1 (research/validation)",
    "Accept": "application/json",
}

# Known sample corporation numbers from VR01 + VR03
SAMPLE_CORPS = [
    {"number": "1794852-2", "name": "17948522 CANADA INC.", "source": "VR03"},
    {"number": "1806189-1", "name": "18061891 CANADA INC.", "source": "VR03"},
    {"number": "8660115",   "name": "MINDANGLER CAPITAL INC.", "source": "VR01"},
    {"number": "821080",    "name": "AIRMEC CLIMATISATION LTEE", "source": "VR01"},
]

# Pause between API calls — conservative rate
REQUEST_DELAY = 1.5  # seconds


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def fetch(url: str, api_key: str | None = None, timeout: int = 30) -> tuple[int, dict | str | None, dict]:
    """
    Returns (status_code, parsed_body, response_headers).
    body is parsed JSON dict if possible, raw string otherwise, None on error.
    """
    headers = dict(HEADERS)
    if api_key:
        headers["x-api-key"] = api_key

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read()
            resp_headers = dict(resp.headers)
            try:
                body = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                body = raw.decode("utf-8", errors="replace")[:2000]
            return status, body, resp_headers
    except HTTPError as e:
        raw = e.read()
        resp_headers = dict(e.headers) if e.headers else {}
        try:
            body = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            body = raw.decode("utf-8", errors="replace")[:500]
        return e.code, body, resp_headers
    except URLError as e:
        return 0, str(e), {}
    except Exception as e:
        return 0, str(e), {}


# ---------------------------------------------------------------------------
# Step 1 — Download OpenAPI spec
# ---------------------------------------------------------------------------

def fetch_openapi_spec() -> dict | None:
    """Try known OpenAPI spec URLs. Return parsed spec or None."""
    urls_to_try = [OPENAPI_URL] + OPENAPI_FALLBACK_URLS

    for url in urls_to_try:
        print(f"Trying OpenAPI spec: {url}")
        status, body, _ = fetch(url)
        print(f"  → HTTP {status}")

        if status == 200 and isinstance(body, dict):
            OPENAPI_FILE.write_text(
                json.dumps(body, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"  → Saved: {OPENAPI_FILE}")
            return body

        time.sleep(REQUEST_DELAY)

    print("  → Could not retrieve OpenAPI spec from any known URL.")
    return None


def extract_endpoints(spec: dict) -> dict:
    """Extract paths, operations, and servers from OpenAPI spec."""
    servers = spec.get("servers", [])
    paths = spec.get("paths", {})

    endpoint_list = []
    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch"]:
            op = path_item.get(method)
            if op:
                endpoint_list.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": op.get("summary", ""),
                    "operation_id": op.get("operationId", ""),
                    "parameters": [
                        p.get("name") for p in op.get("parameters", [])
                        if isinstance(p, dict)
                    ],
                })

    base_urls = [s.get("url", "") for s in servers if isinstance(s, dict)]

    return {
        "servers": servers,
        "base_urls": base_urls,
        "endpoints": endpoint_list,
    }


# ---------------------------------------------------------------------------
# Step 2 — Probe base URL / auth without spec
# ---------------------------------------------------------------------------

def probe_base_urls() -> dict:
    """Try API base URL candidates to find a live one."""
    results = {}
    for base in API_BASE_CANDIDATES:
        url = base + "/"
        print(f"Probing base: {url}")
        status, body, headers = fetch(url)
        print(f"  → HTTP {status}")
        results[base] = {
            "status": status,
            "body_preview": str(body)[:300] if body else None,
            "rate_limit_headers": {
                k: v for k, v in headers.items()
                if any(x in k.lower() for x in ["rate", "limit", "retry", "x-api"])
            },
        }
        time.sleep(REQUEST_DELAY)
    return results


# ---------------------------------------------------------------------------
# Step 3 — Probe corporation endpoints
# ---------------------------------------------------------------------------

def probe_corporation(base_url: str, corp_number: str, api_key: str | None = None) -> dict:
    """Probe all known corporation endpoint patterns for one corp number."""
    results = {}

    # Normalize corp number — try both with and without hyphen
    corp_clean = corp_number.replace("-", "")

    endpoint_patterns = [
        f"/corporations/{corp_number}",
        f"/corporations/{corp_clean}",
        f"/corporation/{corp_number}",
        f"/corporation/{corp_clean}",
        f"/businesses/{corp_number}",
        f"/businesses/{corp_clean}",
    ]

    for path in endpoint_patterns:
        url = base_url.rstrip("/") + path
        print(f"  GET {url}")
        status, body, headers = fetch(url, api_key=api_key)
        print(f"    → HTTP {status}")

        results[path] = {
            "status": status,
            "fields": sorted(body.keys()) if isinstance(body, dict) else None,
            "body_preview": body if isinstance(body, dict) else str(body)[:300],
            "rate_limit_headers": {
                k: v for k, v in headers.items()
                if any(x in k.lower() for x in ["rate", "limit", "retry"])
            },
        }

        if status == 200:
            print(f"    → SUCCESS — fields: {sorted(body.keys()) if isinstance(body, dict) else 'non-JSON'}")
            break  # Found a working pattern — don't try others

        time.sleep(REQUEST_DELAY)

    return results


def probe_sub_endpoints(base_url: str, corp_path: str, corp_number: str, api_key: str | None = None) -> dict:
    """
    Probe sub-resource endpoints under a corporation.
    corp_path = the working base path e.g. /corporations/1794852-2
    """
    sub_resources = [
        "directors",
        "officers",
        "individuals-with-significant-control",
        "isc",
        "activities",
        "history",
        "names",
        "filings",
        "parties",
        "addresses",
    ]

    results = {}
    for sub in sub_resources:
        url = base_url.rstrip("/") + corp_path + "/" + sub
        print(f"  GET {url}")
        status, body, headers = fetch(url, api_key=api_key)
        print(f"    → HTTP {status}")

        results[sub] = {
            "status": status,
            "fields": sorted(body.keys()) if isinstance(body, dict) else None,
            "is_list": isinstance(body, list),
            "list_count": len(body) if isinstance(body, list) else None,
            "body_preview": (
                body[:3] if isinstance(body, list)
                else body if isinstance(body, dict)
                else str(body)[:300]
            ),
        }

        if status == 200:
            print(f"    → SUCCESS")

        time.sleep(REQUEST_DELAY)

    return results


def probe_search(base_url: str, api_key: str | None = None) -> dict:
    """Probe search/query endpoints."""
    search_paths = [
        "/corporations?name=MINDANGLER+CAPITAL",
        "/corporations?businessNumber=835752437",
        "/corporations/search?q=MINDANGLER",
        "/search/corporations?name=MINDANGLER",
        "/corporations?corporationNumber=8660115",
    ]

    results = {}
    for path in search_paths:
        url = base_url.rstrip("/") + path
        print(f"  GET {url}")
        status, body, headers = fetch(url, api_key=api_key)
        print(f"    → HTTP {status}")

        results[path] = {
            "status": status,
            "is_list": isinstance(body, list),
            "list_count": len(body) if isinstance(body, list) else None,
            "fields": sorted(body.keys()) if isinstance(body, dict) else None,
            "body_preview": str(body)[:400],
        }

        time.sleep(REQUEST_DELAY)

    return results


# ---------------------------------------------------------------------------
# Step 4 — Collect all date fields from a response
# ---------------------------------------------------------------------------

def extract_date_fields(obj: dict | list, prefix: str = "") -> list[tuple[str, str]]:
    """Recursively find all fields that look like dates."""
    found = []
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str) and date_pattern.search(v):
                found.append((path, v))
            elif isinstance(v, (dict, list)):
                found.extend(extract_date_fields(v, path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:5]):
            found.extend(extract_date_fields(item, f"{prefix}[{i}]"))

    return found


# ---------------------------------------------------------------------------
# Step 5 — Write report
# ---------------------------------------------------------------------------

def write_report(findings: dict) -> None:
    lines = [
        "# VR04 — Corporations Canada Federal API",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## 1. OpenAPI Specification",
        "",
    ]

    spec_result = findings.get("openapi")
    if spec_result and spec_result.get("found"):
        lines += [
            f"- Status: found ✅",
            f"- Saved: `{OPENAPI_FILE.name}`",
            f"- Servers: {spec_result.get('servers')}",
            f"- Endpoint count: {spec_result.get('endpoint_count')}",
            "",
            "### Endpoints discovered from spec",
            "",
            "| Method | Path | Summary |",
            "|---|---|---|",
        ]
        for ep in spec_result.get("endpoints", []):
            lines.append(
                f"| `{ep['method']}` | `{ep['path']}` | {ep['summary']} |"
            )
    else:
        lines += [
            "- Status: not retrieved ❌",
            "- All known OpenAPI spec URLs returned non-200 or non-JSON responses.",
            "- Endpoint paths probed manually using known patterns.",
            "",
        ]

    lines += [
        "",
        "## 2. Base URL Probe",
        "",
        "| Base URL | HTTP Status | Notes |",
        "|---|---|---|",
    ]
    for base_url, result in findings.get("base_probe", {}).items():
        notes = ""
        if result["rate_limit_headers"]:
            notes = f"Rate headers: {result['rate_limit_headers']}"
        lines.append(
            f"| `{base_url}` | {result['status']} | {notes} |"
        )

    lines += [
        "",
        "## 3. Authentication",
        "",
    ]
    auth = findings.get("auth", {})
    lines += [
        f"- API key required (documented): {auth.get('documented_requirement', 'subscription + API key')}",
        f"- Documented rate limit: {auth.get('documented_rate_limit', '60 hits/minute (public plan)')}",
        f"- Unauthenticated HTTP status observed: {auth.get('unauthenticated_status', 'see base probe')}",
        "",
    ]

    lines += [
        "## 4. Corporation Lookup",
        "",
    ]
    for corp in findings.get("corporation_probes", []):
        lines += [
            f"### {corp['number']} — {corp['name']} ({corp['source']})",
            "",
        ]
        for path, result in corp.get("results", {}).items():
            lines += [
                f"- Path: `{path}` → HTTP {result['status']}",
            ]
            if result.get("fields"):
                lines.append(f"  - Fields: `{', '.join(result['fields'])}`")
            if result.get("body_preview") and isinstance(result["body_preview"], dict):
                for k, v in list(result["body_preview"].items())[:8]:
                    lines.append(f"  - `{k}`: `{str(v)[:100]}`")
        lines.append("")

    lines += [
        "## 5. Sub-resource Endpoints",
        "",
    ]
    for corp in findings.get("sub_probes", []):
        lines += [
            f"### Sub-resources for {corp['number']}",
            "",
            "| Endpoint | HTTP | Fields / Notes |",
            "|---|---|---|",
        ]
        for sub, result in corp.get("results", {}).items():
            notes = ""
            if result.get("fields"):
                notes = ", ".join(result["fields"])
            elif result.get("is_list"):
                notes = f"list — {result['list_count']} items"
            elif result.get("body_preview"):
                notes = str(result["body_preview"])[:100]
            lines.append(
                f"| `{sub}` | {result['status']} | {notes} |"
            )
        lines.append("")

    lines += [
        "## 6. Date Fields Observed",
        "",
        "| Field path | Example value | Interpretation |",
        "|---|---|---|",
    ]
    for item in findings.get("date_fields", []):
        lines.append(
            f"| `{item[0]}` | `{item[1]}` | *(to be documented)* |"
        )
    if not findings.get("date_fields"):
        lines.append("| *(no date fields observed — API may require authentication)* | | |")

    lines += [
        "",
        "## 7. Search / Query Capability",
        "",
        "| Query | HTTP | Notes |",
        "|---|---|---|",
    ]
    for path, result in findings.get("search_probe", {}).items():
        notes = ""
        if result.get("list_count") is not None:
            notes = f"{result['list_count']} results"
        elif result.get("fields"):
            notes = ", ".join(result["fields"][:5])
        else:
            notes = str(result.get("body_preview", ""))[:80]
        lines.append(f"| `{path}` | {result['status']} | {notes} |")

    lines += [
        "",
        "## 8. Rate Limit",
        "",
        "- Documented public plan limit: 60 hits/minute",
        "- Rate-limit headers observed: see base probe table above",
        "- Deliberate rate-limit testing: NOT performed (respect documented limit)",
        "- Conservative probe rate used: 1 request per 1.5 seconds",
        "",
    ]

    # Capability summary table
    lines += [
        "## 9. Capability Summary",
        "",
        "| Capability | API result | Useful for system? |",
        "|---|---|---|",
    ]
    for row in findings.get("capability_summary", []):
        lines.append(
            f"| {row['capability']} | {row['result']} | {row['useful']} |"
        )

    lines += [
        "",
        "## 10. API Role Assessment",
        "",
    ]
    role = findings.get("role_assessment", "Not yet determined — authentication required to measure field availability.")
    lines.append(role)

    lines += [
        "",
        "## 11. What this API cannot provide",
        "",
        "- Employee count (not in federal corporate registry)",
        "- NAICS / industry classification (not in federal corporate registry)",
        "- Phone, email, website (not filed with Corporations Canada)",
        "- Operational decision-makers beyond filed directors/officers",
        "",
        "## 12. Open questions",
        "",
        "- [ ] Obtain API key and re-run probe to measure actual field responses",
        "- [ ] Confirm ISC endpoint availability programmatically",
        "- [ ] Confirm name history / activities endpoint paths",
        "- [ ] Measure response time at conservative production rate",
        "- [ ] Confirm commercial use permitted under API subscription terms",
        "",
    ]

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written: {REPORT_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("VR04 — CORPORATIONS CANADA FEDERAL API PROBE")
    print("=" * 80)
    print()

    findings: dict = {}

    # ---- Step 1: OpenAPI spec ----
    print("STEP 1 — OpenAPI Specification")
    print("-" * 40)
    spec = fetch_openapi_spec()
    if spec:
        extracted = extract_endpoints(spec)
        findings["openapi"] = {
            "found": True,
            "servers": extracted["base_urls"],
            "endpoint_count": len(extracted["endpoints"]),
            "endpoints": extracted["endpoints"],
        }
        print(f"Endpoints found in spec: {len(extracted['endpoints'])}")
        for ep in extracted["endpoints"]:
            print(f"  {ep['method']:6} {ep['path']:60} {ep['summary']}")
        # Use base URL from spec if available
        if extracted["base_urls"]:
            api_base = extracted["base_urls"][0]
            print(f"\nUsing spec base URL: {api_base}")
        else:
            api_base = None
    else:
        findings["openapi"] = {"found": False}
        api_base = None
    print()

    # ---- Step 2: Base URL probe ----
    print("STEP 2 — Base URL Probe")
    print("-" * 40)

    # If spec gave us a base, add it to candidates
    candidates = list(API_BASE_CANDIDATES)
    if api_base and api_base not in candidates:
        candidates.insert(0, api_base)

    base_results = {}
    working_base = None
    for base in candidates:
        url = base.rstrip("/") + "/corporations/8660115"
        print(f"Probing: {url}")
        status, body, headers = fetch(url)
        print(f"  → HTTP {status}")

        rate_headers = {
            k: v for k, v in headers.items()
            if any(x in k.lower() for x in ["rate", "limit", "retry", "x-api"])
        }

        base_results[base] = {
            "status": status,
            "body_preview": str(body)[:200] if body else None,
            "rate_limit_headers": rate_headers,
        }

        if status in (200, 401, 403) and working_base is None:
            working_base = base
            print(f"  → Working base candidate: {base}")

        time.sleep(REQUEST_DELAY)

    findings["base_probe"] = base_results
    findings["auth"] = {
        "documented_requirement": "API key required — subscription via ISED developer portal",
        "documented_rate_limit": "60 hits/minute (public plan)",
        "unauthenticated_status": str({b: r["status"] for b, r in base_results.items()}),
    }

    if working_base is None:
        working_base = API_BASE_CANDIDATES[0]
        print(f"\nNo confirmed working base — using default: {working_base}")
    else:
        print(f"\nWorking base: {working_base}")
    print()

    # ---- Step 3: Corporation lookup ----
    print("STEP 3 — Corporation Lookup")
    print("-" * 40)
    corp_probes = []
    for corp in SAMPLE_CORPS[:2]:  # 2 samples is enough for field discovery
        print(f"\nProbing: {corp['number']} — {corp['name']}")
        results = probe_corporation(working_base, corp["number"])
        corp_probes.append({**corp, "results": results})
    findings["corporation_probes"] = corp_probes
    print()

    # ---- Step 4: Sub-resources ----
    print("STEP 4 — Sub-resource Endpoints")
    print("-" * 40)
    sub_probes = []

    # Use first corp — try both number formats to find a working path
    corp = SAMPLE_CORPS[0]
    # Determine which path worked in step 3
    working_corp_path = None
    for path, result in corp_probes[0]["results"].items():
        if result["status"] == 200:
            working_corp_path = path
            break

    if working_corp_path is None:
        # Try the most likely pattern even if it returned 401/403
        working_corp_path = f"/corporations/{corp['number']}"
        print(f"No 200 response — using assumed path: {working_corp_path}")

    print(f"\nProbing sub-resources for: {corp['number']} at {working_corp_path}")
    sub_results = probe_sub_endpoints(working_base, working_corp_path, corp["number"])
    sub_probes.append({**corp, "results": sub_results})
    findings["sub_probes"] = sub_probes
    print()

    # ---- Step 5: Collect date fields ----
    date_fields: list[tuple[str, str]] = []
    for probe in corp_probes:
        for path, result in probe["results"].items():
            if isinstance(result.get("body_preview"), dict):
                date_fields.extend(
                    extract_date_fields(result["body_preview"])
                )
    for probe in sub_probes:
        for sub, result in probe["results"].items():
            preview = result.get("body_preview")
            if isinstance(preview, (dict, list)):
                date_fields.extend(extract_date_fields(preview, prefix=sub))
    findings["date_fields"] = date_fields

    # ---- Step 6: Search ----
    print("STEP 5 — Search / Query Capability")
    print("-" * 40)
    findings["search_probe"] = probe_search(working_base)
    print()

    # ---- Step 7: Capability summary ----
    # Build from what we actually observed
    def result_for(corp_results: list, sub_results: list, keys: list[str]) -> str:
        """Return 'observed' / 'HTTP NNN' / 'not found' for a capability."""
        for probe in corp_results:
            for _, r in probe["results"].items():
                if r["status"] == 200 and r.get("fields"):
                    matched = [k for k in keys if any(k.lower() in f.lower() for f in r["fields"])]
                    if matched:
                        return f"present — `{'`, `'.join(matched)}`"
        for probe in sub_results:
            for sub, r in probe["results"].items():
                if sub in keys and r["status"] == 200:
                    return f"HTTP 200 at `/{sub}`"
                if sub in keys:
                    return f"HTTP {r['status']} at `/{sub}`"
        return "not observed"

    # Determine auth status from probes
    all_statuses = [
        r["status"]
        for r in base_results.values()
    ]
    auth_note = "auth required (401/403)" if any(s in (401, 403) for s in all_statuses) else "open"

    capability_rows = []
    for cap, keys in [
        ("Corporation lookup",          ["corporationNumber", "corporation_number", "id"]),
        ("Business Number (BN)",        ["businessNumber", "business_number", "bn"]),
        ("Current legal name",          ["name", "corporateName", "legalName"]),
        ("Name history",                ["names"]),
        ("Status",                      ["status"]),
        ("Registered office / address", ["address", "registeredOffice", "street"]),
        ("Directors",                   ["directors"]),
        ("Director history",            ["directors"]),
        ("ISC",                         ["individuals-with-significant-control", "isc"]),
        ("Corporate activities",        ["activities", "history", "filings"]),
        ("Incorporation date",          ["incorporationDate", "effectiveDate"]),
        ("Transaction / history dates", ["activities", "history"]),
        ("NAICS",                       ["naics", "industry"]),
        ("Employees",                   ["employees", "employeeCount"]),
        ("Website",                     ["website", "url"]),
        ("Phone",                       ["phone", "telephone"]),
        ("Email",                       ["email"]),
        ("Search / pagination",         ["search"]),
        ("Rate limit",                  []),
    ]:
        if cap == "Rate limit":
            result = "60 hits/min (documented)"
            useful = "Yes — production planning"
        elif cap in ("NAICS", "Employees", "Website", "Phone", "Email"):
            result = "not expected in registry"
            useful = "No — not a registry field"
        else:
            result = auth_note if any(s in (401, 403) for s in all_statuses) else result_for(
                corp_probes, sub_probes, keys
            )
            useful = "Pending auth" if "auth" in result else "Yes" if "present" in result or "200" in result else "Unknown"

        capability_rows.append({
            "capability": cap,
            "result": result,
            "useful": useful,
        })

    findings["capability_summary"] = capability_rows

    # Role assessment
    if any(s in (401, 403) for s in all_statuses):
        findings["role_assessment"] = (
            "**Role: Targeted verification/enrichment (expected) — pending authenticated probe.**\n\n"
            "All API endpoints returned 401 or 403 without an API key. "
            "This confirms authentication is required. "
            "The documented public plan (60 hits/minute) is sufficient for targeted lookups "
            "against known corporation numbers from the bulk CSV. "
            "An authenticated re-run is required to measure actual field availability for "
            "directors, ISC, activities, name history, and date semantics."
        )
    elif any(s == 200 for s in all_statuses):
        findings["role_assessment"] = (
            "**Role: Targeted verification/enrichment — confirmed accessible.**\n\n"
            "See capability summary table for measured field availability."
        )
    else:
        findings["role_assessment"] = (
            "**Role: Undetermined — no successful API responses.**\n\n"
            "No API base URL returned a useful response. "
            "The official ISED developer portal must be consulted to obtain "
            "the correct base URL and an API key before re-running this probe."
        )

    # ---- Write report ----
    write_report(findings)

    # ---- Terminal summary ----
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"OpenAPI spec retrieved: {findings['openapi']['found']}")
    print(f"HTTP statuses observed: {all_statuses}")
    print(f"Working base URL: {working_base}")
    print(f"Date fields found: {len(date_fields)}")
    print(f"Capability rows: {len(capability_rows)}")
    print()


if __name__ == "__main__":
    main()
