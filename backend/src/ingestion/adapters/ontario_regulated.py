"""Ontario Regulated Sector Adapters (×6).

All six adapters extend a shared OntarioRegulatedBaseAdapter.

Sources (all from Ontario Open Data / CKAN, OGL-Ontario):
  1. DairyDistributorsAdapter    — Dairy Distributors (non-shopkeepers)
  2. DairyPlantsAdapter          — Provincially Licensed Dairy Plants
  3. MeatPlantsAdapter           — Provincially Licensed Meat Plants
  4. TobaccoAdapter              — Tobacco Tax Registrant List
  5. FuelAdapter                 — Fuel and Gasoline Tax Registrant List
  6. CSBIFAdapter                — Community Small Business Investment Funds (CSBIF)

Role: enrichment only — phone/postal for regulated-sector ON businesses.
Grain: LICENCE for all six.
Licence: Open Government Licence – Ontario (commercial use permitted).

Field availability by source (VR20):
  - Dairy Distributors: name, address, city, postal_code, telephone, licence_number
  - Dairy Plants:       name, address, city, postal_code, telephone, licence_number
  - Meat Plants:        name, address, city, postal_code, telephone, coordinates, animal_class
  - Tobacco:            name, address, modification_date
  - Fuel:               name, address, authorization info
  - CSBIF:              name, address, contact info, registration_date, registration_number, status

Requirements: 3.8
"""

from __future__ import annotations

import csv
import hashlib
import io
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from ._http import sha256_hex
from ..base_adapter import SourceAdapter, SourceFetchError, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_USER_AGENT = "baa-pipeline/0.1 (canada-b2b-data)"
_CKAN_API = "https://data.ontario.ca/api/3/action/package_show"

# "N/A" sentinel values — treated as NULL (consistent with Ontario Select Licence)
_NULL_SENTINELS = frozenset({"n/a", "na", "none", "", "null", "-", "not available"})


def _null_or_value(raw: str) -> str:
    """Return empty string for N/A sentinels, otherwise the stripped raw value."""
    if raw.strip().lower() in _NULL_SENTINELS:
        return ""
    return raw.strip()


def _fetch_ckan_csv(package_id: str, resource_keyword: str) -> str:
    """Fetch the latest CSV URL for a CKAN resource matching resource_keyword.

    Returns the direct download URL for the matching resource,
    or raises SourceFetchError if none found.
    """
    source_key = f"ontario_{package_id}"
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.get(
                _CKAN_API,
                params={"id": package_id},
                headers={"User-Agent": _USER_AGENT},
            )
            if response.status_code != 200:
                raise SourceFetchError(
                    source_key,
                    f"CKAN API returned HTTP {response.status_code} for {package_id}",
                )
            pkg = response.json()
            resources = pkg.get("result", {}).get("resources", [])

            keyword_lower = resource_keyword.lower()
            for resource in resources:
                name = (resource.get("name") or "").lower()
                fmt = (resource.get("format") or "").upper()
                if keyword_lower in name and fmt == "CSV":
                    url = resource.get("url")
                    if url:
                        return url

    except SourceFetchError:
        raise
    except Exception as exc:
        raise SourceFetchError(source_key, f"CKAN API error: {exc}") from exc

    raise SourceFetchError(
        source_key,
        f"No CSV resource matching '{resource_keyword}' found in CKAN package '{package_id}'",
    )


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class OntarioRegulatedBaseAdapter(SourceAdapter):
    """Shared base for all 6 Ontario regulated-sector CKAN CSV adapters.

    Subclasses must define:
      - source_key (str)
      - _package_id (str) — CKAN package ID
      - _resource_keyword (str) — keyword to match the CSV resource name
      - _fallback_url (str) — hardcoded direct URL if CKAN lookup fails
      - _column_map (dict) — raw column header → canonical field name
      - _source_name (str)
      - _schedule_cron (str)

    The base class handles: fetch, validate, and get_metadata.
    Subclasses MAY override parse() for source-specific field extraction.
    """

    source_key: str
    _package_id: str
    _resource_keyword: str
    _fallback_url: str
    _column_map: dict[str, str]
    _source_name: str
    _schedule_cron: str

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch the CSV via CKAN API discovery, falling back to hardcoded URL."""
        try:
            csv_url = _fetch_ckan_csv(self._package_id, self._resource_keyword)
        except SourceFetchError:
            csv_url = self._fallback_url

        now = datetime.now(tz=timezone.utc)

        try:
            with httpx.Client(timeout=120, follow_redirects=True) as client:
                response = client.get(csv_url, headers={"User-Agent": _USER_AGENT})
        except httpx.RequestError as exc:
            raise SourceFetchError(self.source_key, f"transport error: {exc}") from exc

        if response.status_code >= 400:
            raise SourceFetchError(
                self.source_key,
                f"HTTP {response.status_code} from {csv_url}",
                status_code=response.status_code,
            )

        raw = response.content
        return RawArtifact(
            source_key=self.source_key,
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
            raise SourceParseError(self.source_key, f"CSV parse failed: {exc}") from exc

        records: list[RawRecord] = []
        for row in rows:
            cleaned: dict[str, str] = {}
            for raw_key, val in row.items():
                # Map raw header to canonical name, or use normalised raw header
                canonical = self._column_map.get(
                    raw_key.strip().lower(),
                    raw_key.strip().lower().replace(" ", "_"),
                )
                cleaned[canonical] = _null_or_value(val or "")

            # Skip empty rows
            if not any(cleaned.values()):
                continue

            name = cleaned.get("name", "")
            licence_number = cleaned.get("licence_number", "")
            record_id = (
                licence_number
                if licence_number
                else hashlib.sha256(str(cleaned).encode()).hexdigest()[:32]
            )

            records.append(
                RawRecord(
                    source_key=self.source_key,
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
            if not rec.raw_payload.get("name"):
                row_errors.append("missing name")

            if row_errors:
                invalid += 1
                errors.setdefault(rec.source_record_id[:12], []).extend(row_errors)

        return ValidationResult(
            source_key=self.source_key,
            ingestion_run_id=records[0].ingestion_run_id if records else uuid.uuid4(),
            total_records=len(records),
            valid_records=len(records) - invalid,
            invalid_records=invalid,
            errors=errors,
            passed=invalid == 0,
        )

    def get_metadata(self) -> SourceMetadata:
        return SourceMetadata(
            source_key=self.source_key,
            source_name=self._source_name,
            adapter_class=type(self).__name__,
            province="ON",
            source_type="CSV",
            source_class="C",
            licence="Open Government Licence – Ontario",
            schedule_cron=self._schedule_cron,
            rate_limit_rpm=None,
            base_url="https://data.ontario.ca",
            default_grain=SourceGrain.LICENCE,
        )


# ---------------------------------------------------------------------------
# 1. DairyDistributorsAdapter
# ---------------------------------------------------------------------------


class DairyDistributorsAdapter(OntarioRegulatedBaseAdapter):
    """Ontario Dairy Distributors (non-shopkeepers).

    Fields: name, address, city, postal_code, telephone, licence_number
    """

    source_key = "ontario_dairy_distributors"
    _package_id = "dairy-distributors"
    _resource_keyword = "dairy distributor"
    _fallback_url = (
        "https://data.ontario.ca/dataset/dairy-distributors/"
        "resource/download"
    )
    _source_name = "Ontario — Dairy Distributors (non-shopkeepers)"
    _schedule_cron = "0 8 1 * *"  # monthly

    _column_map: dict[str, str] = {
        "name": "name",
        "business name": "name",
        "distributor name": "name",
        "address": "address",
        "street": "address",
        "street address": "address",
        "city": "city",
        "postal code": "postal_code",
        "postal": "postal_code",
        "telephone": "phone",
        "phone": "phone",
        "phone number": "phone",
        "licence number": "licence_number",
        "license number": "licence_number",
        "licence no": "licence_number",
        "licence #": "licence_number",
        "province": "province",
    }


# ---------------------------------------------------------------------------
# 2. DairyPlantsAdapter
# ---------------------------------------------------------------------------


class DairyPlantsAdapter(OntarioRegulatedBaseAdapter):
    """Ontario Provincially Licensed Dairy Plants.

    Fields: name, address, city, postal_code, telephone, licence_number
    """

    source_key = "ontario_dairy_plants"
    _package_id = "provincially-licensed-dairy-plants"
    _resource_keyword = "dairy plant"
    _fallback_url = (
        "https://data.ontario.ca/dataset/provincially-licensed-dairy-plants/"
        "resource/download"
    )
    _source_name = "Ontario — Provincially Licensed Dairy Plants"
    _schedule_cron = "0 8 1 * *"  # monthly

    _column_map: dict[str, str] = {
        "name": "name",
        "plant name": "name",
        "business name": "name",
        "address": "address",
        "street address": "address",
        "city": "city",
        "postal code": "postal_code",
        "postal": "postal_code",
        "telephone": "phone",
        "phone": "phone",
        "phone number": "phone",
        "licence number": "licence_number",
        "license number": "licence_number",
        "licence no": "licence_number",
        "licence #": "licence_number",
        "province": "province",
    }


# ---------------------------------------------------------------------------
# 3. MeatPlantsAdapter
# ---------------------------------------------------------------------------


class MeatPlantsAdapter(OntarioRegulatedBaseAdapter):
    """Ontario Provincially Licensed Meat Plants.

    Fields: name, address, city, postal_code, telephone, coordinates, animal_class
    """

    source_key = "ontario_meat_plants"
    _package_id = "provincially-licensed-meat-plants"
    _resource_keyword = "meat plant"
    _fallback_url = (
        "https://data.ontario.ca/dataset/provincially-licensed-meat-plants/"
        "resource/download"
    )
    _source_name = "Ontario — Provincially Licensed Meat Plants"
    _schedule_cron = "0 8 1 * *"  # monthly

    _column_map: dict[str, str] = {
        "name": "name",
        "plant name": "name",
        "business name": "name",
        "address": "address",
        "street address": "address",
        "city": "city",
        "postal code": "postal_code",
        "postal": "postal_code",
        "telephone": "phone",
        "phone": "phone",
        "phone number": "phone",
        "licence number": "licence_number",
        "license number": "licence_number",
        "licence no": "licence_number",
        "licence #": "licence_number",
        "latitude": "latitude",
        "longitude": "longitude",
        "animal class": "animal_class",
        "class": "animal_class",
        "province": "province",
    }


# ---------------------------------------------------------------------------
# 4. TobaccoAdapter
# ---------------------------------------------------------------------------


class TobaccoAdapter(OntarioRegulatedBaseAdapter):
    """Ontario Tobacco Tax Registrant List.

    Fields: name, address, modification_date
    Note: Less contact data than dairy/meat sources — enrichment value is
    identity/address for tobacco-sector businesses.
    """

    source_key = "ontario_tobacco"
    _package_id = "tobacco-tax-registrant-list"
    _resource_keyword = "tobacco"
    _fallback_url = (
        "https://data.ontario.ca/dataset/tobacco-tax-registrant-list/"
        "resource/download"
    )
    _source_name = "Ontario — Tobacco Tax Registrant List"
    _schedule_cron = "0 8 1 * *"  # monthly

    _column_map: dict[str, str] = {
        "name": "name",
        "registrant name": "name",
        "business name": "name",
        "address": "address",
        "street address": "address",
        "city": "city",
        "province": "province",
        "postal code": "postal_code",
        "postal": "postal_code",
        "phone": "phone",
        "telephone": "phone",
        "modification date": "modification_date",
        "date modified": "modification_date",
        "modified": "modification_date",
        "registration number": "licence_number",
        "registrant number": "licence_number",
    }


# ---------------------------------------------------------------------------
# 5. FuelAdapter
# ---------------------------------------------------------------------------


class FuelAdapter(OntarioRegulatedBaseAdapter):
    """Ontario Fuel and Gasoline Tax Registrant List.

    Fields: name, address, authorization info
    """

    source_key = "ontario_fuel"
    _package_id = "fuel-and-gasoline-tax-registrant-list"
    _resource_keyword = "fuel"
    _fallback_url = (
        "https://data.ontario.ca/dataset/fuel-and-gasoline-tax-registrant-list/"
        "resource/download"
    )
    _source_name = "Ontario — Fuel and Gasoline Tax Registrant List"
    _schedule_cron = "0 8 1 * *"  # monthly

    _column_map: dict[str, str] = {
        "name": "name",
        "registrant name": "name",
        "business name": "name",
        "address": "address",
        "street address": "address",
        "city": "city",
        "province": "province",
        "postal code": "postal_code",
        "postal": "postal_code",
        "phone": "phone",
        "telephone": "phone",
        "authorization number": "licence_number",
        "registration number": "licence_number",
        "registrant number": "licence_number",
        "authorization type": "authorization_type",
        "type": "authorization_type",
    }


# ---------------------------------------------------------------------------
# 6. CSBIFAdapter
# ---------------------------------------------------------------------------


class CSBIFAdapter(OntarioRegulatedBaseAdapter):
    """Ontario Community Small Business Investment Funds (CSBIF).

    Fields: name, address, contact info, registration_date,
            registration_number, status
    """

    source_key = "ontario_csbif"
    _package_id = "community-small-business-investment-funds"
    _resource_keyword = "csbif"
    _fallback_url = (
        "https://data.ontario.ca/dataset/community-small-business-investment-funds/"
        "resource/download"
    )
    _source_name = "Ontario — Community Small Business Investment Funds (CSBIF)"
    _schedule_cron = "0 8 1 * *"  # monthly

    _column_map: dict[str, str] = {
        "name": "name",
        "fund name": "name",
        "business name": "name",
        "address": "address",
        "street address": "address",
        "city": "city",
        "province": "province",
        "postal code": "postal_code",
        "postal": "postal_code",
        "phone": "phone",
        "telephone": "phone",
        "contact": "contact_name",
        "contact name": "contact_name",
        "primary contact": "contact_name",
        "email": "email",
        "website": "website",
        "registration number": "licence_number",
        "registration #": "licence_number",
        "registration date": "registration_date",
        "date registered": "registration_date",
        "status": "licence_status",
    }
