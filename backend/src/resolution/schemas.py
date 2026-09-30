"""Pydantic schemas for the entity resolution service HTTP boundary.

POST /resolve  — receive NormalisedRecord[], return ResolutionResult[]

Requirements: 5.1, 5.2, 2.5
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel

from ..normalisation.schemas import NormalisedRecord


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MatchConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ResolutionStatus(str, Enum):
    MATCHED = "MATCHED"    # HIGH — auto-merged into existing entity
    CANDIDATE = "CANDIDATE"  # MEDIUM — merge_candidate queued
    NEW = "NEW"            # no match — new entity created
    UNRESOLVED = "UNRESOLVED"  # insufficient business identity; source record retained
    SKIPPED = "SKIPPED"    # e.g. NNI terms not cleared


# ---------------------------------------------------------------------------
# Match result (internal, used by matchers)
# ---------------------------------------------------------------------------


class MatchResult(BaseModel):
    """Internal match result returned by each matcher stage."""

    matched: bool
    entity_id: uuid.UUID | None = None
    confidence: MatchConfidence | None = None
    match_method: str | None = None
    match_score: float | None = None


# ---------------------------------------------------------------------------
# Resolution request / response
# ---------------------------------------------------------------------------


class ResolveRequest(BaseModel):
    """Payload for POST /resolve."""

    run_id: uuid.UUID
    source_id: uuid.UUID | None = None
    records: list[NormalisedRecord] | None = None


class ResolutionResult(BaseModel):
    """Per-record resolution outcome returned by POST /resolve."""

    source_record_id: str
    source_key: str
    resolution_status: ResolutionStatus
    confidence: MatchConfidence | None = None
    entity_id: uuid.UUID | None = None
    match_method: str | None = None
    match_score: float | None = None
    field_observations_written: int = 0


class ResolveResponse(BaseModel):
    """Response from POST /resolve."""

    run_id: uuid.UUID
    records_resolved: int
    records_new: int
    records_merged: int
    records_candidate: int
    records_unresolved: int = 0
    results: list[ResolutionResult]
