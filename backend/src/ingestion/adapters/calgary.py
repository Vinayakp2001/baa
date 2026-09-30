"""CalgaryAdapter — City of Calgary Business Licences (Socrata CSV).

Source: City of Calgary Open Data — Business Licences
Format: Socrata CSV export with optional date filter
Grain: LICENCE
Supports incremental fetch via `first_iss_dt >= last_run`
Licence: Open Government Licence (City of Calgary)
Requirements: 3.8, 10.1, 10.5
"""

from __future__ import annotations

import csv
import hashlib
import io
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "calgary"

# Socrata OData/CSV export endpoint for Business Licences dataset
_BASE_URL = "https://data.calgary.ca/resource/ineq-k8qb.csv"

_REQUIRED_FIELDS = {"tradename", "jobstatusdesc"}


class CalgaryAdapter(SourceAdapter):
    """Adapter for City of Calgary business licence data via Socrata CSV API.

    Supports incremental fetch: if `since` is provided the adapter adds a
    ``$where=first_iss_dt >= '{since}'`` filter to the Socrata query.
    """

    source_key = _SOURCE_KEY

    def __init__(self, base_url: str = _BASE_URL, page_size: int = 50_000) -> None:
        self._base_url = base_url
        self._page_size = page_size

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        now = datetime.now(tz=timezone.utc)

        params: dict[str, str | int] = {"$limit": self._page_size}
        if since is not None:
            # Socrata date filter: ISO 8601 string
            params["$where"] = f"first_iss_dt >= '{since.strftime('%Y-%m-%dT%H:%M:%S')}'"

        url = f"{self._base_url}?{urlencode(params)}"
        raw, http_status, content_type = fetch_bytes(url, source_key=_SOURCE_KEY)

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=url,
            retrieval_timestamp=now,
            http_status=http_status,
            content_type=content_type,
            checksum_sha256=sha256_hex(raw),
            payload_ref=raw.decode("utf-8-sig", errors="replace"),
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        try:
            reader = csv.DictReader(io.StringIO(artifact.payload_ref))
            rows = list(reader)
        except Exception as exc:
            raise SourceParseError(_SOURCE_KEY, f"CSV parse failed: {exc}") from exc

        records: list[RawRecord] = []
        for row in rows:
            cleaned = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}

            # Prefer licencenumber as stable identifier; fall back to row hash
            record_id = (
                cleaned.get("licencenumber")
                or cleaned.get("licence_number")
                or hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]
            )

            records.append(
                RawRecord(
                    source_key=_SOURCE_KEY,
                    ingestion_run_id=artifact.ingestion_run_id,
                    source_record_id=record_id,
                    raw_payload=cleaned,
                    source_grain=SourceGrain.LICENCE,
                )
            )
        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        errors: dict[str, list[str]] = {}
        invalid = 0

        for rec in records:
            row_errors = [
                f"missing {f}" for f in _REQUIRED_FIELDS if not rec.raw_payload.get(f)
            ]
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
            source_name="City of Calgary — Business Licences",
            adapter_class="CalgaryAdapter",
            province="AB",
            source_type="CSV",
            source_class="A",
            licence="Open Government Licence (City of Calgary)",
            schedule_cron="0 6 * * *",
            rate_limit_rpm=None,
            base_url=_BASE_URL,
            default_grain=SourceGrain.LICENCE,
        )
