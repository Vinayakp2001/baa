"""Pydantic schemas for the events service HTTP boundary.

POST /events/detect  — receive entity_id + ingestion_run_id, detect and
                       create all applicable events, return events_created count.

Requirements: 6.1, 6.2, 6.4, 6.5
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class DetectEventsRequest(BaseModel):
    """Payload for POST /events/detect."""

    entity_id: uuid.UUID | None = None
    ingestion_run_id: uuid.UUID


class DetectEventsResponse(BaseModel):
    """Response from POST /events/detect."""

    entity_id: uuid.UUID | None = None
    ingestion_run_id: uuid.UUID
    entities_processed: int = 0
    events_created: int
    event_types: list[str]
