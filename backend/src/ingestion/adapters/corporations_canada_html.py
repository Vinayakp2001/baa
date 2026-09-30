"""CorporationsCanadaHTMLAdapter — Monthly CBCA Incorporations HTML table.

Source: Corporations Canada — Monthly Transactions (Certificates of Incorporation)
Format: HTML table, single page (latest month only)
Grain: EVENT
Event type: FEDERAL_INCORPORATION
Licence: Open Government Licence – Canada

Key field notes (VR03):
  - Table headers: Corporation Number, Name of Corporation, Registered Office, Effective Date
  - Date format: YYYY-MM-DD
  - `Registered Office` contains the province in parentheses: "Ontario (ON)"
  - Only the latest month is published — job must archive locally on capture

Requirements: 3.8, 6.2
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "corporations_canada_html"

_HTML_URL = (
    "https://ised-isde.canada.ca/site/corporations-canada/en/data-services/"
    "monthly-transactions/certificates-incorporation-cbca"
)

# Expected headers (lowercase) — proven in VR03 probe
_EXPECTED_HEADERS = {
    "corporation number",
    "name of corporation",
    "registered office",
    "effective date",
}


def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _parse_incorporation_table(html: str) -> list[dict[str, str]]:
    """Extract the CBCA incorporations table from HTML."""
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        header_cells = rows[0].find_all(["th", "td"])
        headers_lower = {
            _normalize_text(c.get_text(" ", strip=True)).lower()
            for c in header_cells
        }

        if not _EXPECTED_HEADERS.issubset(headers_lower):
            continue

        # Found the right table
        headers = [
            _normalize_text(c.get_text(" ", strip=True))
            for c in header_cells
        ]

        records: list[dict[str, str]] = []
        for row in rows[1:]:
            cells = [
                _normalize_text(c.get_text(" ", strip=True))
                for c in row.find_all(["td", "th"])
            ]
            if not cells:
                continue
            if len(cells) != len(headers):
                continue  # skip malformed rows
            records.append(dict(zip(headers, cells)))

        return records

    raise SourceParseError(
        _SOURCE_KEY,
        "CBCA incorporation table not found — page structure may have changed",
    )


class CorporationsCanadaHTMLAdapter(SourceAdapter):
    """Adapter for Corporations Canada monthly CBCA incorporation HTML table.

    Fetches the current month's incorporation page, parses the HTML table
    with BeautifulSoup, and emits one RawRecord per corporation row with
    grain=EVENT and event_type=FEDERAL_INCORPORATION.

    The `source_record_id` is the Corporation Number where available,
    otherwise a SHA-256 of the row dict.
    """

    source_key = _SOURCE_KEY

    def __init__(self, html_url: str = _HTML_URL) -> None:
        self._html_url = html_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch the monthly incorporations HTML page."""
        now = datetime.now(tz=timezone.utc)
        raw, http_status, content_type = fetch_bytes(
            self._html_url, source_key=_SOURCE_KEY
        )

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=self._html_url,
            retrieval_timestamp=now,
            http_status=http_status,
            content_type=content_type,
            checksum_sha256=sha256_hex(raw),
            payload_ref=raw.decode("utf-8", errors="replace"),
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        try:
            rows = _parse_incorporation_table(artifact.payload_ref)
        except SourceParseError:
            raise
        except Exception as exc:
            raise SourceParseError(_SOURCE_KEY, f"parse failed: {exc}") from exc

        records: list[RawRecord] = []
        for row in rows:
            # Normalise keys to lowercase
            cleaned = {k.lower(): v for k, v in row.items()}

            # Annotate with event type for downstream event detection
            cleaned["event_type"] = "FEDERAL_INCORPORATION"

            corp_num = cleaned.get("corporation number", "")
            record_id = corp_num or hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]

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
            payload = rec.raw_payload
            row_errors: list[str] = []

            if not payload.get("name of corporation"):
                row_errors.append("missing name of corporation")
            if not payload.get("effective date"):
                row_errors.append("missing effective date")

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
            source_name="Corporations Canada — Monthly CBCA Incorporations (HTML)",
            adapter_class="CorporationsCanadaHTMLAdapter",
            province=None,  # federal
            source_type="HTML",
            source_class="B",
            licence="Open Government Licence – Canada",
            schedule_cron="0 8 1 * *",  # monthly, 1st of month
            rate_limit_rpm=None,
            base_url="https://ised-isde.canada.ca",
            default_grain=SourceGrain.EVENT,
        )
