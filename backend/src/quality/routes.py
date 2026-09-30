"""FastAPI routes for the quality scoring service.

POST /quality/score  — compute all confidence components + composite score,
                       upsert business_quality_score, update business.lead_quality_score
                       and business.sales_ready.

Requirements: 9.1, 9.2, 9.3
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..db.session import get_db
from ..models.quality import LeadFlag
from ..models.business import (
    Business,
    BusinessContact,
    BusinessEmployeeData,
    BusinessIdentifier,
    BusinessIndustry,
    BusinessLocation,
    Person,
)
from ..models.provenance import SourceRecord
from ..models.quality import BusinessQualityScore
from ..models.source import Source
from .schemas import EntityScoreResult, ScoreRequest, ScoreResponse
from .scoring import (
    compute_composite_score,
    is_sales_ready,
    score_address,
    score_contact,
    score_email,
    score_employee,
    score_identity,
    score_industry,
    score_phone,
    score_recency,
    score_source_reliability,
)

router = APIRouter(prefix="/quality", tags=["quality"])
logger = get_logger(__name__)

_UTC = timezone.utc


@router.post("/score", response_model=ScoreResponse)
async def score_entities(
    request: ScoreRequest,
    db: AsyncSession = Depends(get_db),
) -> ScoreResponse:
    """Compute quality scores for a batch of entities.

    For each entity:
    1. Loads all sub-objects needed for scoring (contacts, identifiers, locations,
       employees, industries, persons, source_records).
    2. Computes each confidence component via scoring.py functions.
    3. Computes composite lead_quality_score.
    4. Evaluates sales_ready threshold.
    5. Upserts business_quality_score row.
    6. Updates business.lead_quality_score and business.sales_ready.

    Requirements: 9.1, 9.2, 9.3
    """
    entity_ids = request.entity_ids
    if request.ingestion_run_id is not None:
        entity_result = await db.execute(
            select(SourceRecord.entity_id)
            .where(
                SourceRecord.ingestion_run_id == request.ingestion_run_id,
                SourceRecord.entity_id.is_not(None),
            )
            .distinct()
            .order_by(SourceRecord.entity_id)
        )
        entity_ids = [row[0] for row in entity_result.all()]

    results: list[EntityScoreResult] = []

    for entity_id in entity_ids:
        # Load entity
        entity_result = await db.execute(
            select(Business).where(Business.entity_id == entity_id)
        )
        entity = entity_result.scalar_one_or_none()
        if entity is None:
            logger.warning("quality_score_entity_not_found", entity_id=str(entity_id))
            continue

        # Load related data
        contacts_result = await db.execute(
            select(BusinessContact).where(BusinessContact.entity_id == entity_id)
        )
        contacts = contacts_result.scalars().all()

        identifiers_result = await db.execute(
            select(BusinessIdentifier).where(BusinessIdentifier.entity_id == entity_id)
        )
        identifiers = identifiers_result.scalars().all()

        locations_result = await db.execute(
            select(BusinessLocation).where(BusinessLocation.entity_id == entity_id)
        )
        locations = locations_result.scalars().all()

        employees_result = await db.execute(
            select(BusinessEmployeeData).where(BusinessEmployeeData.entity_id == entity_id)
        )
        employees = employees_result.scalars().all()

        industries_result = await db.execute(
            select(BusinessIndustry).where(BusinessIndustry.entity_id == entity_id)
        )
        industries = industries_result.scalars().all()

        persons_result = await db.execute(
            select(Person).where(Person.entity_id == entity_id)
        )
        persons = persons_result.scalars().all()

        # Fetch source classes for source_reliability
        source_records_result = await db.execute(
            select(SourceRecord.source_id).where(SourceRecord.entity_id == entity_id).distinct()
        )
        source_ids = [row[0] for row in source_records_result.all()]

        source_classes: list[str] = []
        if source_ids:
            sources_result = await db.execute(
                select(Source.source_class).where(Source.source_id.in_(source_ids))
            )
            source_classes = [row[0] for row in sources_result.all()]

        # --- Derive booleans for scoring ---
        id_types = {i.id_type for i in identifiers}
        has_corp_number = "CORP_NUMBER" in id_types
        has_bn = "BN" in id_types

        primary_location = next((l for l in locations if l.is_primary), None) or (
            locations[0] if locations else None
        )
        has_coordinates = bool(
            primary_location
            and primary_location.latitude is not None
            and primary_location.longitude is not None
        )

        phones = [c for c in contacts if c.contact_type == "PHONE"]
        emails = [c for c in contacts if c.contact_type == "EMAIL"]
        websites = [c for c in contacts if c.contact_type == "WEBSITE"]

        has_phone = bool(phones)
        has_email = bool(emails)
        has_website = bool(websites)

        phone_valid = any(c.is_valid for c in phones) if phones else None
        email_valid = any(c.is_valid for c in emails) if emails else None

        # Best phone/email source class
        phone_source_class = phones[0].confidence if phones else None
        email_source_class = emails[0].confidence if emails else None

        has_employee_data = bool(employees)
        employee_exact = any(e.employee_exact for e in employees) if employees else False

        has_naics = any(i.source_naics for i in industries)
        has_naics_sector = any(i.naics_sector for i in industries)

        directors = [p for p in persons if p.role_type == "DIRECTOR"]
        has_primary_contact = any(
            p.role_type in ("PRIMARY_CONTACT", "GENERAL_MANAGER", "PRESIDENT")
            for p in persons
        )
        has_director = bool(directors)

        # --- Compute components ---
        identity = score_identity(
            canonical_name=entity.canonical_name,
            legal_name=entity.legal_name,
            entity_type=entity.entity_type,
            has_corp_number=has_corp_number,
            has_bn=has_bn,
        )

        address = score_address(
            address_line1=primary_location.address_line1 if primary_location else None,
            city=primary_location.city if primary_location else None,
            province=primary_location.province if primary_location else entity.province,
            postal_code=primary_location.postal_code if primary_location else None,
            postal_valid=None,  # not stored on location; normalised during ingestion
            has_coordinates=has_coordinates,
        )

        phone_score = score_phone(
            has_phone=has_phone,
            phone_valid=phone_valid,
            source_class=phone_source_class,
        )

        email_score = score_email(
            has_email=has_email,
            email_valid=email_valid,
            source_class=email_source_class,
        )

        employee_score = score_employee(
            has_employee_data=has_employee_data,
            employee_exact=employee_exact,
        )

        industry_score = score_industry(
            has_naics=has_naics,
            has_naics_sector=has_naics_sector,
        )

        contact_score = score_contact(
            director_count=len(directors),
            has_primary_contact=has_primary_contact,
        )

        recency = score_recency(last_verified_at=entity.last_verified_at)

        reliability = score_source_reliability(source_classes=source_classes)

        composite = compute_composite_score(
            identity=identity,
            address=address,
            phone=phone_score,
            email=email_score,
            employee=employee_score,
            industry=industry_score,
            contact=contact_score,
            recency=recency,
            source_reliability=reliability,
        )

        sales_ready = is_sales_ready(
            canonical_name=entity.canonical_name,
            address_line1=primary_location.address_line1 if primary_location else None,
            province=primary_location.province if primary_location else entity.province,
            status=entity.status,
            has_phone=has_phone,
            has_email=has_email,
            has_website=has_website,
            has_director=has_director,
        )

        # DNC disqualifier — if a DNC flag exists, override sales_ready to False.
        # The disqualifier is NOT stored in the quality model (Req 13.4).
        dnc_result = await db.execute(
            select(LeadFlag.flag_id).where(
                LeadFlag.entity_id == entity_id,
                LeadFlag.flag_type == "DNC",
            ).limit(1)
        )
        if dnc_result.scalar_one_or_none():
            sales_ready = False

        # --- Upsert business_quality_score ---
        await db.execute(
            pg_insert(BusinessQualityScore)
            .values(
                entity_id=entity_id,
                identity_confidence=identity,
                address_confidence=address,
                phone_confidence=phone_score,
                email_confidence=email_score,
                employee_confidence=employee_score,
                industry_confidence=industry_score,
                contact_confidence=contact_score,
                recency_confidence=recency,
                source_reliability=reliability,
                lead_quality_score=composite,
                scored_at=datetime.now(_UTC),
            )
            .on_conflict_do_update(
                index_elements=["entity_id"],
                set_={
                    "identity_confidence": identity,
                    "address_confidence": address,
                    "phone_confidence": phone_score,
                    "email_confidence": email_score,
                    "employee_confidence": employee_score,
                    "industry_confidence": industry_score,
                    "contact_confidence": contact_score,
                    "recency_confidence": recency,
                    "source_reliability": reliability,
                    "lead_quality_score": composite,
                    "scored_at": datetime.now(_UTC),
                },
            )
        )

        # Update denormalised fields on business
        entity.lead_quality_score = composite
        entity.sales_ready = sales_ready
        entity.updated_at = datetime.now(_UTC)

        results.append(
            EntityScoreResult(
                entity_id=entity_id,
                identity_confidence=identity,
                address_confidence=address,
                phone_confidence=phone_score,
                email_confidence=email_score,
                employee_confidence=employee_score,
                industry_confidence=industry_score,
                contact_confidence=contact_score,
                recency_confidence=recency,
                source_reliability=reliability,
                lead_quality_score=composite,
                sales_ready=sales_ready,
            )
        )

    await db.commit()
    logger.info("quality_scoring_complete", entities_scored=len(results))
    return ScoreResponse(entities_scored=len(results), results=results)
