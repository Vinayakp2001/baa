"""CorporationsCanadaAPIAdapter — Federal Director Enrichment API.

Source: Corporations Canada REST API
Format: JSON (REST)
Grain: CORPORATION (enrichment — directors only)
Licence: Open Government Licence – Canada (API subscription required)

Rate limit: 60 requests/minute (public plan, user-key header).
Token-bucket rate limiter enforced using asyncio timestamps.

CRITICAL CONSTRAINTS (Req 3.5, 8.3):
  - Only submit records with a valid `corp_number` (federal CBCA corps only).
  - Enrichment is event-triggered or sample-based — NOT a full-population sweep.
  - Enriching all 645,005 corps would require ~180 hours at 60 req/min.
  - Directors stored with role_type=DIRECTOR in the `person` table.

API endpoint pattern:
  GET /cc/api/corporations/{corp_number}
  Header: user-key: <api_key>
  Response: { "_embedded": { "directors": [{ "firstName", "lastName", "serviceAddress" }] } }

Requirements: 3.5, 8.3, 8.4
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from ._http import sha256_hex
from ..base_adapter import SourceAdapter, SourceFetchError, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "corporations_canada_api"
_API_BASE = "https://api.ic.gc.ca/corporations-canada/v1"
_RATE_LIMIT_RPM = 60
_USER_AGENT = "baa-pipeline/0.1 (canada-b2b-data)"


class _TokenBucket:
    """Asyncio-compatible token bucket rate limiter.

    Allows up to `rate` tokens per 60 seconds. Each call to `acquire()`
    waits until a token is available.

    Uses timestamps (not threading.Lock) so it is safe to use from
    async and sync contexts alike.
    """

    def __init__(self, rate: int = _RATE_LIMIT_RPM) -> None:
        self._rate = rate                   # tokens per minute
        self._tokens = float(rate)
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        # Add tokens proportional to elapsed time (rate/60 per second)
        new_tokens = elapsed * (self._rate / 60.0)
        self._tokens = min(self._rate, self._tokens + new_tokens)
        self._last_refill = now

    def acquire_sync(self) -> None:
        """Block (synchronous) until a token is available."""
        while True:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            # Sleep for the time needed to accumulate one token
            deficit = 1.0 - self._tokens
            sleep_s = deficit / (self._rate / 60.0)
            time.sleep(sleep_s)

    async def acquire(self) -> None:
        """Async wait until a token is available."""
        while True:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            deficit = 1.0 - self._tokens
            sleep_s = deficit / (self._rate / 60.0)
            await asyncio.sleep(sleep_s)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class CorporationsCanadaAPIAdapter(SourceAdapter):
    """Adapter for Corporations Canada REST API — director enrichment.

    Fetches director data for a batch of known corp_numbers.
    Each corp_number generates one RawRecord whose raw_payload contains
    the parsed directors list ready for downstream person-table insertion.

    Usage:
        adapter = CorporationsCanadaAPIAdapter(api_key="your-key")
        artifact = adapter.fetch(corp_numbers=["8660115", "821080"])
        records  = adapter.parse(artifact)

    The `since` parameter is ignored — this adapter is always called
    with an explicit list of corp_numbers (event-triggered, not full-sweep).
    """

    source_key = _SOURCE_KEY

    def __init__(
        self,
        api_key: str,
        api_base: str = _API_BASE,
        rate_limit_rpm: int = _RATE_LIMIT_RPM,
    ) -> None:
        self._api_key = api_key
        self._api_base = api_base.rstrip("/")
        self._bucket = _TokenBucket(rate=rate_limit_rpm)

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        since: datetime | None = None,
        *,
        corp_numbers: list[str] | None = None,
    ) -> RawArtifact:
        """Fetch director data for the given corp_numbers.

        Args:
            since: Not used. Present for interface compatibility.
            corp_numbers: List of federal corporation numbers to look up.
                          Invalid (empty/None) entries are silently skipped.

        Returns:
            RawArtifact whose payload_ref is a JSON-serialisable list of
            per-corporation director response dicts.
        """
        if not corp_numbers:
            raise SourceFetchError(
                _SOURCE_KEY,
                "corp_numbers must be provided — this adapter is event-triggered",
            )

        # Filter to valid corp numbers only (non-empty strings)
        valid_corps = [c for c in corp_numbers if c and isinstance(c, str) and c.strip()]
        if not valid_corps:
            raise SourceFetchError(
                _SOURCE_KEY,
                "No valid corp_numbers after filtering — only federal CBCA corps accepted",
            )

        now = datetime.now(tz=timezone.utc)
        headers = {
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
            "user-key": self._api_key,
        }

        results: list[dict[str, Any]] = []

        with httpx.Client(timeout=30, follow_redirects=True) as client:
            for corp_num in valid_corps:
                self._bucket.acquire_sync()

                url = f"{self._api_base}/corporations/{corp_num.strip()}"
                try:
                    response = client.get(url, headers=headers)
                except httpx.RequestError as exc:
                    raise SourceFetchError(
                        _SOURCE_KEY, f"transport error for {corp_num}: {exc}"
                    ) from exc

                if response.status_code == 404:
                    # Corporation not found — not an error, skip gracefully
                    results.append({
                        "corp_number": corp_num,
                        "http_status": 404,
                        "directors": [],
                        "error": "not_found",
                    })
                    continue

                if response.status_code >= 400:
                    raise SourceFetchError(
                        _SOURCE_KEY,
                        f"HTTP {response.status_code} for corp {corp_num}",
                        status_code=response.status_code,
                    )

                try:
                    data = response.json()
                except Exception as exc:
                    raise SourceFetchError(
                        _SOURCE_KEY,
                        f"JSON parse error for corp {corp_num}: {exc}",
                    ) from exc

                # Extract directors from HAL _embedded structure
                directors: list[dict] = []
                embedded = data.get("_embedded", {})
                if isinstance(embedded, dict):
                    directors = embedded.get("directors", [])
                    if not isinstance(directors, list):
                        directors = []

                results.append({
                    "corp_number": corp_num,
                    "http_status": response.status_code,
                    "directors": directors,
                    "raw_corp_data": data,
                })

        import json

        payload_str = json.dumps(results, ensure_ascii=False)
        checksum = sha256_hex(payload_str.encode())

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=f"{self._api_base}/corporations/[batch:{len(valid_corps)}]",
            retrieval_timestamp=now,
            http_status=200,
            content_type="application/json",
            checksum_sha256=checksum,
            payload_ref=payload_str,
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        """Parse each corp's director list into RawRecord instances.

        One RawRecord per director per corporation.
        raw_payload fields:
          - corp_number
          - director_first_name
          - director_last_name
          - director_full_name
          - service_address (dict with street, city, province, postal, country)
          - role_type (always "DIRECTOR")
        """
        import json

        try:
            corp_results: list[dict] = json.loads(artifact.payload_ref)
        except Exception as exc:
            raise SourceParseError(_SOURCE_KEY, f"payload parse failed: {exc}") from exc

        records: list[RawRecord] = []
        for corp_entry in corp_results:
            corp_number = corp_entry.get("corp_number", "")
            directors = corp_entry.get("directors", [])

            if not corp_number:
                continue

            if not directors:
                # Corp found but no directors — emit a stub record for provenance
                records.append(
                    RawRecord(
                        source_key=_SOURCE_KEY,
                        ingestion_run_id=artifact.ingestion_run_id,
                        source_record_id=f"{corp_number}:no_directors",
                        raw_payload={
                            "corp_number": corp_number,
                            "directors": [],
                            "role_type": "DIRECTOR",
                            "http_status": corp_entry.get("http_status"),
                        },
                        source_grain=SourceGrain.CORPORATION,
                    )
                )
                continue

            for idx, director in enumerate(directors):
                first = (director.get("firstName") or "").strip()
                last = (director.get("lastName") or "").strip()
                full_name = f"{first} {last}".strip()

                # serviceAddress may be a dict or string
                service_addr = director.get("serviceAddress", {})
                if isinstance(service_addr, str):
                    service_addr = {"raw": service_addr}

                payload = {
                    "corp_number": corp_number,
                    "director_first_name": first,
                    "director_last_name": last,
                    "director_full_name": full_name,
                    "service_address": service_addr,
                    "role_type": "DIRECTOR",
                    "director_index": idx,
                    "raw_director": director,
                }

                # Stable record ID: corp_number + director name hash
                record_id = hashlib.sha256(
                    f"{corp_number}:{full_name}".encode()
                ).hexdigest()[:32]

                records.append(
                    RawRecord(
                        source_key=_SOURCE_KEY,
                        ingestion_run_id=artifact.ingestion_run_id,
                        source_record_id=record_id,
                        raw_payload=payload,
                        source_grain=SourceGrain.CORPORATION,
                    )
                )

        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        errors: dict[str, list[str]] = {}
        invalid = 0

        for rec in records:
            payload = rec.raw_payload
            row_errors: list[str] = []

            # A director record must have a corp_number and at least a last name
            if not payload.get("corp_number"):
                row_errors.append("missing corp_number")
            if not payload.get("director_last_name") and payload.get("directors") != []:
                row_errors.append("missing director_last_name")

            if row_errors:
                invalid += 1
                errors.setdefault(rec.source_record_id[:12], []).extend(row_errors)

        return ValidationResult(
            source_key=_SOURCE_KEY,
            ingestion_run_id=records[0].ingestion_run_id if records else uuid.uuid4(),
            total_records=len(records),
            valid_records=len(records) - invalid,
            invalid_records=invalid,
            errors=errors,
            passed=invalid == 0,
        )

    def get_metadata(self) -> SourceMetadata:
        return SourceMetadata(
            source_key=_SOURCE_KEY,
            source_name="Corporations Canada — Federal API (Director Enrichment)",
            adapter_class="CorporationsCanadaAPIAdapter",
            province=None,  # federal
            source_type="API",
            source_class="C",
            licence="Open Government Licence – Canada (API subscription)",
            schedule_cron=None,  # event-triggered, not scheduled
            rate_limit_rpm=_RATE_LIMIT_RPM,
            base_url=_API_BASE,
            default_grain=SourceGrain.CORPORATION,
        )
