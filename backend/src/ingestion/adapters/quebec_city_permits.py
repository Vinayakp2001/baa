"""QuebecCityPermitsAdapter — Ville de Québec permits event feed.

Source: Données Québec, Permis délivrés à la Ville de Québec
Format: weekly CSV
Grain: EVENT
Licence: CC-BY 4.0

Permit rows do not identify businesses. Keep them as source observations until
entity resolution can safely link them to a canonical business.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone

from ..base_adapter import SourceAdapter, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult
from ._http import fetch_bytes, sha256_hex

_SOURCE_KEY = "quebec_city_permits"
_DATASET_URL = (
    "https://www.donneesquebec.ca/recherche/dataset/"
    "879abf6e-c6b2-430a-b44a-16335467c6f6"
)
_CSV_URL = (
    "https://www.donneesquebec.ca/recherche/dataset/"
    "879abf6e-c6b2-430a-b44a-16335467c6f6/resource/"
    "9555031e-cfc5-4b78-bec9-4ab84b549f67/download/vdq-permis.csv"
)
_REQUIRED_FIELDS = ("NUMERO_PERMIS", "DATE_DELIVRANCE")


class QuebecCityPermitsAdapter(SourceAdapter):
    """Fetch validated permit rows without treating permits as businesses."""

    source_key = _SOURCE_KEY

    def __init__(self, csv_url: str = _CSV_URL) -> None:
        self._csv_url = csv_url

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        now = datetime.now(timezone.utc)
        content, http_status, content_type = fetch_bytes(
            self._csv_url,
            source_key=_SOURCE_KEY,
        )
        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=self._csv_url,
            retrieval_timestamp=now,
            http_status=http_status,
            content_type=content_type,
            checksum_sha256=sha256_hex(content),
            payload_ref=content.decode("utf-8-sig", errors="replace"),
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        try:
            reader = csv.DictReader(io.StringIO(artifact.payload_ref))
            if not reader.fieldnames:
                raise ValueError("CSV has no header row")
            rows = list(reader)
        except Exception as exc:
            raise SourceParseError(_SOURCE_KEY, f"CSV parse failed: {exc}") from exc

        records: list[RawRecord] = []
        for row in rows:
            raw_payload = {key: value for key, value in row.items() if key is not None}
            permit_number = (raw_payload.get("NUMERO_PERMIS") or "").strip()
            if permit_number:
                record_id = permit_number
            else:
                stable_row = json.dumps(
                    raw_payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                record_id = hashlib.sha256(stable_row.encode("utf-8")).hexdigest()[:32]

            records.append(
                RawRecord(
                    source_key=_SOURCE_KEY,
                    ingestion_run_id=artifact.ingestion_run_id,
                    source_record_id=record_id,
                    raw_payload=raw_payload,
                    source_grain=SourceGrain.EVENT,
                )
            )
        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        errors: dict[str, list[str]] = {}
        invalid = 0
        for record in records:
            row_errors = [
                f"missing {field}"
                for field in _REQUIRED_FIELDS
                if not str(record.raw_payload.get(field) or "").strip()
            ]
            if row_errors:
                invalid += 1
                errors.setdefault(record.source_record_id[:12], []).extend(row_errors)

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
            source_name="Ville de Québec — Permis délivrés",
            adapter_class="QuebecCityPermitsAdapter",
            province="QC",
            source_type="CSV",
            source_class="B",
            licence="Creative Commons Attribution 4.0 (CC-BY 4.0)",
            schedule_cron="0 9 * * 5",
            rate_limit_rpm=None,
            base_url=_DATASET_URL,
            default_grain=SourceGrain.EVENT,
        )