"""Exact identifier matcher — Step 1 of the entity resolution pipeline.

Queries business_identifier for:
  a. federal corporation number (CORP_NUMBER)
  b. Business Number / BN (BN)
  c. source licence ID within the same source (LICENCE_ID)

Returns a HIGH-confidence match if any identifier matches exactly.

Requirements: 5.1a, 5.1b, 5.1c, 5.2
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.business import BusinessIdentifier
from ...normalisation.schemas import NormalisedRecord
from ..schemas import MatchConfidence, MatchResult


async def match_exact_identifier(
    record: NormalisedRecord,
    source_id: uuid.UUID,
    db: AsyncSession,
) -> MatchResult:
    """Query business_identifier for exact matches on strong identifiers.

    Priority order:
      1. corp_number  (CORP_NUMBER)
      2. business number / BN  (BN)
      3. source licence ID within same source  (LICENCE_ID)

    Returns MatchResult with confidence=HIGH if any identifier matches,
    otherwise returns MatchResult(matched=False).
    """
    extra = record.extra or {}

    # Build candidate (id_type, id_value, match_method) tuples
    candidates: list[tuple[str, str, str]] = []

    # 5.1a — federal corporation number
    corp_number = extra.get("corp_number") or extra.get("corp_no")
    if corp_number:
        candidates.append(("CORP_NUMBER", str(corp_number).strip(), "exact_corp_number"))

    # 5.1b — Business Number / BN
    bn = extra.get("business_number_bn") or extra.get("bn") or extra.get("business_number")
    if bn:
        candidates.append(("BN", str(bn).strip(), "exact_bn"))

    # 5.1c — source licence ID within the same source
    # The source_record_id is the source-provided licence/record identifier
    if record.source_record_id:
        candidates.append((
            "LICENCE_ID",
            str(record.source_record_id).strip(),
            "exact_licence_id_same_source",
        ))

    if not candidates:
        return MatchResult(matched=False)

    # Try each candidate in priority order — return first hit
    for id_type, id_value, method in candidates:
        stmt = select(BusinessIdentifier).where(
            BusinessIdentifier.id_type == id_type,
            BusinessIdentifier.id_value == id_value,
        )
        # For licence ID, scope to the same source to avoid cross-source collisions (5.1c)
        if id_type == "LICENCE_ID":
            stmt = stmt.where(BusinessIdentifier.source_id == source_id)

        result = await db.execute(stmt)
        identifier = result.scalar_one_or_none()

        if identifier is not None:
            return MatchResult(
                matched=True,
                entity_id=identifier.entity_id,
                confidence=MatchConfidence.HIGH,
                match_method=method,
                match_score=100.0,
            )

    return MatchResult(matched=False)
