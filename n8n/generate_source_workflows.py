"""Generate per-source n8n workflow JSON files.

Each source workflow is a thin wrapper that:
  1. Fires on its own cron schedule
  2. Passes the source_key into the generic ingest-source sub-workflow
     (via executeWorkflow node referencing ingest-source by name)

Run: python n8n/generate_source_workflows.py

Req 10.1 — each source has its own schedule_expression.
"""

import json
import os

# (source_key, cron_expression, display_name)
SOURCES = [
    # Class A — daily
    ("calgary", "0 6 * * *", "Calgary Business Licences"),
    ("edmonton", "0 6 * * *", "Edmonton Business Licences"),
    ("vancouver", "0 5 * * *", "Vancouver Business Licences"),
    ("winnipeg", "0 7 * * *", "Winnipeg Business Licences"),
    # Class A — weekly
    ("corporations_canada_csv", "0 4 * * 1", "Corporations Canada CSV"),
    ("manitoba_weekly_pdf", "0 9 * * 5", "Manitoba Weekly PDF"),
    ("saskatoon_all_biz", "0 8 * * 1", "Saskatoon All Businesses"),
    ("saskatoon_new_biz", "0 8 * * 1", "Saskatoon New Businesses"),
    ("quebec_city_permits", "0 9 * * 5", "Québec City Permits"),
    # Class A/B — monthly
    ("corporations_canada_html", "0 8 1 * *", "Corporations Canada Monthly HTML"),
    ("ontario_select_licence", "0 8 1 * *", "Ontario Select Licence"),
    ("ontario_dairy", "0 8 1 * *", "Ontario Dairy Processors"),
    ("ontario_meat", "0 8 1 * *", "Ontario Meat Processors"),
    ("ontario_tobacco", "0 8 1 * *", "Ontario Tobacco Dealers"),
    ("ontario_fuel", "0 8 1 * *", "Ontario Fuel Dealers"),
    ("ontario_csbif", "0 8 1 * *", "Ontario CSBIF"),
    ("ontario_dairy_plants", "0 8 1 * *", "Ontario Dairy Plants"),
    ("bc_indigenous", "0 8 1 * *", "BC Indigenous Business Listings"),
    # Class A — annually
    ("montreal_commercial", "0 8 1 1 *", "Montréal Commercial Premises"),
]


def make_per_source_workflow(source_key: str, cron: str, display_name: str) -> dict:
    """Build a minimal per-source workflow that triggers on cron and calls the generic ingest-source workflow."""
    return {
        "name": f"ingest-{source_key.replace('_', '-')}",
        "nodes": [
            {
                "parameters": {
                    "rule": {
                        "interval": [
                            {
                                "field": "cronExpression",
                                "expression": cron,
                            }
                        ]
                    }
                },
                "id": f"cron-{source_key}",
                "name": "Cron Trigger",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.1,
                "position": [240, 300],
            },
            {
                "parameters": {
                    "jsCode": f"return [{{ json: {{ source_key: '{source_key}' }} }}];",
                },
                "id": f"set-source-key-{source_key}",
                "name": "Set source_key",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [460, 300],
            },
            {
                "parameters": {
                    "workflowId": {
                        "__rl": True,
                        "value": "ingest-source",
                        "mode": "name",
                    },
                    "workflowInputs": {
                        "mappingMode": "defineBelow",
                        "value": {
                            "source_key": "={{ $json.source_key }}",
                        },
                    },
                    "options": {
                        "waitForSubWorkflow": True,
                    },
                },
                "id": f"call-ingest-source-{source_key}",
                "name": "Call ingest-source",
                "type": "n8n-nodes-base.executeWorkflow",
                "typeVersion": 1.1,
                "position": [680, 300],
            },
        ],
        "connections": {
            "Cron Trigger": {
                "main": [
                    [{"node": "Set source_key", "type": "main", "index": 0}]
                ]
            },
            "Set source_key": {
                "main": [
                    [{"node": "Call ingest-source", "type": "main", "index": 0}]
                ]
            },
        },
        "settings": {
            "executionOrder": "v1",
            "saveManualExecutions": True,
            "errorWorkflow": "ingest-source-error-handler",
            "saveDataErrorExecution": "all",
            "saveDataSuccessExecution": "all",
        },
        "staticData": None,
        "meta": {"templateCredsSetupCompleted": True},
        "pinData": {},
        "versionId": "1",
        "triggerCount": 0,
        "tags": [
            {
                "createdAt": "2026-09-28T00:00:00.000Z",
                "updatedAt": "2026-09-28T00:00:00.000Z",
                "id": "ingestion",
                "name": "ingestion",
            }
        ],
    }


def main() -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "workflows")
    os.makedirs(out_dir, exist_ok=True)

    for source_key, cron, display_name in SOURCES:
        workflow = make_per_source_workflow(source_key, cron, display_name)
        filename = f"ingest-{source_key.replace('_', '-')}.json"
        filepath = os.path.join(out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(workflow, fh, indent=2, ensure_ascii=False)
        print(f"  wrote {filename}  [{cron}]  ({display_name})")

    print(f"\nGenerated {len(SOURCES)} per-source workflow files in {out_dir}")


if __name__ == "__main__":
    main()
