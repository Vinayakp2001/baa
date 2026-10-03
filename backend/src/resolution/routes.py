"""Entity resolution service FastAPI routes.

POST /resolve  — receive NormalisedRecord[], run resolution pipeline,
                 return ResolutionResult[]

Writes field_observation rows for every field of every processed record.

Requirements: 5.1, 2.5
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import bind_pipeline_context, get_logger
from ..db.session import get_db
from ..models.provenance import SourceRecord
from ..models.source import IngestionRun, Source
from ..normalisation.schemas import NormalisedRecord
from .matchers.composite_deterministic import match_composite_deterministic
from .matchers.exact_identifier import match_exact_identifier
from .matchers.fuzzy import match_fuzzy
from .merge import (
    create_new_entity,
    create_with_low_confidence_candidate,
    merge_high_confidence,
    queue_medium_confidence,
)
from ..events.detectors import detect_new_business_events
from .merge import _write_field_observations
from .schemas import (
    MatchConfidence,
    ResolveRequest,
    ResolveResponse,
    ResolutionResult,
    ResolutionStatus,
)

router = APIRouter(prefix="/resolve", tags=["resolution"])
logger = get_logger(__name__)


def _has_business_identity(record: NormalisedRecord) -> bool:
    """Return whether the source supplied a business name or stable business ID."""
    if record.name and (record.name.legal_name or record.name.trade_name):
        return True

    extra = record.extra or {}
    return any(
        extra.get(key)
        for key in (
            "corp_number",
            "corp_no",
            "business_number_bn",
            "bn",
            "business_number",
        )
    )


@router.post(
    "",
    response_model=ResolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve a batch of normalised records to canonical entities",
)
async def resolve(
    body: ResolveRequest,
    db: AsyncSession = Depends(get_db),
) -> ResolveResponse:
    """Run the full entity resolution pipeline on a batch of NormalisedRecords.

    Resolution priority (per Req 5.1):
      1. Exact identifier match  → HIGH  → auto-merge
      2. Composite deterministic → MEDIUM → merge_candidate queue
      3. Fuzzy name+postal       → LOW   → new entity + candidate link
      4. No match                         → new entity

    Writes field_observation rows for every non-null field in every record.
    Preserves source_id, source_grain, source_record_id, ingestion_run_id on
    every contributing source_record row (Req 5.6, 5.7).
    """
    run_only = body.records is None
    if run_only:
        run_result = await db.execute(
            select(IngestionRun).where(IngestionRun.run_id == body.run_id)
        )
        run = run_result.scalar_one_or_none()
        if run is None:
            raise HTTPException(status_code=404, detail=f"Ingestion run '{body.run_id}' not found")
        source_id = run.source_id
        if body.source_id is not None and body.source_id != source_id:
            raise HTTPException(status_code=409, detail="Source does not match ingestion run")
    elif body.source_id is None:
        raise HTTPException(status_code=422, detail="source_id is required when records are supplied")
    else:
        source_id = body.source_id

    bind_pipeline_context(run_id=str(body.run_id))
    logger.info(
        "resolve_start",
        record_count=len(body.records) if body.records is not None else None,
        source_id=str(source_id),
        run_only=run_only,
    )

    results: list[ResolutionResult] = []
    counts = {"new": 0, "merged": 0, "candidate": 0, "unresolved": 0}

    async def process_record(norm_record: NormalisedRecord) -> None:
        try:
            result = await _resolve_single(
                record=norm_record,
                source_id=source_id,
                ingestion_run_id=body.run_id,
                db=db,
                source_record_row=source_record if run_only else None,
            )
        except Exception as exc:
            logger.error(
                "resolve_record_error",
                source_record_id=norm_record.source_record_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Resolution failed for record {norm_record.source_record_id}: {exc}",
            ) from exc

        if not run_only:
            results.append(result)
        if result.resolution_status == ResolutionStatus.MATCHED:
            counts["merged"] += 1
        elif result.resolution_status == ResolutionStatus.CANDIDATE:
            counts["candidate"] += 1
        elif result.resolution_status == ResolutionStatus.UNRESOLVED:
            counts["unresolved"] += 1
        else:
            counts["new"] += 1

        if result.entity_id is not None:
            await _link_referenced_unresolved_records(
                record=norm_record,
                entity_id=result.entity_id,
                current_source_id=source_id,
                current_run_id=body.run_id,
                db=db,
            )

    if run_only:
        last_record_id = None
        while True:
            records_query = select(SourceRecord).where(
                SourceRecord.ingestion_run_id == body.run_id,
                SourceRecord.normalised_payload.is_not(None),
                SourceRecord.resolution_status.in_(("PENDING", "UNRESOLVED")),
            )
            if last_record_id is not None:
                records_query = records_query.where(SourceRecord.record_id > last_record_id)
            records_query = records_query.order_by(SourceRecord.record_id).limit(1000)
            records_result = await db.execute(records_query)
            source_records = records_result.scalars().all()
            if not source_records:
                break

            for source_record in source_records:
                await process_record(NormalisedRecord.model_validate(source_record.normalised_payload))
            last_record_id = source_records[-1].record_id
            await db.commit()
    else:
        for norm_record in body.records:
            await process_record(norm_record)

    logger.info(
        "resolve_complete",
        total=sum(counts.values()),
        new=counts["new"],
        merged=counts["merged"],
        candidates=counts["candidate"],
    )

    return ResolveResponse(
        run_id=body.run_id,
        records_resolved=sum(counts.values()),
        records_new=counts["new"],
        records_merged=counts["merged"],
        records_candidate=counts["candidate"],
        records_unresolved=counts["unresolved"],
        results=results,
    )


async def _resolve_single(
    record,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    db: AsyncSession,
    source_record_row: SourceRecord | None = None,
) -> ResolutionResult:
    """Resolve a single NormalisedRecord through the full pipeline."""

    if source_record_row is None:
        stmt = select(SourceRecord).where(
            SourceRecord.source_record_id == record.source_record_id,
            SourceRecord.ingestion_run_id == ingestion_run_id,
        )
        result = await db.execute(stmt)
        source_record_row = result.scalars().first()

    if source_record_row is None:
        # Synthesise a minimal row so resolution can proceed without blocking
        logger.warning(
            "resolve_source_record_not_found",
            source_record_id=record.source_record_id,
            run_id=str(ingestion_run_id),
        )
        source_record_row = SourceRecord(
            source_id=source_id,
            ingestion_run_id=ingestion_run_id,
            source_record_id=record.source_record_id,
            source_grain=record.extra.get("source_grain") if record.extra else None,
            raw_payload=record.model_dump(mode="json"),
            normalised_payload=record.model_dump(mode="json"),
        )
        db.add(source_record_row)
        await db.flush()
    else:
        source_record_row.normalised_payload = record.model_dump(mode="json")

    # Step 1 — Exact identifier match (HIGH)
    match = await match_exact_identifier(record, source_id, db)

    if match.matched and match.confidence == MatchConfidence.HIGH:
        obs = await merge_high_confidence(
            record=record,
            match=match,
            source_record_row=source_record_row,
            source_id=source_id,
            ingestion_run_id=ingestion_run_id,
            db=db,
        )
        return ResolutionResult(
            source_record_id=record.source_record_id,
            source_key=record.source_key,
            resolution_status=ResolutionStatus.MATCHED,
            confidence=MatchConfidence.HIGH,
            entity_id=match.entity_id,
            match_method=match.match_method,
            match_score=match.match_score,
            field_observations_written=obs,
        )

    # Step 2 — Composite deterministic match (MEDIUM)
    match = await match_composite_deterministic(record, db)

    if match.matched and match.confidence == MatchConfidence.MEDIUM:
        new_id, obs = await queue_medium_confidence(
            record=record,
            match=match,
            source_record_row=source_record_row,
            source_id=source_id,
            ingestion_run_id=ingestion_run_id,
            db=db,
        )
        return ResolutionResult(
            source_record_id=record.source_record_id,
            source_key=record.source_key,
            resolution_status=ResolutionStatus.CANDIDATE,
            confidence=MatchConfidence.MEDIUM,
            entity_id=new_id,
            match_method=match.match_method,
            match_score=match.match_score,
            field_observations_written=obs,
        )

    # Step 3 — Fuzzy match (LOW)
    match = await match_fuzzy(record, db)

    if match.matched and match.confidence == MatchConfidence.LOW:
        new_id, obs = await create_with_low_confidence_candidate(
            record=record,
            match=match,
            source_record_row=source_record_row,
            source_id=source_id,
            ingestion_run_id=ingestion_run_id,
            db=db,
        )
        return ResolutionResult(
            source_record_id=record.source_record_id,
            source_key=record.source_key,
            resolution_status=ResolutionStatus.NEW,
            confidence=MatchConfidence.LOW,
            entity_id=new_id,
            match_method=match.match_method,
            match_score=match.match_score,
            field_observations_written=obs,
        )

    # Keep source observations that do not identify a business out of the canonical layer.
    if not _has_business_identity(record):
        source_record_row.entity_id = None
        source_record_row.resolution_status = ResolutionStatus.UNRESOLVED.value
        source_record_row.resolution_confidence = None
        return ResolutionResult(
            source_record_id=record.source_record_id,
            source_key=record.source_key,
            resolution_status=ResolutionStatus.UNRESOLVED,
            confidence=None,
            entity_id=None,
            match_method="INSUFFICIENT_IDENTITY",
            match_score=None,
            field_observations_written=0,
        )

    # Step 4 — No match with sufficient identity → new entity
    new_id, obs = await create_new_entity(
        record=record,
        source_record_row=source_record_row,
        source_id=source_id,
        ingestion_run_id=ingestion_run_id,
        db=db,
    )
    return ResolutionResult(
        source_record_id=record.source_record_id,
        source_key=record.source_key,
        resolution_status=ResolutionStatus.NEW,
        confidence=None,
        entity_id=new_id,
        match_method=None,
        match_score=None,
        field_observations_written=obs,
    )


async def _link_referenced_unresolved_records(
    *,
    record: NormalisedRecord,
    entity_id: uuid.UUID,
    current_source_id: uuid.UUID,
    current_run_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Link only explicitly referenced prior source rows to the resolved entity."""
    for reference in record.source_references:
        result = await db.execute(
            select(SourceRecord)
            .join(Source, Source.source_id == SourceRecord.source_id)
            .where(
                Source.source_key == reference.source_key,
                SourceRecord.source_record_id == reference.source_record_id,
                SourceRecord.entity_id.is_(None),
                SourceRecord.resolution_status == ResolutionStatus.UNRESOLVED.value,
            )
        )
        unresolved_records = result.scalars().all()
        for unresolved in unresolved_records:
            unresolved.entity_id = entity_id
            unresolved.resolution_status = ResolutionStatus.MATCHED.value
            unresolved.resolution_confidence = MatchConfidence.HIGH.value

            unresolved_record = NormalisedRecord.model_validate(
                unresolved.normalised_payload
            )
            await _write_field_observations(
                entity_id=entity_id,
                record=unresolved_record,
                source_record_db_id=unresolved.record_id,
                source_id=unresolved.source_id,
                ingestion_run_id=unresolved.ingestion_run_id,
                confidence=MatchConfidence.HIGH,
                db=db,
            )
            await detect_new_business_events(
                entity_id=entity_id,
                ingestion_run_id=unresolved.ingestion_run_id,
                source_id=unresolved.source_id,
                db=db,
            )
