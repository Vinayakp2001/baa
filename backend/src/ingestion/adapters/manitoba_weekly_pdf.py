"""ManitobaWeeklyPDFAdapter — Manitoba Companies Office Weekly Filing PDF.

Source: Manitoba Companies Office — Listing of Recent Filings
Format: PDF (weekly, pdfplumber)
Grain: EVENT
Event type: PROVINCIAL_REGISTRATION
Licence: Government of Manitoba public access

Key field notes (VR08):
  - Listing page: https://companiesoffice.gov.mb.ca/listings.html
  - PDFs follow pattern: YYYY-MM-DD.en.pdf
  - The "Certificates of Incorporation" / "Incorporations" section contains new registrations
  - Each record has: File No., company name, registered_office
  - Zero cross-week overlap confirmed (VR08) → de-duplicate by file_no within run
  - Only the latest PDF is downloaded; prior weeks must be archived separately

Requirements: 3.8, 6.2
"""

from __future__ import annotations

import hashlib
import io
import re
import uuid
from datetime import datetime, timezone

import pdfplumber
from bs4 import BeautifulSoup

from ._http import fetch_bytes, sha256_hex
from ..base_adapter import SourceAdapter, SourceFetchError, SourceParseError
from ..contracts import RawArtifact, RawRecord, SourceGrain, SourceMetadata, ValidationResult

_SOURCE_KEY = "manitoba_weekly_pdf"

_LISTING_URL = "https://companiesoffice.gov.mb.ca/listings.html"
_PDF_BASE = "https://companiesoffice.gov.mb.ca/comp_off/listings/"

# Section headings that indicate new incorporation / registration events
_INCORPORATION_PATTERNS = [
    r"certificates?\s+of\s+incorporation",
    r"articles?\s+of\s+incorporation",
    r"incorporations?",
    r"business\s+name\s+registrations?",
    r"registrations?\s+of\s+business\s+names?",
]


def _is_incorporation_section(heading: str) -> bool:
    for pat in _INCORPORATION_PATTERNS:
        if re.search(pat, heading, re.IGNORECASE):
            return True
    return False


def _discover_latest_pdf_url(listing_html: str) -> str | None:
    """Parse listing page HTML to find the most recent PDF URL."""
    soup = BeautifulSoup(listing_html, "lxml")
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    links: list[tuple[str, str]] = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".en.pdf" in href.lower() or (
            "listings" in href.lower() and href.lower().endswith(".pdf")
        ):
            m = date_pattern.search(href)
            if m:
                date_str = m.group(1)
                if href.startswith("http"):
                    full_url = href
                elif href.startswith("/"):
                    full_url = "https://companiesoffice.gov.mb.ca" + href
                else:
                    full_url = _PDF_BASE + href.split("/")[-1]
                links.append((date_str, full_url))

    if not links:
        return None

    # Sort newest-first, return the most recent
    links.sort(reverse=True)
    return links[0][1]


def _extract_text_from_pdf(raw_bytes: bytes) -> str:
    """Extract all page text from PDF bytes using pdfplumber."""
    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except Exception as exc:
        raise SourceParseError(_SOURCE_KEY, f"pdfplumber failed: {exc}") from exc


def _parse_incorporation_records(text: str) -> list[dict[str, str]]:
    """Extract records from the Incorporations section of the filing PDF."""
    lines = text.split("\n")

    # Locate the incorporation section boundaries
    in_section = False
    section_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_section:
                section_lines.append(line)
            continue

        if _is_incorporation_section(stripped):
            in_section = True
            continue

        # A new non-incorporation heading ends the section
        if in_section and re.match(r"^[A-Z][A-Za-z\s/]+$", stripped) and len(stripped) > 4:
            # Check if this is another major section heading
            looks_like_heading = (
                stripped.isupper() or
                re.match(r"(amendments?|revivals?|dissolutions?|amalgamation|continuations?)", stripped, re.IGNORECASE)
            )
            if looks_like_heading and stripped not in section_lines:
                break

        if in_section:
            section_lines.append(line)

    if not section_lines:
        return []

    section_text = "\n".join(section_lines)

    # Split into record blocks by "File No." marker
    blocks = re.split(r"(?=file\s+no\.?\s*:?\s*[\w\-]+)", section_text, flags=re.IGNORECASE)

    records: list[dict[str, str]] = []
    seen_file_nos: set[str] = set()

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        record: dict[str, str] = {}

        # File No.
        m = re.search(r"file\s+no\.?\s*:?\s*([\w\-]+)", block, re.IGNORECASE)
        if m:
            file_no = m.group(1).strip()
            # De-duplicate within this run
            if file_no in seen_file_nos:
                continue
            seen_file_nos.add(file_no)
            record["file_no"] = file_no

        # Company name — first meaningful ALL-CAPS line
        cap_lines = [
            ln.strip() for ln in block.split("\n")
            if ln.strip().isupper() and 4 < len(ln.strip()) < 150
        ]
        if cap_lines:
            record["company_name"] = cap_lines[0]

        # Registered office
        m = re.search(r"registered\s+office\s*:?\s*(.+?)(?=\n|$)", block, re.IGNORECASE)
        if m:
            record["registered_office"] = m.group(1).strip()[:200]

        # Date of incorporation
        for label in ["date of incorporation", "date of registration", "effective date", "date"]:
            m = re.search(
                rf"{label}\s*:?\s*(\w+ \d+,? \d{{4}}|\d{{4}}-\d{{2}}-\d{{2}})",
                block, re.IGNORECASE
            )
            if m:
                record["incorporation_date"] = m.group(1).strip()
                break

        record["event_type"] = "PROVINCIAL_REGISTRATION"

        if record.get("file_no") or record.get("company_name"):
            records.append(record)

    return records


class ManitobaWeeklyPDFAdapter(SourceAdapter):
    """Adapter for Manitoba Companies Office weekly filing PDF.

    Fetches the listing page, discovers the most recent PDF URL, downloads
    the PDF, extracts text with pdfplumber, and parses Incorporations section
    records with grain=EVENT and event_type=PROVINCIAL_REGISTRATION.

    De-duplicates within the run by file_no.
    """

    source_key = _SOURCE_KEY

    def __init__(
        self,
        listing_url: str = _LISTING_URL,
    ) -> None:
        self._listing_url = listing_url

    # ------------------------------------------------------------------
    # SourceAdapter interface
    # ------------------------------------------------------------------

    def fetch(self, since: datetime | None = None) -> RawArtifact:
        now = datetime.now(tz=timezone.utc)

        # Step 1: parse listing page to discover latest PDF URL
        listing_raw, _, _ = fetch_bytes(self._listing_url, source_key=_SOURCE_KEY)
        listing_html = listing_raw.decode("utf-8", errors="replace")
        pdf_url = _discover_latest_pdf_url(listing_html)

        if pdf_url is None:
            raise SourceFetchError(_SOURCE_KEY, "no PDF links found on listing page")

        # Step 2: download the PDF
        pdf_raw, http_status, content_type = fetch_bytes(pdf_url, source_key=_SOURCE_KEY)

        # Extract the date from the URL for source_version
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", pdf_url)
        source_version = date_match.group(1) if date_match else None

        return RawArtifact(
            source_key=_SOURCE_KEY,
            ingestion_run_id=uuid.uuid4(),
            retrieval_url=pdf_url,
            retrieval_timestamp=now,
            http_status=http_status,
            content_type=content_type,
            checksum_sha256=sha256_hex(pdf_raw),
            # Store raw PDF as latin-1 string for transport
            payload_ref=pdf_raw.decode("latin-1"),
            source_version=source_version,
        )

    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        pdf_bytes = artifact.payload_ref.encode("latin-1")
        text = _extract_text_from_pdf(pdf_bytes)
        rows = _parse_incorporation_records(text)

        records: list[RawRecord] = []
        for row in rows:
            record_id = (
                row.get("file_no")
                or hashlib.sha256(str(row).encode()).hexdigest()[:32]
            )
            records.append(
                RawRecord(
                    source_key=_SOURCE_KEY,
                    ingestion_run_id=artifact.ingestion_run_id,
                    source_record_id=record_id,
                    raw_payload=row,
                    source_grain=SourceGrain.EVENT,
                )
            )
        return records

    def validate(self, records: list[RawRecord]) -> ValidationResult:
        errors: dict[str, list[str]] = {}
        invalid = 0

        for rec in records:
            row_errors: list[str] = []
            if not rec.raw_payload.get("company_name"):
                row_errors.append("missing company_name")
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
            source_name="Manitoba Companies Office — Weekly Filing Listings (PDF)",
            adapter_class="ManitobaWeeklyPDFAdapter",
            province="MB",
            source_type="PDF",
            source_class="B",
            licence="Manitoba Government public access",
            schedule_cron="0 9 * * 5",  # weekly Friday 9am
            rate_limit_rpm=None,
            base_url="https://companiesoffice.gov.mb.ca",
            default_grain=SourceGrain.EVENT,
        )
