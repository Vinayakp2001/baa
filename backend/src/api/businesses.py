"""Public REST API — /businesses endpoints.

GET /businesses          — paginated, filterable business list  (Req 11.1, 11.2, 11.3)
GET /businesses/{id}     — full business detail                  (Req 11.1)
GET /businesses/{id}/history — field_observation history          (Req 11.4)
GET /businesses/{id}/sources — contributing source_records        (Req 11.1)

Requirements: 11.1, 11.2, 11.3, 11.4
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.logging import get_logger
from ..db.session import get_db
from ..models.business import (
    Business,
    BusinessContact,
    BusinessEmployeeData,
    BusinessIdentifier,
    BusinessIndustry,
    BusinessLocation,
    Person,
)
from ..models.events import BusinessEvent
from ..models.provenance import FieldObservation, SourceRecord
from ..models.quality import LeadFlag
from .schemas import (
    BusinessDetail,
    BusinessHistoryResponse,
    BusinessSummary,
    FieldHistory,
    FieldObservationOut,
    PaginatedBusinesses,
    SourceRecordOut,
)

router = APIRouter(prefix="/businesses", tags=["businesses"])
logger = get_logger(__name__)

_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 500


# ---------------------------------------------------------------------------
# GET /businesses
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedBusinesses)
async def list_businesses(
    # Filters (Req 11.2)
    province: str | None = Query(None),
    city: str | None = Query(None),
    naics_sector: str | None = Query(None),
    employee_bucket: str | None = Query(None),
    status: str | None = Query(None),
    sales_ready: bool | None = Query(None),
    has_phone: bool | None = Query(None),
    has_email: bool | None = Query(None),
    has_website: bool | None = Query(None),
    has_director: bool | None = Query(None),
    new_since: date | None = Query(None),
    event_type: str | None = Query(None),
    source_id: uuid.UUID | None = Query(None),
    dnc: bool | None = Query(None),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
) -> PaginatedBusinesses:
    """Paginated, filterable list of canonical business entities.

    Requirements: 11.1, 11.2, 11.3
    """
    offset = (page - 1) * page_size

    # Base query
    q = select(Business)

    # Simple column filters
    if province:
        q = q.where(Business.province == province.upper())
    if status:
        q = q.where(Business.status == status.upper())
    if sales_ready is not None:
        q = q.where(Business.sales_ready == sales_ready)

    # City filter — join through location
    if city:
        city_sub = select(BusinessLocation.entity_id).where(
            func.lower(BusinessLocation.city) == city.lower()
        )
        q = q.where(Business.entity_id.in_(city_sub))

    # NAICS sector filter
    if naics_sector:
        naics_sub = select(BusinessIndustry.entity_id).where(
            BusinessIndustry.naics_sector == naics_sector
        )
        q = q.where(Business.entity_id.in_(naics_sub))

    # Employee bucket filter
    if employee_bucket:
        emp_sub = select(BusinessEmployeeData.entity_id).where(
            BusinessEmployeeData.employee_bucket == employee_bucket
        )
        q = q.where(Business.entity_id.in_(emp_sub))

    # Contact filters
    if has_phone is not None:
        phone_sub = select(BusinessContact.entity_id).where(
            BusinessContact.contact_type == "PHONE"
        )
        if has_phone:
            q = q.where(Business.entity_id.in_(phone_sub))
        else:
            q = q.where(Business.entity_id.not_in(phone_sub))

    if has_email is not None:
        email_sub = select(BusinessContact.entity_id).where(
            BusinessContact.contact_type == "EMAIL"
        )
        if has_email:
            q = q.where(Business.entity_id.in_(email_sub))
        else:
            q = q.where(Business.entity_id.not_in(email_sub))

    if has_website is not None:
        web_sub = select(BusinessContact.entity_id).where(
            BusinessContact.contact_type == "WEBSITE"
        )
        if has_website:
            q = q.where(Business.entity_id.in_(web_sub))
        else:
            q = q.where(Business.entity_id.not_in(web_sub))

    if has_director is not None:
        dir_sub = select(Person.entity_id).where(Person.role_type == "DIRECTOR")
        if has_director:
            q = q.where(Business.entity_id.in_(dir_sub))
        else:
            q = q.where(Business.entity_id.not_in(dir_sub))

    # new_since filter — join through business_event
    if new_since:
        new_sub = select(BusinessEvent.entity_id).where(
            BusinessEvent.event_date >= new_since
        )
        q = q.where(Business.entity_id.in_(new_sub))

    # event_type filter
    if event_type:
        evt_sub = select(BusinessEvent.entity_id).where(
            BusinessEvent.event_type == event_type
        )
        q = q.where(Business.entity_id.in_(evt_sub))

    # source_id filter — business appeared in a specific source
    if source_id:
        src_sub = select(SourceRecord.entity_id).where(
            SourceRecord.source_id == source_id,
            SourceRecord.entity_id.is_not(None),
        )
        q = q.where(Business.entity_id.in_(src_sub))

    # DNC filter — exclude (dnc=True) or require (dnc=False) DNC flags
    if dnc is not None:
        dnc_sub = select(LeadFlag.entity_id).where(LeadFlag.flag_type == "DNC")
        if dnc:
            q = q.where(Business.entity_id.in_(dnc_sub))
        else:
            q = q.where(Business.entity_id.not_in(dnc_sub))

    # Count total
    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    # Fetch page
    q = q.order_by(Business.first_seen_at.desc()).offset(offset).limit(page_size)
    rows = await db.execute(q)
    entities = rows.scalars().all()

    next_cursor = page + 1 if (offset + page_size) < total else None

    return PaginatedBusinesses(
        total=total,
        page=page,
        page_size=page_size,
        next_cursor=next_cursor,
        results=[BusinessSummary.model_validate(e) for e in entities],
    )


# ---------------------------------------------------------------------------
# GET /businesses/{id}
# ---------------------------------------------------------------------------


@router.get("/{entity_id}", response_model=BusinessDetail)
async def get_business(
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BusinessDetail:
    """Full canonical entity with all enrichment sub-objects.

    Requirements: 11.1
    """
    result = await db.execute(
        select(Business)
        .options(
            selectinload(Business.locations),
            selectinload(Business.identifiers),
            selectinload(Business.contacts),
            selectinload(Business.persons),
            selectinload(Business.employee_data),
            selectinload(Business.industries),
            selectinload(Business.quality_score),
        )
        .where(Business.entity_id == entity_id)
    )
    entity = result.scalar_one_or_none()
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Business {entity_id} not found")

    return BusinessDetail.model_validate(entity)


# ---------------------------------------------------------------------------
# GET /businesses/{id}/history
# ---------------------------------------------------------------------------


@router.get("/{entity_id}/history", response_model=BusinessHistoryResponse)
async def get_business_history(
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BusinessHistoryResponse:
    """All field_observation records grouped by field, with source attribution.

    Requirements: 11.4
    """
    result = await db.execute(
        select(FieldObservation)
        .where(FieldObservation.entity_id == entity_id)
        .order_by(FieldObservation.field_name, FieldObservation.observed_at.desc())
    )
    observations = result.scalars().all()

    if not observations:
        # Verify entity exists
        exists = await db.execute(
            select(Business.entity_id).where(Business.entity_id == entity_id)
        )
        if not exists.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Business {entity_id} not found")

    # Group by field_name
    grouped: dict[str, list[FieldObservationOut]] = {}
    for obs in observations:
        out = FieldObservationOut.model_validate(obs)
        grouped.setdefault(obs.field_name, []).append(out)

    fields = [
        FieldHistory(field_name=fn, observations=obs_list)
        for fn, obs_list in grouped.items()
    ]

    return BusinessHistoryResponse(entity_id=entity_id, fields=fields)


# ---------------------------------------------------------------------------
# GET /businesses/{id}/sources
# ---------------------------------------------------------------------------


@router.get("/{entity_id}/sources", response_model=list[SourceRecordOut])
async def get_business_sources(
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SourceRecordOut]:
    """All contributing source_record rows for this entity.

    Requirements: 11.1
    """
    result = await db.execute(
        select(SourceRecord)
        .where(SourceRecord.entity_id == entity_id)
        .order_by(SourceRecord.created_at.desc())
    )
    records = result.scalars().all()

    if not records:
        exists = await db.execute(
            select(Business.entity_id).where(Business.entity_id == entity_id)
        )
        if not exists.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Business {entity_id} not found")

    return [SourceRecordOut.model_validate(r) for r in records]


# ---------------------------------------------------------------------------
# POST /businesses/{id}/flags  — set a lead flag (e.g. DNC)  Req 13.1, 13.2
# ---------------------------------------------------------------------------

from .schemas import LeadFlagOut, SetFlagRequest


@router.post("/{entity_id}/flags", response_model=LeadFlagOut, status_code=201)
async def set_lead_flag(
    entity_id: uuid.UUID,
    body: SetFlagRequest,
    db: AsyncSession = Depends(get_db),
) -> LeadFlagOut:
    """Set a lead flag (DNC, CONTACTED, QUALIFIED, etc.) on a business.

    Flags are stored in the lead_flag table only — no canonical entity fields
    are modified. Requirements: 13.1, 13.2
    """
    # Verify entity exists
    exists = await db.execute(select(Business.entity_id).where(Business.entity_id == entity_id))
    if not exists.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Business {entity_id} not found")

    flag = LeadFlag(
        entity_id=entity_id,
        flag_type=body.flag_type.upper(),
        flag_value=body.flag_value,
        set_by=body.set_by,
        notes=body.notes,
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    logger.info("lead_flag_set", entity_id=str(entity_id), flag_type=body.flag_type)
    return LeadFlagOut.model_validate(flag)


# ---------------------------------------------------------------------------
# DELETE /businesses/{id}/flags/{flag_type}  — remove a flag  Req 13.2
# ---------------------------------------------------------------------------

from fastapi import status as http_status


@router.delete(
    "/{entity_id}/flags/{flag_type}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
)
async def remove_lead_flag(
    entity_id: uuid.UUID,
    flag_type: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove all flags of a given type from a business entity.

    Requirements: 13.2
    """
    from sqlalchemy import delete as sql_delete

    await db.execute(
        sql_delete(LeadFlag).where(
            LeadFlag.entity_id == entity_id,
            LeadFlag.flag_type == flag_type.upper(),
        )
    )
    await db.commit()
    logger.info("lead_flag_removed", entity_id=str(entity_id), flag_type=flag_type)


# ---------------------------------------------------------------------------
# GET /businesses/{id}/flags  — list flags  Req 13.1
# ---------------------------------------------------------------------------


@router.get("/{entity_id}/flags", response_model=list[LeadFlagOut])
async def list_lead_flags(
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[LeadFlagOut]:
    """List all lead flags for a business entity. Requirements: 13.1"""
    result = await db.execute(
        select(LeadFlag)
        .where(LeadFlag.entity_id == entity_id)
        .order_by(LeadFlag.set_at.desc())
    )
    return [LeadFlagOut.model_validate(f) for f in result.scalars().all()]
