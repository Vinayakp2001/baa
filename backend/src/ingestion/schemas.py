"""Request/response Pydantic schemas for ingestion service routes.

Separate from contracts.py (which holds the adapter-layer data types).
These are the HTTP-boundary schemas used by FastAPI route handlers.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .contracts import RawRecord, SourceGrain


# ---------------------------------------------------------------------------
# POST /ingestion/start
# ---------------------------------------------------------------------------


class IngestionStartRequest(BaseModel):
    """Start a new ingestion run for a named source."""

    source_key: str
    source_url: str | None = None
    # Optional: caller can pass the retrieval timestamp if it already fetched
    retrieval_timestamp: datetime | None = None
    source_version_or_date: str | None = None


class IngestionStartResponse(BaseModel):
    """Returned after a new ingestion_run row is created."""

    run_id: uuid.UUID
    source_id: uuid.UUID
    source_key: str
    run_started_at: datetime


# ---------------------------------------------------------------------------
# POST /ingestion/fetch
# ---------------------------------------------------------------------------


class IngestionFetchRequest(BaseModel):
    """Fetch a registered source or submit already parsed raw records."""

    run_id: uuid.UUID
    source_key: str
    limit: int | None = Field(default=None, ge=1, le=1000)
    records: list[RawRecord] | None = None
    # Metadata captured during fetch — stored on the ingestion_run
    retrieval_url: str | None = None
    retrieval_timestamp: datetime | None = None
    checksum_sha256: str | None = None
    source_version_or_date: str | None = None
    http_status: int | None = None


class IngestionFetchResponse(BaseModel):
    """Returned after source_record rows are persisted."""

    run_id: uuid.UUID
    records_stored: int


# ---------------------------------------------------------------------------
# POST /ingestion/complete
# ---------------------------------------------------------------------------


class IngestionCompleteRequest(BaseModel):
    """Mark an ingestion run as COMPLETED and store final stats."""

    run_id: uuid.UUID
    record_count_raw: int | None = None
    record_count_normalised: int | None = None
    record_count_new: int | None = None
    record_count_updated: int | None = None
    record_count_flagged: int | None = None
    source_version_or_date: str | None = None
    checksum_sha256: str | None = None


class IngestionCompleteResponse(BaseModel):
    run_id: uuid.UUID
    run_status: str
    run_completed_at: datetime


# ---------------------------------------------------------------------------
# POST /ingestion/fail
# ---------------------------------------------------------------------------


class IngestionFailRequest(BaseModel):
    """Mark an ingestion run as FAILED and record the error."""

    run_id: uuid.UUID
    error_message: str


class IngestionFailResponse(BaseModel):
    run_id: uuid.UUID
    run_status: str
    retry_count: int
