"""Fuzzy matcher — Step 3 of the entity resolution pipeline.

Uses RapidFuzz token_sort_ratio on normalised_name + postal_code
against the candidate set of existing businesses in the same province/postal area.

Default threshold: 88 (configurable via env var FUZZY_MATCH_THRESHOLD).
Returns a LOW-confidence match if the best score meets the threshold.

Requirements: 5.1g, 5.2
"""

from __future__ import annotations

import os

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.business import Business, BusinessLocation
from ...normalisation.schemas import NormalisedRecord
from ..schemas import MatchConfidence, MatchResult

# Configurable threshold — default 88 per design doc
_DEFAULT_THRESHOLD = 88


def _get_threshold() -> int:
    try:
        return int(os.environ.get("FUZZY_MATCH_THRESHOLD", _DEFAULT_THRESHOLD))
    except (TypeError, ValueError):
        return _DEFAULT_THRESHOLD


def _build_match_key(name: str, postal: str) -> str:
    """Concatenate normalised name and postal for fuzzy comparison."""
    return f"{name.lower().strip()} {postal.upper().strip()}"


async def match_fuzzy(
    record: NormalisedRecord,
    db: AsyncSession,
) -> MatchResult:
    """Run fuzzy token_sort_ratio match on name + postal_code (Req 5.1g).

    Fetches candidate businesses sharing the same postal code prefix (first
    3 characters — the FSA) to keep the comparison set manageable, then
    applies RapidFuzz token_sort_ratio against the full key.

    Returns MatchResult with confidence=LOW on best match above threshold,
    or MatchResult(matched=False) if no candidate meets the threshold.
    """
    legal_name = record.name.legal_name if record.name else None
    trade_name = record.name.trade_name if record.name else None
    normalised_name = legal_name or trade_name
    postal = record.address.postal_code if record.address else None

    if not normalised_name or not postal:
        return MatchResult(matched=False)

    threshold = _get_threshold()
    query_key = _build_match_key(normalised_name, postal)

    # Narrow candidate set to businesses in the same FSA (first 3 chars of postal)
    fsa = postal[:3].upper()
    stmt = (
        select(Business.entity_id, Business.canonical_name, Business.legal_name, Business.trade_name)
        .join(BusinessLocation, BusinessLocation.entity_id == Business.entity_id)
        .where(BusinessLocation.postal_code.like(f"{fsa}%"))
        .distinct()
    )
    result = await db.execute(stmt)
    candidates = result.all()

    if not candidates:
        return MatchResult(matched=False)

    best_score = 0.0
    best_entity_id = None

    for row in candidates:
        # Build candidate key using whichever name is available
        candidate_name = row.legal_name or row.trade_name or row.canonical_name or ""
        candidate_key = _build_match_key(candidate_name, postal)
        score = fuzz.token_sort_ratio(query_key, candidate_key)

        if score > best_score:
            best_score = score
            best_entity_id = row.entity_id

    if best_score >= threshold and best_entity_id is not None:
        return MatchResult(
            matched=True,
            entity_id=best_entity_id,
            confidence=MatchConfidence.LOW,
            match_method="fuzzy_name_postal",
            match_score=round(best_score, 2),
        )

    return MatchResult(matched=False)
