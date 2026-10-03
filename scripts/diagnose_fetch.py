"""Diagnose why /ingestion/fetch returns 0 records for calgary.

1. Checks the source registry row for calgary
2. Calls the API and captures the full error response
3. Queries ingestion_run directly via psql to see what happened
"""
import json
import os
import subprocess
import sys

try:
    import requests
except ImportError:
    print("pip install requests first")
    sys.exit(1)

BASE = "http://localhost/api"
SOURCE_KEY = "calgary"

s = requests.Session()
s.headers["Content-Type"] = "application/json"

# --- 1. Check source registry ---
print("=== GET /sources (looking for calgary) ===")
r = s.get(f"{BASE}/sources")
if r.ok:
    sources = r.json() if isinstance(r.json(), list) else r.json().get("results", [])
    for src in sources:
        if src.get("source_key") == SOURCE_KEY:
            print(json.dumps(src, indent=2))
            break
    else:
        print("calgary NOT found in source registry")
else:
    print(f"GET /sources failed: {r.status_code} {r.text[:300]}")

# --- 2. Start a fresh run ---
print("\n=== POST /ingestion/start ===")
r = s.post(f"{BASE}/ingestion/start", json={"source_key": SOURCE_KEY, "source_url": None, "retrieval_timestamp": None})
print(f"  status: {r.status_code}")
print(f"  body:   {r.text[:500]}")
if not r.ok:
    sys.exit(1)
run_id = r.json()["run_id"]
print(f"  run_id: {run_id}")

# --- 3. Attempt fetch — capture full response ---
print("\n=== POST /ingestion/fetch (full response) ===")
r = s.post(f"{BASE}/ingestion/fetch", json={"run_id": run_id, "source_key": SOURCE_KEY, "limit": 10})
print(f"  status: {r.status_code}")
print(f"  body:   {r.text[:2000]}")

# --- 4. Check API logs for errors ---
print("\n=== API container logs (last 40 lines) ===")
result = subprocess.run(
    ["docker", "compose", "logs", "--no-log-prefix", "--tail=40", "api"],
    capture_output=True, text=True
)
print(result.stdout[-3000:] if result.stdout else "(no stdout)")
if result.stderr:
    print("STDERR:", result.stderr[-500:])
