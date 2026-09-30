"""Individual confidence score calculators for the quality scoring service.

Each function returns an integer 0–100 representing confidence for one component.
The composite lead_quality_score is derived from weighted components.

Component weights (documented, deterministic — Req 9.2):
  identity    × 0.25
  address     × 0.20
  phone       × 0.15
  email       × 0.10
  contact     × 0.10
  recency     × 0.10
  employee    × 0.05
  industry    × 0.05

sales_ready threshold (Req 9.3):
  business_name + address + province + status=ACTIVE
  + at least one of (phone | email | website | director_name)

Requirements: 9.1, 9.2, 9.3
"""

from __future__ import annotations

from datetime import datetime, timezone

_UTC = timezone.utc

# Source class reliability weights (Req 9.1 — source_reliability component)
_SOURCE_CLASS_WEIGHTS: dict[str, int] = {
    "A": 100,  # primary discovery (federal CSV, municipal licences)
    "B": 70,   # event-only (Winnipeg, Manitoba PDF)
    "C": 85,   # enrichment (Corp Canada API, BC OrgBook, BC Indigenous)
    "D": 0,    # statistical only — StatsCan (never individual records)
}

# Days thresholds for recency_confidence
_RECENCY_THRESHOLDS = [
    (30, 100),
    (90, 80),
    (180, 60),
    (365, 40),
    (730, 20),
]


def score_identity(
    canonical_name: str | None,
    legal_name: str | None,
    entity_type: str | None,
    has_corp_number: bool,
    has_bn: bool,
) -> int:
    """Score identity completeness and consistency (0–100).

    Full score requires: name, entity_type, at least one strong identifier.
    """
    score = 0
    if canonical_name:
        score += 40
    if legal_name:
        score += 20
    if entity_type:
        score += 10
    if has_corp_number:
        score += 20
    elif has_bn:
        score += 10
    return min(score, 100)


def score_address(
    address_line1: str | None,
    city: str | None,
    province: str | None,
    postal_code: str | None,
    postal_valid: bool | None,
    has_coordinates: bool,
) -> int:
    """Score address completeness and postal validity (0–100)."""
    score = 0
    if address_line1:
        score += 30
    if city:
        score += 20
    if province:
        score += 20
    if postal_code:
        score += 15
        if postal_valid:
            score += 10
    if has_coordinates:
        score += 5
    return min(score, 100)


def score_phone(
    has_phone: bool,
    phone_valid: bool | None,
    source_class: str | None,
) -> int:
    """Score phone presence, validity, and source reliability (0–100)."""
    if not has_phone:
        return 0
    score = 40
    if phone_valid:
        score += 40
    reliability = _SOURCE_CLASS_WEIGHTS.get(source_class or "", 50)
    score += int(reliability * 0.20)
    return min(score, 100)


def score_email(
    has_email: bool,
    email_valid: bool | None,
    source_class: str | None,
) -> int:
    """Score email presence, validity, and source reliability (0–100)."""
    if not has_email:
        return 0
    score = 40
    if email_valid:
        score += 40
    reliability = _SOURCE_CLASS_WEIGHTS.get(source_class or "", 50)
    score += int(reliability * 0.20)
    return min(score, 100)


def score_employee(
    has_employee_data: bool,
    employee_exact: bool,
) -> int:
    """Score employee data presence and precision (0–100)."""
    if not has_employee_data:
        return 0
    return 100 if employee_exact else 60


def score_industry(
    has_naics: bool,
    has_naics_sector: bool,
) -> int:
    """Score industry classification completeness (0–100)."""
    if has_naics:
        return 100
    if has_naics_sector:
        return 60
    return 0


def score_contact(
    director_count: int,
    has_primary_contact: bool,
) -> int:
    """Score presence of any person/director record (0–100)."""
    if director_count > 0:
        return min(60 + director_count * 10, 100)
    if has_primary_contact:
        return 40
    return 0


def score_recency(last_verified_at: datetime | None) -> int:
    """Score how recently the entity was verified (0–100)."""
    if last_verified_at is None:
        return 0
    now = datetime.now(_UTC)
    if last_verified_at.tzinfo is None:
        last_verified_at = last_verified_at.replace(tzinfo=_UTC)
    days_ago = (now - last_verified_at).days
    for threshold, points in _RECENCY_THRESHOLDS:
        if days_ago <= threshold:
            return points
    return 10


def score_source_reliability(source_classes: list[str]) -> int:
    """Score the reliability of contributing sources (0–100).

    Uses the highest-class source that contributed to the entity.
    """
    if not source_classes:
        return 0
    best = max(
        (_SOURCE_CLASS_WEIGHTS.get(cls, 0) for cls in source_classes),
        default=0,
    )
    return best


def compute_composite_score(
    identity: int | None,
    address: int | None,
    phone: int | None,
    email: int | None,
    employee: int | None,
    industry: int | None,
    contact: int | None,
    recency: int | None,
    source_reliability: int | None,
) -> int:
    """Compute the composite lead_quality_score from components.

    Weights (documented, deterministic — Req 9.2):
      identity    0.25
      address     0.20
      phone       0.15
      email       0.10
      contact     0.10
      recency     0.10
      employee    0.05
      industry    0.05

    source_reliability is factored as a multiplier (0.8–1.0) on the composite.
    """
    weighted = (
        (identity or 0) * 0.25
        + (address or 0) * 0.20
        + (phone or 0) * 0.15
        + (email or 0) * 0.10
        + (contact or 0) * 0.10
        + (recency or 0) * 0.10
        + (employee or 0) * 0.05
        + (industry or 0) * 0.05
    )
    # source_reliability scales composite: 100→×1.0, 70→×0.85, 0→×0.70
    reliability = source_reliability or 50
    multiplier = 0.70 + (reliability / 100.0) * 0.30
    return min(int(round(weighted * multiplier)), 100)


def is_sales_ready(
    canonical_name: str | None,
    address_line1: str | None,
    province: str | None,
    status: str | None,
    has_phone: bool,
    has_email: bool,
    has_website: bool,
    has_director: bool,
) -> bool:
    """Determine if an entity meets the minimum sales-ready threshold.

    Requires: name + address + province + status=ACTIVE
              + at least one of (phone | email | website | director)

    Requirements: 9.3
    """
    if not canonical_name:
        return False
    if not address_line1:
        return False
    if not province:
        return False
    if (status or "").upper() != "ACTIVE":
        return False
    return any([has_phone, has_email, has_website, has_director])
