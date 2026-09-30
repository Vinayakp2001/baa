"""BCOrgBookAPIAdapter — BC OrgBook targeted identity/status verification.

Source: BC OrgBook API v4
Format: REST JSON
Grain: CORPORATION (targeted enrichment/verification)
Licence: BC Government Terms of Use

CRITICAL CONSTRAINTS (Req 3.6, 8.9):
  - Targeted lookup ONLY — by BC Reg ID or business name.
  - Bulk enumeration is PROHIBITED by BC Government Terms of Use.
  - The adapter MUST reject any call that attempts to enumerate all entities.
  - 10-page search limit is enforced by the API to prevent enumeration.
  - Throttle at 1.5s between requests per BC guidance.

Fields available from OrgBook (VR09):
  - legal_name, entity_type, entity_status, registration_date
  - credential history (timeline of status changes)
  - jurisdiction (registered_jurisdiction, home_jurisdiction)
  - reason_description (filing event type, e.g. Filing:AMALX)

Fields NOT available (legislatively restricted):
  - address, phone, email, website, directors, ownership, employee count

API endpoints used:
  GET /api/v4/search/autocomplete?q={query}   → find topic_source_id
  GET /api/v4/topic/{topic_id}/credential-set → get full credential history

Requirements: 3.6, 8.9
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from ._http import sha256_hex
from ..base_adapter import SourceAdapter, SourceFetchError, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "bc_orgbook"
_API_BASE = "https://orgbook.gov.bc.ca/api/v4"
_REQUEST_DELAY_S = 1.5  # per BC guidance
_USER_AGENT = "baa-pipeline/0.1 (canada-b2b-data)"

# Maximum results fetched per autocomplete query — hard limit to prevent enumeration
_MAX_AUTOCOMPLETE_RESULTS = 10


class _EnumerationError(Exception):
    """Raised when a caller attempts to enumerate all OrgBook entities."""


class BCOrgBookAPIAdapter(SourceAdapter):
    """Adapter for BC OrgBook API — targeted BC business identity verification.

    Accepts a list of lookup targets, each as either:
      - {"bc_reg_id": "BC0616127"}
      - {"business_name": "TELUS Communications Inc."}
      - {"cra_bn": "123456789"}

    HARD GUARD: the adapter raises an error if called with more than
    `max_bulk_lookups` targets in a single call, preventing accidental
    enumeration via batching. Default limit: 500.

    Usage:
        adapter = BCOrgBookAPIAdapter()
        targets = [
            {"bc_reg_id": "BC0616127"},
            {"business_name": "ACME Corp"},
        ]
        artifact = adapter.fetch(lookup_targets=targets)
        records  = adapter.parse(artifact)
    """

    source_key = _SOURCE_KEY

    # Hard cap — prevents accidental bulk enumeration via large batches
    MAX_BULK_LOOKUPS = 500

    def __init__(
        self,
        api_base: str = _API_BASE,
        request_delay_s: float = _REQUEST_DELAY_S,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._request_delay_s = request_delay_s

    # ------------------------------------------------------------------
    # Enumeration guard
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_not_enumeration(targets: list[dict]) -> None:
        """Raise if the call looks like an attempt to enumerate all entities.

        Specifically rejects:
          - Wildcard / empty queries that would match everything
          - Batch sizes exceeding MAX_BULK_LOOKUPS
        """
        for t in targets:
            query = (
                t.get("business_name") or t.get("bc_reg_id") or t.get("cra_bn") or ""
            ).strip()
            if not query:
                raise _EnumerationError(
                    "BCOrgBookAPIAdapter: empty query rejected — "
                    "targeted lookups only. Bulk enumeration is prohibited by BC Terms of Use."
                )
            if len(query) < 2:
                raise _EnumerationError(
                    f"BCOrgBookAPIAdapter: query '{query}' is too short — "
                    "single-character queries would match too many entities. "
                    "Provide a specific name, BC Reg ID, or CRA BN."
                )

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get_json(self, client: httpx.Client, url: str) -> Any:
        """Fetch a JSON endpoint with throttle and error handling."""
        time.sleep(self._request_delay_s)
        try:
            response = client.get(url)
        except httpx.RequestError as exc:
            raise SourceFetchError(_SOURCE_KEY, f"transport error: {exc}") from exc

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise SourceFetchError(
                _SOURCE_KEY,
                f"HTTP {response.status_code} from {url}",
                status_code=response.status_code,
            )
        try:
            return response.json()
        except Exception as exc:
            raise SourceFetchError(_SOURCE_KEY, f"JSON parse error: {exc}") from exc

    def _autocomplete(self, client: httpx.Client, query: str) -> list[dict]:
        """Run one autocomplete search. Returns up to _MAX_AUTOCOMPLETE_RESULTS."""
        url = f"{self._api_base}/search/autocomplete?q={quote(query)}&page_size={_MAX_AUTOCOMPLETE_RESULTS}"
        data = self._get_json(client, url)
        if data is None:
            return []
        results = data.get("results", data.get("objects", []))
        if isinstance(results, list):
            return results[:_MAX_AUTOCOMPLETE_RESULTS]
        return []

    def _get_credential_set(self, client: httpx.Client, topic_id: int | str) -> list[dict]:
        """Fetch the full credential set for a known topic_id."""
        url = f"{self._api_base}/topic/{topic_id}/credential-set"
        data = self._get_json(client, url)
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return data.get("results", [])

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        since: datetime | None = None,
        *,
        lookup_targets: list[dict] | None = None,
    ) -> RawArtifact:
        """Fetch OrgBook data for a list of targeted lookup queries.

        Args:
            since: Not used. Present for interface compatibility.
            lookup_targets: List of dicts, each with exactly one of:
                - {"bc_reg_id": "BC0616127"}
                - {"business_name": "ACME Corp Inc."}
                - {"cra_bn": "123456789"}

        Raises:
            SourceFetchError: on transport or HTTP errors.
            _EnumerationError: if targets appear to be an enumeration attempt.
        """
        if not lookup_targets:
            raise SourceFetchError(
                _SOURCE_KEY,
                "lookup_targets must be provided — BCOrgBookAPIAdapter is targeted-lookup only",
            )

        if len(lookup_targets) > self.MAX_BULK_LOOKUPS:
            raise _EnumerationError(
                f"BCOrgBookAPIAdapter: {len(lookup_targets)} targets exceeds "
                f"MAX_BULK_LOOKUPS={self.MAX_BULK_LOOKUPS}. "
                "Bulk enumeration is prohibited by BC Terms of Use. "
                "Use targeted lookups for known BC entities only."
            )

        self._assert_not_enumeration(lookup_targets)

        now = datetime.now(tz=timezone.utc)
        all_results: list[dict] = []

        headers = {
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        }

        with httpx.Client(
            timeout=30, follow_redirects=True, headers=headers
        ) as client:
            for target in lookup_targets:
                query = (
                    target.get("bc_reg_id")
                    or target.get("business_name")
                    or target.get("cra_bn")
                    or ""
                ).strip()
                query_type = (
                    "bc_reg_id" if target.get("bc_reg_id")
                    else "cra_bn" if target.get("cra_bn")
                    else "business_name"
                )

                autocomplete_results = self._autocomplete(client, query)

                entry: dict[str, Any] = {
                    "query": query,
                    "query_type": query_type,
                    "autocomplete_count": len(autocomplete_results),
                    "credential_sets": [],
                }

                # For each autocomplete hit, fetch its credential set
                for hit in autocomplete_results[:_MAX_AUTOCOMPLETE_RESULTS]:
                    topic_id = hit.get("id") or hit.get("topic_id")
                    topic_source_id = hit.get("topic_source_id") or hit.get("source_id")

                    if not topic_id:
                        continue

                    cred_set = self._get_credential_set(client, topic_id)

                    entry["credential_sets"].append({
                        "topic_id": topic_id,
                        "topic_source_id": topic_source_id,
                        "autocomplete_hit": hit,
                        "credentials": cred_set,
                    })

                all_results.append(entry)

        payload_str = json.dumps(all_results, ensure_ascii=False, default=str)
        checksum = sha256_hex(payload_str.encode())

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=f"{self._api_base}/search/autocomplete[{len(lookup_targets)} targets]",
            retrieval_timestamp=now,
            http_status=200,
            content_type="application/json",
            checksum_sha256=checksum,
            payload_ref=payload_str,
            source_version=None,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        """Parse OrgBook credential data into RawRecord instances.

        One RawRecord per credential-set entry, containing:
          - legal_name, status, registration_date, entity_type, jurisdiction
          - credential_history list (timeline of changes)
          - source query context (query, query_type, topic_source_id)
        """
        try:
            all_results: list[dict] = json.loads(artifact.payload_ref)
        except Exception as exc:
            raise SourceParseError(_SOURCE_KEY, f"payload parse failed: {exc}") from exc

        records: list[RawRecord] = []

        for entry in all_results:
            query = entry.get("query", "")
            query_type = entry.get("query_type", "")

            for cred_set_entry in entry.get("credential_sets", []):
                topic_source_id = cred_set_entry.get("topic_source_id", "")
                topic_id = cred_set_entry.get("topic_id")
                credentials = cred_set_entry.get("credentials", [])

                # Extract fields from the latest (non-revoked) credential
                legal_name = ""
                status = ""
                registration_date = None
                entity_type = ""
                entity_status = ""
                entity_status_effective = None
                registered_jurisdiction = ""
                home_jurisdiction = ""
                reason_description = ""
                credential_history: list[dict] = []

                # Process all credentials — build history timeline
                for cred in credentials:
                    cred_type_obj = cred.get("credential_type", {})
                    if isinstance(cred_type_obj, dict):
                        cred_type = cred_type_obj.get("description", "")
                    else:
                        cred_type = str(cred_type_obj)

                    attrs = cred.get("attributes", [])
                    cred_attrs: dict[str, str] = {}
                    for attr in attrs:
                        attr_type = (attr.get("type") or attr.get("name") or "").lower()
                        attr_val = str(attr.get("value") or "")
                        cred_attrs[attr_type] = attr_val

                    names = cred.get("names", [])
                    cred_legal_name = ""
                    for n in names:
                        if n.get("type") in ("entity_name", "legal_name"):
                            cred_legal_name = n.get("text") or n.get("value") or ""
                            break
                    if not cred_legal_name and names:
                        cred_legal_name = names[0].get("text") or names[0].get("value") or ""

                    history_entry = {
                        "credential_id": cred.get("id"),
                        "credential_type": cred_type,
                        "effective_date": cred.get("effective_date"),
                        "revoked": cred.get("revoked", False),
                        "revoked_date": cred.get("revoked_date"),
                        "latest": cred.get("latest", False),
                        "inactive": cred.get("inactive", False),
                        "legal_name": cred_legal_name,
                        "attributes": cred_attrs,
                    }
                    credential_history.append(history_entry)

                    # Use the latest credential for canonical fields
                    if cred.get("latest"):
                        legal_name = cred_legal_name or legal_name
                        registration_date = cred_attrs.get("registration_date") or registration_date
                        entity_type = cred_attrs.get("entity_type") or entity_type
                        entity_status = cred_attrs.get("entity_status") or entity_status
                        entity_status_effective = (
                            cred_attrs.get("entity_status_effective") or entity_status_effective
                        )
                        registered_jurisdiction = (
                            cred_attrs.get("registered_jurisdiction") or registered_jurisdiction
                        )
                        home_jurisdiction = (
                            cred_attrs.get("home_jurisdiction") or home_jurisdiction
                        )
                        reason_description = (
                            cred_attrs.get("reason_description") or reason_description
                        )

                # Map OrgBook entity_status codes to pipeline canonical status
                status = _map_orgbook_status(entity_status)

                payload = {
                    "query": query,
                    "query_type": query_type,
                    "topic_source_id": topic_source_id,
                    "topic_id": topic_id,
                    "legal_name": legal_name,
                    "status": status,
                    "entity_status_raw": entity_status,
                    "entity_status_effective": entity_status_effective,
                    "registration_date": registration_date,
                    "entity_type": entity_type,
                    "registered_jurisdiction": registered_jurisdiction,
                    "home_jurisdiction": home_jurisdiction,
                    "reason_description": reason_description,
                    "credential_history": credential_history,
                    "credential_count": len(credentials),
                }

                # Stable record ID: topic_source_id (BC Reg ID) or query hash
                if topic_source_id:
                    record_id = topic_source_id
                else:
                    record_id = hashlib.sha256(
                        f"{query}:{topic_id}".encode()
                    ).hexdigest()[:32]

                records.append(
                    RawRecord(
                        source_key=_SOURCE_KEY,
                        ingestion_run_id=artifact.ingestion_run_id,
                        source_record_id=record_id,
                        raw_payload=payload,
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

            if not payload.get("topic_source_id") and not payload.get("query"):
                row_errors.append("missing identity context (topic_source_id or query)")
            if not payload.get("legal_name"):
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
            source_name="BC OrgBook — Targeted BC Identity/Status Verification",
            adapter_class="BCOrgBookAPIAdapter",
            province="BC",
            source_type="API",
            source_class="C",
            licence="BC Government Terms of Use",
            schedule_cron=None,  # event-triggered only
            rate_limit_rpm=None,  # throttled by request delay, not hard RPM
            base_url=_API_BASE,
            default_grain=SourceGrain.CORPORATION,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _map_orgbook_status(entity_status_code: str) -> str:
    """Map OrgBook entity_status codes to pipeline canonical vocabulary."""
    mapping = {
        "ACT": "ACTIVE",
        "HIS": "DISSOLVED",      # Historical — ceased or amalgamated
        "DIS": "DISSOLVED",
        "SUS": "SUSPENDED",
        "LIQ": "INACTIVE",       # In liquidation
        "":    "UNKNOWN",
    }
    return mapping.get(entity_status_code.upper() if entity_status_code else "", "UNKNOWN")
