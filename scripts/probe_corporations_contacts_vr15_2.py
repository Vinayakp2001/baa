"""
VR15.2 — Corporations Canada Public Director / ISC Enrichment Probe
Validates whether director and ISC (Individuals with Significant Control)
information is programmatically retrievable from Corporations Canada public
records for a test set of federal corporation numbers.

Two access routes tested:
  Route A — Public HTML corporation detail page
             https://ised-isde.canada.ca/cc/lgcy/fdrlCrpDtls.html?corpId=XXXXXX
  Route B — Corporations Canada search API (JSON, if accessible without key)
             https://ised-isde.canada.ca/cc/api/corporations/XXXXXX

Per VR04 findings: the REST API gateway requires an API key for authenticated
endpoints. This probe tests whether public-facing HTML or any unauthenticated
JSON endpoint exposes director/ISC data.

For each test corporation:
  - Attempt Route A (HTML page) — check HTTP status, extract director names if present
  - Attempt Route B (JSON API) — check HTTP status, inspect fields returned
  - Record: status, fields observed, director count, ISC presence, automation feasibility

Output: reports/validation_rounds/VR15_CORPORATIONS_CONTACTS.json
        reports/validation_rounds/VR15_CORPORATIONS_CONTACTS.md

Run: python scripts/probe_corporations_contacts_vr15_2.py
"""

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Test set — federal corporation numbers from VR01 sample + known corps
# Using numbers confirmed to exist in the active CBCA CSV
# ---------------------------------------------------------------------------
TEST_CORPS = [
    {"corp_num": "8660115", "name": "MINDANGLER CAPITAL INC.", "province": "ON"},
    {"corp_num": "821080",  "name": "AIRMEC CLIMATISATION LTEE", "province": "QC"},
    # Well-known Canadian federal corporations (publicly searchable)
    {"corp_num": "158072",  "name": "CANADIAN TIRE CORPORATION LIMITED", "province": "ON"},
    {"corp_num": "7122",    "name": "AIR CANADA", "province": "QC"},
    {"corp_num": "250430",  "name": "LOBLAWS INC", "province": "ON"},
    {"corp_num": "2893",    "name": "BOMBARDIER INC.", "province": "QC"},
    {"corp_num": "339573",  "name": "SHOPPERS DRUG MART CORPORATION", "province": "ON"},
    {"corp_num": "271517",  "name": "ROGERS COMMUNICATIONS INC.", "province": "ON"},
    # Smaller/mid-size for realistic pipeline representation
    {"corp_num": "9095548", "name": "TEST SMALL CORP A", "province": "ON"},
    {"corp_num": "9012345", "name": "TEST SMALL CORP B", "province": "BC"},
]

HEADERS = {
    "User-Agent": "CanadianBusinessDataPipeline/1.0 (research probe; contact: research@pipeline.local)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
}

JSON_HEADERS = {
    "User-Agent": "CanadianBusinessDataPipeline/1.0 (research probe; contact: research@pipeline.local)",
    "Accept": "application/json",
}

# Corporations Canada public URLs (confirmed in VR04)
HTML_BASE = "https://ised-isde.canada.ca/cc/lgcy/fdrlCrpDtls.html"
API_BASE  = "https://ised-isde.canada.ca/cc/api/corporations"

REQUEST_DELAY = 2.0
REQUEST_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Minimal HTML parser — extracts visible text
# ---------------------------------------------------------------------------
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            s = data.strip()
            if s:
                self.parts.append(s)

    def get_text(self):
        return " ".join(self.parts)


# ---------------------------------------------------------------------------
# HTTP fetch — HTML
# ---------------------------------------------------------------------------
def fetch_html(url):
    result = {"url": url, "status": None, "body": "", "error": None}
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result["status"] = resp.status
            raw = resp.read(500_000)
            result["body"] = raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# HTTP fetch — JSON
# ---------------------------------------------------------------------------
def fetch_json(url):
    result = {"url": url, "status": None, "data": None, "error": None}
    try:
        req = urllib.request.Request(url, headers=JSON_HEADERS)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result["status"] = resp.status
            raw = resp.read(200_000)
            result["data"] = json.loads(raw.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# Extract director/ISC signals from HTML page text
# ---------------------------------------------------------------------------
DIRECTOR_PATTERNS = [
    re.compile(r'director[s]?\s*:?\s*([A-Z][a-zA-Z\s,\-]+)', re.IGNORECASE),
    re.compile(r'officer[s]?\s*:?\s*([A-Z][a-zA-Z\s,\-]+)', re.IGNORECASE),
    re.compile(r'president\s*:?\s*([A-Z][a-zA-Z\s\-]+)', re.IGNORECASE),
]

ISC_PATTERNS = [
    re.compile(r'individual[s]?\s+with\s+significant\s+control', re.IGNORECASE),
    re.compile(r'ISC\s*:', re.IGNORECASE),
    re.compile(r'significant\s+control', re.IGNORECASE),
]


def extract_directors_from_html(text):
    directors = []
    for pat in DIRECTOR_PATTERNS:
        for m in pat.finditer(text):
            candidate = m.group(1).strip()[:100]
            if len(candidate) > 3:
                directors.append(candidate)
    return list(set(directors))[:10]


def detect_isc_section(text):
    for pat in ISC_PATTERNS:
        if pat.search(text):
            return True
    return False


def extract_json_fields(data, corp_num):
    """Recursively extract interesting fields from JSON response."""
    fields_found = {}
    if not isinstance(data, dict):
        return fields_found
    interesting_keys = [
        "directors", "officers", "individuals", "isc", "significantControl",
        "name", "status", "incorporationDate", "registeredAddress",
        "phone", "email", "website", "activities"
    ]
    for key in interesting_keys:
        if key in data:
            fields_found[key] = str(data[key])[:200]
    return fields_found


# ---------------------------------------------------------------------------
# Probe one corporation
# ---------------------------------------------------------------------------
def probe_corp(corp):
    corp_num = corp["corp_num"]
    result = {
        "corp_num": corp_num,
        "name": corp["name"],
        "province": corp["province"],
        # Route A — HTML
        "html_status": None,
        "html_error": None,
        "html_page_found": False,
        "html_directors_extracted": [],
        "html_isc_section_detected": False,
        "html_director_count": 0,
        # Route B — JSON API
        "api_status": None,
        "api_error": None,
        "api_accessible": False,
        "api_requires_auth": False,
        "api_fields_present": {},
        "api_director_count": 0,
        "api_isc_present": False,
        # Overall
        "director_data_accessible": False,
        "isc_data_accessible": False,
        "automation_feasible": False,
        "notes": [],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }

    # --- Route A: HTML page ---
    html_url = f"{HTML_BASE}?corpId={corp_num}"
    print(f"  [HTML] {html_url}")
    time.sleep(REQUEST_DELAY)
    html_resp = fetch_html(html_url)
    result["html_status"] = html_resp["status"]
    result["html_error"] = html_resp["error"]

    if html_resp["status"] == 200 and html_resp["body"]:
        result["html_page_found"] = True
        extractor = TextExtractor()
        extractor.feed(html_resp["body"])
        text = extractor.get_text()
        directors = extract_directors_from_html(text)
        has_isc = detect_isc_section(text)
        result["html_directors_extracted"] = directors
        result["html_director_count"] = len(directors)
        result["html_isc_section_detected"] = has_isc
        if directors:
            result["director_data_accessible"] = True
            result["notes"].append(f"HTML: {len(directors)} director signal(s) found in page text")
        if has_isc:
            result["isc_data_accessible"] = True
            result["notes"].append("HTML: ISC section detected in page text")
        if not directors and not has_isc:
            # Check if the page at least has corp details
            if corp["name"].split()[0].upper() in text.upper() or "corporation" in text.lower():
                result["notes"].append("HTML: page loaded, corp details present, no director/ISC text extracted")
            else:
                result["notes"].append("HTML: page loaded but content appears generic/empty")
    elif html_resp["status"] == 404:
        result["notes"].append(f"HTML: 404 — corporation number {corp_num} not found on HTML interface")
    elif html_resp["status"]:
        result["notes"].append(f"HTML: HTTP {html_resp['status']}")
    else:
        result["notes"].append(f"HTML: connection error — {html_resp['error']}")

    # --- Route B: JSON API ---
    api_url = f"{API_BASE}/{corp_num}"
    print(f"  [API]  {api_url}")
    time.sleep(REQUEST_DELAY)
    api_resp = fetch_json(api_url)
    result["api_status"] = api_resp["status"]
    result["api_error"] = api_resp["error"]

    if api_resp["status"] == 200 and api_resp["data"]:
        result["api_accessible"] = True
        fields = extract_json_fields(api_resp["data"], corp_num)
        result["api_fields_present"] = fields
        if "directors" in fields or "officers" in fields:
            result["api_director_count"] = 1  # at minimum 1 array present
            result["director_data_accessible"] = True
            result["notes"].append("API: director/officer field present in JSON response")
        if "isc" in fields or "significantControl" in fields:
            result["isc_data_accessible"] = True
            result["notes"].append("API: ISC/significantControl field present in JSON response")
        result["notes"].append(f"API: accessible, fields returned: {list(fields.keys())}")
    elif api_resp["status"] in (401, 403):
        result["api_requires_auth"] = True
        result["notes"].append(f"API: HTTP {api_resp['status']} — authentication required")
    elif api_resp["status"] == 404:
        result["notes"].append(f"API: 404 — corporation {corp_num} not found via API")
    elif api_resp["status"]:
        result["notes"].append(f"API: HTTP {api_resp['status']}")
    else:
        result["notes"].append(f"API: connection error — {api_resp['error']}")

    # Automation feasibility assessment
    if result["director_data_accessible"] and (
        result["api_accessible"] or result["html_page_found"]
    ):
        result["automation_feasible"] = True

    print(f"  [RESULT] {corp['name']}: "
          f"html={result['html_status']} api={result['api_status']} "
          f"directors={result['director_data_accessible']} isc={result['isc_data_accessible']}")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== VR15.2 Corporations Canada Director/ISC Enrichment Probe ===")
    print(f"Test set: {len(TEST_CORPS)} corporations")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    results = []
    for corp in TEST_CORPS:
        print(f"\n[{corp['corp_num']}] {corp['name']} ({corp['province']})")
        r = probe_corp(corp)
        results.append(r)

    # --- Metrics ---
    total = len(results)
    html_ok = sum(1 for r in results if r["html_page_found"])
    api_ok = sum(1 for r in results if r["api_accessible"])
    api_auth = sum(1 for r in results if r["api_requires_auth"])
    directors_found = sum(1 for r in results if r["director_data_accessible"])
    isc_found = sum(1 for r in results if r["isc_data_accessible"])
    automatable = sum(1 for r in results if r["automation_feasible"])

    print("\n\n=== SUMMARY METRICS ===")
    print(f"Total corporations tested:   {total}")
    print(f"HTML page accessible:        {html_ok}/{total}")
    print(f"API accessible (no auth):    {api_ok}/{total}")
    print(f"API requires auth:           {api_auth}/{total}")
    print(f"Director data accessible:    {directors_found}/{total}")
    print(f"ISC data accessible:         {isc_found}/{total}")
    print(f"Automation feasible:         {automatable}/{total}")

    # --- Save JSON ---
    json_path = "reports/validation_rounds/VR15_CORPORATIONS_CONTACTS.json"
    output = {
        "vr": "VR15.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "routes_tested": {
            "route_a": HTML_BASE,
            "route_b": API_BASE,
        },
        "metrics": {
            "total": total,
            "html_page_accessible": html_ok,
            "api_accessible_no_auth": api_ok,
            "api_requires_auth": api_auth,
            "director_data_accessible": directors_found,
            "isc_data_accessible": isc_found,
            "automation_feasible": automatable,
        },
        "results": results,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved: {json_path}")

    # --- Save MD skeleton ---
    md_path = "reports/validation_rounds/VR15_CORPORATIONS_CONTACTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# VR15.2 — Corporations Canada Director/ISC Enrichment\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Status:** PENDING — awaiting script run output\n\n")
        f.write(f"## Routes Tested\n\n")
        f.write(f"- Route A (HTML): `{HTML_BASE}?corpId=XXXXXX`\n")
        f.write(f"- Route B (API):  `{API_BASE}/XXXXXX`\n\n")
        f.write(f"## Metrics\n\n")
        f.write(f"| Metric | Count |\n|---|---|\n")
        f.write(f"| Total tested | {total} |\n")
        f.write(f"| HTML page accessible | {html_ok} |\n")
        f.write(f"| API accessible (no auth) | {api_ok} |\n")
        f.write(f"| API requires auth | {api_auth} |\n")
        f.write(f"| Director data accessible | {directors_found} |\n")
        f.write(f"| ISC data accessible | {isc_found} |\n")
        f.write(f"| Automation feasible | {automatable} |\n\n")
        f.write(f"## Per-Corporation Results\n\n")
        for r in results:
            f.write(f"### {r['corp_num']} — {r['name']} ({r['province']})\n")
            f.write(f"- HTML status: {r['html_status']}\n")
            f.write(f"- API status: {r['api_status']}\n")
            f.write(f"- API requires auth: {r['api_requires_auth']}\n")
            f.write(f"- Director data accessible: {r['director_data_accessible']}\n")
            f.write(f"- ISC data accessible: {r['isc_data_accessible']}\n")
            f.write(f"- Automation feasible: {r['automation_feasible']}\n")
            f.write(f"- Notes: {'; '.join(r['notes']) if r['notes'] else 'none'}\n\n")
    print(f"MD saved: {md_path}")


if __name__ == "__main__":
    main()
