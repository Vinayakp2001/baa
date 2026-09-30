"""Business name normaliser.

Lowercase → expand abbreviations → strip punctuation variants → strip whitespace.
Preserves both legal_name and trade_name/dba as distinct fields.

Requirements: 4.2
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Ordered longest-first to avoid partial substitutions (e.g. "CORP" before "CO")
_ABBREVIATIONS: list[tuple[str, str]] = [
    (r"\bLTD\b", "LIMITED"),
    (r"\bINC\b", "INCORPORATED"),
    (r"\bCORP\b", "CORPORATION"),
    (r"\bCO\b", "COMPANY"),
    (r"\bST\b", "SAINT"),
]

# Strip punctuation that commonly appears in business names but adds no meaning
# Keep apostrophes and hyphens (O'Brien, Wal-Mart) — strip periods, commas, etc.
_PUNCT_RE = re.compile(r"[.,!?;:\"#@$%^&*(){}<>\[\]|\\~/`]")
# Collapse runs of whitespace
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class NameResult:
    legal_name: str | None       # normalised legal name
    trade_name: str | None       # normalised trade/dba name
    raw_legal_name: str | None   # preserved as-received
    raw_trade_name: str | None   # preserved as-received


def _normalise_single(raw: str | None) -> str | None:
    """Apply normalisation pipeline to a single name string."""
    if raw is None:
        return None

    s = raw.strip()
    if not s:
        return None

    # Uppercase for abbreviation matching, then we'll lowercase at the end
    s = s.upper()
    for pattern, replacement in _ABBREVIATIONS:
        s = re.sub(pattern, replacement, s)

    # Now lowercase
    s = s.lower()
    # Strip punctuation variants
    s = _PUNCT_RE.sub(" ", s)
    # Collapse whitespace
    s = _WHITESPACE_RE.sub(" ", s).strip()

    return s if s else None


def normalise_business_name(
    legal_name: str | None = None,
    trade_name: str | None = None,
) -> NameResult:
    """Normalise legal and trade names independently.

    Either or both may be provided. The normalised form is suitable for
    entity resolution matching. Both raw values are preserved.

    Args:
        legal_name: The registered legal name from the source.
        trade_name: The operating/trading/DBA name from the source.

    Returns:
        NameResult with both normalised and raw forms for each name type.
    """
    return NameResult(
        legal_name=_normalise_single(legal_name),
        trade_name=_normalise_single(trade_name),
        raw_legal_name=legal_name,
        raw_trade_name=trade_name,
    )
