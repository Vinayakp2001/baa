"""Push all n8n workflow JSONs to the running n8n instance via REST API.

Logs in via n8n's /rest/login endpoint to get a session cookie, then
PUTs each workflow. Avoids PowerShell ConvertTo-Json serialization issues.

Usage:
    python scripts/push_workflows.py
"""

import http.cookiejar
import json
import urllib.request
import urllib.error
import os

BASE = "http://localhost/n8n"
LOGIN_URL = f"{BASE}/rest/login"
BASE_URL = f"{BASE}/rest/workflows"

N8N_USER = os.environ.get("N8N_BASIC_AUTH_USER", "admin")
N8N_PASS = os.environ.get("N8N_BASIC_AUTH_PASSWORD", "")

# Build a cookie-aware opener so the session cookie persists across requests
_CJ = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_CJ))


def login() -> bool:
    payload = json.dumps({"email": N8N_USER, "password": N8N_PASS}).encode()
    req = urllib.request.Request(
        LOGIN_URL,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with _OPENER.open(req) as resp:
            data = json.loads(resp.read())
            print(f"  Login OK — user: {data.get('data', {}).get('email', '?')}")
            return True
    except urllib.error.HTTPError as e:
        print(f"  Login FAIL — HTTP {e.code}: {e.read().decode()[:200]}")
        return False
    except Exception as e:
        print(f"  Login FAIL — {e}")
        return False

ID_MAP = {
    "enrich-directors":               "CC22iIsm3pl6F69i",
    "enrich-orgbook":                 "lxChQKeVXB4HAiSl",
    "ingest-bc-indigenous":           "v33PlhIcD8g5hupW",
    "ingest-calgary":                 "YA6R2QF2F9EF4MeU",
    "ingest-corporations-canada-csv": "rYtXSXgnXvTRa4OS",
    "ingest-corporations-canada-html":"DXOWmFpMxRDpFiRB",
    "ingest-edmonton":                "zjcqTBe3BPPO97WB",
    "ingest-manitoba-weekly-pdf":     "eaIEGG6JJDXQrgQx",
    "ingest-montreal-commercial":     "1gvw4MsRmi9Pqvej",
    "ingest-ontario-csbif":           "tbKZztxSQVA3eZ2J",
    "ingest-ontario-dairy":           "Hh15rIA9YdcSEzXk",
    "ingest-ontario-dairy-plants":    "XJ0UxKeZha5YJLKB",
    "ingest-ontario-fuel":            "OIaifDvBighJMkXz",
    "ingest-ontario-meat":            "tsaxJtRDG1n2QF6T",
    "ingest-ontario-select-licence":  "buQp7bjNzUouhmkb",
    "ingest-ontario-tobacco":         "oIgz4EbtSy9zTmdK",
    "ingest-quebec-city-permits":     "Q3O7Ejlgsela8wih",
    "ingest-saskatoon-all-biz":       "X1dq78rpsizhTQ34",
    "ingest-saskatoon-new-biz":       "c1RiYUjuLYQ5OUtW",
    "ingest-source":                  "M3VpN32lUuH3n5fX",
    "ingest-source-error-handler":    "FI0JgWc225VH9SWj",
    "ingest-vancouver":               "3HhzSzBwMaRwFPoe",
    "ingest-winnipeg":                "TVVt5znyNUy03pdk",
}

WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "..", "n8n", "workflows")


def push_workflow(name: str, wf_id: str) -> None:
    json_path = os.path.join(WORKFLOW_DIR, f"{name}.json")
    if not os.path.exists(json_path):
        print(f"  SKIP  {name} — file not found")
        return

    with open(json_path, encoding="utf-8") as f:
        payload = json.load(f)

    # Ensure the id field matches the target DB row
    payload["id"] = wf_id

    body = json.dumps(payload).encode("utf-8")
    url = f"{BASE_URL}/{wf_id}"

    req = urllib.request.Request(
        url,
        data=body,
        method="PUT",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with _OPENER.open(req) as resp:
            result = json.loads(resp.read())
            node_count = len(result.get("nodes", []))
            print(f"  OK    {name} ({wf_id}) — {node_count} nodes")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")
        print(f"  FAIL  {name} ({wf_id}) — HTTP {e.code}: {body_err[:200]}")
    except Exception as e:
        print(f"  FAIL  {name} ({wf_id}) — {e}")


def main() -> None:
    print(f"Pushing {len(ID_MAP)} workflows to {BASE_URL}\n")
    if not login():
        print("Aborting — login failed.")
        return
    print()
    for name, wf_id in ID_MAP.items():
        push_workflow(name, wf_id)
    print("\nDone.")


if __name__ == "__main__":
    main()
