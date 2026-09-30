"""URL / domain normaliser.

Extracts registered domain, strips www., lowercases.
Stores raw_url and normalised_domain separately.

Requirements: 4.6
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

_NULL_SENTINELS = {"n/a", "na", "none", "null", "unknown", "-", "--", "n.a.", ""}

# Matches "www." (with optional extra subdomains like "www2.")
_WWW_RE = re.compile(r"^www\d*\.", re.IGNORECASE)


@dataclass
class URLResult:
    raw_url: str | None
    normalised_domain: str | None   # e.g. "example.com" — no scheme, no www
    url_valid: bool | None          # None if no value provided


def normalise_url(raw: str | None) -> URLResult:
    """Normalise a URL or domain string to a canonical registered domain.

    Args:
        raw: Raw URL or domain as received from source.

    Returns:
        URLResult with raw_url and normalised_domain.
    """
    if raw is None:
        return URLResult(raw_url=None, normalised_domain=None, url_valid=None)

    stripped = raw.strip()
    if stripped.lower() in _NULL_SENTINELS:
        return URLResult(raw_url=None, normalised_domain=None, url_valid=None)

    # Add scheme if missing so urlparse can extract netloc
    parse_target = stripped if "://" in stripped else f"http://{stripped}"

    try:
        parsed = urlparse(parse_target)
        netloc = parsed.netloc or parsed.path
        # Strip port if present
        domain = netloc.split(":")[0].lower()
        # Remove www. prefix
        domain = _WWW_RE.sub("", domain)
        if not domain or "." not in domain:
            return URLResult(raw_url=stripped, normalised_domain=None, url_valid=False)
        return URLResult(raw_url=stripped, normalised_domain=domain, url_valid=True)
    except Exception:
        return URLResult(raw_url=stripped, normalised_domain=None, url_valid=False)
