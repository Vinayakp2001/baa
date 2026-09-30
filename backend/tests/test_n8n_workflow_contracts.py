import json
from pathlib import Path

from n8n.generate_source_workflows import SOURCES


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = WORKSPACE_ROOT / "n8n" / "workflows"


def test_per_source_workflows_match_generator_schedules() -> None:
    assert len(SOURCES) == 19

    for source_key, cron, _display_name in SOURCES:
        filename = f"ingest-{source_key.replace('_', '-')}.json"
        workflow = json.loads((WORKFLOW_DIR / filename).read_text(encoding="utf-8"))
        nodes = {node["name"]: node for node in workflow["nodes"]}

        cron_node = nodes["Cron Trigger"]
        assert cron_node["parameters"]["rule"]["interval"][0]["expression"] == cron

        source_node = nodes["Set source_key"]
        assert f"source_key: '{source_key}'" in source_node["parameters"]["jsCode"]

        execute_node = nodes["Call ingest-source"]
        assert execute_node["parameters"]["workflowId"]["value"] == "ingest-source"


def test_generic_workflow_sends_required_api_fields() -> None:
    workflow = json.loads(
        (WORKFLOW_DIR / "ingest-source.json").read_text(encoding="utf-8")
    )
    nodes = {node["name"]: node for node in workflow["nodes"]}

    required_fields = {
        "POST /ingestion/start": {"source_key"},
        "POST /ingestion/fetch": {"run_id", "source_key"},
        "POST /normalise": {"run_id"},
        "POST /resolve": {"run_id"},
        "POST /events/detect": {"ingestion_run_id"},
        "POST /quality/score": {"ingestion_run_id"},
        "POST /ingestion/complete": {"run_id"},
        "POST /ingestion/fail": {"run_id", "error_message"},
    }

    for node_name, required in required_fields.items():
        supplied = {
            parameter["name"]
            for parameter in nodes[node_name]["parameters"]["bodyParameters"]["parameters"]
        }
        assert required <= supplied, f"{node_name} missing {required - supplied}"