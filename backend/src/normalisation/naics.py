"""NAICS normaliser.

Preserves source_naics. Maps to 2-digit naics_sector where unambiguous.
Does NOT infer NAICS for records where no source provides it.

Requirements: 4.8
"""

from __future__ import annotations

from dataclasses import dataclass

# NAICS 2-digit sector codes (Statistics Canada 2022 version)
# Maps prefix → sector description (we store the 2-digit code, not the description)
_NAICS_SECTORS: dict[str, str] = {
    "11": "11",  # Agriculture, Forestry, Fishing and Hunting
    "21": "21",  # Mining, Quarrying, and Oil and Gas Extraction
    "22": "22",  # Utilities
    "23": "23",  # Construction
    "31": "31",  # Manufacturing (31-33)
    "32": "32",  # Manufacturing
    "33": "33",  # Manufacturing
    "41": "41",  # Wholesale Trade
    "44": "44",  # Retail Trade (44-45)
    "45": "45",  # Retail Trade
    "48": "48",  # Transportation and Warehousing (48-49)
    "49": "49",  # Transportation and Warehousing
    "51": "51",  # Information and Cultural Industries
    "52": "52",  # Finance and Insurance
    "53": "53",  # Real Estate and Rental and Leasing
    "54": "54",  # Professional, Scientific and Technical Services
    "55": "55",  # Management of Companies and Enterprises
    "56": "56",  # Administrative and Support, Waste Management
    "61": "61",  # Educational Services
    "62": "62",  # Health Care and Social Assistance
    "71": "71",  # Arts, Entertainment and Recreation
    "72": "72",  # Accommodation and Food Services
    "81": "81",  # Other Services (except Public Administration)
    "91": "91",  # Public Administration
}

# SCIAN (French NAICS) codes are identical numerically — no separate mapping needed


@dataclass
class NAICSResult:
    source_naics: str | None   # preserved exactly as source provided
    naics_sector: str | None   # 2-digit sector, or None if cannot determine unambiguously


def normalise_naics(raw: str | None) -> NAICSResult:
    """Normalise a NAICS or SCIAN code.

    Preserves the source value. Maps to 2-digit sector only when unambiguous.
    Does NOT infer or fabricate a sector when raw is None/empty.

    Args:
        raw: NAICS/SCIAN code string as provided by source (may be 2, 4, 5, or 6 digits).

    Returns:
        NAICSResult. source_naics is preserved; naics_sector is the 2-digit prefix
        if recognisable, else None.
    """
    if not raw or not raw.strip():
        return NAICSResult(source_naics=None, naics_sector=None)

    source_naics = raw.strip()

    # Extract numeric prefix — strip any non-digit suffix (e.g. "44-45", "311XXX")
    digits = "".join(c for c in source_naics if c.isdigit())

    if len(digits) >= 2:
        prefix = digits[:2]
        sector = _NAICS_SECTORS.get(prefix)
        return NAICSResult(source_naics=source_naics, naics_sector=sector)

    # Single digit or non-numeric — preserve but can't map to sector
    return NAICSResult(source_naics=source_naics, naics_sector=None)
