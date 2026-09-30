"""Public REST API — events, sources, stats, and export endpoints.

GET /events      — paginated event stream                     (Req 11.1)
GET /sources     — source registry with last run status       (Req 11.1)
GET /stats       — pipeline coverage statistics               (Req 11.1)
GET /export      — CSV/JSON export with filters               (Req 11.1, 13.3)

Requirements: 11.1, 13.3
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..db.session import get_db
from ..models.business import Business, BusinessContact, BusinessLocation
from ..models.events import BusinessEvent
from ..models.provenance import SourceRecord
from ..models.quality import LeadFlag, ProvinceCoverageGap
from ..models.source import IngestionRun, Source
from .schemas import (
    EventOut,
    PaginatedEvents,
    PipelineStats,
    ProvinceStats,
    SourceStatusOut,
)

router = APIRouter(tags=["misc"])
logger = get_logger(__name__)

_DEFAULT_PAGE_SIZE = 100
_MAX_PAGE_SIZE = 1000
_UTC = timezone.utc


# ---------------------------------------------------------------------------
# GET /events
# ---------------------------------------------------------------------------


@router.get("/events", response_model=PaginatedEvents)
async def list_events(
    event_type: str | None = Query(None),
    province: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
) -> PaginatedEvents:
    """Paginated event stream, filterable by event_type, province, date_range.

    Requirements: 11.1
    """
    offset = (page - 1) * page_size
    q = select(BusinessEvent)

    if event_type:
        q = q.where(BusinessEvent.event_type == event_type)
    if date_from:
        q = q.where(BusinessEvent.event_date >= date_from)
    if date_to:
        q = q.where(BusinessEvent.event_date <= date_to)
    if province:
        # Filter via business province
        prov_sub = select(Business.entity_id).where(Business.province == province.upper())
        q = q.where(BusinessEvent.entity_id.in_(prov_sub))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    q = q.order_by(BusinessEvent.event_date.desc(), BusinessEvent.created_at.desc())
    q = q.offset(offset).limit(page_size)
    rows = await db.execute(q)
    events = rows.scalars().all()

    next_cursor = page + 1 if (offset + page_size) < total else None

    return PaginatedEvents(
        total=total,
        page=page,
        page_size=page_size,
        next_cursor=next_cursor,
        results=[EventOut.model_validate(e) for e in events],
    )


# ---------------------------------------------------------------------------
# GET /sources
# ---------------------------------------------------------------------------


@router.get("/sources", response_model=list[SourceStatusOut])
async def list_sources(
    db: AsyncSession = Depends(get_db),
) -> list[SourceStatusOut]:
    """Source registry with last ingestion run status per source.

    Requirements: 11.1
    """
    sources_result = await db.execute(select(Source).order_by(Source.source_name))
    sources = sources_result.scalars().all()

    output: list[SourceStatusOut] = []
    for source in sources:
        # Latest run for this source
        run_result = await db.execute(
            select(IngestionRun)
            .where(IngestionRun.source_id == source.source_id)
            .order_by(IngestionRun.run_started_at.desc())
            .limit(1)
        )
        last_run = run_result.scalar_one_or_none()

        output.append(
            SourceStatusOut(
                source_id=source.source_id,
                source_key=source.source_key,
                source_name=source.source_name,
                province=source.province,
                source_type=source.source_type,
                source_class=source.source_class,
                is_enabled=source.is_enabled,
                schedule_cron=source.schedule_cron,
                last_run_status=last_run.run_status if last_run else None,
                last_run_at=last_run.run_started_at if last_run else None,
                last_run_record_count=last_run.record_count_raw if last_run else None,
            )
        )

    return output


# ---------------------------------------------------------------------------
# GET /stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=PipelineStats)
async def get_stats(db: AsyncSession = Depends(get_db)) -> PipelineStats:
    """Pipeline coverage statistics — totals, by province, by source, field fill rates.

    Requirements: 11.1
    """
    # Totals
    total = (await db.execute(select(func.count(Business.entity_id)))).scalar_one()
    sales_ready_count = (
        await db.execute(
            select(func.count(Business.entity_id)).where(Business.sales_ready.is_(True))
        )
    ).scalar_one()

    # New last 30 days (BUSINESS_DISCOVERED events)
    from datetime import timedelta

    cutoff = date.today() - timedelta(days=30)
    new_30 = (
        await db.execute(
            select(func.count(BusinessEvent.event_id)).where(
                BusinessEvent.event_type == "BUSINESS_DISCOVERED",
                BusinessEvent.event_date >= cutoff,
            )
        )
    ).scalar_one()

    # Province coverage gaps
    gap_result = await db.execute(
        select(ProvinceCoverageGap.province).where(
            ProvinceCoverageGap.gap_level.in_(["CONFIRMED", "PARTIAL"])
        )
    )
    gap_provinces = [row[0] for row in gap_result.all()]

    # By province breakdown
    prov_result = await db.execute(
        select(Business.province, func.count(Business.entity_id))
        .group_by(Business.province)
        .order_by(Business.province)
    )
    prov_rows = prov_result.all()

    sr_by_prov = {}
    for prov_code, _ in prov_rows:
        if prov_code:
            sr_count = (
                await db.execute(
                    select(func.count(Business.entity_id)).where(
                        Business.province == prov_code,
                        Business.sales_ready.is_(True),
                    )
                )
            ).scalar_one()
            sr_by_prov[prov_code] = sr_count

    province_stats = [
        ProvinceStats(
            province=prov or "UNKNOWN",
            total_businesses=count,
            sales_ready=sr_by_prov.get(prov or "UNKNOWN", 0),
            has_coverage_gap=(prov in gap_provinces),
        )
        for prov, count in prov_rows
    ]

    # By source — count distinct entities per source
    src_result = await db.execute(
        select(Source.source_key, func.count(SourceRecord.entity_id.distinct()))
        .join(SourceRecord, SourceRecord.source_id == Source.source_id)
        .where(SourceRecord.entity_id.is_not(None))
        .group_by(Source.source_key)
    )
    by_source = {row[0]: row[1] for row in src_result.all()}

    # Field fill rates: phone, email, website, director
    fill_rates: dict[str, float] = {}
    if total > 0:
        phone_count = (
            await db.execute(
                select(func.count(BusinessContact.entity_id.distinct())).where(
                    BusinessContact.contact_type == "PHONE"
                )
            )
        ).scalar_one()
        email_count = (
            await db.execute(
                select(func.count(BusinessContact.entity_id.distinct())).where(
                    BusinessContact.contact_type == "EMAIL"
                )
            )
        ).scalar_one()
        website_count = (
            await db.execute(
                select(func.count(BusinessContact.entity_id.distinct())).where(
                    BusinessContact.contact_type == "WEBSITE"
                )
            )
        ).scalar_one()
        from ..models.business import Person

        director_count = (
            await db.execute(
                select(func.count(Person.entity_id.distinct())).where(
                    Person.role_type == "DIRECTOR"
                )
            )
        ).scalar_one()

        fill_rates = {
            "phone": round(phone_count / total, 4),
            "email": round(email_count / total, 4),
            "website": round(website_count / total, 4),
            "director": round(director_count / total, 4),
        }

    return PipelineStats(
        total_businesses=total,
        sales_ready_count=sales_ready_count,
        new_last_30_days=new_30,
        province_coverage_gaps=gap_provinces,
        by_province=province_stats,
        by_source=by_source,
        field_fill_rates=fill_rates,
    )


# ---------------------------------------------------------------------------
# GET /export
# ---------------------------------------------------------------------------


@router.get("/export")
async def export_businesses(
    format: str = Query("csv", regex="^(csv|json)$"),
    province: str | None = Query(None),
    status: str | None = Query(None),
    sales_ready: bool | None = Query(None),
    has_phone: bool | None = Query(None),
    has_email: bool | None = Query(None),
    include_dnc: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export filtered businesses as CSV or JSON.

    DNC-flagged records excluded by default; include_dnc=true to override.

    Requirements: 11.1, 13.3
    """
    q = select(Business)

    if province:
        q = q.where(Business.province == province.upper())
    if status:
        q = q.where(Business.status == status.upper())
    if sales_ready is not None:
        q = q.where(Business.sales_ready == sales_ready)

    if has_phone:
        phone_sub = select(BusinessContact.entity_id).where(
            BusinessContact.contact_type == "PHONE"
        )
        q = q.where(Business.entity_id.in_(phone_sub))
    if has_email:
        email_sub = select(BusinessContact.entity_id).where(
            BusinessContact.contact_type == "EMAIL"
        )
        q = q.where(Business.entity_id.in_(email_sub))

    # Exclude DNC unless explicitly opted in (Req 13.3)
    if not include_dnc:
        dnc_sub = select(LeadFlag.entity_id).where(LeadFlag.flag_type == "DNC")
        q = q.where(Business.entity_id.not_in(dnc_sub))

    rows_result = await db.execute(q.order_by(Business.canonical_name))
    entities = rows_result.scalars().all()

    if format == "json":
        data = [
            {
                "entity_id": str(e.entity_id),
                "canonical_name": e.canonical_name,
                "legal_name": e.legal_name,
                "trade_name": e.trade_name,
                "province": e.province,
                "status": e.status,
                "sales_ready": e.sales_ready,
                "lead_quality_score": e.lead_quality_score,
                "first_seen_at": e.first_seen_at.isoformat() if e.first_seen_at else None,
                "last_verified_at": e.last_verified_at.isoformat() if e.last_verified_at else None,
            }
            for e in entities
        ]
        content = json.dumps(data, ensure_ascii=False, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=businesses.json"},
        )

    # CSV export
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "entity_id", "canonical_name", "legal_name", "trade_name",
            "province", "status", "sales_ready", "lead_quality_score",
            "first_seen_at", "last_verified_at",
        ],
    )
    writer.writeheader()
    for e in entities:
        writer.writerow(
            {
                "entity_id": str(e.entity_id),
                "canonical_name": e.canonical_name,
                "legal_name": e.legal_name or "",
                "trade_name": e.trade_name or "",
                "province": e.province or "",
                "status": e.status or "",
                "sales_ready": e.sales_ready,
                "lead_quality_score": e.lead_quality_score or "",
                "first_seen_at": e.first_seen_at.isoformat() if e.first_seen_at else "",
                "last_verified_at": e.last_verified_at.isoformat() if e.last_verified_at else "",
            }
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=businesses.csv"},
    )
