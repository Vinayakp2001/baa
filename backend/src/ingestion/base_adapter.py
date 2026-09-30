"""SourceAdapter abstract base class.

Every source adapter MUST subclass this and implement all four methods.
The interface is intentionally narrow — domain logic lives in the adapter,
orchestration lives in the ingestion service routes.

Requirements: 3.1, 3.2
"""

from __future__ import annotations

import abc
from datetime import datetime

from .contracts import RawArtifact, RawRecord, SourceMetadata, ValidationResult


class SourceAdapter(abc.ABC):
    """Abstract base class for all source adapters.

    Subclasses implement exactly four methods:
      - fetch()        → retrieve raw bytes/content from source
      - parse()        → convert artifact into structured RawRecord list
      - validate()     → assert the parsed records meet expected schema
      - get_metadata() → return static source configuration

    The adapter is stateless between calls. Any state (e.g. last_run_at)
    is passed in as arguments or read from the database by the caller.
    """

    #: Every subclass must declare its source_key to match source.source_key in DB
    source_key: str

    @abc.abstractmethod
    def fetch(self, since: datetime | None = None) -> RawArtifact:
        """Fetch raw data from the source.

        Args:
            since: If the source supports incremental fetching, only retrieve
                   records newer than this timestamp. None means full refresh.

        Returns:
            RawArtifact containing the payload reference and retrieval metadata.

        Raises:
            SourceFetchError: on any retrieval failure. The caller logs the error
                              and marks the ingestion_run as FAILED.
        """

    @abc.abstractmethod
    def parse(self, artifact: RawArtifact) -> list[RawRecord]:
        """Parse a raw artifact into a list of RawRecord instances.

        Args:
            artifact: The artifact returned by fetch().

        Returns:
            List of RawRecord, one per source row/entity.

        Raises:
            SourceParseError: on unrecoverable parse failures.
        """

    @abc.abstractmethod
    def validate(self, records: list[RawRecord]) -> ValidationResult:
        """Validate parsed records against the expected source schema.

        Validation is advisory — the ingestion service logs failures but
        does not abort on partial validation failures. Adapters decide what
        constitutes a hard failure vs. a skippable row.

        Args:
            records: Output from parse().

        Returns:
            ValidationResult with pass/fail summary and per-field errors.
        """

    @abc.abstractmethod
    def get_metadata(self) -> SourceMetadata:
        """Return static configuration metadata for this adapter.

        Used to register or verify the source row in the source registry table.
        """


# ---------------------------------------------------------------------------
# Adapter-specific exceptions
# ---------------------------------------------------------------------------


class SourceFetchError(Exception):
    """Raised when a source adapter cannot retrieve data.

    Requirement 3.4: failure reason must be recorded in ingestion_run.
    """

    def __init__(self, source_key: str, reason: str, status_code: int | None = None) -> None:
        self.source_key = source_key
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"[{source_key}] fetch failed: {reason}")


class SourceParseError(Exception):
    """Raised when a source adapter cannot parse a fetched artifact."""

    def __init__(self, source_key: str, reason: str) -> None:
        self.source_key = source_key
        self.reason = reason
        super().__init__(f"[{source_key}] parse failed: {reason}")
