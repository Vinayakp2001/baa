"""ORM models for provenance tables (migration 003).

Tables: source_record, field_observation
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class SourceRecord(Base):
    __tablename__ = "source_record"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="RESTRICT"), nullable=False
    )
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_run.run_id", ondelete="RESTRICT"), nullable=False
    )
    source_record_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_grain: Mapped[str | None] = mapped_column(String(30), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalised_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="SET NULL"), nullable=True
    )
    resolution_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resolution_confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source")
    ingestion_run: Mapped["IngestionRun"] = relationship("IngestionRun", back_populates="source_records")
    business: Mapped["Business | None"] = relationship("Business", back_populates="source_records")
    field_observations: Mapped[list["FieldObservation"]] = relationship(
        "FieldObservation", back_populates="source_record"
    )

    __table_args__ = (
        Index("ix_source_record_source_id", "source_id"),
        Index("ix_source_record_ingestion_run_id", "ingestion_run_id"),
        Index("ix_source_record_entity_id", "entity_id"),
        Index("ix_source_record_resolution_status", "resolution_status"),
    )


class FieldObservation(Base):
    __tablename__ = "field_observation"

    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalised_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="RESTRICT"), nullable=False
    )
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_run.run_id", ondelete="RESTRICT"), nullable=False
    )
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_record.record_id", ondelete="SET NULL"), nullable=True
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="field_observations")
    source: Mapped["Source"] = relationship("Source")
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="field_observations"
    )
    source_record: Mapped["SourceRecord | None"] = relationship(
        "SourceRecord", back_populates="field_observations"
    )

    __table_args__ = (
        Index("ix_field_observation_entity_field_observed", "entity_id", "field_name", "observed_at"),
        Index("ix_field_observation_entity_id", "entity_id"),
        Index("ix_field_observation_is_current", "is_current"),
    )
