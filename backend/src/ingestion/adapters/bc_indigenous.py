"""BCIndigenousAdapter — BC Indigenous Business Listings (Direct CSV).

Source: BC Indigenous Business & Employment Development
Format: Direct CSV download
Grain: CORPORATION (enrichment — contact + employee data)
Licence: Open Government Licence – BC (OGL-BC)

Field notes:
  - `name`: business name
  - `phone`: phone number (may be absent)
  - `email`: email address (may be absent)
  - `website`: website URL (may be absent)
  - `Primary Contact`: contact person name
  - `employee_range`: employee range string — passes to employee normaliser
      Examples: "10 to 19", "55 to 99", "500 plus", "1 to 4"
  - `Industry Sector`: industry/sector string

Employee range rules (Req 7.3–7.5):
  - "55 to 99" → flag EMPLOYEE_RANGE_AMBIGUITY (non-standard bucket boundary)
  - "500 plus" → employee_min=500, employee_max=NULL per Req 7.4
  - Values passed raw to normalisation service — adapter does NOT normalise

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

_SOURCE_KEY = "bc_indigenous"

# BC Indigenous Business listings direct CSV URL
# Licence: Open Government Licence – BC
_CSV_URL = (
    "https://www2.gov.bc.ca/assets/gov/data/geographic/land-use/"
    "crown-land/certified_aboriginal_businesses.csv"
)

_REQUIRED_FIELDS = {"name"}

# Column name variants observed in BC Indigenous CSV
# Keys are normalised (lowercase + stripped); values are canonical field names
_COLUMN_MAP = {
    "business name": "name",
    "name": "name",
    "company name": "name",
    "phone": "phone",
    "telephone": "phone",
    "phone number": "phone",
    "email": "email",
    "email address": "email",
    "website": "website",
    "web site": "website",
    "url": "website",
    "primary contact": "primary_contact",
    "contact name": "primary_contact",
    "contact": "primary_contact",
    "employee range": "employee_range",
    "number of employees": "employee_range",
    "employees": "employee_range",
    "industry sector": "industry_sector",
    "industry": "industry_sector",
    "sector": "industry_sector",
    "category": "industry_sector",
    "city": "city",
    "community": "city",
    "location": "city",
    "province": "province",
    "postal code": "postal_code",
    "postal": "postal_code",
    "address": "address",
    "street address": "address",
    "mailing address": "address",
}


def _map_column(raw_header: str) -> str:
    """Map a raw CSV header to a canonical field name."""
    normalised = raw_header.strip().lower()
    return _COLUMN_MAP.get(normalised, normalised)


class BCIndigenousAdapter(SourceAdapter):
    """Adapter for BC Indigenous Business listings CSV.

    Fetches the direct CSV, maps column variants to canonical field names,
    and passes employee_range raw to the normalisation service.

    Employee range anomalies ("55 to 99") are flagged via a payload field
    so the normalisation service can emit EMPLOYEE_RANGE_AMBIGUITY flags.
    """

    source_key = _SOURCE_KEY

    def __init__(self, csv_url: str = _CSV_URL) -> None:
        self._csv_url = csv_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch the BC Indigenous CSV. No incremental support — full refresh."""
        now = datetime.now(tz=timezone.utc)
        raw, http_status, content_type = fetch_bytes(
            self._csv_url, source_key=_SOURCE_KEY
        )

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
            # Map raw headers to canonical field names
            cleaned: dict[str, str] = {}
            for raw_key, val in row.items():
                canonical_key = _map_column(raw_key)
                cleaned[canonical_key] = (val.strip() if val else "")

            # Skip completely empty rows
            if not any(cleaned.values()):
                continue

            # Flag "55 to 99" employee range anomaly for normaliser
            employee_range = cleaned.get("employee_range", "")
            if employee_range.strip().lower() in ("55 to 99", "55-99"):
                cleaned["employee_range_anomaly"] = "EMPLOYEE_RANGE_AMBIGUITY"

            # Preserve raw employee value explicitly
            cleaned["raw_employee_value"] = employee_range

            # Stable record ID: name + city hash (no unique ID in source)
            name = cleaned.get("name") or cleaned.get("business name", "")
            city = cleaned.get("city", "")
            record_id = hashlib.sha256(
                f"{name}:{city}".encode()
            ).hexdigest()[:32]

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
            source_name="BC Indigenous Business Listings",
            adapter_class="BCIndigenousAdapter",
            province="BC",
            source_type="CSV",
            source_class="C",
            licence="Open Government Licence – BC",
            schedule_cron="0 8 1 * *",  # monthly
            rate_limit_rpm=None,
            base_url="https://www2.gov.bc.ca",
            default_grain=SourceGrain.CORPORATION,
        )
