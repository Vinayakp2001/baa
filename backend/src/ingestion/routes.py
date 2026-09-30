"""Ingestion service FastAPI routes.

Four endpoints that together form the ingestion lifecycle:

  POST /ingestion/start    → create ingestion_run, return run_id
  POST /ingestion/fetch    → store source_record rows, update run metadata
  POST /ingestion/complete → mark run COMPLETED, store final stats
  POST /ingestion/fail     → mark run FAILED, store error, increment retry_count

Requirements: 2.1, 2.2, 3.3, 3.4
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import bind_pipeline_context, get_logger
from ..db.session import get_db
from ..ingestion.adapters.registry import AdapterNotAvailableError, create_ingestion_adapter
from ..ingestion.adapters.nni import NNIAdapter
from ..ingestion.base_adapter import SourceFetchError, SourceParseError
from ..ingestion.contracts import RawRecord
from ..models.provenance import SourceRecord
from ..models.source import IngestionRun, Source
from .schemas import (
    IngestionCompleteRequest,
    IngestionCompleteResponse,
    IngestionFailRequest,
    IngestionFailResponse,
    IngestionFetchRequest,
    IngestionFetchResponse,
    IngestionStartRequest,
    IngestionStartResponse,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_source_by_key(db: AsyncSession, source_key: str) -> Source:
    """Fetch a Source row by source_key, raising 404 if not found."""
    result = await db.execute(select(Source).where(Source.source_key == source_key))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_key}' not found in registry.",
        )
    return source


async def _get_run(db: AsyncSession, run_id: uuid.UUID) -> IngestionRun:
    """Fetch an IngestionRun by run_id, raising 404 if not found."""
    result = await db.execute(select(IngestionRun).where(IngestionRun.run_id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion run '{run_id}' not found.",
        )
    return run


# ---------------------------------------------------------------------------
# POST /ingestion/start
# ---------------------------------------------------------------------------


@router.post(
    "/start",
    response_model=IngestionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new ingestion run",
)
async def ingestion_start(
    body: IngestionStartRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionStartResponse:
    """Create a new ingestion_run row for the given source and return the run_id.

    The caller (n8n workflow) stores the run_id and passes it to all subsequent
    calls in the same pipeline execution.
    """
    source = await _get_source_by_key(db, body.source_key)

    now = datetime.now(tz=timezone.utc)
    run = IngestionRun(
        source_id=source.source_id,
        run_started_at=now,
        run_status="RUNNING",
        source_url=body.source_url,
        retrieval_timestamp=body.retrieval_timestamp,
        source_version_or_date=body.source_version_or_date,
    )
    db.add(run)
    await db.flush()  # populate run_id before commit

    bind_pipeline_context(source_key=body.source_key, run_id=str(run.run_id))
    logger.info("ingestion_run_started", source_key=body.source_key)

    return IngestionStartResponse(
        run_id=run.run_id,
        source_id=source.source_id,
        source_key=body.source_key,
        run_started_at=now,
    )


# ---------------------------------------------------------------------------
# POST /ingestion/fetch
# ---------------------------------------------------------------------------


@router.post(
    "/fetch",
    response_model=IngestionFetchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store raw records from a source into source_record table",
)
async def ingestion_fetch(
    body: IngestionFetchRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionFetchResponse:
    """Fetch and parse a registered adapter, or persist caller-supplied RawRecord objects.

    Adapter I/O and parsing run in a worker thread so synchronous source clients do not
    block FastAPI's event loop. Parsed records remain inside the service and are persisted
    in bounded batches rather than passed through n8n.

    Requirements: 2.1, 2.2
    """
    run = await _get_run(db, body.run_id)
    source = await _get_source_by_key(db, body.source_key)
    if source.source_id != run.source_id:
        raise HTTPException(status_code=409, detail="Source does not match ingestion run")
    if not source.is_enabled and source.terms_status != "UNRESOLVED":
        raise HTTPException(status_code=409, detail=f"Source '{body.source_key}' is disabled")

    bind_pipeline_context(source_key=body.source_key, run_id=str(body.run_id))

    records = body.records
    if records is None:
        try:
            adapter = create_ingestion_adapter(source.adapter_class, source.source_key)
            last_run_result = await db.execute(
                select(IngestionRun.run_completed_at)
                .where(
                    IngestionRun.source_id == source.source_id,
                    IngestionRun.run_status == "COMPLETED",
                    IngestionRun.run_id != run.run_id,
                )
                .order_by(IngestionRun.run_completed_at.desc())
                .limit(1)
            )
            since = last_run_result.scalar_one_or_none()
            if isinstance(adapter, NNIAdapter):
                artifact = await asyncio.to_thread(
                    adapter.fetch, since=since, terms_status=source.terms_status
                )
            else:
                artifact = await asyncio.to_thread(adapter.fetch, since=since)
            records = await asyncio.to_thread(adapter.parse, artifact)
            validation = await asyncio.to_thread(adapter.validate, records)
            if not validation.passed:
                logger.warning(
                    "ingestion_validation_issues",
                    source_key=body.source_key,
                    invalid_records=validation.invalid_records,
                    errors=validation.errors,
                )

            run.source_url = artifact.retrieval_url
            run.retrieval_timestamp = artifact.retrieval_timestamp
            run.checksum_sha256 = artifact.checksum_sha256
            run.source_version_or_date = artifact.source_version
            run.record_count_raw = len(records)
        except (AdapterNotAvailableError, SourceFetchError, SourceParseError) as exc:
            logger.error("ingestion_adapter_failed", source_key=body.source_key, error=str(exc))
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("ingestion_adapter_unexpected_error", source_key=body.source_key)
            raise HTTPException(status_code=502, detail=f"Adapter failed: {exc}") from exc
    else:
        if body.retrieval_url is not None:
            run.source_url = body.retrieval_url
        if body.retrieval_timestamp is not None:
            run.retrieval_timestamp = body.retrieval_timestamp
        if body.checksum_sha256 is not None:
            run.checksum_sha256 = body.checksum_sha256
        if body.source_version_or_date is not None:
            run.source_version_or_date = body.source_version_or_date
        run.record_count_raw = (run.record_count_raw or 0) + len(records)

    # Keep batch size bounded; large federal CSV files must not inflate the ORM identity map.
    # COMPLIANCE: assert no individual records from StatsCan aggregate sources (Req 15.1)
    from ..core.compliance import assert_not_statscan_individual
    for raw in records:
        assert_not_statscan_individual(source.source_key, raw.raw_payload)
    rows = [
        {
            "source_id": run.source_id,
            "ingestion_run_id": run.run_id,
            "source_record_id": raw.source_record_id,
            "source_grain": raw.source_grain.value,
            "raw_payload": raw.raw_payload,
            "resolution_status": "PENDING",
        }
        for raw in records
    ]
    for offset in range(0, len(rows), 1000):
        await db.execute(insert(SourceRecord), rows[offset : offset + 1000])

    logger.info("ingestion_records_stored", count=len(rows))

    return IngestionFetchResponse(run_id=body.run_id, records_stored=len(rows))


# ---------------------------------------------------------------------------
# POST /ingestion/complete
# ---------------------------------------------------------------------------


@router.post(
    "/complete",
    response_model=IngestionCompleteResponse,
    summary="Mark an ingestion run as COMPLETED",
)
async def ingestion_complete(
    body: IngestionCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionCompleteResponse:
    """Set run_status=COMPLETED and store final pipeline stats.

    Requirements: 2.1, 10.4
    """
    run = await _get_run(db, body.run_id)

    now = datetime.now(tz=timezone.utc)
    run.run_status = "COMPLETED"
    run.run_completed_at = now

    if body.record_count_raw is not None:
        run.record_count_raw = body.record_count_raw
    if body.record_count_normalised is not None:
        run.record_count_normalised = body.record_count_normalised
    if body.record_count_new is not None:
        run.record_count_new = body.record_count_new
    if body.record_count_updated is not None:
        run.record_count_updated = body.record_count_updated
    if body.record_count_flagged is not None:
        run.record_count_flagged = body.record_count_flagged
    if body.source_version_or_date is not None:
        run.source_version_or_date = body.source_version_or_date
    if body.checksum_sha256 is not None:
        run.checksum_sha256 = body.checksum_sha256

    logger.info(
        "ingestion_run_completed",
        run_id=str(body.run_id),
        record_count_raw=run.record_count_raw,
        record_count_new=run.record_count_new,
    )

    return IngestionCompleteResponse(
        run_id=run.run_id,
        run_status=run.run_status,
        run_completed_at=now,
    )


# ---------------------------------------------------------------------------
# POST /ingestion/fail
# ---------------------------------------------------------------------------


@router.post(
    "/fail",
    response_model=IngestionFailResponse,
    summary="Mark an ingestion run as FAILED",
)
async def ingestion_fail(
    body: IngestionFailRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionFailResponse:
    """Set run_status=FAILED, store error_message, increment retry_count.

    The prior successful ingestion data remains active — only the run record
    is marked failed. Requirements: 3.4, 10.3, 10.7.
    """
    run = await _get_run(db, body.run_id)

    run.run_status = "FAILED"
    run.run_completed_at = datetime.now(tz=timezone.utc)
    run.error_message = body.error_message
    run.retry_count = (run.retry_count or 0) + 1

    logger.warning(
        "ingestion_run_failed",
        run_id=str(body.run_id),
        error=body.error_message,
        retry_count=run.retry_count,
    )

    return IngestionFailResponse(
        run_id=run.run_id,
        run_status=run.run_status,
        retry_count=run.retry_count,
    )
