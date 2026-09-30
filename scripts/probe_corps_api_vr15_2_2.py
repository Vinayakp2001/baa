"""
VR15.2.2 — Corporations Canada Federal Corporation API (authenticated)
-----------------------------------------------------------------------
Purpose: Validate the ISED Federal Corporation API Public Plan using an API key.
         Test corporation lookup, directors, ISC, names/history endpoints.
         Record exact JSON response schemas, rate-limit behaviour, error patterns.

Auth: X-API-Key request header (confirmed from ISED help documentation).
      Do NOT use user_key query parameter — header is the correct production mechanism.

Hostname: api.ised-isde.canada.ca  (resolves correctly — confirmed via nslookup)
          NOT api.canada.ca         (that host does not resolve from this machine)

Rate limit: 60 requests/minute (Public Plan). Script throttles to 1.2 req/sec (safe margin).

Mode:
  SINGLE_TEST = True   → 1 corp × 1 endpoint only (connectivity/auth check)
  SINGLE_TEST = False  → full 5 corps × 4 endpoints

Corp numbers: sourced from the authoritative CBCA active CSV (VR01).

Usage:
  python scripts/probe_corps_api_vr15_2_2.py

Output:
  reports/validation_rounds/VR15_2_2_CORPS_API.json
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("ISED_API_KEY", "490fff09becefbe9245841cb84073be8")

# Corrected hostname — api.ised-isde.canada.ca resolves (nslookup confirmed 205.194.37.193)
# api.canada.ca does NOT resolve from this environment
BASE_URL = "https://api.ised-isde.canada.ca/federal-corporations"

# Set True for single connectivity/auth test (1 corp, 1 endpoint).
# Set False for full probe once single test confirms reachability.
SINGLE_TEST = True

CORP_NUMBERS = [
    "8660115",   # MINDANGLER CAPITAL INC. (ON)
    "821080",    # AIRMEC CLIMATISATION LTEE (QC)
    "4396626",   # AIR CANADA (QC)
    "158072",    # CANADIAN TIRE CORPORATION LIMITED (ON)
    "271517",    # ROGERS COMMUNICATIONS INC. (ON)
]

THROTTLE_SECONDS = 1.2  # slightly under 60/min to stay clear of the rate-limit boundary

ENDPOINTS_TO_TEST = [
    ("corporation_lookup",  "/api/v1/corporations/{corp_num}"),
    ("directors",           "/api/v1/corporations/{corp_num}/directors"),
    ("isc",                 "/api/v1/corporations/{corp_num}/isc"),
    ("names_history",       "/api/v1/corporations/{corp_num}/names"),
]

OUTPUT_FILE = "reports/validation_rounds/VR15_2_2_CORPS_API.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(url: str, api_key: str) -> dict:
    """
    GET request authenticated via X-API-Key header (ISED documented mechanism).
    Returns status, content_type, body bytes, 2000-char sample, top-level JSON keys, error.
    """
    headers = {
        "User-Agent": "Canada-Biz-Pipeline-Research/1.0 (VR15.2.2; non-commercial validation)",
        "Accept":     "application/json",
        "X-API-Key":  api_key,
    }

    result = {
        "url":          url,
        "status":       None,
        "content_type": None,
        "body_bytes":   None,
        "body_sample":  None,
        "json_keys":    None,
        "error":        None,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result["status"] = resp.status
            result["content_type"] = resp.headers.get("Content-Type", "")
            raw = resp.read()
            result["body_bytes"] = len(raw)
            text = raw.decode("utf-8", errors="replace")
            result["body_sample"] = text[:2000]
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    result["json_keys"] = list(parsed.keys())
                elif isinstance(parsed, list) and parsed:
                    result["json_keys"] = ["[array]", f"length={len(parsed)}"]
                    if isinstance(parsed[0], dict):
                        result["json_keys"].append(f"item_keys={list(parsed[0].keys())}")
            except (json.JSONDecodeError, ValueError):
                pass
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTPError {e.code}: {e.reason}"
        try:
            result["body_sample"] = e.read().decode("utf-8", errors="replace")[:1000]
        except Exception:
            pass
    except Exception as e:
        result["error"] = str(e)

    return result


# ---------------------------------------------------------------------------
# Main probe
# ---------------------------------------------------------------------------

def run_probe():
    if not API_KEY:
        print("ERROR: API key not set.")
        return

    corps = CORP_NUMBERS[:1] if SINGLE_TEST else CORP_NUMBERS
    endpoints = ENDPOINTS_TO_TEST[:1] if SINGLE_TEST else ENDPOINTS_TO_TEST
    mode_label = "SINGLE TEST (1 corp × 1 endpoint)" if SINGLE_TEST else f"FULL PROBE ({len(corps)} corps × {len(endpoints)} endpoints)"

    print("VR15.2.2 — Corporations Canada API probe")
    print(f"Mode: {mode_label}")
    print(f"Auth: X-API-Key header (len={len(API_KEY)})")
    print(f"Base URL: {BASE_URL}")
    print(f"Total requests: {len(corps) * len(endpoints)}")
    print()

    results = []
    request_count = 0

    for corp_num in corps:
        print(f"  Corp {corp_num}")
        corp_result = {"corp_num": corp_num, "endpoints": []}

        for label, path_template in endpoints:
            path = path_template.format(corp_num=corp_num)
            url = BASE_URL.rstrip("/") + path
            print(f"    [{label}] GET {url}")

            if request_count > 0:
                time.sleep(THROTTLE_SECONDS)

            r = make_request(url, API_KEY)
            request_count += 1

            status_str = str(r["status"]) if r["status"] else "ERR"
            bytes_str  = f"{r['body_bytes']}B" if r["body_bytes"] is not None else "—"
            keys_str   = str(r["json_keys"]) if r["json_keys"] else "—"
            err_str    = f" ⚠ {r['error']}" if r["error"] else ""
            print(f"      → {status_str}  {bytes_str}  keys={keys_str}{err_str}")
            if r.get("body_sample"):
                print(f"      body: {r['body_sample'][:300]}")

            corp_result["endpoints"].append({"endpoint": label, **r})

        results.append(corp_result)
        print()

    statuses = {}
    for c in results:
        for ep in c["endpoints"]:
            s = str(ep["status"]) if ep["status"] else "ERR"
            statuses[s] = statuses.get(s, 0) + 1

    print("Summary:")
    for s, count in sorted(statuses.items()):
        print(f"  HTTP {s}: {count}")

    if SINGLE_TEST:
        print()
        print("If HTTP 200 above: set SINGLE_TEST = False and re-run for full probe.")
        print("If HTTP 401/403: API key or header format needs correction.")
        print("If ERR/DNS: hostname still wrong — check nslookup output.")

    output = {
        "vr":              "VR15.2.2",
        "mode":            mode_label,
        "generated":       datetime.now(timezone.utc).isoformat(),
        "base_url":        BASE_URL,
        "auth_mechanism":  "X-API-Key header",
        "status_summary":  statuses,
        "results":         results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nOutput written: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_probe()
