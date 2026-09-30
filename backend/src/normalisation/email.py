"""Email normaliser.

Lowercase domain, validate RFC 5321 format. "N/A" and similar → NULL.

Requirements: 4.5
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# RFC 5321 simplified validation — local@domain.tld
# We intentionally keep this permissive (no TLD exhaustive check) to avoid
# false negatives on unusual valid addresses.
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

_NULL_SENTINELS = {"n/a", "na", "none", "null", "unknown", "-", "--", "n.a.", ""}


@dataclass
class EmailResult:
    raw_email: str | None
    normalised_email: str | None   # lowercased domain; None if invalid/absent
    email_valid: bool | None       # None if no value provided


def normalise_email(raw: str | None) -> EmailResult:
    """Normalise an email address.

    Args:
        raw: Raw email string from source.

    Returns:
        EmailResult. Sentinel/empty inputs → all None.
        Valid format → email_valid=True, normalised_email with domain lowercased.
        Invalid format → email_valid=False, normalised_email=None.
    """
    if raw is None:
        return EmailResult(raw_email=None, normalised_email=None, email_valid=None)

    stripped = raw.strip()
    if stripped.lower() in _NULL_SENTINELS:
        return EmailResult(raw_email=None, normalised_email=None, email_valid=None)

    # Normalise: lowercase the whole address (local part is case-insensitive in practice)
    normalised = stripped.lower()

    if _EMAIL_RE.match(normalised):
        return EmailResult(raw_email=stripped, normalised_email=normalised, email_valid=True)

    return EmailResult(raw_email=stripped, normalised_email=None, email_valid=False)
