"""
VR05 follow-up — extract unique values from Table B dimension columns
that were missed in the main profiling pass:
  - Business dynamics measure  (opening/closure category)
  - REF_DATE unique values     (resolve 2026-01 vs June 2026 question)
  - STATUS unique values       (confirm suppression codes)
  - GEO at national/provincial level only

Reads the already-downloaded data/raw/statcan_33100722.zip.
Prints results to terminal — no new report file needed.
"""
from __future__ import annotations

import csv
import io
import zipfile
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZIP_FILE = PROJECT_ROOT / "data" / "raw" / "statcan_33100722.zip"
DATA_FILE = "33100722.csv"

PROVINCIAL_GEOS = {
    "Canada", "Alberta", "British Columbia", "Manitoba",
    "New Brunswick", "Newfoundland and Labrador", "Northwest Territories",
    "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island",
    "Quebec", "Saskatchewan", "Yukon",
}


def main() -> None:
    print("=" * 70)
    print("VR05 Table B — Dimension probe")
    print(f"Source: {ZIP_FILE.name}")
    print("=" * 70)

    if not ZIP_FILE.exists():
        print(f"ERROR: {ZIP_FILE} not found. Run profile_statscan_business_counts.py first.")
        return

    dynamics_counter: Counter = Counter()
    ref_date_counter: Counter = Counter()
    status_counter: Counter = Counter()
    geo_provincial: Counter = Counter()

    print("\nStreaming rows (8.5M — may take ~30s)...")

    with zipfile.ZipFile(ZIP_FILE) as zf:
        with zf.open(DATA_FILE) as f:
            text = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")
            reader = csv.DictReader(text)
            for i, row in enumerate(reader):
                dynamics_counter[row.get("Business dynamics measure", "")] += 1
                ref_date_counter[row.get("REF_DATE", "")] += 1
                status_counter[row.get("STATUS", "")] += 1

                # Collect provincial/national geo counts (strip trailing whitespace)
                geo = row.get("GEO", "").strip()
                if geo in PROVINCIAL_GEOS:
                    geo_provincial[geo] += 1

                if i % 500_000 == 0 and i > 0:
                    print(f"  ...{i:,} rows processed")

    print("\n" + "=" * 70)
    print("Business dynamics measure — unique values")
    print("=" * 70)
    for val, count in sorted(dynamics_counter.items(), key=lambda x: -x[1]):
        print(f"  {count:>10,}  {val!r}")

    print("\n" + "=" * 70)
    print("REF_DATE — unique values (first 20 and last 5)")
    print("=" * 70)
    all_dates = sorted(ref_date_counter.keys())
    for d in all_dates[:20]:
        print(f"  {d}  ({ref_date_counter[d]:,} rows)")
    if len(all_dates) > 25:
        print("  ...")
    for d in all_dates[-5:]:
        print(f"  {d}  ({ref_date_counter[d]:,} rows)")
    print(f"  Total unique periods: {len(all_dates)}")

    print("\n" + "=" * 70)
    print("STATUS — suppression codes")
    print("=" * 70)
    total = sum(status_counter.values())
    for val, count in sorted(status_counter.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {count:>10,}  ({pct:5.1f}%)  {val!r}")

    print("\n" + "=" * 70)
    print("Provincial/national rows — row counts by GEO")
    print("=" * 70)
    for geo, count in sorted(geo_provincial.items(), key=lambda x: -x[1]):
        print(f"  {count:>8,}  {geo}")

    print("\nDone.")


if __name__ == "__main__":
    main()
