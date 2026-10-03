"""Merge and entity creation logic for the entity resolution pipeline.

Handles all four outcomes of the resolution pipeline:
  - HIGH confidence  → auto-merge into existing entity
  - MEDIUM confidence → create merge_candidate, do NOT auto-merge
  - LOW confidence   → create new entity, link as merge_candidate
  - No match         → create new entity (resolution_status=NEW)

For every merged record, writes field_observation rows for every field.

Requirements: 5.3, 5.4, 5.5, 5.6, 5.7, 2.5
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.business import Business, BusinessContact, BusinessIdentifier, BusinessLocation
from ..models.events import MergeCandidate
from ..models.provenance import FieldObservation, SourceRecord
from ..normalisation.schemas import NormalisedRecord
from .schemas import MatchConfidence, MatchResult, ResolutionStatus

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

# Maps NormalisedRecord sub-fields to (field_name, raw_value, normalised_value)
# Only non-None values produce observation rows.
def _extract_field_observations(
    record: NormalisedRecord,
) -> list[tuple[str, str | None, str | None]]:
    """Return list of (field_name, raw_value, normalised_value) from a NormalisedRecord."""
    obs: list[tuple[str, str | None, str | None]] = []

    if record.name:
        if record.name.raw_legal_name or record.name.legal_name:
            obs.append(("legal_name", record.name.raw_legal_name, record.name.legal_name))
        if record.name.raw_trade_name or record.name.trade_name:
            obs.append(("trade_name", record.name.raw_trade_name, record.name.trade_name))

    if record.address:
        if record.address.raw_address or record.address.normalised_address:
            obs.append(("address", record.address.raw_address, record.address.normalised_address))
        if record.address.postal_code:
            obs.append(("postal_code", record.address.postal_code, record.address.postal_code))
        if record.address.city:
            obs.append(("city", record.address.city, record.address.city))
        if record.address.province:
            obs.append(("province", record.address.province, record.address.province))

    if record.phone:
        if record.phone.raw_phone or record.phone.normalised_phone:
            obs.append(("phone", record.phone.raw_phone, record.phone.normalised_phone))

    if record.email:
        if record.email.raw_email or record.email.normalised_email:
            obs.append(("email", record.email.raw_email, record.email.normalised_email))

    if record.website:
        if record.website.raw_url or record.website.normalised_domain:
            obs.append(("website", record.website.raw_url, record.website.normalised_domain))

    if record.status:
        if record.status.raw_status or record.status.canonical_status:
            obs.append(("status", record.status.raw_status, record.status.canonical_status))

    if record.employee:
        if record.employee.raw_employee_value:
            obs.append((
                "employee_value",
                record.employee.raw_employee_value,
                record.employee.employee_bucket,
            ))

    if record.naics:
        if record.naics.source_naics or record.naics.naics_sector:
            obs.append(("naics", record.naics.source_naics, record.naics.naics_sector))

    if record.issued_date:
        obs.append(("issued_date", record.issued_date, record.issued_date))

    if record.incorporation_date:
        obs.append(("incorporation_date", record.incorporation_date, record.incorporation_date))

    # Pass-through extra fields (e.g. corp_number)
    if record.extra:
        for k, v in record.extra.items():
            if v is not None:
                obs.append((f"extra.{k}", str(v), str(v)))

    return obs


# ---------------------------------------------------------------------------
# Field observation writer
# ---------------------------------------------------------------------------

async def _write_field_observations(
    entity_id: uuid.UUID,
    record: NormalisedRecord,
    source_record_db_id: uuid.UUID,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    confidence: MatchConfidence | None,
    db: AsyncSession,
    expire_current: bool = True,
) -> int:
    """Write a field_observation row for every non-null field in the record.

    Marks prior observations for the same entity+field as is_current=False
    before inserting the new observation, preserving full history (Req 2.5, 2.6).
    """
    from sqlalchemy import update
    from ..models.provenance import FieldObservation

    fields = _extract_field_observations(record)
    now = datetime.now(timezone.utc)
    written = 0

    for field_name, raw_value, normalised_value in fields:
        if raw_value is None and normalised_value is None:
            continue

        if expire_current:
            await db.execute(
                update(FieldObservation)
                .where(
                    FieldObservation.entity_id == entity_id,
                    FieldObservation.field_name == field_name,
                    FieldObservation.is_current.is_(True),
                )
                .values(is_current=False)
            )

        obs = FieldObservation(
            entity_id=entity_id,
            field_name=field_name,
            raw_value=str(raw_value) if raw_value is not None else None,
            normalised_value=str(normalised_value) if normalised_value is not None else None,
            source_id=source_id,
            ingestion_run_id=ingestion_run_id,
            source_record_id=source_record_db_id,
            observed_at=now,
            confidence=confidence.value if confidence else None,
            is_current=True,
        )
        db.add(obs)
        written += 1

    return written


# ---------------------------------------------------------------------------
# Entity creation helper
# ---------------------------------------------------------------------------

def _build_new_business(record: NormalisedRecord) -> Business:
    """Create a new Business ORM object from a NormalisedRecord."""
    legal_name = record.name.legal_name if record.name else None
    trade_name = record.name.trade_name if record.name else None
    canonical_name = legal_name or trade_name or record.source_key
    province = record.address.province if record.address else None
    status_val = record.status.canonical_status if record.status else "UNKNOWN"

    return Business(
        canonical_name=canonical_name,
        legal_name=legal_name,
        trade_name=trade_name,
        province=province,
        status=status_val,
    )


async def _add_identifiers(
    entity_id: uuid.UUID,
    record: NormalisedRecord,
    source_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Store strong identifiers for a newly created entity."""
    extra = record.extra or {}

    id_pairs: list[tuple[str, str]] = []
    corp_number = extra.get("corp_number") or extra.get("corp_no")
    if corp_number:
        id_pairs.append(("CORP_NUMBER", str(corp_number).strip()))

    bn = extra.get("business_number_bn") or extra.get("bn") or extra.get("business_number")
    if bn:
        id_pairs.append(("BN", str(bn).strip()))

    source_licence_id = (
        extra.get("externalid") or extra.get("external_id")
        if record.source_key == "edmonton"
        else None
    )
    if source_licence_id:
        id_pairs.append(("LICENCE_ID", str(source_licence_id).strip()))

    if record.source_record_id:
        id_pairs.append(("LICENCE_ID", str(record.source_record_id).strip()))

    for id_type, id_value in id_pairs:
        db.add(BusinessIdentifier(
            entity_id=entity_id,
            id_type=id_type,
            id_value=id_value,
            source_id=source_id,
        ))


async def _add_location(
    entity_id: uuid.UUID,
    record: NormalisedRecord,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Store primary location from a NormalisedRecord."""
    if not record.address:
        return
    addr = record.address
    db.add(BusinessLocation(
        entity_id=entity_id,
        address_line1=addr.address_line1,
        address_line2=addr.address_line2,
        city=addr.city,
        province=addr.province,
        postal_code=addr.postal_code,
        raw_address=addr.raw_address,
        is_primary=True,
        location_type="OPERATING",
        source_id=source_id,
        ingestion_run_id=ingestion_run_id,
    ))


async def _add_contacts(
    entity_id: uuid.UUID,
    record: NormalisedRecord,
    source_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Store phone, email, and website contacts from a NormalisedRecord."""
    if record.phone and (record.phone.raw_phone or record.phone.normalised_phone):
        db.add(BusinessContact(
            entity_id=entity_id,
            contact_type="PHONE",
            raw_value=record.phone.raw_phone or "",
            normalised_value=record.phone.normalised_phone,
            is_valid=record.phone.phone_valid,
            source_id=source_id,
            confidence="HIGH" if record.phone.phone_valid else "LOW",
        ))

    if record.email and (record.email.raw_email or record.email.normalised_email):
        db.add(BusinessContact(
            entity_id=entity_id,
            contact_type="EMAIL",
            raw_value=record.email.raw_email or "",
            normalised_value=record.email.normalised_email,
            is_valid=record.email.email_valid,
            source_id=source_id,
            confidence="HIGH" if record.email.email_valid else "LOW",
        ))

    if record.website and (record.website.raw_url or record.website.normalised_domain):
        db.add(BusinessContact(
            entity_id=entity_id,
            contact_type="WEBSITE",
            raw_value=record.website.raw_url or "",
            normalised_value=record.website.normalised_domain,
            is_valid=record.website.url_valid,
            source_id=source_id,
            confidence="MEDIUM",
        ))


# ---------------------------------------------------------------------------
# Public resolution functions
# ---------------------------------------------------------------------------

async def merge_high_confidence(
    record: NormalisedRecord,
    match: MatchResult,
    source_record_row: SourceRecord,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    """AUTO-MERGE: link source_record to existing entity, write field_observations.

    Requirements: 5.3
    """
    assert match.entity_id is not None
    entity_id = match.entity_id

    # Update source_record to link this entity and mark resolution
    source_record_row.entity_id = entity_id
    source_record_row.resolution_status = ResolutionStatus.MATCHED.value
    source_record_row.resolution_confidence = MatchConfidence.HIGH.value

    obs_count = await _write_field_observations(
        entity_id=entity_id,
        record=record,
        source_record_db_id=source_record_row.record_id,
        source_id=source_id,
        ingestion_run_id=ingestion_run_id,
        confidence=MatchConfidence.HIGH,
        db=db,
    )

    logger.info(
        "entity_merged_high",
        entity_id=str(entity_id),
        method=match.match_method,
        observations=obs_count,
    )
    return obs_count


async def queue_medium_confidence(
    record: NormalisedRecord,
    match: MatchResult,
    source_record_row: SourceRecord,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[uuid.UUID, int]:
    """MEDIUM: create a new entity stub + merge_candidate, do NOT auto-merge.

    The new entity is created from the inbound record. The merge_candidate
    links new entity (B) to the existing candidate (A) for operator review.

    Requirements: 5.4
    """
    assert match.entity_id is not None

    # Create new entity for the inbound record
    new_business = _build_new_business(record)
    db.add(new_business)
    await db.flush()  # populate entity_id

    new_entity_id = new_business.entity_id

    await _add_identifiers(new_entity_id, record, source_id, db)
    await _add_location(new_entity_id, record, source_id, ingestion_run_id, db)
    await _add_contacts(new_entity_id, record, source_id, db)

    # Link source_record to new entity, mark as CANDIDATE — not MATCHED
    source_record_row.entity_id = new_entity_id
    source_record_row.resolution_status = ResolutionStatus.CANDIDATE.value
    source_record_row.resolution_confidence = MatchConfidence.MEDIUM.value

    # Create merge_candidate for operator review
    candidate = MergeCandidate(
        entity_id_a=match.entity_id,   # existing entity
        entity_id_b=new_entity_id,     # new entity from this record
        confidence=MatchConfidence.MEDIUM.value,
        match_method=match.match_method,
        match_score=match.match_score,
        auto_resolved=False,
    )
    db.add(candidate)

    obs_count = await _write_field_observations(
        entity_id=new_entity_id,
        record=record,
        source_record_db_id=source_record_row.record_id,
        source_id=source_id,
        ingestion_run_id=ingestion_run_id,
        confidence=MatchConfidence.MEDIUM,
        db=db,
        expire_current=False,
    )

    logger.info(
        "entity_candidate_medium",
        new_entity_id=str(new_entity_id),
        existing_entity_id=str(match.entity_id),
        method=match.match_method,
        score=match.match_score,
    )
    return new_entity_id, obs_count


async def create_with_low_confidence_candidate(
    record: NormalisedRecord,
    match: MatchResult,
    source_record_row: SourceRecord,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[uuid.UUID, int]:
    """LOW: create new entity + merge_candidate with auto_resolved=False.

    Requirements: 5.5
    """
    assert match.entity_id is not None

    new_business = _build_new_business(record)
    db.add(new_business)
    await db.flush()

    new_entity_id = new_business.entity_id

    await _add_identifiers(new_entity_id, record, source_id, db)
    await _add_location(new_entity_id, record, source_id, ingestion_run_id, db)
    await _add_contacts(new_entity_id, record, source_id, db)

    source_record_row.entity_id = new_entity_id
    source_record_row.resolution_status = ResolutionStatus.NEW.value
    source_record_row.resolution_confidence = MatchConfidence.LOW.value

    candidate = MergeCandidate(
        entity_id_a=match.entity_id,
        entity_id_b=new_entity_id,
        confidence=MatchConfidence.LOW.value,
        match_method=match.match_method,
        match_score=match.match_score,
        auto_resolved=False,
    )
    db.add(candidate)

    obs_count = await _write_field_observations(
        entity_id=new_entity_id,
        record=record,
        source_record_db_id=source_record_row.record_id,
        source_id=source_id,
        ingestion_run_id=ingestion_run_id,
        confidence=MatchConfidence.LOW,
        db=db,
        expire_current=False,
    )

    logger.info(
        "entity_new_low_confidence",
        new_entity_id=str(new_entity_id),
        fuzzy_match_entity=str(match.entity_id),
        score=match.match_score,
    )
    return new_entity_id, obs_count


async def create_new_entity(
    record: NormalisedRecord,
    source_record_row: SourceRecord,
    source_id: uuid.UUID,
    ingestion_run_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[uuid.UUID, int]:
    """NO MATCH: create a brand-new canonical entity.

    Requirements: 5.3 (no-match branch), 5.6, 5.7
    """
    new_business = _build_new_business(record)
    db.add(new_business)
    await db.flush()

    new_entity_id = new_business.entity_id

    await _add_identifiers(new_entity_id, record, source_id, db)
    await _add_location(new_entity_id, record, source_id, ingestion_run_id, db)
    await _add_contacts(new_entity_id, record, source_id, db)

    source_record_row.entity_id = new_entity_id
    source_record_row.resolution_status = ResolutionStatus.NEW.value
    source_record_row.resolution_confidence = None

    obs_count = await _write_field_observations(
        entity_id=new_entity_id,
        record=record,
        source_record_db_id=source_record_row.record_id,
        source_id=source_id,
        ingestion_run_id=ingestion_run_id,
        confidence=None,
        db=db,
        expire_current=False,
    )

    logger.info("entity_created_new", entity_id=str(new_entity_id))
    return new_entity_id, obs_count
