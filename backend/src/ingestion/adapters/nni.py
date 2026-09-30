"""NNIAdapter — Nunavummi Nangminiqaqtunik Ikajuuti (NNI) Business Registry.

Source: NNI Business Registry — nni.gov.nu.ca
Format: HTML (Drupal CMS) — scraped via BeautifulSoup
Grain: CORPORATION
Licence: UNRESOLVED — NNI Regulations PDF review required

CRITICAL CONSTRAINT (Req 3.7):
  THIS ADAPTER MUST CHECK `source.terms_status` BEFORE ANY PROCESSING.
  If terms_status != 'CLEARED', the adapter MUST:
    - Log a warning
    - Return an empty RawArtifact (no records)
    - NOT write any data to the canonical layer

  The adapter enforces this at fetch() time via a terms_status parameter.
  The caller (ingestion service) is responsible for reading terms_status
  from the source registry and passing it in.

Source notes (VR13.1):
  - 187 active businesses at /business/list (all-Nunavut)
  - Profile pages at /business/profile/{id}
  - Fields: business_name, business_number, business_type, street_address,
    city_community, postal_code, phone, email, contact_name, no_of_employees
    (integer), sectors[], goods[], services[], territory_province,
    business_status, effective_date
  - No pagination on /business/list (187 rows, single page)
  - Phone is conditional — present on some records, absent on others
  - Effective date = NNI registration/renewal date (NOT incorporation date)
  - employee count is a raw integer — passed to normaliser as-is

Ingestion pattern (VR13.1):
  1. GET /business/list → extract all 187 rows + profile_ids
  2. GET /business/profile/{id} for each → parse full field set
  3. Throttle between requests (Drupal CMS — respect server)

Requirements: 3.7, 8.10
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceFetchError, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult
from ...core.logging import get_logger

_SOURCE_KEY = "nni"
_BASE_URL = "https://nni.gov.nu.ca"
_LIST_URL = f"{_BASE_URL}/business/list"
_PROFILE_URL_TEMPLATE = f"{_BASE_URL}/business/profile/{{profile_id}}"
_REQUEST_DELAY_S = 1.0  # conservative — Drupal CMS
_USER_AGENT = "baa-pipeline/0.1 (canada-b2b-data)"

logger = get_logger(__name__)

# terms_status value that must be present before any data is processed
_REQUIRED_TERMS_STATUS = "CLEARED"


class NNITermsNotClearedError(Exception):
    """Raised when NNI terms_status != CLEARED."""


class NNIAdapter(SourceAdapter):
    """Adapter for NNI Business Registry — Nunavut businesses.

    TERMS GUARD: The adapter requires `terms_status='CLEARED'` before
    processing any data. Pass `terms_status` to `fetch()`:

        adapter = NNIAdapter()
        artifact = adapter.fetch(terms_status='CLEARED')  # when cleared

    If terms_status is anything other than 'CLEARED', fetch() returns an
    empty artifact and logs a warning. No canonical data is written.
    """

    source_key = _SOURCE_KEY

    def __init__(
        self,
        base_url: str = _BASE_URL,
        request_delay_s: float = _REQUEST_DELAY_S,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._list_url = f"{self._base_url}/business/list"
        self._request_delay_s = request_delay_s

    # ------------------------------------------------------------------
    # Terms enforcement
    # ------------------------------------------------------------------

    def _check_terms(self, terms_status: str) -> bool:
        """Return True if terms are cleared, False + log warning otherwise."""
        if terms_status != _REQUIRED_TERMS_STATUS:
            logger.warning(
                "nni_terms_not_cleared",
                source_key=_SOURCE_KEY,
                terms_status=terms_status,
                message=(
                    "NNI Regulations PDF has not been reviewed and marked CLEARED. "
                    "NNI data will NOT be processed into the canonical layer. "
                    "Review the NNI Regulations PDF at "
                    "https://nni.gov.nu.ca/sites/nni.gov.nu.ca/files/NNI-Regs-amendment_2.pdf "
                    "and update source.terms_status to 'CLEARED' when confirmed permissible."
                ),
            )
            return False
        return True

    # ------------------------------------------------------------------
    # HTML parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_profile_ids(html: str) -> list[int]:
        """Extract all business profile IDs from the /business/list page."""
        soup = BeautifulSoup(html, "lxml")
        ids: list[int] = []

        # Profile links are /business/profile/{id}
        for link in soup.find_all("a", href=re.compile(r"/business/profile/(\d+)")):
            m = re.search(r"/business/profile/(\d+)", link["href"])
            if m:
                ids.append(int(m.group(1)))

        return list(dict.fromkeys(ids))  # deduplicate preserving order

    @staticmethod
    def _extract_list_row(html: str) -> list[dict[str, str]]:
        """Extract summary rows (name, effective_date, community) from list page."""
        soup = BeautifulSoup(html, "lxml")
        rows: list[dict[str, str]] = []

        # NNI list: each business is a <tr> or <div> with name/date/community
        # Try table rows first
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                if name and name.lower() != "company name":
                    row: dict[str, str] = {"company_name": name}
                    if len(cells) >= 2:
                        row["effective_date"] = cells[1].get_text(strip=True)
                    if len(cells) >= 3:
                        row["community"] = cells[2].get_text(strip=True)
                    rows.append(row)

        return rows

    @staticmethod
    def _parse_profile_page(html: str, profile_id: int) -> dict[str, Any]:
        """Parse a single /business/profile/{id} page into a field dict.

        Profile pages use <table> with <td> label/value pairs (VR13.1).
        """
        soup = BeautifulSoup(html, "lxml")
        fields: dict[str, Any] = {"profile_id": profile_id}

        # Extract all label/value table pairs
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) == 2:
                label = cells[0].get_text(strip=True).lower().rstrip(":")
                value = cells[1].get_text(separator=" ", strip=True)
                fields[label] = value

        # Extract <time datetime="..."> for effective_date
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            fields["effective_date"] = time_tag["datetime"]

        # Extract sector/goods/services lists
        for section_label in ("sectors", "goods", "services"):
            ul = soup.find("ul", class_=re.compile(section_label, re.I))
            if not ul:
                # Try to find by heading proximity
                heading = soup.find(
                    lambda tag: tag.name in ("h3", "h4", "td", "th", "strong")
                    and section_label in tag.get_text(strip=True).lower()
                )
                if heading:
                    ul = heading.find_next("ul")

            if ul:
                items = [li.get_text(strip=True) for li in ul.find_all("li")]
                fields[section_label] = items

        return fields

    @staticmethod
    def _normalise_profile_fields(raw: dict[str, Any]) -> dict[str, Any]:
        """Map raw profile field labels to canonical field names."""
        # Common label variants observed in VR13.1
        label_map = {
            "business name": "business_name",
            "company name": "business_name",
            "business number": "business_number",
            "registration number": "business_number",
            "business type": "business_type",
            "type": "business_type",
            "street address": "street_address",
            "address": "street_address",
            "city/community": "community",
            "community": "community",
            "city": "community",
            "location": "community",
            "postal code": "postal_code",
            "postal": "postal_code",
            "phone": "phone",
            "telephone": "phone",
            "phone number": "phone",
            "contact name": "contact_name",
            "primary contact": "contact_name",
            "contact": "contact_name",
            "no. of employees": "employee_count",
            "no of employees": "employee_count",
            "number of employees": "employee_count",
            "employees": "employee_count",
            "email": "email",
            "email address": "email",
            "website": "website",
            "web site": "website",
            "territory/province": "territory_province",
            "territory": "territory_province",
            "province": "territory_province",
            "status": "business_status",
            "business status": "business_status",
            "effective date": "effective_date",
            "sectors": "sectors",
            "goods": "goods",
            "services": "services",
            "profile_id": "profile_id",
        }

        normalised: dict[str, Any] = {}
        for key, val in raw.items():
            canonical = label_map.get(key.lower(), key)
            normalised[canonical] = val

        # Parse employee_count to integer if present
        emp_raw = normalised.get("employee_count", "")
        if emp_raw and isinstance(emp_raw, str):
            m = re.search(r"\d+", emp_raw)
            if m:
                normalised["employee_count"] = int(m.group())
                normalised["raw_employee_value"] = emp_raw
            else:
                normalised["employee_count"] = None
                normalised["raw_employee_value"] = emp_raw
        elif isinstance(emp_raw, int):
            normalised["raw_employee_value"] = str(emp_raw)

        return normalised

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        since: datetime | None = None,
        *,
        terms_status: str = "UNRESOLVED",
    ) -> RawArtifact:
        """Fetch NNI business list and all profile pages.

        TERMS GUARD: Returns an empty artifact immediately if
        terms_status != 'CLEARED'.

        Args:
            since: Not used — NNI is a full snapshot (187 businesses).
            terms_status: Value from source.terms_status in the registry.
                          Must be 'CLEARED' to proceed.

        Returns:
            RawArtifact with JSON payload of all business profiles.
            Empty artifact (empty list payload) if terms not cleared.
        """
        now = datetime.now(tz=timezone.utc)

        # TERMS CHECK — must happen before any processing
        if not self._check_terms(terms_status):
            empty_payload = json.dumps([], ensure_ascii=False)
            return RawArtifact(
                source_key=_SOURCE_KEY,
                ingestion_run_id=uuid.uuid4(),
                retrieval_url=self._list_url,
                retrieval_timestamp=now,
                http_status=0,
                content_type=None,
                checksum_sha256=sha256_hex(b""),
                payload_ref=empty_payload,
                source_version=f"terms_status:{terms_status}",
            )

        # Fetch the business list page
        headers = {"User-Agent": _USER_AGENT}
        list_raw, list_status, _ = fetch_bytes(
            self._list_url, source_key=_SOURCE_KEY, headers=headers
        )

        profile_ids = self._extract_profile_ids(list_raw.decode("utf-8", errors="replace"))
        if not profile_ids:
            raise SourceParseError(
                _SOURCE_KEY,
                "No profile IDs found on /business/list — page structure may have changed",
            )

        # Fetch each profile page
        all_profiles: list[dict[str, Any]] = []
        for profile_id in profile_ids:
            time.sleep(self._request_delay_s)

            profile_url = f"{self._base_url}/business/profile/{profile_id}"
            try:
                profile_raw, _, _ = fetch_bytes(
                    profile_url, source_key=_SOURCE_KEY, headers=headers
                )
                raw_fields = self._parse_profile_page(
                    profile_raw.decode("utf-8", errors="replace"), profile_id
                )
                normalised = self._normalise_profile_fields(raw_fields)
                normalised["profile_url"] = profile_url
                all_profiles.append(normalised)
            except SourceFetchError:
                # Log and continue — don't abort on single profile failure
                logger.warning(
                    "nni_profile_fetch_failed",
                    profile_id=profile_id,
                    profile_url=profile_url,
                )
                continue

        payload_str = json.dumps(all_profiles, ensure_ascii=False, default=str)
        checksum = sha256_hex(payload_str.encode())

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=self._list_url,
            retrieval_timestamp=now,
            http_status=list_status,
            content_type="text/html",
            checksum_sha256=checksum,
            payload_ref=payload_str,
            source_version=now.date().isoformat(),
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        try:
            profiles: list[dict] = json.loads(artifact.payload_ref)
        except Exception as exc:
            raise SourceParseError(_SOURCE_KEY, f"payload parse failed: {exc}") from exc

        records: list[RawRecord] = []
        for profile in profiles:
            business_name = profile.get("business_name", "")
            business_number = profile.get("business_number", "")
            community = profile.get("community", "")
            profile_id = profile.get("profile_id")

            # Stable record ID: business_number if available, else profile_id, else hash
            if business_number:
                record_id = str(business_number)
            elif profile_id:
                record_id = f"nni:{profile_id}"
            else:
                record_id = hashlib.sha256(
                    f"{business_name}:{community}".encode()
                ).hexdigest()[:32]

            records.append(
                RawRecord(
                    source_key=_SOURCE_KEY,
                    ingestion_run_id=artifact.ingestion_run_id,
                    source_record_id=record_id,
                    raw_payload=profile,
                    source_grain=SourceGrain.CORPORATION,
                )
            )
        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        errors: dict[str, list[str]] = {}
        invalid = 0

        for rec in records:
            payload = rec.raw_payload
            row_errors: list[str] = []

            if not payload.get("business_name"):
                row_errors.append("missing business_name")
            if not payload.get("community") and not payload.get("street_address"):
                row_errors.append("missing location (community or street_address)")

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
            source_name="NNI Business Registry — Nunavut",
            adapter_class="NNIAdapter",
            province="NU",
            source_type="HTML",
            source_class="A",  # Would be A/B/C when cleared — set A as placeholder
            licence="UNRESOLVED — NNI Regulations PDF review required",
            schedule_cron="0 8 1 * *",  # monthly — effective when cleared
            rate_limit_rpm=None,
            base_url=_BASE_URL,
            default_grain=SourceGrain.CORPORATION,
        )
