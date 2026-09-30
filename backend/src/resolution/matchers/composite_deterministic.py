"""Composite deterministic matcher — Step 2 of the entity resolution pipeline.

Attempts three deterministic compound matches in priority order:
  d. normalised_domain + postal_code
  e. normalised_phone + postal_code
  f. normalised_name + normalised_address

Queries indexed columns in business and business_contact tables.
Returns a MEDIUM-confidence match if any combination matches exactly.

Requirements: 5.1d, 5.1e, 5.1f, 5.2
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.business import Business, BusinessContact, BusinessLocation
from ...normalisation.schemas import NormalisedRecord
from ..schemas import MatchConfidence, MatchResult


async def match_composite_deterministic(
    record: NormalisedRecord,
    db: AsyncSession,
) -> MatchResult:
    """Attempt compound deterministic matches in priority order d → e → f.

    Returns MatchResult with confidence=MEDIUM on first hit,
    or MatchResult(matched=False) if nothing matches.
    """

    # 5.1d — domain + postal_code
    result = await _match_domain_postal(record, db)
    if result.matched:
        return result

    # 5.1e — phone + postal_code
    result = await _match_phone_postal(record, db)
    if result.matched:
        return result

    # 5.1f — normalised_name + normalised_address
    result = await _match_name_address(record, db)
    if result.matched:
        return result

    return MatchResult(matched=False)


async def _match_domain_postal(
    record: NormalisedRecord,
    db: AsyncSession,
) -> MatchResult:
    """Match on normalised_domain + postal_code (Req 5.1d)."""
    domain = record.website.normalised_domain if record.website else None
    postal = record.address.postal_code if record.address else None

    if not domain or not postal:
        return MatchResult(matched=False)

    # Find a business_contact row (WEBSITE) with matching domain, then join
    # to business_location to confirm matching postal code.
    stmt = (
        select(BusinessContact.entity_id)
        .join(BusinessLocation, BusinessLocation.entity_id == BusinessContact.entity_id)
        .where(
            BusinessContact.contact_type == "WEBSITE",
            BusinessContact.normalised_value == domain,
            BusinessLocation.postal_code == postal,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    entity_id = result.scalar_one_or_none()

    if entity_id is not None:
        return MatchResult(
            matched=True,
            entity_id=entity_id,
            confidence=MatchConfidence.MEDIUM,
            match_method="domain_postal",
            match_score=90.0,
        )
    return MatchResult(matched=False)


async def _match_phone_postal(
    record: NormalisedRecord,
    db: AsyncSession,
) -> MatchResult:
    """Match on normalised_phone + postal_code (Req 5.1e)."""
    phone = record.phone.normalised_phone if record.phone else None
    postal = record.address.postal_code if record.address else None

    if not phone or not postal:
        return MatchResult(matched=False)

    stmt = (
        select(BusinessContact.entity_id)
        .join(BusinessLocation, BusinessLocation.entity_id == BusinessContact.entity_id)
        .where(
            BusinessContact.contact_type == "PHONE",
            BusinessContact.normalised_value == phone,
            BusinessLocation.postal_code == postal,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    entity_id = result.scalar_one_or_none()

    if entity_id is not None:
        return MatchResult(
            matched=True,
            entity_id=entity_id,
            confidence=MatchConfidence.MEDIUM,
            match_method="phone_postal",
            match_score=85.0,
        )
    return MatchResult(matched=False)


async def _match_name_address(
    record: NormalisedRecord,
    db: AsyncSession,
) -> MatchResult:
    """Match on normalised_name + normalised_address (Req 5.1f)."""
    legal_name = record.name.legal_name if record.name else None
    trade_name = record.name.trade_name if record.name else None
    # Use whichever name is available; prefer legal_name
    normalised_name = legal_name or trade_name
    normalised_address = record.address.normalised_address if record.address else None

    if not normalised_name or not normalised_address:
        return MatchResult(matched=False)

    # Match canonical_name or legal_name or trade_name against normalised_name,
    # combined with normalised address from business_location.raw_address.
    stmt = (
        select(Business.entity_id)
        .join(BusinessLocation, BusinessLocation.entity_id == Business.entity_id)
        .where(
            # Check canonical, legal, and trade name columns (any may match)
            (Business.canonical_name == normalised_name)
            | (Business.legal_name == normalised_name)
            | (Business.trade_name == normalised_name),
            BusinessLocation.raw_address == normalised_address,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    entity_id = result.scalar_one_or_none()

    if entity_id is not None:
        return MatchResult(
            matched=True,
            entity_id=entity_id,
            confidence=MatchConfidence.MEDIUM,
            match_method="name_address",
            match_score=80.0,
        )
    return MatchResult(matched=False)
