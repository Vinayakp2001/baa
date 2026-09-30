"""Compliance enforcement guards for the BAA pipeline.

Centralised runtime assertions that prevent misuse of legally or
technically restricted data sources. These guards are called at
adapter initialisation or data-write time and raise hard errors
rather than logging warnings so they cannot be silently bypassed.

Guards implemented:
  - assert_not_statscan_individual: block individual-record payloads
    from source_class='D' (StatsCan aggregate-only) sources.
  - assert_orgbook_targeted: block bulk enumeration via BC OrgBook.
  - assert_nni_terms_cleared: block NNI processing unless CLEARED.
  - robots_txt_allowed: cache-backed robots.txt check before crawling.

Requirements: 15.1, 15.2, 15.3, 15.7, 15.9
"""

from __future__ import annotations

import threading
import time
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from .logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# StatsCan source-class='D' guard  (Req 15.1)
# ---------------------------------------------------------------------------

#: source_keys known to be aggregate-only (source_class='D').
#: Any adapter whose source_key appears here must NEVER receive or persist
#: individual business record payloads.
_STATSCAN_AGGREGATE_SOURCE_KEYS: frozenset[str] = frozenset(
    {
        "statscan_business_counts",
        "statscan_cbp",
        "statscan_fbs",
    }
)


def assert_not_statscan_individual(source_key: str, payload: dict[str, Any]) -> None:
    """Raise ValueError if an individual entity payload is detected for a StatsCan source.

    StatsCan aggregate counts (source_class='D') MUST NOT be stored as
    individual business records. The payload must not contain entity-level
    identifier fields (business_name, corp_number, etc.).

    Raises:
        ValueError: if an individual entity payload is detected.

    Requirements: 15.1
    """
    if source_key not in _STATSCAN_AGGREGATE_SOURCE_KEYS:
        return

    _individual_indicators = {
        "business_name", "corp_number", "corporate_name", "company_name",
        "business_number", "entity_id", "registration_number",
    }

    found = _individual_indicators.intersection(payload.keys())
    if found:
        raise ValueError(
            f"COMPLIANCE VIOLATION: source '{source_key}' is source_class='D' "
            f"(Statistics Canada aggregate data). Individual entity payloads "
            f"are prohibited. Found individual-record keys: {sorted(found)}. "
            "Use StatsCan data for aggregate reference only, not for entity creation."
        )


# ---------------------------------------------------------------------------
# BC OrgBook enumeration guard  (Req 15.2)
# ---------------------------------------------------------------------------


def assert_orgbook_targeted(lookup_targets: list[dict[str, Any]]) -> None:
    """Raise ValueError if the OrgBook call looks like a bulk enumeration attempt.

    BC Government Terms of Use prohibit bulk enumeration of OrgBook.
    Each lookup must be for a specific known entity.

    Raises:
        ValueError: if any target is empty, too short, or the batch exceeds
                    the safe lookup limit.

    Requirements: 15.2, 3.6, 8.9
    """
    _MAX_SAFE_BATCH = 500

    if not lookup_targets:
        raise ValueError(
            "COMPLIANCE VIOLATION: BCOrgBookAPIAdapter requires at least one "
            "explicit lookup target. Bulk enumeration is prohibited."
        )

    if len(lookup_targets) > _MAX_SAFE_BATCH:
        raise ValueError(
            f"COMPLIANCE VIOLATION: {len(lookup_targets)} OrgBook targets exceeds "
            f"safe batch limit of {_MAX_SAFE_BATCH}. "
            "BC Government Terms of Use prohibit bulk enumeration via large batches."
        )

    for target in lookup_targets:
        query = (
            target.get("bc_reg_id")
            or target.get("business_name")
            or target.get("cra_bn")
            or ""
        ).strip()

        if not query:
            raise ValueError(
                "COMPLIANCE VIOLATION: Empty OrgBook lookup target. "
                "Each target must specify bc_reg_id, business_name, or cra_bn. "
                "Wildcard/empty queries are prohibited."
            )

        if len(query) < 2:
            raise ValueError(
                f"COMPLIANCE VIOLATION: OrgBook query '{query}' is too short "
                "(minimum 2 characters). Single-character queries match too many entities "
                "and constitute enumeration."
            )


# ---------------------------------------------------------------------------
# NNI terms guard  (Req 15.3)
# ---------------------------------------------------------------------------

_NNI_REQUIRED_TERMS_STATUS = "CLEARED"


def assert_nni_terms_cleared(terms_status: str) -> None:
    """Raise ValueError if NNI terms have not been reviewed and cleared.

    NNI (Nunavummi Nangminiqaqtunik Ikajuuti) has an Unresolved terms status
    until the NNI Regulations PDF is reviewed and confirmed permissible.
    No NNI data may enter the canonical layer until cleared.

    Raises:
        ValueError: if terms_status is not 'CLEARED'.

    Requirements: 15.3, 3.7, 8.10
    """
    if terms_status != _NNI_REQUIRED_TERMS_STATUS:
        raise ValueError(
            f"COMPLIANCE VIOLATION: NNI source has terms_status='{terms_status}'. "
            "NNI data MUST NOT be processed into the canonical layer until the NNI "
            "Regulations PDF is reviewed and source.terms_status is updated to 'CLEARED'. "
            "Reference: https://nni.gov.nu.ca/sites/nni.gov.nu.ca/files/NNI-Regs-amendment_2.pdf"
        )


# ---------------------------------------------------------------------------
# robots.txt check utility  (Req 15.7, 15.9)
# ---------------------------------------------------------------------------

_robots_cache: dict[str, tuple[RobotFileParser, float]] = {}
_robots_lock = threading.Lock()
_ROBOTS_CACHE_TTL_S = 3600  # re-fetch robots.txt after 1 hour
_CRAWLER_USER_AGENT = "baa-pipeline"


def _fetch_robots(domain: str) -> RobotFileParser:
    """Fetch and parse robots.txt for a domain."""
    parser = RobotFileParser()
    parser.set_url(f"https://{domain}/robots.txt")
    try:
        parser.read()
    except Exception as exc:
        # If robots.txt cannot be fetched, default to disallow-nothing
        # (conservative for open data sites that don't have robots.txt).
        # Log so operators know.
        logger.warning("robots_txt_fetch_failed", domain=domain, error=str(exc))
    return parser


def robots_txt_allowed(url: str, *, user_agent: str = _CRAWLER_USER_AGENT) -> bool:
    """Return True if the URL is allowed for the given crawler user agent.

    Checks robots.txt for the domain of the given URL, with in-memory caching
    (1-hour TTL). Fetches fresh robots.txt on cache miss or expiry.

    A fetch failure returns True (allow) with a warning — failing open is
    appropriate for open data sources that typically do not have robots.txt.

    Args:
        url:        Full URL to check.
        user_agent: Crawler user agent string (default: "baa-pipeline").

    Returns:
        True  — crawling is allowed (or robots.txt could not be fetched).
        False — crawling is disallowed by robots.txt.

    Requirements: 15.7, 15.9
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
    except Exception:
        logger.warning("robots_txt_url_parse_failed", url=url)
        return True  # default allow on parse failure

    now = time.monotonic()

    with _robots_lock:
        cached = _robots_cache.get(domain)
        if cached is not None:
            parser, cached_at = cached
            if now - cached_at < _ROBOTS_CACHE_TTL_S:
                return parser.can_fetch(user_agent, url)

    # Cache miss or expired — fetch outside lock to avoid blocking
    parser = _fetch_robots(domain)

    with _robots_lock:
        _robots_cache[domain] = (parser, now)

    allowed = parser.can_fetch(user_agent, url)

    if not allowed:
        logger.warning(
            "robots_txt_disallowed",
            domain=domain,
            url=url,
            user_agent=user_agent,
        )

    return allowed
