"""VancouverAdapter — City of Vancouver Business Licences (OpenDataSoft CSV).

Source: City of Vancouver Open Data — Business Licences
Format: OpenDataSoft CSV export with optional date filter
Grain: LICENCE
Supports incremental fetch via `issueddate >= last_run`
Licence: Open Government Licence (City of Vancouver)

Key field notes (VR09/VR15):
  - `LicenceRSN` is the stable source record ID — preserved verbatim
  - `numberofemployees` is a float-string (e.g. "385.0") — passed raw to normaliser
  - Multi-licence businesses (17.7%): employee conflict resolved at entity layer,
    not here — adapter emits all records as-is

Requirements: 3.8, 5.9, 10.1, 10.5
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "vancouver"

# OpenDataSoft export endpoint — City of Vancouver business licences
_BASE_URL = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/business-licences/exports/csv"

_REQUIRED_FIELDS = {"businessname", "status"}


class VancouverAdapter(SourceAdapter):
    """Adapter for City of Vancouver business licence data.

    Uses OpenDataSoft CSV export. Supports incremental fetch via
    ``where=issueddate >= '{since}'`` query parameter.

    `LicenceRSN` is preserved as the source_record_id per Req 5.9.
    Employee values are passed raw for the normalisation service.
    """

    source_key = _SOURCE_KEY

    def __init__(self, base_url: str = _BASE_URL, page_size: int = 250_000) -> None:
        self._base_url = base_url
        self._page_size = page_size

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        now = datetime.now(tz=timezone.utc)

        params: dict[str, str | int] = {"limit": self._page_size, "delimiter": ","}
        if since is not None:
            params["where"] = f"issueddate >= '{since.strftime('%Y-%m-%d')}'"

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
            # Preserve original casing for known fields, lowercase the rest
            cleaned: dict[str, str] = {}
            licence_rsn = ""
            for k, v in row.items():
                key = k.strip()
                val = v.strip() if v else ""
                if key == "LicenceRSN":
                    licence_rsn = val
                cleaned[key.lower()] = val

            # LicenceRSN is the stable source_record_id (Req 5.9)
            record_id = licence_rsn or cleaned.get("licencersn") or cleaned.get("licence_id") or ""
            if not record_id:
                import hashlib
                record_id = hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]

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
            source_name="City of Vancouver — Business Licences",
            adapter_class="VancouverAdapter",
            province="BC",
            source_type="CSV",
            source_class="A",
            licence="Open Government Licence (City of Vancouver)",
            schedule_cron="0 5 * * *",
            rate_limit_rpm=None,
            base_url=_BASE_URL,
            default_grain=SourceGrain.LICENCE,
        )
