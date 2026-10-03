"""Resume a stalled ingestion run from a specific stage.

Usage:
    python scripts/resume_run.py --run-id <uuid> --source-key <key> [--from-stage resolve|events|quality|complete]

Runs the selected stage and subsequent processing stages:
    resolve → events/detect → quality/score
Call with --from-stage complete separately once processing stages are verified.

Safe to run on a run that already completed resolution — each endpoint is idempotent
(events/detect skips already-detected events, quality/score overwrites scores).
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE = "http://localhost/api"

STAGES = ["normalise", "resolve", "events", "quality", "complete"]


def ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def fail(msg: str, detail: str = "") -> None:
    print(f"  ✗  {msg}")
    if detail:
        print(f"     {detail[:500]}")
    sys.exit(1)


def post(session: requests.Session, path: str, body: dict) -> dict:
    r = session.post(f"{BASE}{path}", json=body)
    if not r.ok:
        fail(f"POST {path} → {r.status_code}", r.text)
    return r.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-key", required=True)
    parser.add_argument(
        "--from-stage",
        choices=STAGES,
        default="events",
        help="Stage to start from (default: events); use 'normalise' to re-normalise stale payloads",
    )
    args = parser.parse_args()

    run_id = args.run_id
    source_key = args.source_key
    start_idx = STAGES.index(args.from_stage)

    session = requests.Session()
    session.headers["Content-Type"] = "application/json"

    print(f"\nResuming run {run_id} (source: {source_key}) from stage: {args.from_stage}\n")

    if start_idx <= STAGES.index("normalise"):
        print("--- POST /normalise (re-normalise from raw_payload) ---")
        resp = post(session, "/normalise", {"run_id": run_id})
        ok(f"records_normalised = {resp.get('records_normalised', 0)}")

    if start_idx <= STAGES.index("resolve"):
        print("--- POST /resolve ---")
        resp = post(session, "/resolve", {"run_id": run_id, "source_key": source_key})
        ok(f"records_resolved = {resp.get('records_resolved', 0)}")
        ok(f"records_new = {resp.get('records_new', 0)}")

    if start_idx <= STAGES.index("events"):
        print("--- POST /events/detect ---")
        resp = post(session, "/events/detect", {"ingestion_run_id": run_id})
        ok(f"events_created = {resp.get('events_created', 0)}")

    if start_idx <= STAGES.index("quality"):
        print("--- POST /quality/score ---")
        resp = post(session, "/quality/score", {"ingestion_run_id": run_id})
        ok(f"entities_scored = {resp.get('entities_scored', 0)}")

    if args.from_stage == "complete":
        print("--- POST /ingestion/complete ---")
        resp = post(session, "/ingestion/complete", {
            "run_id": run_id,
        })
        status = resp.get("run_status")
        ok(f"run_status = {status}")
        if status != "COMPLETED":
            fail(f"Expected COMPLETED, got {status}")

    if args.from_stage == "complete":
        print(f"\nDone. Run {run_id} is now COMPLETED.\n")
    else:
        print(f"\nDone. Processing stages finished for run {run_id}; completion was not requested.\n")


if __name__ == "__main__":
    main()
