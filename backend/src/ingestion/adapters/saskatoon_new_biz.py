"""SaskatoonNewBizAdapter — City of Saskatoon New Business Licences (XLSX).

Source: City of Saskatoon — Business Statistics & Publications page
Format: XLSX (openpyxl), explicit "new businesses" file
Grain: LICENCE
Event type: MUNICIPAL_LICENCE_FIRST_ISSUE
Licence: City of Saskatoon Open Data Licence

Key field notes (VR07):
  - This file is explicitly labelled "New Businesses" by the city — direct new-licence signal
  - Fields: Business_License_Id, name, address, NAICS sub-sector
  - Old CKAN portal retired Aug 26 2024

Requirements: 3.8, 6.2
"""

from __future__ import annotations

import hashlib
import io
import uuid
from datetime import datetime, timezone

import openpyxl

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "saskatoon_new_biz"

_XLSX_URL = (
    "https://www.saskatoon.ca/sites/default/files/media/documents/"
    "New%20Businesses%20as%20of%20August%2031%2C%202026.xlsx"
)


def _parse_xlsx_bytes(raw: bytes) -> list[dict[str, str]]:
    try:
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header_row = next(rows_iter, None)
        if header_row is None:
            return []
        headers = [
            str(h).strip() if h is not None else f"col_{i}"
            for i, h in enumerate(header_row)
        ]
        rows: list[dict[str, str]] = []
        for raw_row in rows_iter:
            row_dict = {
                h: ("" if raw_row[i] is None else str(raw_row[i]).strip())
                for i, h in enumerate(headers)
                if i < len(raw_row)
            }
            if any(v for v in row_dict.values()):
                rows.append(row_dict)
        wb.close()
        return rows
    except Exception as exc:
        raise SourceParseError(_SOURCE_KEY, f"XLSX parse failed: {exc}") from exc


class SaskatoonNewBizAdapter(SourceAdapter):
    """Adapter for City of Saskatoon new-businesses XLSX.

    Emits records with grain=LICENCE and event_type=MUNICIPAL_LICENCE_FIRST_ISSUE
    because this file is the city's explicit new-licence issuance signal.
    """

    source_key = _SOURCE_KEY

    def __init__(self, xlsx_url: str = _XLSX_URL) -> None:
        self._xlsx_url = xlsx_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        now = datetime.now(tz=timezone.utc)
        raw, http_status, content_type = fetch_bytes(self._xlsx_url, source_key=_SOURCE_KEY)

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=self._xlsx_url,
            retrieval_timestamp=now,
            http_status=http_status,
            content_type=content_type,
            checksum_sha256=sha256_hex(raw),
            payload_ref=raw.decode("latin-1"),
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        raw_bytes = artifact.payload_ref.encode("latin-1")
        rows = _parse_xlsx_bytes(raw_bytes)

        records: list[RawRecord] = []
        for row in rows:
            cleaned = {k.lower(): v for k, v in row.items()}
            cleaned["event_type"] = "MUNICIPAL_LICENCE_FIRST_ISSUE"

            record_id = (
                cleaned.get("business_license_id")
                or cleaned.get("business license id")
                or cleaned.get("bus_lic_acct_id")
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
            payload = rec.raw_payload
            has_name = any(
                payload.get(k)
                for k in ("business name", "name", "business_name")
            )
            if not has_name:
                invalid += 1
                errors.setdefault(rec.source_record_id[:12], []).append("missing name")

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
            source_name="City of Saskatoon — New Businesses",
            adapter_class="SaskatoonNewBizAdapter",
            province="SK",
            source_type="XLSX",
            source_class="B",
            licence="City of Saskatoon Open Data Licence",
            schedule_cron="0 8 * * 1",  # weekly Monday 8am
            rate_limit_rpm=None,
            base_url="https://www.saskatoon.ca",
            default_grain=SourceGrain.LICENCE,
        )
