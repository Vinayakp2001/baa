"""Pydantic response schemas for the public REST API.

Requirements: 11.1, 11.2, 11.3, 11.4
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class LocationOut(BaseModel):
    location_id: uuid.UUID
    address_line1: str | None
    address_line2: str | None
    city: str | None
    province: str | None
    postal_code: str | None
    country: str
    latitude: Decimal | None
    longitude: Decimal | None
    location_type: str | None
    is_primary: bool

    class Config:
        from_attributes = True


class ContactOut(BaseModel):
    contact_id: uuid.UUID
    contact_type: str
    raw_value: str
    normalised_value: str | None
    is_valid: bool | None
    enrichment_source: str | None
    confidence: str | None

    class Config:
        from_attributes = True


class PersonOut(BaseModel):
    person_id: uuid.UUID
    person_name: str
    role_type: str | None
    role_label_raw: str | None
    confidence: str | None
    source_url: str | None

    class Config:
        from_attributes = True


class EmployeeOut(BaseModel):
    employee_id: uuid.UUID
    raw_employee_value: str
    employee_min: int | None
    employee_max: int | None
    employee_bucket: str | None
    employee_exact: bool
    data_quality_flag: str | None

    class Config:
        from_attributes = True


class IndustryOut(BaseModel):
    industry_id: uuid.UUID
    source_naics: str | None
    naics_sector: str | None
    source_industry_str: str | None

    class Config:
        from_attributes = True


class IdentifierOut(BaseModel):
    id_type: str
    id_value: str

    class Config:
        from_attributes = True


class QualityScoreOut(BaseModel):
    identity_confidence: int | None
    address_confidence: int | None
    phone_confidence: int | None
    email_confidence: int | None
    employee_confidence: int | None
    industry_confidence: int | None
    contact_confidence: int | None
    recency_confidence: int | None
    source_reliability: int | None
    lead_quality_score: int | None
    scored_at: datetime | None

    class Config:
        from_attributes = True


class EventOut(BaseModel):
    event_id: uuid.UUID
    event_type: str
    event_date: date | None
    raw_value: str | None
    previous_value: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SourceRecordOut(BaseModel):
    record_id: uuid.UUID
    source_id: uuid.UUID
    ingestion_run_id: uuid.UUID
    source_record_id: str | None
    source_grain: str | None
    resolution_status: str | None
    resolution_confidence: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FieldObservationOut(BaseModel):
    observation_id: uuid.UUID
    field_name: str
    raw_value: str | None
    normalised_value: str | None
    source_id: uuid.UUID
    observed_at: datetime
    confidence: str | None
    is_current: bool

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Business summary (list endpoint)
# ---------------------------------------------------------------------------


class BusinessSummary(BaseModel):
    entity_id: uuid.UUID
    canonical_name: str
    legal_name: str | None
    trade_name: str | None
    entity_type: str | None
    province: str | None
    status: str | None
    sales_ready: bool
    lead_quality_score: int | None
    first_seen_at: datetime
    last_verified_at: datetime | None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Business detail (single entity endpoint)
# ---------------------------------------------------------------------------


class BusinessDetail(BusinessSummary):
    locations: list[LocationOut] = []
    identifiers: list[IdentifierOut] = []
    contacts: list[ContactOut] = []
    persons: list[PersonOut] = []
    employee_data: list[EmployeeOut] = []
    industries: list[IndustryOut] = []
    quality_score: QualityScoreOut | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Pagination wrapper
# ---------------------------------------------------------------------------


class PaginatedBusinesses(BaseModel):
    total: int
    page: int
    page_size: int
    next_cursor: int | None
    results: list[BusinessSummary]


# ---------------------------------------------------------------------------
# History / provenance response
# ---------------------------------------------------------------------------


class FieldHistory(BaseModel):
    field_name: str
    observations: list[FieldObservationOut]


class BusinessHistoryResponse(BaseModel):
    entity_id: uuid.UUID
    fields: list[FieldHistory]


# ---------------------------------------------------------------------------
# Events list
# ---------------------------------------------------------------------------


class PaginatedEvents(BaseModel):
    total: int
    page: int
    page_size: int
    next_cursor: int | None
    results: list[EventOut]


# ---------------------------------------------------------------------------
# Sources status
# ---------------------------------------------------------------------------


class SourceStatusOut(BaseModel):
    source_id: uuid.UUID
    source_key: str
    source_name: str
    province: str | None
    source_type: str
    source_class: str
    is_enabled: bool
    schedule_cron: str | None
    last_run_status: str | None
    last_run_at: datetime | None
    last_run_record_count: int | None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class ProvinceStats(BaseModel):
    province: str
    total_businesses: int
    sales_ready: int
    has_coverage_gap: bool


class PipelineStats(BaseModel):
    total_businesses: int
    sales_ready_count: int
    new_last_30_days: int
    province_coverage_gaps: list[str]
    by_province: list[ProvinceStats]
    by_source: dict[str, int]
    field_fill_rates: dict[str, float]


# ---------------------------------------------------------------------------
# Lead flags (DNC / sales layer)
# ---------------------------------------------------------------------------


class LeadFlagOut(BaseModel):
    flag_id: uuid.UUID
    entity_id: uuid.UUID
    flag_type: str | None
    flag_value: str | None
    set_by: str | None
    set_at: datetime
    notes: str | None

    class Config:
        from_attributes = True


class SetFlagRequest(BaseModel):
    flag_type: str          # e.g. DNC, CONTACTED, QUALIFIED
    flag_value: str | None = None
    set_by: str | None = None
    notes: str | None = None
