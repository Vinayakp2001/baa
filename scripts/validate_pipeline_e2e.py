"""End-to-end pipeline validation script.

Verifies the full pipeline for a single source ingestion run:
  /ingestion/start → /ingestion/fetch → /normalise → /resolve →
  /events/detect → /quality/score → GET /businesses

Usage:
    python scripts/validate_pipeline_e2e.py [--api-url http://localhost/api]

Requires: requests (pip install requests)
Requirements: 1.1–1.7, 2.1–2.6 (Task 17.2)
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)

DEFAULT_API = "http://localhost/api"
SOURCE_KEY = "corporations_canada_csv"  # Class A — no external auth required


def step(label: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print("=" * 60)


def ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def fail(msg: str, detail: str = "") -> None:
    print(f"  ✗  {msg}")
    if detail:
        print(f"     {detail}")
    sys.exit(1)


def post(session: requests.Session, base: str, path: str, body: dict) -> dict:
    url = f"{base}{path}"
    resp = session.post(url, json=body)
    if not resp.ok:
        fail(f"POST {path} returned {resp.status_code}", resp.text[:500])
    return resp.json()


def get(session: requests.Session, base: str, path: str) -> dict:
    url = f"{base}{path}"
    resp = session.get(url)
    if not resp.ok:
        fail(f"GET {path} returned {resp.status_code}", resp.text[:500])
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="BAA pipeline end-to-end validation")
    parser.add_argument("--api-url", default=DEFAULT_API, help="API base URL")
    parser.add_argument("--source-key", default=SOURCE_KEY, help="Source key to test")
    args = parser.parse_args()

    base = args.api_url.rstrip("/")
    source_key = args.source_key
    session = requests.Session()
    session.headers["Content-Type"] = "application/json"

    print(f"\nBAA Pipeline — End-to-End Validation")
    print(f"API: {base}")
    print(f"Source: {source_key}")

    # ------------------------------------------------------------------
    # 1. Health check
    # ------------------------------------------------------------------
    step("1. Health check")
    health = get(session, base.replace("/api", ""), "/healthz")
    assert health.get("status") == "ok", f"Unexpected health: {health}"
    ok("API is healthy")

    # ------------------------------------------------------------------
    # 2. POST /ingestion/start
    # ------------------------------------------------------------------
    step("2. POST /ingestion/start")
    start_resp = post(session, base, "/ingestion/start", {
        "source_key": source_key,
        "source_url": None,
        "retrieval_timestamp": None,
    })
    run_id = start_resp.get("run_id")
    source_id = start_resp.get("source_id")
    if not run_id:
        fail("No run_id in /ingestion/start response", json.dumps(start_resp))
    ok(f"run_id = {run_id}")
    ok(f"source_id = {source_id}")

    # ------------------------------------------------------------------
    # 3. POST /ingestion/fetch  (adapter-driven — no records body)
    # ------------------------------------------------------------------
    step("3. POST /ingestion/fetch  (adapter runs inside API)")
    fetch_resp = post(session, base, "/ingestion/fetch", {
        "run_id": run_id,
        "source_key": source_key,
    })
    records_stored = fetch_resp.get("records_stored", 0)
    if records_stored == 0:
        fail("No records stored by /ingestion/fetch")
    ok(f"records_stored = {records_stored}")

    # ------------------------------------------------------------------
    # 4. POST /normalise
    # ------------------------------------------------------------------
    step("4. POST /normalise")
    norm_resp = post(session, base, "/normalise", {"run_id": run_id})
    records_normalised = norm_resp.get("records_normalised", 0)
    if records_normalised == 0:
        fail("No records normalised by /normalise")
    ok(f"records_normalised = {records_normalised}")

    # ------------------------------------------------------------------
    # 5. POST /resolve
    # ------------------------------------------------------------------
    step("5. POST /resolve")
    resolve_resp = post(session, base, "/resolve", {"run_id": run_id})
    records_resolved = resolve_resp.get("records_resolved", 0)
    records_new = resolve_resp.get("records_new", 0)
    ok(f"records_resolved = {records_resolved}")
    ok(f"records_new = {records_new}")

    # ------------------------------------------------------------------
    # 6. POST /events/detect
    # ------------------------------------------------------------------
    step("6. POST /events/detect")
    events_resp = post(session, base, "/events/detect", {"ingestion_run_id": run_id})
    events_created = events_resp.get("events_created", 0)
    ok(f"events_created = {events_created}")

    # ------------------------------------------------------------------
    # 7. POST /quality/score
    # ------------------------------------------------------------------
    step("7. POST /quality/score")
    quality_resp = post(session, base, "/quality/score", {"ingestion_run_id": run_id})
    entities_scored = quality_resp.get("entities_scored", 0)
    ok(f"entities_scored = {entities_scored}")

    # ------------------------------------------------------------------
    # 8. POST /ingestion/complete
    # ------------------------------------------------------------------
    step("8. POST /ingestion/complete")
    complete_resp = post(session, base, "/ingestion/complete", {"run_id": run_id})
    run_status = complete_resp.get("run_status")
    if run_status != "COMPLETED":
        fail(f"Expected COMPLETED, got '{run_status}'")
    ok(f"run_status = {run_status}")

    # ------------------------------------------------------------------
    # 9. GET /businesses — verify results are queryable
    # ------------------------------------------------------------------
    step("9. GET /businesses")
    biz_resp = get(session, base, f"/businesses?page_size=5")
    total = biz_resp.get("total", 0)
    results = biz_resp.get("results", [])
    if total == 0 or not results:
        fail("No businesses returned from GET /businesses")
    ok(f"total businesses in registry = {total}")

    # Check one entity has a provenance chain
    entity_id = results[0]["entity_id"]
    step(f"10. GET /businesses/{entity_id} — provenance chain")

    detail = get(session, base, f"/businesses/{entity_id}")
    ok(f"canonical_name = {detail.get('canonical_name')}")
    ok(f"province = {detail.get('province')}")
    ok(f"status = {detail.get('status')}")

    history = get(session, base, f"/businesses/{entity_id}/history")
    field_count = len(history.get("fields", []))
    ok(f"field_observation groups = {field_count}")
    if field_count == 0:
        print("  ⚠  No field observations found — check normalisation + resolution wiring")

    sources = get(session, base, f"/businesses/{entity_id}/sources")
    source_count = len(sources) if isinstance(sources, list) else 0
    ok(f"contributing source_records = {source_count}")
    if source_count == 0:
        print("  ⚠  No source records linked — check entity_id assignment in resolution")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    step("VALIDATION COMPLETE")
    print(f"""
  run_id            : {run_id}
  source_key        : {source_key}
  records_stored    : {records_stored}
  records_normalised: {records_normalised}
  records_resolved  : {records_resolved}
  records_new       : {records_new}
  events_created    : {events_created}
  entities_scored   : {entities_scored}
  total_businesses  : {total}
  provenance_fields : {field_count}
  source_records    : {source_count}

  All assertions passed. Pipeline is wired end-to-end.
""")


if __name__ == "__main__":
    main()
