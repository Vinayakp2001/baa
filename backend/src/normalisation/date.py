"""Date normaliser.

Multi-format parser → ISO 8601 UTC datetime.
Returns None for absent/unparseable dates.

Requirements: 4.10
"""

from __future__ import annotations

from datetime import datetime, timezone

# Formats to try in order (most specific → least specific)
_DATE_FORMATS: list[str] = [
    "%Y-%m-%dT%H:%M:%S.%f%z",   # ISO with microseconds and tz
    "%Y-%m-%dT%H:%M:%S%z",       # ISO with tz
    "%Y-%m-%dT%H:%M:%S",         # ISO no tz (treat as UTC)
    "%Y-%m-%d %H:%M:%S",         # common SQL datetime
    "%Y-%m-%d",                   # ISO date only
    "%d/%m/%Y %H:%M:%S",          # DD/MM/YYYY HH:MM:SS
    "%d/%m/%Y",                   # DD/MM/YYYY
    "%m/%d/%Y %H:%M:%S",          # MM/DD/YYYY HH:MM:SS (US style — some sources)
    "%m/%d/%Y",                   # MM/DD/YYYY
    "%Y%m%d",                     # compact YYYYMMDD
    "%B %d, %Y",                  # "January 15, 2024"
    "%b %d, %Y",                  # "Jan 15, 2024"
    "%d %B %Y",                   # "15 January 2024"
    "%d %b %Y",                   # "15 Jan 2024"
]

_NULL_SENTINELS = {"n/a", "na", "none", "null", "unknown", "-", "", "0000-00-00"}


def normalise_date(raw: str | None) -> datetime | None:
    """Parse a raw date string to a UTC-aware datetime.

    Args:
        raw: Raw date string as received from source.

    Returns:
        UTC-aware datetime, or None if the input is absent/unparseable.
        Timezone-naive inputs are assumed UTC.
    """
    if raw is None:
        return None

    stripped = raw.strip()
    if stripped.lower() in _NULL_SENTINELS:
        return None

    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(stripped, fmt)
            # If no tzinfo, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            continue

    # Unparseable — return None rather than raising
    return None
