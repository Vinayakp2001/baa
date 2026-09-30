"""FastAPI routes for the enrichment service.

POST /enrich/directors  — batch director enrichment via Corporations Canada API
POST /enrich/orgbook    — targeted BC OrgBook identity/status enrichment
POST /enrich/website    — optional website phone extraction (low confidence)

All enriched fields carry enrichment_source, enriched_at, enrichment_confidence,
enrichment_run_id as required by Req 8.2.

Requirements: 8.2, 8.3, 8.9
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import bind_pipeline_context, get_logger
from ..db.session import get_db
from ..models.business import Business, BusinessContact
from ..models.provenance import FieldObservation
from ..models.source import IngestionRun
from ..normalisation.phone import normalise_phone
from .schemas import (
    EnrichDirectorsRequest,
    EnrichDirectorsResponse,
    EnrichOrgBookRequest,
    EnrichOrgBookResponse,
    EnrichWebsiteRequest,
    EnrichWebsiteResponse,
)

router = APIRouter(prefix="/enrich", tags=["enrichment"])
logger = get_logger(__name__)

_UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(_UTC)


async def _write_enrichment_observation(
    entity_id: uuid.UUID,
    field_name: str,
    raw_value: str,
    normalised_value: str | None,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    enrichment_source: str,
    confidence: str,
    db: AsyncSession,
) -> None:
    """Write one field_observation row, expiring any prior current value."""
    # Expire prior current observation for this field
    await db.execute(
        update(FieldObservation)
        .where(
            FieldObservation.entity_id == entity_id,
            FieldObservation.field_name == field_name,
            FieldObservation.is_current.is_(True),
        )
        .values(is_current=False)
    )
    db.add(
        FieldObservation(
            entity_id=entity_id,
            field_name=field_name,
            raw_value=raw_value,
            normalised_value=normalised_value,
            source_id=source_id,
            ingestion_run_id=ingestion_run_id,
            observed_at=_now(),
            confidence=confidence,
            is_current=True,
        )
    )


# ---------------------------------------------------------------------------
# POST /enrich/directors
# ---------------------------------------------------------------------------


@router.post("/directors", response_model=EnrichDirectorsResponse)
async def enrich_directors(
    request: EnrichDirectorsRequest,
    db: AsyncSession = Depends(get_db),
) -> EnrichDirectorsResponse:
    """Enrich federal CBCA corporations with director data from the Corporations Canada API.

    - Only submits valid corp_numbers (non-empty strings).
    - Respects 60 req/min rate limit via the adapter's token bucket.
    - Writes person rows with role_type=DIRECTOR.
    - Each director field stored with enrichment_source=corporations_canada_api.

    Requirements: 8.3, 8.4
    """
    from ..ingestion.adapters.corporations_canada_api import CorporationsCanadaAPIAdapter
    from ..models.business import Person

    api_key = os.environ.get("CORPS_CANADA_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="CORPS_CANADA_API_KEY not configured")

    bind_pipeline_context(run_id=str(request.run_id))
    logger.info("enrich_directors_start", corp_count=len(request.corp_numbers))

    # Filter to valid corp numbers only (Req 8.3)
    valid_corps = [c.strip() for c in request.corp_numbers if c and c.strip()]
    if not valid_corps:
        raise HTTPException(status_code=400, detail="No valid corp_numbers provided")

    adapter = CorporationsCanadaAPIAdapter(api_key=api_key)
    try:
        artifact = adapter.fetch(corp_numbers=valid_corps)
        records = adapter.parse(artifact)
    except Exception as exc:
        logger.error("enrich_directors_fetch_failed", error=str(exc))
        raise HTTPException(status_code=502, detail=f"Corporations Canada API error: {exc}") from exc

    directors_written = 0
    corps_not_found = 0

    for rec in records:
        payload = rec.raw_payload
        corp_number = payload.get("corp_number", "")
        full_name = payload.get("director_full_name", "")

        if payload.get("error") == "not_found" or not payload.get("directors", True) == []:
            # Stub record — corp not found or no directors
            if payload.get("http_status") == 404:
                corps_not_found += 1
            continue

        if not full_name:
            continue

        # Look up entity by corp_number identifier
        from ..models.business import BusinessIdentifier
        id_result = await db.execute(
            select(BusinessIdentifier).where(
                BusinessIdentifier.id_type == "CORP_NUMBER",
                BusinessIdentifier.id_value == corp_number,
            )
        )
        identifier = id_result.scalar_one_or_none()
        if not identifier:
            logger.warning("enrich_directors_no_entity", corp_number=corp_number)
            continue

        entity_id = identifier.entity_id

        # Upsert person row — avoid duplicate directors
        from ..models.business import Person as PersonModel
        existing = await db.execute(
            select(PersonModel).where(
                PersonModel.entity_id == entity_id,
                PersonModel.person_name == full_name,
                PersonModel.role_type == "DIRECTOR",
            )
        )
        if existing.scalar_one_or_none():
            continue  # already stored

        service_addr = payload.get("service_address", {})
        source_url = (
            f"https://api.ic.gc.ca/corporations-canada/v1/corporations/{corp_number}"
        )

        db.add(
            PersonModel(
                entity_id=entity_id,
                person_name=full_name,
                role_type="DIRECTOR",
                role_label_raw="Director",
                source_id=request.source_id,
                source_url=source_url,
                confidence="HIGH",
                verified_at=_now(),
            )
        )

        # Write field_observation for director presence
        await _write_enrichment_observation(
            entity_id=entity_id,
            field_name="director_name",
            raw_value=full_name,
            normalised_value=full_name,
            source_id=request.source_id,
            ingestion_run_id=request.run_id,
            enrichment_source="corporations_canada_api",
            confidence="HIGH",
            db=db,
        )
        directors_written += 1

    await db.commit()
    logger.info(
        "enrich_directors_complete",
        directors_written=directors_written,
        corps_not_found=corps_not_found,
    )
    return EnrichDirectorsResponse(
        run_id=request.run_id,
        corps_requested=len(valid_corps),
        directors_written=directors_written,
        corps_not_found=corps_not_found,
    )


# ---------------------------------------------------------------------------
# POST /enrich/orgbook
# ---------------------------------------------------------------------------


@router.post("/orgbook", response_model=EnrichOrgBookResponse)
async def enrich_orgbook(
    request: EnrichOrgBookRequest,
    db: AsyncSession = Depends(get_db),
) -> EnrichOrgBookResponse:
    """Enrich a BC entity with legal name, status, and registration date from OrgBook.

    Targeted lookup only — no enumeration (Req 3.6, 8.9).
    Stores: legal_name, status, registration_date, entity_type
    All with enrichment_source=bc_orgbook, confidence=MEDIUM.

    Requirements: 8.2, 8.9
    """
    from ..ingestion.adapters.bc_orgbook import BCOrgBookAPIAdapter

    if not request.bc_reg_id and not request.business_name:
        raise HTTPException(
            status_code=400, detail="Either bc_reg_id or business_name must be provided"
        )

    bind_pipeline_context(run_id=str(request.run_id), entity_id=str(request.entity_id))
    logger.info("enrich_orgbook_start", entity_id=str(request.entity_id))

    # Verify entity exists
    entity_result = await db.execute(
        select(Business).where(Business.entity_id == request.entity_id)
    )
    entity = entity_result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {request.entity_id} not found")

    target: dict
    if request.bc_reg_id:
        target = {"bc_reg_id": request.bc_reg_id}
    else:
        target = {"business_name": request.business_name}

    adapter = BCOrgBookAPIAdapter()
    try:
        artifact = adapter.fetch(lookup_targets=[target])
        records = adapter.parse(artifact)
    except Exception as exc:
        logger.error("enrich_orgbook_fetch_failed", error=str(exc))
        raise HTTPException(status_code=502, detail=f"BC OrgBook API error: {exc}") from exc

    if not records:
        logger.info("enrich_orgbook_no_results", entity_id=str(request.entity_id))
        return EnrichOrgBookResponse(
            run_id=request.run_id,
            entity_id=request.entity_id,
            enriched=False,
            fields_updated=[],
        )

    # Use first result (best match from autocomplete)
    rec = records[0]
    payload = rec.raw_payload
    fields_updated: list[str] = []

    field_map = [
        ("legal_name", payload.get("legal_name")),
        ("status", payload.get("status")),
        ("registration_date", payload.get("registration_date")),
        ("entity_type", payload.get("entity_type")),
    ]

    for field_name, value in field_map:
        if not value:
            continue
        await _write_enrichment_observation(
            entity_id=request.entity_id,
            field_name=field_name,
            raw_value=str(value),
            normalised_value=str(value),
            source_id=request.source_id,
            ingestion_run_id=request.run_id,
            enrichment_source="bc_orgbook",
            confidence="MEDIUM",
            db=db,
        )
        fields_updated.append(field_name)

    # Update business.status if OrgBook provides it
    if payload.get("status"):
        entity.status = payload["status"]
        entity.last_verified_at = _now()

    await db.commit()
    logger.info(
        "enrich_orgbook_complete",
        entity_id=str(request.entity_id),
        fields_updated=fields_updated,
    )
    return EnrichOrgBookResponse(
        run_id=request.run_id,
        entity_id=request.entity_id,
        enriched=bool(fields_updated),
        fields_updated=fields_updated,
    )


# ---------------------------------------------------------------------------
# POST /enrich/website  (optional — Req 8.6, 8.7, 8.8)
# ---------------------------------------------------------------------------


@router.post("/website", response_model=EnrichWebsiteResponse)
async def enrich_website(
    request: EnrichWebsiteRequest,
    db: AsyncSession = Depends(get_db),
) -> EnrichWebsiteResponse:
    """Optional website phone extraction.

    Crawls /contact and homepage of the provided domain for Canadian phone numbers.
    Applies CA NPA validation — only valid Canadian numbers are stored.
    Stored with source=website_crawl, confidence=LOW.

    This endpoint is optional — failure does NOT block any other pipeline step.

    Requirements: 8.6, 8.7, 8.8
    """
    import re

    import httpx

    bind_pipeline_context(run_id=str(request.run_id), entity_id=str(request.entity_id))

    # Verify entity exists
    entity_result = await db.execute(
        select(Business).where(Business.entity_id == request.entity_id)
    )
    entity = entity_result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {request.entity_id} not found")

    domain = request.domain.strip().lower().rstrip("/")
    if not domain:
        raise HTTPException(status_code=400, detail="domain must be provided")

    # Ensure scheme
    base_url = domain if domain.startswith("http") else f"https://{domain}"
    urls_to_try = [base_url, f"{base_url}/contact", f"{base_url}/contact-us"]

    # Naive phone regex — 10-digit Canadian patterns
    phone_pattern = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
    found_phones: set[str] = set()

    headers = {"User-Agent": "baa-pipeline/0.1 (canada-b2b-data)"}

    for url in urls_to_try:
        try:
            # Respect robots.txt before crawling (Req 15.7, 15.9)
            from ..core.compliance import robots_txt_allowed
            if not robots_txt_allowed(url):
                logger.info("website_crawl_robots_disallowed", url=url)
                continue
            async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    raw_phones = phone_pattern.findall(resp.text)
                    found_phones.update(raw_phones)
        except Exception:
            continue  # optional — never block on crawl failure

    phones_written = 0
    for raw_phone in found_phones:
        result = normalise_phone(raw_phone)
        if not result.phone_valid or not result.normalised_phone:
            continue  # discard invalid or non-CA phones (Req 8.6)

        # Check not already stored
        existing = await db.execute(
            select(BusinessContact).where(
                BusinessContact.entity_id == request.entity_id,
                BusinessContact.contact_type == "PHONE",
                BusinessContact.normalised_value == result.normalised_phone,
            )
        )
        if existing.scalar_one_or_none():
            continue

        db.add(
            BusinessContact(
                entity_id=request.entity_id,
                contact_type="PHONE",
                raw_value=raw_phone,
                normalised_value=result.normalised_phone,
                is_valid=True,
                source_id=request.source_id,
                enrichment_source="website_crawl",
                confidence="LOW",
                verified_at=_now(),
            )
        )
        await _write_enrichment_observation(
            entity_id=request.entity_id,
            field_name="phone",
            raw_value=raw_phone,
            normalised_value=result.normalised_phone,
            source_id=request.source_id,
            ingestion_run_id=request.run_id,
            enrichment_source="website_crawl",
            confidence="LOW",
            db=db,
        )
        phones_written += 1

    if phones_written:
        await db.commit()

    logger.info(
        "enrich_website_complete",
        entity_id=str(request.entity_id),
        domain=domain,
        phones_found=phones_written,
    )
    return EnrichWebsiteResponse(
        run_id=request.run_id,
        entity_id=request.entity_id,
        phones_found=phones_written,
        enriched=phones_written > 0,
    )
