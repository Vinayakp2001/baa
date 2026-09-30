"""Pydantic schemas for the quality scoring service HTTP boundary.

POST /quality/score  — receive entity_id[], compute all components + composite,
                       persist scores, return results.

Requirements: 9.1, 9.2, 9.3
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, model_validator


class ScoreRequest(BaseModel):
    """Payload for POST /quality/score."""

    entity_ids: list[uuid.UUID] = Field(default_factory=list)
    ingestion_run_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def require_entity_ids_or_run_id(self) -> "ScoreRequest":
        if bool(self.entity_ids) == (self.ingestion_run_id is not None):
            raise ValueError("Provide exactly one of entity_ids or ingestion_run_id")
        return self


class EntityScoreResult(BaseModel):
    entity_id: uuid.UUID
    identity_confidence: int | None = None
    address_confidence: int | None = None
    phone_confidence: int | None = None
    email_confidence: int | None = None
    employee_confidence: int | None = None
    industry_confidence: int | None = None
    contact_confidence: int | None = None
    recency_confidence: int | None = None
    source_reliability: int | None = None
    lead_quality_score: int | None = None
    sales_ready: bool = False


class ScoreResponse(BaseModel):
    """Response from POST /quality/score."""

    entities_scored: int
    results: list[EntityScoreResult]
