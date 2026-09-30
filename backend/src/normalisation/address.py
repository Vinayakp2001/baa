"""Address normaliser.

Standardises street type abbreviations, unit/suite formats, province codes,
and formats postal codes as "A1A 1A1". Validates Canadian postal code format.

Requirements: 4.3, 4.4
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Canadian postal code pattern: Letter-Digit-Letter (space) Digit-Letter-Digit
# Forward Sortation Areas (FSA): A[0-9][A-Z] — excludes D, F, I, O, Q, U
# We validate the general LDL-DLD pattern without being exhaustive on FSA validity
_POSTAL_RE = re.compile(
    r"^([A-CEGHJ-NPR-TVXYa-ceghj-npr-tvxy]\d[A-Za-z])\s*(\d[A-Za-z]\d)$"
)

# Street type abbreviations → full form (order matters for multi-word like "ST S")
_STREET_TYPE_MAP: dict[str, str] = {
    "ST": "STREET",
    "AVE": "AVENUE",
    "AV": "AVENUE",
    "BLVD": "BOULEVARD",
    "BOUL": "BOULEVARD",
    "DR": "DRIVE",
    "RD": "ROAD",
    "PL": "PLACE",
    "CRT": "COURT",
    "CT": "COURT",
    "CRES": "CRESCENT",
    "CR": "CRESCENT",
    "LN": "LANE",
    "HWY": "HIGHWAY",
    "PKY": "PARKWAY",
    "PKWY": "PARKWAY",
    "SQ": "SQUARE",
    "TER": "TERRACE",
    "TERR": "TERRACE",
    "TRL": "TRAIL",
    "CIR": "CIRCLE",
    "CIRC": "CIRCLE",
    "GT": "GATE",
    "GRV": "GROVE",
    "PK": "PARK",
    "GLN": "GLEN",
    "GDNS": "GARDENS",
    "GDN": "GARDEN",
    "WAY": "WAY",
    "PT": "POINT",
    "VISTA": "VISTA",
    "PROMENADE": "PROMENADE",
}

# Build regex from map keys — match whole words only, case-insensitive
_STREET_TYPE_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _STREET_TYPE_MAP) + r")\b",
    re.IGNORECASE,
)

# Unit/suite format normalisation: "Suite 100" / "Ste 100" / "Unit 100" → "SUITE 100"
_UNIT_RE = re.compile(
    r"\b(SUITE|STE|UNIT|APT|APARTMENT|RM|ROOM|BLDG|BUILDING)\s*[#:]?\s*(\w+)\b",
    re.IGNORECASE,
)

_UNIT_LABELS: dict[str, str] = {
    "SUITE": "SUITE",
    "STE": "SUITE",
    "UNIT": "UNIT",
    "APT": "APT",
    "APARTMENT": "APT",
    "RM": "ROOM",
    "ROOM": "ROOM",
    "BLDG": "BLDG",
    "BUILDING": "BLDG",
}

# Province abbreviation uppercase list (for validation)
_VALID_PROVINCES = {
    "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"
}

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class AddressResult:
    normalised_address: str | None   # full normalised address string
    raw_address: str | None          # preserved original
    address_line1: str | None
    address_line2: str | None
    city: str | None
    province: str | None             # uppercase 2-char code
    postal_code: str | None          # "A1A 1A1" format
    postal_valid: bool | None        # None if no postal provided


def _normalise_postal(raw: str | None) -> tuple[str | None, bool | None]:
    """Normalise and validate a Canadian postal code.

    Returns (normalised, valid) where normalised is "A1A 1A1" or None.
    valid is None if no postal provided.
    """
    if not raw or not raw.strip():
        return None, None

    cleaned = raw.strip().upper().replace("-", "").replace(" ", "")
    m = _POSTAL_RE.match(cleaned[:3] + " " + cleaned[3:] if len(cleaned) == 6 else cleaned)
    if m:
        formatted = f"{m.group(1).upper()} {m.group(2).upper()}"
        return formatted, True
    return raw.strip(), False


def _normalise_street(street: str) -> str:
    """Expand street type abbreviations and normalise unit formats."""

    def replace_street_type(m: re.Match) -> str:
        return _STREET_TYPE_MAP[m.group(0).upper()]

    result = _STREET_TYPE_RE.sub(replace_street_type, street)

    def replace_unit(m: re.Match) -> str:
        label = _UNIT_LABELS.get(m.group(1).upper(), m.group(1).upper())
        return f"{label} {m.group(2).upper()}"

    result = _UNIT_RE.sub(replace_unit, result)
    return _WHITESPACE_RE.sub(" ", result).strip()


def normalise_address(
    street: str | None = None,
    city: str | None = None,
    province: str | None = None,
    postal_code: str | None = None,
) -> AddressResult:
    """Normalise a Canadian address.

    Args:
        street: Street address line(s) as received from source.
        city: City name.
        province: Province/territory code or name.
        postal_code: Raw postal code string.

    Returns:
        AddressResult with normalised components and a full normalised_address string.
    """
    raw_parts = [p for p in [street, city, province, postal_code] if p and p.strip()]
    raw_address = ", ".join(raw_parts) if raw_parts else None

    # Street
    norm_street = _normalise_street(street) if street and street.strip() else None
    # Split into line1 / line2 if unit/suite appears after comma or dash
    addr_line1 = norm_street
    addr_line2: str | None = None
    if norm_street:
        # If there's a comma separating street from unit, split there
        parts = norm_street.split(",", 1)
        if len(parts) == 2:
            addr_line1 = parts[0].strip()
            addr_line2 = parts[1].strip()

    # City
    norm_city = city.strip().title() if city and city.strip() else None

    # Province — uppercase 2-char code
    norm_province: str | None = None
    if province and province.strip():
        norm_province = province.strip().upper()
        if norm_province not in _VALID_PROVINCES:
            # Keep it but don't validate further — province field may be a full name
            norm_province = province.strip().upper()

    # Postal code
    norm_postal, postal_valid = _normalise_postal(postal_code)

    # Build full normalised address string
    norm_parts = [p for p in [addr_line1, addr_line2, norm_city, norm_province, norm_postal] if p]
    normalised_address = ", ".join(norm_parts) if norm_parts else None

    return AddressResult(
        normalised_address=normalised_address,
        raw_address=raw_address,
        address_line1=addr_line1,
        address_line2=addr_line2,
        city=norm_city,
        province=norm_province,
        postal_code=norm_postal,
        postal_valid=postal_valid,
    )
