"""Patch n8n workflow nodes directly in the PostgreSQL database.

Bypasses n8n REST API auth entirely. Reads each local JSON file and
updates the nodes/connections/settings columns in n8n.workflow_entity.

Usage:
    python scripts/patch_workflows_db.py
"""

import json
import os
import subprocess

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


def build_sql(name: str, wf_id: str) -> str | None:
    json_path = os.path.join(WORKFLOW_DIR, f"{name}.json")
    if not os.path.exists(json_path):
        print(f"  SKIP  {name} — file not found")
        return None

    with open(json_path, encoding="utf-8") as f:
        payload = json.load(f)

    nodes = json.dumps(payload.get("nodes", []))
    connections = json.dumps(payload.get("connections", {}))
    settings = json.dumps(payload.get("settings", {}))

    # Escape single quotes for PostgreSQL by doubling them
    def esc(s: str) -> str:
        return s.replace("'", "''")

    return (
        f"UPDATE n8n.workflow_entity "
        f"SET nodes = '{esc(nodes)}'::jsonb, "
        f"    connections = '{esc(connections)}'::jsonb, "
        f"    settings = '{esc(settings)}'::jsonb "
        f"WHERE id = '{wf_id}';"
    )


def main() -> None:
    sqls = []
    for name, wf_id in ID_MAP.items():
        sql = build_sql(name, wf_id)
        if sql:
            sqls.append((name, wf_id, sql))

    print(f"Patching {len(sqls)} workflows via psql...\n")

    for name, wf_id, sql in sqls:
        # Write SQL to a temp file inside the container
        cmd = [
            "docker", "compose", "exec", "-T", "postgres",
            "psql", "-U", "baa", "-d", "baa", "-c", sql
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if "UPDATE 1" in result.stdout:
            # Count nodes from the JSON for confirmation
            json_path = os.path.join(WORKFLOW_DIR, f"{name}.json")
            with open(json_path, encoding="utf-8") as f:
                node_count = len(json.load(f).get("nodes", []))
            print(f"  OK    {name} ({wf_id}) — {node_count} nodes")
        else:
            print(f"  FAIL  {name} ({wf_id})")
            if result.stderr:
                print(f"        {result.stderr[:200]}")

    print("\nDone. Restart n8n to reload from DB:")
    print("  docker compose restart n8n")


if __name__ == "__main__":
    main()
