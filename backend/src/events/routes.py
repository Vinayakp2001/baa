"""FastAPI routes for the events service.

POST /events/detect  — receive entity_id + ingestion_run_id, run all
                       detectors, return events_created count.

Requirements: 6.1, 6.4, 6.5
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import bind_pipeline_context, get_logger
from ..db.session import get_db
from ..models.provenance import SourceRecord
from ..models.source import IngestionRun
from .detectors import detect_change_events, detect_new_business_events
from .schemas import DetectEventsRequest, DetectEventsResponse

router = APIRouter(prefix="/events", tags=["events"])
logger = get_logger(__name__)


@router.post("/detect", response_model=DetectEventsResponse)
async def detect_events(
    request: DetectEventsRequest,
    db: AsyncSession = Depends(get_db),
) -> DetectEventsResponse:
    """Run all event detectors for a resolved entity in a given ingestion run.

    Detectors run in order:
    1. new_business_detector  — BUSINESS_DISCOVERED + typed events
    2. change_detector        — STATUS_CHANGED, NAME_CHANGED, LOCATION_CHANGED,
                                BUSINESS_UPDATED

    Requirements: 6.1, 6.2, 6.4, 6.5
    """
    # Resolve source_id from the ingestion_run so detectors can attribute events
    run_result = await db.execute(
        select(IngestionRun).where(IngestionRun.run_id == request.ingestion_run_id)
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"ingestion_run {request.ingestion_run_id} not found",
        )
    source_id = run.source_id

    bind_pipeline_context(run_id=str(request.ingestion_run_id))
    logger.info(
        "events_detect_start",
        entity_id=str(request.entity_id) if request.entity_id else None,
    )

    events_created = 0
    event_types: set[str] = set()
    entities_processed = 0

    async def process_entity(entity_id):
        nonlocal events_created, entities_processed
        bind_pipeline_context(
            entity_id=str(entity_id),
            run_id=str(request.ingestion_run_id),
        )
        new_events = await detect_new_business_events(
            entity_id=entity_id,
            ingestion_run_id=request.ingestion_run_id,
            source_id=source_id,
            db=db,
        )
        change_events = await detect_change_events(
            entity_id=entity_id,
            ingestion_run_id=request.ingestion_run_id,
            source_id=source_id,
            db=db,
        )
        for event in new_events + change_events:
            event_types.add(event.event_type)
        events_created += len(new_events) + len(change_events)
        entities_processed += 1

    if request.entity_id is not None:
        await process_entity(request.entity_id)
    else:
        last_entity_id = None
        while True:
            entities_query = select(SourceRecord.entity_id).where(
                SourceRecord.ingestion_run_id == request.ingestion_run_id,
                SourceRecord.entity_id.is_not(None),
            )
            if last_entity_id is not None:
                entities_query = entities_query.where(SourceRecord.entity_id > last_entity_id)
            entities_query = (
                entities_query.distinct()
                .order_by(SourceRecord.entity_id)
                .limit(1000)
            )
            entities_result = await db.execute(entities_query)
            entity_ids = [row[0] for row in entities_result.all()]
            if not entity_ids:
                break
            for entity_id in entity_ids:
                await process_entity(entity_id)
            last_entity_id = entity_ids[-1]

    await db.commit()
    logger.info(
        "events_detect_complete",
        entity_id=str(request.entity_id) if request.entity_id else None,
        entities_processed=entities_processed,
        events_created=events_created,
        event_types=sorted(event_types),
    )

    return DetectEventsResponse(
        entity_id=request.entity_id,
        ingestion_run_id=request.ingestion_run_id,
        entities_processed=entities_processed,
        events_created=events_created,
        event_types=sorted(event_types),
    )
