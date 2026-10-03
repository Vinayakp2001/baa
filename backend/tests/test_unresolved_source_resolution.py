from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from src.events.detectors import detect_new_business_events
from src.models.provenance import SourceRecord
from src.normalisation.schemas import (
    NormalisedAddress,
    NormalisedName,
    NormalisedRecord,
    SourceRecordReference,
)
from src.resolution import routes as resolution_routes
from src.resolution.schemas import (
    MatchConfidence,
    MatchResult,
    ResolutionStatus,
    ResolveRequest,
)


class FakeResult:
    def __init__(self, rows: list[object] | object | None) -> None:
        self.rows = rows

    def scalar_one_or_none(self):
        if isinstance(self.rows, list):
            return self.rows[0] if self.rows else None
        return self.rows

    def scalars(self):
        return self

    def all(self):
        if self.rows is None:
            return []
        return self.rows if isinstance(self.rows, list) else [self.rows]

    def first(self):
        rows = self.all()
        return rows[0] if rows else None


class FakeSession:
    def __init__(self, source_record: SourceRecord) -> None:
        self.source_record = source_record
        self.source_records = [source_record]
        self.source_keys = {source_record.source_id: "quebec_city_permits"}
        self.events: list[object] = []
        self.added: list[object] = []
        self.run_only_reads = 0

    async def execute(self, statement):
        sql = str(statement)
        if "FROM ingestion_run" in sql:
            return FakeResult(
                SimpleNamespace(run_id=self.source_record.ingestion_run_id,
                                source_id=self.source_record.source_id)
            )
        if "FROM business_event" in sql:
            return FakeResult(self.events)
        if "JOIN source" in sql and "source_record" in sql:
            params = statement.compile().params
            expected_source_key = next(
                value for key, value in params.items() if "source_key" in key
            )
            expected_record_id = next(
                value for key, value in params.items() if "source_record_id" in key
            )
            return FakeResult(
                [row for row in self.source_records
                 if row.entity_id is None
                 and row.resolution_status == "UNRESOLVED"
                 and self.source_keys.get(row.source_id) == expected_source_key
                 and row.source_record_id == expected_record_id]
            )
        if "FROM source_record" in sql and "resolution_status IN" in sql:
            self.run_only_reads += 1
            if self.run_only_reads == 1:
                return FakeResult([
                    row for row in self.source_records
                    if row.resolution_status in ("PENDING", "UNRESOLVED")
                ])
            return FakeResult([])
        if "FROM source_record" in sql:
            return FakeResult(self.source_record)
        return FakeResult(self.source_record)

    async def commit(self) -> None:
        return None

    async def flush(self) -> None:
        return None

    def add(self, obj: object) -> None:
        self.added.append(obj)
        if getattr(obj, "__tablename__", None) == "business_event":
            self.events.append(obj)


def make_permit_record(
    run_id: uuid.UUID,
    *,
    business_name: str | None = None,
    corp_number: str | None = None,
) -> NormalisedRecord:
    extra = {
        "permit_number": "QC-PERMIT-123",
        "event_type": "MUNICIPAL_PERMIT_ISSUED",
    }
    if corp_number:
        extra["corp_number"] = corp_number

    return NormalisedRecord(
        source_key="quebec_city_permits",
        ingestion_run_id=run_id,
        source_record_id="QC-PERMIT-123",
        name=(
            NormalisedName(
                raw_legal_name=business_name,
                legal_name=business_name.lower(),
            )
            if business_name
            else NormalisedName()
        ),
        address=NormalisedAddress(
            raw_address="100 Rue Exemple",
            address_line1="100 Rue Exemple",
            city="Québec",
            province="QC",
        ),
        issued_date="2026-09-27T00:00:00+00:00",
        extra=extra,
    )


def make_source_record(
    source_id: uuid.UUID,
    run_id: uuid.UUID,
    normalized: NormalisedRecord,
    *,
    resolution_status: str = "PENDING",
) -> SourceRecord:
    return SourceRecord(
        record_id=uuid.uuid4(),
        source_id=source_id,
        ingestion_run_id=run_id,
        source_record_id=normalized.source_record_id,
        source_grain="EVENT",
        raw_payload={
            "permit_number": "QC-PERMIT-123",
            "issue_date": "2026-09-27",
            "event_type": "MUNICIPAL_PERMIT_ISSUED",
        },
        normalised_payload=normalized.model_dump(mode="json"),
        entity_id=None,
        resolution_status=resolution_status,
    )


async def no_match(*_args, **_kwargs) -> MatchResult:
    return MatchResult(matched=False)


@pytest.mark.asyncio
async def test_permit_without_business_identity_remains_unresolved(monkeypatch) -> None:
    source_id = uuid.uuid4()
    run_id = uuid.uuid4()
    record = make_permit_record(run_id)
    source_record = make_source_record(source_id, run_id, record)
    db = FakeSession(source_record)

    monkeypatch.setattr(resolution_routes, "match_exact_identifier", no_match)
    monkeypatch.setattr(resolution_routes, "match_composite_deterministic", no_match)
    monkeypatch.setattr(resolution_routes, "match_fuzzy", no_match)

    async def unexpected_business_creation(*_args, **_kwargs):
        raise AssertionError("permit-only source record must not create a business")

    monkeypatch.setattr(resolution_routes, "create_new_entity", unexpected_business_creation)

    response = await resolution_routes.resolve(
        ResolveRequest(run_id=run_id, source_id=source_id, records=[record]),
        db,
    )

    assert response.records_unresolved == 1
    assert response.results[0].resolution_status == ResolutionStatus.UNRESOLVED
    assert response.results[0].entity_id is None
    assert source_record.entity_id is None
    assert source_record.resolution_status == "UNRESOLVED"
    assert source_record.raw_payload["permit_number"] == "QC-PERMIT-123"
    assert db.added == []
    assert db.events == []


@pytest.mark.asyncio
async def test_later_match_links_same_record_and_creates_event_once(monkeypatch) -> None:
    source_id = uuid.uuid4()
    run_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    record = make_permit_record(
        run_id,
        business_name="Example Construction Ltd.",
        corp_number="1234567",
    )
    source_record = make_source_record(
        source_id,
        run_id,
        record,
        resolution_status="UNRESOLVED",
    )
    original_record_id = source_record.record_id
    original_payload = source_record.raw_payload.copy()
    db = FakeSession(source_record)

    async def match_corp_number(*_args, **_kwargs) -> MatchResult:
        return MatchResult(
            matched=True,
            entity_id=entity_id,
            confidence=MatchConfidence.HIGH,
            match_method="corp_number",
        )

    async def link_existing_record(
        *, source_record_row: SourceRecord, **_kwargs
    ) -> int:
        source_record_row.entity_id = entity_id
        source_record_row.resolution_status = "MATCHED"
        source_record_row.resolution_confidence = "HIGH"
        return 1

    monkeypatch.setattr(resolution_routes, "match_exact_identifier", match_corp_number)
    monkeypatch.setattr(resolution_routes, "merge_high_confidence", link_existing_record)
    monkeypatch.setattr(resolution_routes, "match_composite_deterministic", no_match)
    monkeypatch.setattr(resolution_routes, "match_fuzzy", no_match)

    response = await resolution_routes.resolve(
        ResolveRequest(run_id=run_id, source_id=source_id, records=[record]),
        db,
    )

    assert response.results[0].resolution_status == ResolutionStatus.MATCHED
    assert response.results[0].entity_id == entity_id
    assert source_record.record_id == original_record_id
    assert source_record.entity_id == entity_id
    assert source_record.resolution_status == "MATCHED"
    assert source_record.raw_payload == original_payload

    first_events = await detect_new_business_events(entity_id, run_id, source_id, db)
    second_events = await detect_new_business_events(entity_id, run_id, source_id, db)

    assert len(first_events) == 1
    assert first_events[0].event_type == "MUNICIPAL_PERMIT_ISSUED"
    assert first_events[0].entity_id == entity_id
    assert second_events == []
    assert len(db.events) == 1


@pytest.mark.asyncio
async def test_later_run_only_resolution_retries_unresolved_record(monkeypatch) -> None:
    source_id = uuid.uuid4()
    run_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    record = make_permit_record(run_id)
    source_record = make_source_record(
        source_id,
        run_id,
        record,
        resolution_status="UNRESOLVED",
    )
    db = FakeSession(source_record)

    async def match_existing_business(*_args, **_kwargs) -> MatchResult:
        return MatchResult(
            matched=True,
            entity_id=entity_id,
            confidence=MatchConfidence.HIGH,
            match_method="corp_number",
        )

    async def link_existing_record(
        *, source_record_row: SourceRecord, **_kwargs
    ) -> int:
        source_record_row.entity_id = entity_id
        source_record_row.resolution_status = "MATCHED"
        source_record_row.resolution_confidence = "HIGH"
        return 1

    monkeypatch.setattr(resolution_routes, "match_exact_identifier", match_existing_business)
    monkeypatch.setattr(resolution_routes, "merge_high_confidence", link_existing_record)
    monkeypatch.setattr(resolution_routes, "match_composite_deterministic", no_match)
    monkeypatch.setattr(resolution_routes, "match_fuzzy", no_match)

    response = await resolution_routes.resolve(
        ResolveRequest(run_id=run_id),
        db,
    )

    assert response.records_resolved == 1
    assert response.records_merged == 1
    assert response.records_unresolved == 0
    assert source_record.entity_id == entity_id
    assert source_record.resolution_status == "MATCHED"
    assert source_record.ingestion_run_id == run_id


@pytest.mark.asyncio
async def test_run_only_resolution_uses_exact_rows_for_duplicate_source_ids(monkeypatch) -> None:
    source_id = uuid.uuid4()
    run_id = uuid.uuid4()
    first_record = make_permit_record(run_id, business_name="First Business Ltd.")
    second_record = make_permit_record(run_id, business_name="Second Business Ltd.")
    second_record = second_record.model_copy(update={"source_record_id": first_record.source_record_id})
    first_source_record = make_source_record(source_id, run_id, first_record)
    second_source_record = make_source_record(source_id, run_id, second_record)
    db = FakeSession(first_source_record)
    db.source_records = [first_source_record, second_source_record]
    created_rows: list[SourceRecord] = []

    monkeypatch.setattr(resolution_routes, "match_exact_identifier", no_match)
    monkeypatch.setattr(resolution_routes, "match_composite_deterministic", no_match)
    monkeypatch.setattr(resolution_routes, "match_fuzzy", no_match)

    async def create_entity(*, source_record_row: SourceRecord, **_kwargs):
        created_rows.append(source_record_row)
        entity_id = uuid.uuid4()
        source_record_row.entity_id = entity_id
        source_record_row.resolution_status = "NEW"
        return entity_id, 0

    monkeypatch.setattr(resolution_routes, "create_new_entity", create_entity)

    response = await resolution_routes.resolve(ResolveRequest(run_id=run_id), db)

    assert response.records_resolved == 2
    assert created_rows == [first_source_record, second_source_record]
    assert first_source_record.entity_id is not None
    assert second_source_record.entity_id is not None
    assert first_source_record.entity_id != second_source_record.entity_id


@pytest.mark.asyncio
async def test_new_ingestion_run_links_explicitly_referenced_unresolved_record(monkeypatch) -> None:
    permit_source_id = uuid.uuid4()
    permit_run_id = uuid.uuid4()
    business_source_id = uuid.uuid4()
    business_run_id = uuid.uuid4()
    entity_id = uuid.uuid4()

    permit_record = make_permit_record(permit_run_id)
    unresolved_permit = make_source_record(
        permit_source_id,
        permit_run_id,
        permit_record,
        resolution_status="UNRESOLVED",
    )
    original_record_id = unresolved_permit.record_id
    original_payload = unresolved_permit.raw_payload.copy()

    business_record = make_permit_record(
        business_run_id,
        business_name="Example Construction Ltd.",
        corp_number="1234567",
    )
    business_record.source_key = "corporations_canada_csv"
    business_record.source_record_id = "CORP-1234567"
    business_record.source_references = [
        SourceRecordReference(
            source_key="quebec_city_permits",
            source_record_id="QC-PERMIT-123",
        )
    ]
    current_business_record = make_source_record(
        business_source_id,
        business_run_id,
        business_record,
    )
    db = FakeSession(current_business_record)
    db.source_records.append(unresolved_permit)
    db.source_keys[permit_source_id] = "quebec_city_permits"

    wrong_source_id = uuid.uuid4()
    wrong_source_record = make_source_record(
        wrong_source_id,
        uuid.uuid4(),
        permit_record,
        resolution_status="UNRESOLVED",
    )
    db.source_records.append(wrong_source_record)
    db.source_keys[wrong_source_id] = "another_source"
    detector_calls = 0
    real_detect_new_business_events = resolution_routes.detect_new_business_events

    async def track_event_detection(*args, **kwargs):
        nonlocal detector_calls
        detector_calls += 1
        return await real_detect_new_business_events(*args, **kwargs)

    monkeypatch.setattr(
        resolution_routes,
        "detect_new_business_events",
        track_event_detection,
    )

    async def match_business(*_args, **_kwargs) -> MatchResult:
        return MatchResult(
            matched=True,
            entity_id=entity_id,
            confidence=MatchConfidence.HIGH,
            match_method="corp_number",
        )

    async def merge_business(
        *, source_record_row: SourceRecord, **_kwargs
    ) -> int:
        source_record_row.entity_id = entity_id
        source_record_row.resolution_status = "MATCHED"
        source_record_row.resolution_confidence = "HIGH"
        return 1

    monkeypatch.setattr(resolution_routes, "match_exact_identifier", match_business)
    monkeypatch.setattr(resolution_routes, "merge_high_confidence", merge_business)

    response = await resolution_routes.resolve(
        ResolveRequest(
            run_id=business_run_id,
            source_id=business_source_id,
            records=[business_record],
        ),
        db,
    )

    assert response.records_merged == 1
    assert unresolved_permit.record_id == original_record_id
    assert unresolved_permit.source_id == permit_source_id
    assert unresolved_permit.ingestion_run_id == permit_run_id
    assert unresolved_permit.entity_id == entity_id
    assert unresolved_permit.resolution_status == "MATCHED"
    assert unresolved_permit.raw_payload == original_payload
    assert wrong_source_record.entity_id is None
    assert wrong_source_record.resolution_status == "UNRESOLVED"
    assert detector_calls == 1
    assert len(db.events) == 1
    assert db.events[0].event_type == "MUNICIPAL_PERMIT_ISSUED"
    assert db.events[0].event_source == permit_source_id
    assert db.events[0].ingestion_run_id == permit_run_id