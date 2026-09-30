"""OntarioSelectLicenceAdapter — Ontario Select Licence and Registration Data.

Source: Ontario Open Data — Select Licence and Registration Data (CKAN)
Format: CKAN CSV (monthly snapshot)
Grain: LICENCE
Licence: Open Government Licence – Ontario

Source notes (VR06):
  - 674 business rows, 14 columns; 369 unique licence numbers
  - Licence types: Payday Lender (64%), Collection Agency (19%), Bailiff (11%),
    Consumer Reporting Agency (5%), Loan Broker (<1%)
  - 674 licence records ≠ 674 businesses — one business may hold multiple licences
  - "N/A" appears in phone, email, website, postal_code, operating_name, expiry_date
    → all "N/A" values MUST be converted to NULL (not treated as invalid)
  - Phone format: 10-digit raw string (e.g. "9057942333") — no formatting
  - Out-of-province records exist (12/674 non-Ontario addresses) — do NOT hard-filter
  - No NAICS or employee count in this source
  - Fields: Legal Name, Operating name, Address, City, Province, Postal code,
    Country, Telephone, Website, Email, Licence type, Licence number,
    Licence status, Expiry date

Requirements: 3.8
"""

from __future__ import annotations

import csv
import hashlib
import io
import uuid
from datetime import datetime, timezone

import httpx

from ._http import sha256_hex
from ..base_adapter import SourceAdapter, SourceFetchError, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "ontario_select_licence"

# CKAN package ID for Ontario Select Licence and Registration Data
_CKAN_API = "https://data.ontario.ca/api/3/action/package_show"
_PACKAGE_ID = "select-licence-and-registration-data"

# Fallback direct CSV URL (business file) — used if CKAN API is unavailable
_FALLBACK_BUSINESS_CSV = (
    "https://data.ontario.ca/dataset/5f0c3532-6e42-4ed7-a92c-ecde22bfea06/"
    "resource/ba4e4b1a-1dd4-4e05-b1e8-f3f06e5b2c00/download"
)

_USER_AGENT = "baa-pipeline/0.1 (canada-b2b-data)"

_REQUIRED_FIELDS = {"legal name"}

# "N/A" sentinel values — treated as NULL throughout (Req 4.5, VR06)
_NULL_SENTINELS = frozenset({"n/a", "na", "none", "", "null", "-"})


def _null_or_value(raw: str) -> str:
    """Return empty string (NULL marker) if value is an N/A sentinel, else the raw value."""
    if raw.strip().lower() in _NULL_SENTINELS:
        return ""
    return raw.strip()


class OntarioSelectLicenceAdapter(SourceAdapter):
    """Adapter for Ontario Select Licence and Registration business data.

    Downloads the monthly CKAN CSV via the CKAN package API to get the
    latest resource URL, then fetches the CSV.

    "N/A" values in phone, email, website, postal_code are normalised to ""
    (NULL equivalent) at parse time. They are NOT flagged as invalid.

    Source grain: LICENCE (not CORPORATION — see VR06 critical note).
    """

    source_key = _SOURCE_KEY

    def __init__(
        self,
        ckan_api: str = _CKAN_API,
        package_id: str = _PACKAGE_ID,
        fallback_csv_url: str = _FALLBACK_BUSINESS_CSV,
    ) -> None:
        self._ckan_api = ckan_api
        self._package_id = package_id
        self._fallback_csv_url = fallback_csv_url

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _discover_csv_url(self) -> str:
        """Query the CKAN API to find the latest business CSV URL.

        Falls back to the hardcoded URL if CKAN API is unreachable.
        """
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                response = client.get(
                    self._ckan_api,
                    params={"id": self._package_id},
                    headers={"User-Agent": _USER_AGENT},
                )
                if response.status_code != 200:
                    return self._fallback_csv_url

                pkg = response.json()
                resources = pkg.get("result", {}).get("resources", [])

                # Find the most recent "Business" CSV resource
                for resource in resources:
                    name = (resource.get("name") or "").lower()
                    fmt = (resource.get("format") or "").upper()
                    if "business" in name and fmt == "CSV":
                        url = resource.get("url")
                        if url:
                            return url

        except Exception:
            pass  # Fall through to hardcoded URL

        return self._fallback_csv_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch the Ontario Select Licence business CSV.

        `since` is ignored — source is a monthly full snapshot with no
        incremental filter capability.
        """
        csv_url = self._discover_csv_url()
        now = datetime.now(tz=timezone.utc)

        try:
            with httpx.Client(timeout=120, follow_redirects=True) as client:
                response = client.get(
                    csv_url, headers={"User-Agent": _USER_AGENT}
                )
        except httpx.RequestError as exc:
            raise SourceFetchError(
                _SOURCE_KEY, f"transport error: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise SourceFetchError(
                _SOURCE_KEY,
                f"HTTP {response.status_code} from {csv_url}",
                status_code=response.status_code,
            )

        raw = response.content

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=csv_url,
            retrieval_timestamp=now,
            http_status=response.status_code,
            content_type=response.headers.get("content-type"),
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
            # Normalise keys: strip whitespace, preserve case for known fields
            raw_cleaned = {
                k.strip(): (v.strip() if v else "")
                for k, v in row.items()
            }

            # Map to canonical snake_case field names
            cleaned: dict[str, str] = {
                "legal_name":      raw_cleaned.get("Legal Name", ""),
                "operating_name":  _null_or_value(raw_cleaned.get("Operating name", "")),
                "address":         raw_cleaned.get("Address", ""),
                "city":            raw_cleaned.get("City", ""),
                "province":        raw_cleaned.get("Province", ""),
                "postal_code":     _null_or_value(raw_cleaned.get("Postal code", "")),
                "country":         _null_or_value(raw_cleaned.get("Country", "")),
                # "N/A" → "" (NULL) for contact fields per Req 4.5 and VR06
                "phone":           _null_or_value(raw_cleaned.get("Telephone", "")),
                "website":         _null_or_value(raw_cleaned.get("Website", "")),
                "email":           _null_or_value(raw_cleaned.get("Email", "")),
                "licence_type":    raw_cleaned.get("Licence type", ""),
                "licence_number":  raw_cleaned.get("Licence number", ""),
                "licence_status":  raw_cleaned.get("Licence status", ""),
                "expiry_date":     _null_or_value(raw_cleaned.get("Expiry date", "")),
            }

            # Skip rows with no legal name
            if not cleaned["legal_name"]:
                continue

            # Stable record ID: licence_number (unique per licence)
            licence_num = cleaned.get("licence_number", "")
            record_id = (
                licence_num
                if licence_num
                else hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]
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
            row_errors: list[str] = []

            if not rec.raw_payload.get("legal_name"):
                row_errors.append("missing legal_name")

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
            source_name="Ontario Select Licence and Registration Data",
            adapter_class="OntarioSelectLicenceAdapter",
            province="ON",
            source_type="CSV",
            source_class="C",
            licence="Open Government Licence – Ontario",
            schedule_cron="0 8 1 * *",  # monthly
            rate_limit_rpm=None,
            base_url="https://data.ontario.ca",
            default_grain=SourceGrain.LICENCE,
        )
