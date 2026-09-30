"""
VR14.1 — ODBus Source Catalogue Extraction
Extract ODBus_Sources.csv from ZIP, build source inventory, group by provider/province.
Output: reports/validation_rounds/VR14_1_ODBUS_SOURCE_INVENTORY.json
"""

import zipfile
import csv
import json
import io
from collections import defaultdict

ZIP_PATH = "data/raw/ODBus_2023.zip"
SOURCES_FILE = "ODBus_v1/ODBus_Sources.csv"
OUTPUT_JSON = "reports/validation_rounds/VR14_1_ODBUS_SOURCE_INVENTORY.json"

def main():
    # --- Extract and parse ODBus_Sources.csv ---
    with zipfile.ZipFile(ZIP_PATH) as z:
        with z.open(SOURCES_FILE) as f:
            raw = f.read().decode("cp1252")

    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)

    print(f"Total source rows: {len(rows)}")
    print(f"Columns: {reader.fieldnames}")
    print()

    # --- Print all rows raw first so we know exact field names ---
    print("=== RAW SOURCE ROWS (first 5) ===")
    for row in rows[:5]:
        for k, v in row.items():
            print(f"  {k!r}: {v!r}")
        print()

    # --- Build inventory with normalized keys ---
    inventory = []
    for row in rows:
        # Use .get with fallback to handle any column name variations
        entry = {k.strip(): v.strip() for k, v in row.items()}
        inventory.append(entry)

    # --- Group by province ---
    by_province = defaultdict(list)
    by_provider = defaultdict(list)

    # Detect province/provider column names dynamically
    cols = list(inventory[0].keys()) if inventory else []
    print(f"All columns: {cols}")
    print()

    # Try common column name patterns
    province_col = next((c for c in cols if "province" in c.lower() or "prov" in c.lower()), None)
    provider_col = next((c for c in cols if "provider" in c.lower() or "source" in c.lower() or "owner" in c.lower()), None)
    url_col = next((c for c in cols if "url" in c.lower() or "link" in c.lower()), None)
    name_col = next((c for c in cols if "name" in c.lower() or "title" in c.lower()), None)

    print(f"Detected province col: {province_col!r}")
    print(f"Detected provider col: {provider_col!r}")
    print(f"Detected url col:      {url_col!r}")
    print(f"Detected name col:     {name_col!r}")
    print()

    for entry in inventory:
        prov = entry.get(province_col, "UNKNOWN") if province_col else "UNKNOWN"
        prov = prov.strip() or "UNKNOWN"
        by_province[prov].append(entry)

        provider = entry.get(provider_col, "UNKNOWN") if provider_col else "UNKNOWN"
        provider = provider.strip() or "UNKNOWN"
        by_provider[provider].append(entry)

    # --- Province distribution ---
    print("=== PROVINCE DISTRIBUTION ===")
    for prov, entries in sorted(by_province.items(), key=lambda x: -len(x[1])):
        print(f"  {prov}: {len(entries)} sources")
    print()

    # --- Provider distribution ---
    print("=== PROVIDER DISTRIBUTION ===")
    for provider, entries in sorted(by_provider.items(), key=lambda x: -len(x[1])):
        print(f"  {provider}: {len(entries)} sources")
    print()

    # --- Print all source URLs for endpoint triage ---
    print("=== ALL SOURCE URLS ===")
    for i, entry in enumerate(inventory, 1):
        name = entry.get(name_col, "?") if name_col else "?"
        url = entry.get(url_col, "?") if url_col else "?"
        prov = entry.get(province_col, "?") if province_col else "?"
        print(f"  [{i:02d}] [{prov}] {name}")
        print(f"        {url}")
    print()

    # --- Save full inventory to JSON ---
    output = {
        "total_sources": len(inventory),
        "columns": cols,
        "province_col_detected": province_col,
        "provider_col_detected": provider_col,
        "url_col_detected": url_col,
        "name_col_detected": name_col,
        "province_distribution": {k: len(v) for k, v in sorted(by_province.items(), key=lambda x: -len(x[1]))},
        "provider_distribution": {k: len(v) for k, v in sorted(by_provider.items(), key=lambda x: -len(x[1]))},
        "sources": inventory
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Saved: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
