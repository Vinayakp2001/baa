"""Pydantic schemas for the enrichment service HTTP boundary.

POST /enrich/directors  — receive corp_number list, call CorporationsCanadaAPIAdapter
POST /enrich/orgbook    — receive entity_id + bc_reg_id, update BC identity data
POST /enrich/website    — optional website phone extraction

Requirements: 8.2, 8.3, 8.9
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class EnrichDirectorsRequest(BaseModel):
    """Payload for POST /enrich/directors."""

    run_id: uuid.UUID
    source_id: uuid.UUID          # must be corporations_canada_api source row
    corp_numbers: list[str]       # federal CBCA corps only


class EnrichDirectorsResponse(BaseModel):
    run_id: uuid.UUID
    corps_requested: int
    directors_written: int
    corps_not_found: int


class EnrichOrgBookRequest(BaseModel):
    """Payload for POST /enrich/orgbook."""

    run_id: uuid.UUID
    source_id: uuid.UUID          # must be bc_orgbook source row
    entity_id: uuid.UUID
    bc_reg_id: str | None = None
    business_name: str | None = None   # fallback if bc_reg_id not available


class EnrichOrgBookResponse(BaseModel):
    run_id: uuid.UUID
    entity_id: uuid.UUID
    enriched: bool
    fields_updated: list[str]


class EnrichWebsiteRequest(BaseModel):
    """Payload for POST /enrich/website (optional enrichment)."""

    run_id: uuid.UUID
    source_id: uuid.UUID
    entity_id: uuid.UUID
    domain: str


class EnrichWebsiteResponse(BaseModel):
    run_id: uuid.UUID
    entity_id: uuid.UUID
    phones_found: int
    enriched: bool
