"""SaskatoonAllBizAdapter — City of Saskatoon All Commercial/Home-Based Businesses.

Source: City of Saskatoon — Business Statistics & Publications page
Format: XLSX (openpyxl)
Grain: LICENCE
Licence: City of Saskatoon Open Data Licence

Key field notes (VR07):
  - Old CKAN portal retired Aug 26 2024 — files served directly from City website
  - XLSX fields: Bus_Lic_Acct_Id, name, address components, NAICS sub-sector
  - No phone/email/website in this file

Requirements: 3.8
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

_SOURCE_KEY = "saskatoon_all_biz"

# Direct XLSX URL from City website (confirmed live VR07, Dec 31 2025 snapshot)
_XLSX_URL = (
    "https://www.saskatoon.ca/sites/default/files/documents/community-services/"
    "planning-development/business-license-mapping-research/business-license/"
    "Dec_31_2025_%20All_Commercial_and_Home_Based_Businesses.xlsx"
)

_REQUIRED_FIELDS = {"bus_lic_acct_id", "business name"}


def _parse_xlsx_bytes(raw: bytes) -> list[dict[str, str]]:
    """Parse an XLSX byte string into a list of row dicts."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header_row = next(rows_iter, None)
        if header_row is None:
            return []
        headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(header_row)]

        rows: list[dict[str, str]] = []
        for raw_row in rows_iter:
            row_dict: dict[str, str] = {}
            for i, h in enumerate(headers):
                v = raw_row[i] if i < len(raw_row) else None
                row_dict[h] = "" if v is None else str(v).strip()
            if any(v for v in row_dict.values()):  # skip blank rows
                rows.append(row_dict)

        wb.close()
        return rows
    except Exception as exc:
        raise SourceParseError(_SOURCE_KEY, f"XLSX parse failed: {exc}") from exc


class SaskatoonAllBizAdapter(SourceAdapter):
    """Adapter for City of Saskatoon all-businesses XLSX.

    Fetches the annual XLSX snapshot, parses with openpyxl, emits one
    RawRecord per licence row with grain=LICENCE.
    """

    source_key = _SOURCE_KEY

    def __init__(self, xlsx_url: str = _XLSX_URL) -> None:
        self._xlsx_url = xlsx_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch XLSX — full snapshot only (no incremental support)."""
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
            # Store raw bytes as latin-1 string for cross-boundary transport
            payload_ref=raw.decode("latin-1"),
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        raw_bytes = artifact.payload_ref.encode("latin-1")
        rows = _parse_xlsx_bytes(raw_bytes)

        records: list[RawRecord] = []
        for row in rows:
            cleaned = {k.lower(): v for k, v in row.items()}

            record_id = (
                cleaned.get("bus_lic_acct_id")
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
            payload = rec.raw_payload
            # Accept either the exact key or a looser match
            has_id = any(payload.get(k) for k in ("bus_lic_acct_id", "licence_number"))
            has_name = any(payload.get(k) for k in ("business name", "business_name", "name"))

            row_errors = []
            if not has_id:
                row_errors.append("missing bus_lic_acct_id or licence_number")
            if not has_name:
                row_errors.append("missing business name")

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
            source_name="City of Saskatoon — All Commercial and Home-Based Businesses",
            adapter_class="SaskatoonAllBizAdapter",
            province="SK",
            source_type="XLSX",
            source_class="A",
            licence="City of Saskatoon Open Data Licence",
            schedule_cron="0 8 * * 1",  # weekly Monday 8am
            rate_limit_rpm=None,
            base_url="https://www.saskatoon.ca",
            default_grain=SourceGrain.LICENCE,
        )
