"""MontrealCommercialPremisesAdapter — Ville de Montréal Commercial Premises.

Source: Données Ouvertes Montréal — Unités d'affaires sur l'île de Montréal
Format: CSV (annual snapshot, updated Dec 2025)
Grain: ESTABLISHMENT
Licence: Creative Commons Attribution 4.0 (CC-BY 4.0)

Key field notes:
  - SCIAN codes (French NAICS equivalent) mapped to NAICS sector in normalisation step
  - `commercial_category` and `occupancy_status` indicate business activity
  - Coordinates (lat/lon) present in the dataset
  - `arrondissement` = borough

Requirements: 3.8
"""

from __future__ import annotations

import csv
import hashlib
import io
import uuid
from datetime import datetime, timezone

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "montreal_commercial_premises"

# Données Ouvertes Montréal — unités d'affaires CSV export
_CSV_URL = (
    "https://donnees.montreal.ca/dataset/c7d0546a-a218-479e-bc9f-ce8f13cf81e4/"
    "resource/a4b7e0c5-e88c-4543-b6fc-36ef3ca06f56/download/unites-affaires.csv"
)

_REQUIRED_FIELDS = {"nom", "adresse"}


class MontrealCommercialPremisesAdapter(SourceAdapter):
    """Adapter for Ville de Montréal commercial premises (annual CSV snapshot).

    Full refresh only — no incremental support (annual dataset).
    """

    source_key = _SOURCE_KEY

    def __init__(self, csv_url: str = _CSV_URL) -> None:
        self._csv_url = csv_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        now = datetime.now(tz=timezone.utc)
        raw, http_status, content_type = fetch_bytes(self._csv_url, source_key=_SOURCE_KEY)

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=self._csv_url,
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

            # Use the source ID field if present, otherwise hash the row
            record_id = (
                cleaned.get("id")
                or cleaned.get("identifiant")
                or cleaned.get("id_uev")
                or hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]
            )

            records.append(
                RawRecord(
                    source_key=_SOURCE_KEY,
                    ingestion_run_id=artifact.ingestion_run_id,
                    source_record_id=record_id,
                    raw_payload=cleaned,
                    source_grain=SourceGrain.ESTABLISHMENT,
                )
            )
        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        errors: dict[str, list[str]] = {}
        invalid = 0

        for rec in records:
            payload = rec.raw_payload
            has_name = any(payload.get(k) for k in ("nom", "name", "nom_etablissement"))
            has_addr = any(payload.get(k) for k in ("adresse", "address", "adresse_complete"))

            row_errors = []
            if not has_name:
                row_errors.append("missing name (nom)")
            if not has_addr:
                row_errors.append("missing address (adresse)")

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
            source_name="Ville de Montréal — Unités d'affaires (Commercial Premises)",
            adapter_class="MontrealCommercialPremisesAdapter",
            province="QC",
            source_type="CSV",
            source_class="A",
            licence="Creative Commons Attribution 4.0 (CC-BY 4.0)",
            schedule_cron="0 8 1 1 *",  # annually January 1
            rate_limit_rpm=None,
            base_url="https://donnees.montreal.ca",
            default_grain=SourceGrain.ESTABLISHMENT,
        )
