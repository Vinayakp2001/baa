"""Status normaliser.

Maps source-specific status strings to canonical vocabulary:
ACTIVE | INACTIVE | SUSPENDED | DISSOLVED | PENDING | UNKNOWN

Preserves raw_status alongside canonical status.

Requirements: 4.9
"""

from __future__ import annotations

from dataclasses import dataclass

# Canonical status vocabulary
CANONICAL_STATUSES = frozenset(
    {"ACTIVE", "INACTIVE", "SUSPENDED", "DISSOLVED", "PENDING", "UNKNOWN"}
)

# Per-source status mapping table.
# Key: (source_key, raw_status_uppercase) → canonical status
# Sources without a specific entry fall through to the generic table.
_SOURCE_STATUS_MAP: dict[tuple[str, str], str] = {
    # Calgary — jobstatusdesc field
    ("calgary", "ACTIVE"): "ACTIVE",
    ("calgary", "INACTIVE"): "INACTIVE",
    ("calgary", "EXPIRED"): "INACTIVE",
    ("calgary", "CANCELLED"): "INACTIVE",
    ("calgary", "SUSPENDED"): "SUSPENDED",
    ("calgary", "PENDING"): "PENDING",
    # Edmonton — no documented status field; licence presence implies active
    ("edmonton", "ISSUED"): "ACTIVE",
    ("edmonton", "ACTIVE"): "ACTIVE",
    ("edmonton", "CANCELLED"): "INACTIVE",
    ("edmonton", "EXPIRED"): "INACTIVE",
    # Vancouver — status field
    ("vancouver", "ISSUED"): "ACTIVE",
    ("vancouver", "GONE OUT OF BUSINESS"): "INACTIVE",
    ("vancouver", "CANCELLED"): "INACTIVE",
    ("vancouver", "SUSPENDED"): "SUSPENDED",
    ("vancouver", "PENDING"): "PENDING",
    ("vancouver", "IN PROGRESS"): "PENDING",
    # Winnipeg — status transitions, Class B event-only
    ("winnipeg", "ACTIVE"): "ACTIVE",
    ("winnipeg", "CLOSED (L)"): "INACTIVE",
    ("winnipeg", "CLOSED"): "INACTIVE",
    ("winnipeg", "SUSPENDED"): "SUSPENDED",
    ("winnipeg", "CANCELLED"): "INACTIVE",
    # Corporations Canada CSV
    ("corporations_canada_csv", "ACTIVE"): "ACTIVE",
    ("corporations_canada_csv", "DISSOLVED"): "DISSOLVED",
    ("corporations_canada_csv", "INACTIVE"): "INACTIVE",
    ("corporations_canada_csv", "AMALGAMATED"): "INACTIVE",
    ("corporations_canada_csv", "CANCELLED"): "INACTIVE",
    ("corporations_canada_csv", "DEFAULTED"): "SUSPENDED",
    # Saskatoon
    ("saskatoon_all_biz", "ACTIVE"): "ACTIVE",
    ("saskatoon_all_biz", "INACTIVE"): "INACTIVE",
    ("saskatoon_new_biz", "ACTIVE"): "ACTIVE",
    # BC Indigenous
    ("bc_indigenous", "ACTIVE"): "ACTIVE",
    ("bc_indigenous", "INACTIVE"): "INACTIVE",
    # Ontario Select Licence
    ("ontario_select_licence", "ACTIVE"): "ACTIVE",
    ("ontario_select_licence", "INACTIVE"): "INACTIVE",
    ("ontario_select_licence", "EXPIRED"): "INACTIVE",
    ("ontario_select_licence", "REVOKED"): "SUSPENDED",
}

# Generic fallback table applied when no source-specific entry exists
_GENERIC_MAP: dict[str, str] = {
    "ACTIVE": "ACTIVE",
    "OPEN": "ACTIVE",
    "ISSUED": "ACTIVE",
    "VALID": "ACTIVE",
    "CURRENT": "ACTIVE",
    "INACTIVE": "INACTIVE",
    "CLOSED": "INACTIVE",
    "EXPIRED": "INACTIVE",
    "CANCELLED": "INACTIVE",
    "REVOKED": "INACTIVE",
    "GONE OUT OF BUSINESS": "INACTIVE",
    "TERMINATED": "INACTIVE",
    "AMALGAMATED": "INACTIVE",
    "DEFAULTED": "SUSPENDED",
    "SUSPENDED": "SUSPENDED",
    "DISSOLVED": "DISSOLVED",
    "PENDING": "PENDING",
    "IN PROGRESS": "PENDING",
    "PENDING REVIEW": "PENDING",
}


@dataclass
class StatusResult:
    raw_status: str | None
    canonical_status: str  # always one of CANONICAL_STATUSES


def normalise_status(raw: str | None, source_key: str = "") -> StatusResult:
    """Map a source status string to the canonical vocabulary.

    Args:
        raw: Raw status string from source.
        source_key: The source_key identifier (e.g. "calgary", "vancouver").
                    Used to apply source-specific mappings first.

    Returns:
        StatusResult with raw_status preserved and canonical_status set.
        Unknown/absent statuses → canonical_status="UNKNOWN".
    """
    if not raw or not raw.strip():
        return StatusResult(raw_status=raw, canonical_status="UNKNOWN")

    upper = raw.strip().upper()

    # Try source-specific mapping first
    canonical = _SOURCE_STATUS_MAP.get((source_key.lower(), upper))
    if canonical:
        return StatusResult(raw_status=raw, canonical_status=canonical)

    # Fall through to generic map
    canonical = _GENERIC_MAP.get(upper, "UNKNOWN")
    return StatusResult(raw_status=raw, canonical_status=canonical)
