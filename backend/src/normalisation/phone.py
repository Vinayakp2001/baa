"""Phone normaliser.

Strips formatting → 10-digit → E.164 → validates Canadian NPA.

Returns PhoneResult with normalised_phone, phone_valid, raw_phone.
"N/A", empty, and None inputs → all fields None (not invalid).

Requirements: 4.1
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import phonenumbers
from phonenumbers import NumberParseException


# Strings that represent "no phone" — treated as NULL, not invalid
_NULL_SENTINELS = {"n/a", "na", "none", "null", "unknown", "-", "--", "n.a.", ""}


@dataclass
class PhoneResult:
    raw_phone: str | None
    normalised_phone: str | None  # E.164 e.g. "+14161234567"
    phone_valid: bool | None      # None means "no value provided"


def normalise_phone(raw: str | None) -> PhoneResult:
    """Normalise a raw phone string to E.164 with Canadian NPA validation.

    Args:
        raw: Raw phone string as received from source, or None.

    Returns:
        PhoneResult. If the input is empty/sentinel → all None.
        If parsing succeeds and NPA is valid Canadian → phone_valid=True.
        If parsing fails or NPA is invalid → phone_valid=False, normalised_phone=None.
    """
    if raw is None:
        return PhoneResult(raw_phone=None, normalised_phone=None, phone_valid=None)

    stripped = raw.strip()
    if stripped.lower() in _NULL_SENTINELS:
        return PhoneResult(raw_phone=None, normalised_phone=None, phone_valid=None)

    # Attempt to parse as Canadian number (country hint: CA)
    try:
        parsed = phonenumbers.parse(stripped, "CA")
    except NumberParseException:
        return PhoneResult(raw_phone=stripped, normalised_phone=None, phone_valid=False)

    # phonenumbers validates structure and NPA implicitly for CA region
    if not phonenumbers.is_valid_number_for_region(parsed, "CA"):
        return PhoneResult(raw_phone=stripped, normalised_phone=None, phone_valid=False)

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    return PhoneResult(raw_phone=stripped, normalised_phone=e164, phone_valid=True)
