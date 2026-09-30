"""CorporationsCanadaCSVAdapter — CBCA active corporations CSV.

Source: Corporations Canada open data, federal active corporations
Format: CSV (~645,000 rows)
Grain: CORPORATION
Licence: Open Government Licence – Canada
Requirements: 3.8, 10.1
"""

from __future__ import annotations

import csv
import hashlib
import io
import uuid
from datetime import datetime, timezone

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceFetchError, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SOURCE_KEY = "corporations_canada_csv"
_CSV_URL = (
    "https://ised-isde.canada.ca/cc/lgcy/fdrlCrpSrch.html?exportType=CSV"
    "&lang=en&srchByNm=&srchByJrdctn=0&srchByStatus=A&searchStatus=&searchStatus=A"
)

# Minimal expected columns (subset — source has more)
_REQUIRED_FIELDS = {
    "corp_num",
    "corp_nme",
    "status",
}


class CorporationsCanadaCSVAdapter(SourceAdapter):
    """Adapter for the Corporations Canada active CBCA CSV export.

    Fetches the full active-corporations CSV, checksums it, and parses each
    row into a RawRecord with source_grain=CORPORATION.
    """

    source_key = _SOURCE_KEY

    def __init__(self, csv_url: str = _CSV_URL) -> None:
        self._csv_url = csv_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch the full active-corporations CSV from Corporations Canada.

        The source does not support incremental queries, so `since` is ignored.
        """
        now = datetime.now(tz=timezone.utc)

        raw, http_status, content_type = fetch_bytes(
            self._csv_url, source_key=_SOURCE_KEY
        )

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),  # caller replaces with real run_id
            retrieval_url=self._csv_url,
            retrieval_timestamp=now,
            http_status=http_status,
            content_type=content_type,
            checksum_sha256=sha256_hex(raw),
            payload_ref=raw.decode("utf-8-sig", errors="replace"),
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        """Parse the raw CSV payload into RawRecord instances."""
        try:
            reader = csv.DictReader(io.StringIO(artifact.payload_ref))
            rows = list(reader)
        except Exception as exc:
            raise SourceParseError(_SOURCE_KEY, f"CSV parse failed: {exc}") from exc

        records: list[RawRecord] = []
        for row in rows:
            # Normalise keys: strip whitespace, lowercase
            cleaned = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}

            corp_num = cleaned.get("corp_num") or cleaned.get("corporation_number") or ""
            record_id = corp_num if corp_num else hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]

            records.append(
                RawRecord(
                    source_key=_SOURCE_KEY,
                    ingestion_run_id=artifact.ingestion_run_id,
                    source_record_id=record_id,
                    raw_payload=cleaned,
                    source_grain=SourceGrain.CORPORATION,
                )
            )
        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        """Check that parsed records contain the expected CBCA fields."""
        errors: dict[str, list[str]] = {}
        invalid = 0

        for rec in records:
            payload = rec.raw_payload
            row_errors: list[str] = []

            for field in _REQUIRED_FIELDS:
                if not payload.get(field):
                    row_errors.append(f"missing {field}")

            if row_errors:
                invalid += 1
                record_key = rec.source_record_id[:12]
                errors.setdefault(record_key, []).extend(row_errors)

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
            source_name="Corporations Canada — Active CBCA CSV",
            adapter_class="CorporationsCanadaCSVAdapter",
            province=None,  # federal
            source_type="CSV",
            source_class="A",
            licence="Open Government Licence – Canada",
            schedule_cron="0 4 * * 1",  # weekly Monday 4am
            rate_limit_rpm=None,
            base_url="https://ised-isde.canada.ca",
            default_grain=SourceGrain.CORPORATION,
        )
