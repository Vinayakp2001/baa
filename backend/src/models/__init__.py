"""ORM models package.

Import order matters here to resolve circular references via SQLAlchemy's
lazy relationship resolution. All models are imported once from this module.
"""

from .base import Base

# Import in dependency order to ensure FK targets are registered first
from .source import Source, IngestionRun
from .business import (
    Business,
    BusinessLocation,
    BusinessIdentifier,
    BusinessContact,
    Person,
    BusinessEmployeeData,
    BusinessIndustry,
)
from .provenance import SourceRecord, FieldObservation
from .events import BusinessEvent, BusinessStatusHistory, MergeCandidate
from .quality import BusinessQualityScore, DataQualityFlag, ProvinceCoverageGap, LeadFlag

__all__ = [
    "Base",
    "Source",
    "IngestionRun",
    "Business",
    "BusinessLocation",
    "BusinessIdentifier",
    "BusinessContact",
    "Person",
    "BusinessEmployeeData",
    "BusinessIndustry",
    "SourceRecord",
    "FieldObservation",
    "BusinessEvent",
    "BusinessStatusHistory",
    "MergeCandidate",
    "BusinessQualityScore",
    "DataQualityFlag",
    "ProvinceCoverageGap",
    "LeadFlag",
]
