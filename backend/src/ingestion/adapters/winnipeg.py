"""WinnipegAdapter — City of Winnipeg Business Licences (Socrata CSV).

Source: City of Winnipeg Open Data — Business Licences
Format: Socrata CSV
Grain: EVENT
Event type: LICENCE_STATUS_CHANGE
Class: B — event/closure detection ONLY

CRITICAL CONSTRAINT (Req 5.8 / VR18):
  Winnipeg dataset is 84.7% "Closed (L)" rows. It MUST NOT be used as a
  primary discovery source. This adapter filters to non-ACTIVE status rows
  only and emits records as LICENCE_STATUS_CHANGE events — not as Class A
  discovery records.

  The `event_only=True` flag in metadata signals to downstream services that
  these records must NOT be submitted to entity discovery logic.

Requirements: 3.8, 5.8, 6.2
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

_SOURCE_KEY = "winnipeg"

_BASE_URL = "https://data.winnipeg.ca/resource/4dny-s4pv.csv"

# Statuses that indicate a non-active / closure / change event
# Active-only records are intentionally excluded (not a discovery source)
_NON_ACTIVE_STATUSES = {"closed (l)", "expired", "revoked", "suspended", "cancelled"}

_REQUIRED_FIELDS = {"trade_name", "status"}


class WinnipegAdapter(SourceAdapter):
    """Adapter for City of Winnipeg business licences — event/closure detection only.

    ONLY emits rows where `status` is non-ACTIVE. Records with status='Active'
    are silently dropped at parse time — Winnipeg is Class B (event-only).

    Downstream services MUST check `metadata.event_only=True` before
    routing these records to entity discovery.
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

        # Filter to non-active statuses at the API level where possible
        params: dict[str, str | int] = {"$limit": self._page_size}
        if since is not None:
            params["$where"] = f"issue_date >= '{since.strftime('%Y-%m-%dT%H:%M:%S')}'"

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

            # CRITICAL: skip Active rows — Winnipeg is event-only (Req 5.8 / VR18)
            status_raw = cleaned.get("status", "").lower()
            if status_raw not in _NON_ACTIVE_STATUSES:
                continue  # drop active and unknown-status rows

            cleaned["event_type"] = "LICENCE_STATUS_CHANGE"

            record_id = (
                cleaned.get("licence_number")
                or cleaned.get("licencenumber")
                or cleaned.get("licence_id")
                or hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]
            )

            records.append(
                RawRecord(
                    source_key=_SOURCE_KEY,
                    ingestion_run_id=artifact.ingestion_run_id,
                    source_record_id=record_id,
                    raw_payload=cleaned,
                    source_grain=SourceGrain.EVENT,
                )
            )
        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        errors: dict[str, list[str]] = {}
        invalid = 0

        for rec in records:
            row_errors = [
                f"missing {f}"
                for f in _REQUIRED_FIELDS
                if not rec.raw_payload.get(f)
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
            source_name="City of Winnipeg — Business Licences (Event/Closure Detection Only)",
            adapter_class="WinnipegAdapter",
            province="MB",
            source_type="CSV",
            source_class="B",
            licence="Open Government Licence (City of Winnipeg)",
            schedule_cron="0 7 * * *",
            rate_limit_rpm=None,
            base_url=_BASE_URL,
            default_grain=SourceGrain.EVENT,
        )
