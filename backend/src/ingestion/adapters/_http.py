"""Shared HTTP fetch utility for source adapters.

Keeps adapter implementations thin — they call fetch_bytes() and get
back (content, http_status, content_type) without reimplementing
request logic.
"""

from __future__ import annotations

import hashlib

import httpx

from ..base_adapter import SourceFetchError

_DEFAULT_TIMEOUT = 120  # seconds
_USER_AGENT = "baa-pipeline/0.1 (canada-b2b-data)"


def fetch_bytes(
    url: str,
    *,
    source_key: str,
    headers: dict[str, str] | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> tuple[bytes, int, str | None]:
    """Synchronous HTTP GET — returns (body, http_status, content_type).

    Raises SourceFetchError on any transport or HTTP error.
    """
    req_headers = {"User-Agent": _USER_AGENT}
    if headers:
        req_headers.update(headers)

    try:
        response = httpx.get(url, headers=req_headers, timeout=timeout, follow_redirects=True)
    except httpx.RequestError as exc:
        raise SourceFetchError(source_key, f"transport error: {exc}") from exc

    if response.status_code >= 400:
        raise SourceFetchError(
            source_key,
            f"HTTP {response.status_code} from {url}",
            status_code=response.status_code,
        )

    content_type = response.headers.get("content-type")
    return response.content, response.status_code, content_type


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
