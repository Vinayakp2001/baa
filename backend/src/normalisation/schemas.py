"""Pydantic schemas for the normalisation service HTTP boundary.

POST /normalise  — receive RawRecord[], return NormalisedRecord[]

Requirements: 4.1
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from ..ingestion.contracts import RawRecord


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class NormaliseRequest(BaseModel):
    """Payload for POST /normalise."""

    run_id: uuid.UUID
    records: list[RawRecord] | None = None


# ---------------------------------------------------------------------------
# Normalised field sub-models
# ---------------------------------------------------------------------------


class NormalisedPhone(BaseModel):
    raw_phone: str | None = None
    normalised_phone: str | None = None
    phone_valid: bool | None = None


class NormalisedEmail(BaseModel):
    raw_email: str | None = None
    normalised_email: str | None = None
    email_valid: bool | None = None


class NormalisedURL(BaseModel):
    raw_url: str | None = None
    normalised_domain: str | None = None
    url_valid: bool | None = None


class NormalisedAddress(BaseModel):
    raw_address: str | None = None
    normalised_address: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    province: str | None = None
    postal_code: str | None = None
    postal_valid: bool | None = None


class NormalisedName(BaseModel):
    raw_legal_name: str | None = None
    raw_trade_name: str | None = None
    legal_name: str | None = None
    trade_name: str | None = None


class NormalisedEmployee(BaseModel):
    raw_employee_value: str | None = None
    employee_min: int | None = None
    employee_max: int | None = None
    employee_bucket: str | None = None
    employee_exact: bool = False
    data_quality_flag: str | None = None


class NormalisedStatus(BaseModel):
    raw_status: str | None = None
    canonical_status: str = "UNKNOWN"


class NormalisedNAICS(BaseModel):
    source_naics: str | None = None
    naics_sector: str | None = None


class SourceRecordReference(BaseModel):
    """Explicit source-provided link from this record to another source row."""

    source_key: str
    source_record_id: str


# ---------------------------------------------------------------------------
# Full NormalisedRecord
# ---------------------------------------------------------------------------


class NormalisedRecord(BaseModel):
    """A fully normalised record derived from a RawRecord.

    All normalised sub-objects are optional — they are populated only when
    the corresponding field is present in the raw_payload.
    """

    # Provenance links
    source_key: str
    ingestion_run_id: uuid.UUID
    source_record_id: str

    # Normalised field groups
    name: NormalisedName | None = None
    address: NormalisedAddress | None = None
    phone: NormalisedPhone | None = None
    email: NormalisedEmail | None = None
    website: NormalisedURL | None = None
    status: NormalisedStatus | None = None
    employee: NormalisedEmployee | None = None
    naics: NormalisedNAICS | None = None

    # Date fields normalised to ISO UTC strings (stored as str for JSON serialisation)
    issued_date: str | None = None         # licence issue / registration date
    expiry_date: str | None = None
    incorporation_date: str | None = None
    source_references: list[SourceRecordReference] = Field(default_factory=list)

    # Pass-through fields (source-specific, not normalised)
    extra: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class NormaliseResponse(BaseModel):
    """Response from POST /normalise."""

    run_id: uuid.UUID
    records_normalised: int
    results: list[NormalisedRecord] = Field(default_factory=list)
