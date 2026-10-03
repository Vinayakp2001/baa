from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.ingestion.adapters.edmonton import EdmontonAdapter
from src.ingestion.contracts import RawArtifact
from src.normalisation.schemas import NormalisedRecord
from src.resolution.matchers.exact_identifier import match_exact_identifier


CSV_SAMPLE = """externalid,business_name,business_address,business_licence_category
L-1,Acme,1 Main Street,Food
L-1,Acme,1 Main Street,Food
L-1,Acme,1 Main Street,Retail
"""


class IdentifierResult:
    def __init__(self, entity_id: uuid.UUID) -> None:
        self.entity_id = entity_id

    def scalar_one_or_none(self):
        return SimpleNamespace(entity_id=self.entity_id)


class IdentifierSession:
    def __init__(self, entity_id: uuid.UUID) -> None:
        self.entity_id = entity_id
        self.query_parameters: list[dict] = []

    async def execute(self, statement):
        self.query_parameters.append(statement.compile().params)
        return IdentifierResult(self.entity_id)


def test_repeated_external_ids_keep_unique_deterministic_row_ids() -> None:
    artifact = RawArtifact(
        source_key="edmonton",
        ingestion_run_id=uuid.uuid4(),
        retrieval_url="https://example.test/edmonton.csv",
        retrieval_timestamp=datetime.now(timezone.utc),
        checksum_sha256="sample-checksum",
        payload_ref=CSV_SAMPLE,
    )
    adapter = EdmontonAdapter()

    records = adapter.parse(artifact)
    repeated_parse = adapter.parse(artifact)

    assert len(records) == 3
    assert len({record.source_record_id for record in records}) == 3
    assert [record.source_record_id for record in records] == [
        record.source_record_id for record in repeated_parse
    ]
    assert all(record.raw_payload["externalid"] == "L-1" for record in records)
    assert all(record.source_record_id.startswith("L-1:") for record in records)


@pytest.mark.asyncio
async def test_edmonton_exact_match_uses_externalid_as_licence_id() -> None:
    source_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    record = NormalisedRecord(
        source_key="edmonton",
        ingestion_run_id=uuid.uuid4(),
        source_record_id="L-1:row-hash:1",
        extra={"externalid": "L-1"},
    )
    db = IdentifierSession(entity_id)

    result = await match_exact_identifier(record, source_id, db)

    assert result.matched
    assert result.entity_id == entity_id
    assert result.match_method == "exact_licence_id_same_source"
    assert any("L-1" in parameters.values() for parameters in db.query_parameters)
