"""Data contracts for the ingestion pipeline.

Pydantic models and enums shared between the SourceAdapter interface,
ingestion routes, and downstream services.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceGrain(str, Enum):
    """The unit of data a source produces per record."""

    CORPORATION = "CORPORATION"
    LICENCE = "LICENCE"
    EVENT = "EVENT"
    REGISTRATION = "REGISTRATION"
    ESTABLISHMENT = "ESTABLISHMENT"


# ---------------------------------------------------------------------------
# Core data transfer objects
# ---------------------------------------------------------------------------


class RawArtifact(BaseModel):
    """Represents a fetched raw artifact from a source before parsing.

    Carries enough metadata to reconstruct the ingestion_run provenance row
    (Requirement 2.1, 3.3).
    """

    source_key: str
    ingestion_run_id: uuid.UUID
    retrieval_url: str
    retrieval_timestamp: datetime
    http_status: int | None = None
    content_type: str | None = None
    checksum_sha256: str
    # filepath or inline reference — adapters decide what to store here
    payload_ref: str
    source_version: str | None = None


class RawRecord(BaseModel):
    """A single parsed record from a source artifact.

    Stored as-is in source_record.raw_payload (Requirement 2.2).
    """

    source_key: str
    ingestion_run_id: uuid.UUID
    # Source-provided identifier or a stable hash of the row
    source_record_id: str
    # Original parsed row — arbitrary dict mirroring the source schema
    raw_payload: dict[str, Any]
    source_grain: SourceGrain


class SourceMetadata(BaseModel):
    """Static configuration metadata for a source adapter (Requirement 3.2)."""

    source_key: str
    source_name: str
    adapter_class: str
    province: str | None = None
    source_type: str  # CSV | JSON | API | HTML | PDF | GeoJSON | XLSX
    source_class: str  # A | B | C | D
    licence: str | None = None
    schedule_cron: str | None = None
    rate_limit_rpm: int | None = None
    base_url: str | None = None
    default_grain: SourceGrain


class ValidationResult(BaseModel):
    """Outcome of adapter.validate() (Requirement 3.1)."""

    source_key: str
    ingestion_run_id: uuid.UUID
    total_records: int
    valid_records: int
    invalid_records: int
    # Per-field issue summary: field_name → list of error messages
    errors: dict[str, list[str]] = Field(default_factory=dict)
    passed: bool

    @classmethod
    def all_valid(cls, source_key: str, run_id: uuid.UUID, count: int) -> "ValidationResult":
        return cls(
            source_key=source_key,
            ingestion_run_id=run_id,
            total_records=count,
            valid_records=count,
            invalid_records=0,
            passed=True,
        )
