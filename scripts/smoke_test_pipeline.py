"""Bounded pipeline smoke test — uses a 200-row sample from Calgary (no auth).

Runs the full pipeline end-to-end but with a small, fast, no-auth source:
  /ingestion/start → /ingestion/fetch → /normalise → /resolve →
  /events/detect → /quality/score → /ingestion/complete → GET /businesses

After the test passes, the run and its records remain in the database.
To clean up: DELETE FROM ingestion_run WHERE source_id = (
    SELECT source_id FROM source WHERE source_key = 'calgary'
) AND run_status = 'COMPLETED' ORDER BY run_started_at DESC LIMIT 1;

Usage:
    python scripts/smoke_test_pipeline.py [--api-url http://localhost/api]

Requires: pip install requests
"""

from __future__ import annotations

import argparse
import json
import sys

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

DEFAULT_API = "http://localhost/api"
SOURCE_KEY = "calgary"  # ~23k rows, CC-BY, no auth, daily Socrata endpoint


def step(label: str) -> None:
    print(f"\n{'─' * 55}")
    print(f"  {label}")
    print("─" * 55)


def ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def warn(msg: str) -> None:
    print(f"  ⚠  {msg}")


def fail(msg: str, detail: str = "") -> None:
    print(f"  ✗  {msg}")
    if detail:
        print(f"     {detail[:300]}")
    sys.exit(1)


def post(session: requests.Session, base: str, path: str, body: dict) -> dict:
    resp = session.post(f"{base}{path}", json=body, timeout=900)
    if not resp.ok:
        fail(f"POST {path} → HTTP {resp.status_code}", resp.text)
    return resp.json()


def get(session: requests.Session, base: str, path: str) -> dict | list:
    resp = session.get(f"{base}{path}", timeout=30)
    if not resp.ok:
        fail(f"GET {path} → HTTP {resp.status_code}", resp.text)
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--limit", type=int, default=200, help="Maximum Calgary rows to process (1-1000)")
    args = parser.parse_args()
    base = args.api_url.rstrip("/")

    session = requests.Session()
    session.headers["Content-Type"] = "application/json"

    print(f"\n  BAA Pipeline — Smoke Test  ({SOURCE_KEY})")
    print(f"  API: {base}\n")

    # ── 1. Health ──────────────────────────────────────────────────────
    step("1. Health check")
    resp = session.get(f"{base}/healthz", timeout=10)
    if resp.ok:
        ok("API healthy (via /api/healthz)")
    else:
        # Healthz may not be proxied through nginx — try a lightweight API call instead
        resp2 = session.get(f"{base}/sources", timeout=10)
        if resp2.ok:
            ok("API reachable (GET /sources returned 200)")
        else:
            fail(f"API not reachable — /api/healthz → {resp.status_code}, /api/sources → {resp2.status_code}")

    # ── 2. Start ───────────────────────────────────────────────────────
    step("2. POST /ingestion/start")
    start = post(session, base, "/ingestion/start", {"source_key": SOURCE_KEY})
    run_id = start.get("run_id")
    source_id = start.get("source_id")
    if not run_id:
        fail("No run_id returned", json.dumps(start))
    if not source_id:
        fail("No source_id returned", json.dumps(start))
    ok(f"run_id = {run_id}")

    # ── 3. Fetch (adapter runs inside API) ────────────────────────────
    step(f"3. POST /ingestion/fetch  [fetches up to {args.limit:,} Calgary rows]")
    fetch = post(session, base, "/ingestion/fetch", {
        "run_id": run_id,
        "source_key": SOURCE_KEY,
        "limit": args.limit,
    })
    stored = fetch.get("records_stored", 0)
    if stored == 0:
        fail("/ingestion/fetch stored 0 records")
    ok(f"records_stored = {stored:,}")

    # ── 4. Normalise ───────────────────────────────────────────────────
    step("4. POST /normalise")
    norm = post(session, base, "/normalise", {"run_id": run_id})
    normalised = norm.get("records_normalised", 0)
    ok(f"records_normalised = {normalised:,}")
    if normalised == 0:
        warn("normalised 0 records — check normaliser for this source")

    # ── 5. Resolve ────────────────────────────────────────────────────
    step("5. POST /resolve")
    resolve = post(session, base, "/resolve", {"run_id": run_id})
    ok(f"records_resolved  = {resolve.get('records_resolved', 0):,}")
    ok(f"records_new       = {resolve.get('records_new', 0):,}")
    ok(f"records_merged    = {resolve.get('records_merged', 0):,}")
    ok(f"records_candidate = {resolve.get('records_candidate', 0):,}")
    unresolved = resolve.get("records_unresolved", 0)
    if unresolved > 0:
        warn(f"records_unresolved = {unresolved:,}  (expected for permit-only records)")

    # ── 6. Events ─────────────────────────────────────────────────────
    step("6. POST /events/detect")
    events = post(session, base, "/events/detect", {"ingestion_run_id": run_id})
    ok(f"events_created = {events.get('events_created', 0):,}")

    # ── 7. Quality ────────────────────────────────────────────────────
    step("7. POST /quality/score")
    quality = post(session, base, "/quality/score", {"ingestion_run_id": run_id})
    ok(f"entities_scored = {quality.get('entities_scored', 0):,}")

    # ── 8. Complete ───────────────────────────────────────────────────
    step("8. POST /ingestion/complete")
    complete = post(session, base, "/ingestion/complete", {"run_id": run_id})
    if complete.get("run_status") != "COMPLETED":
        fail(f"Expected COMPLETED, got {complete.get('run_status')}")
    ok(f"run_status = COMPLETED")

    # ── 9. Query ──────────────────────────────────────────────────────
    step("9. GET Calgary-sourced businesses")
    biz = get(session, base, f"/businesses?source_id={source_id}&page_size=5")
    total = biz.get("total", 0)
    results = biz.get("results", [])
    if total == 0:
        fail("No Calgary-sourced businesses returned — check resolution/entity creation")
    ok(f"total Calgary-sourced businesses = {total:,}")

    entity_id = results[0]["entity_id"]
    step(f"10. Provenance chain for {entity_id[:8]}…")
    detail = get(session, base, f"/businesses/{entity_id}")
    ok(f"canonical_name = {detail.get('canonical_name')}")
    ok(f"status         = {detail.get('status')}")

    history = get(session, base, f"/businesses/{entity_id}/history")
    field_groups = len(history.get("fields", []))
    ok(f"field_observation groups = {field_groups}")
    if field_groups == 0:
        warn("no field observations — check normaliser field mapping")

    sources = get(session, base, f"/businesses/{entity_id}/sources")
    ok(f"contributing source_records = {len(sources) if isinstance(sources, list) else '?'}")

    # ── Summary ───────────────────────────────────────────────────────
    step("SMOKE TEST PASSED")
    print(f"""
  source          : {SOURCE_KEY}
  run_id          : {run_id}
  records_stored  : {stored:,}
  records_resolved: {resolve.get('records_resolved', 0):,}
  records_new     : {resolve.get('records_new', 0):,}
  events_created  : {events.get('events_created', 0):,}
  entities_scored : {quality.get('entities_scored', 0):,}
    Calgary businesses: {total:,}
  provenance_fields: {field_groups}

  Pipeline is wired end-to-end. Safe to run full imports via n8n.
""")


if __name__ == "__main__":
    main()
