"""Normalisation service FastAPI routes.

POST /normalise  — receive RawRecord[], apply all normalisers, return NormalisedRecord[]
                   Stores normalised_payload back into source_record rows in DB.

Requirements: 4.1
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import bind_pipeline_context, get_logger
from ..db.session import get_db
from ..models.provenance import SourceRecord
from ..models.source import IngestionRun, Source
from ..ingestion.contracts import RawRecord, SourceGrain
from .normaliser import normalise_record
from .schemas import NormaliseRequest, NormaliseResponse, NormalisedRecord

router = APIRouter(prefix="/normalise", tags=["normalisation"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=NormaliseResponse,
    status_code=status.HTTP_200_OK,
    summary="Normalise a batch of raw records",
)
async def normalise(
    body: NormaliseRequest,
    db: AsyncSession = Depends(get_db),
) -> NormaliseResponse:
    """Apply all field normalisers to each RawRecord.

    Stores the normalised payload back into source_record.normalised_payload
    (JSONB) keyed by source_record_id.

    Returns the full list of NormalisedRecord objects.
    Requirements: 4.1, 2.3
    """
    bind_pipeline_context(run_id=str(body.run_id))
    logger.info(
        "normalise_start",
        record_count=len(body.records) if body.records is not None else None,
    )

    if body.records is not None:
        normalised: list[NormalisedRecord] = []
        record_id_map: dict[str, NormalisedRecord] = {}
        for raw in body.records:
            result = normalise_record(raw)
            normalised.append(result)
            record_id_map[raw.source_record_id] = result

        if record_id_map:
            result_rows = await db.execute(
                select(SourceRecord).where(
                    SourceRecord.source_record_id.in_(list(record_id_map)),
                    SourceRecord.ingestion_run_id == body.run_id,
                )
            )
            for row in result_rows.scalars().all():
                norm = record_id_map.get(row.source_record_id)
                if norm:
                    row.normalised_payload = norm.model_dump(mode="json")

        return NormaliseResponse(
            run_id=body.run_id,
            records_normalised=len(normalised),
            results=normalised,
        )

    run_result = await db.execute(
        select(IngestionRun).where(IngestionRun.run_id == body.run_id)
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Ingestion run '{body.run_id}' not found")

    source_result = await db.execute(
        select(Source.source_key).where(Source.source_id == run.source_id)
    )
    source_key = source_result.scalar_one()
    records_normalised = 0
    offset = 0
    batch_size = 1000

    while True:
        result_rows = await db.execute(
            select(SourceRecord)
            .where(SourceRecord.ingestion_run_id == body.run_id)
            .order_by(SourceRecord.record_id)
            .limit(batch_size)
            .offset(offset)
        )
        rows = result_rows.scalars().all()
        if not rows:
            break

        for row in rows:
            raw = RawRecord(
                source_key=source_key,
                ingestion_run_id=body.run_id,
                source_record_id=row.source_record_id or str(row.record_id),
                raw_payload=row.raw_payload,
                source_grain=SourceGrain(row.source_grain),
            )
            normalised_record = normalise_record(raw)
            row.normalised_payload = normalised_record.model_dump(mode="json")
            records_normalised += 1

        offset += len(rows)

    run.record_count_normalised = records_normalised
    logger.info("normalise_complete", records_normalised=records_normalised)
    return NormaliseResponse(
        run_id=body.run_id,
        records_normalised=records_normalised,
    )
