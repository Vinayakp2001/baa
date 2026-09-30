"""ORM models for event and history tables (migration 004).

Tables: business_event, business_status_history, merge_candidate
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class BusinessEvent(Base):
    __tablename__ = "business_event"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    event_source: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingestion_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_run.run_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="events")

    __table_args__ = (
        Index("ix_business_event_entity_id", "entity_id"),
        Index("ix_business_event_event_type", "event_type"),
        Index("ix_business_event_event_date", "event_date"),
    )


class BusinessStatusHistory(Base):
    __tablename__ = "business_status_history"

    history_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    ingestion_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_run.run_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="status_history")

    __table_args__ = (Index("ix_business_status_history_entity_id", "entity_id"),)


class MergeCandidate(Base):
    __tablename__ = "merge_candidate"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id_a: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    entity_id_b: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    confidence: Mapped[str] = mapped_column(String(10), nullable=False)
    match_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    auto_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business_a: Mapped["Business"] = relationship(
        "Business", foreign_keys=[entity_id_a], back_populates="merge_candidates_a"
    )
    business_b: Mapped["Business"] = relationship(
        "Business", foreign_keys=[entity_id_b], back_populates="merge_candidates_b"
    )

    __table_args__ = (
        Index("ix_merge_candidate_entity_id_a", "entity_id_a"),
        Index("ix_merge_candidate_entity_id_b", "entity_id_b"),
        Index("ix_merge_candidate_auto_resolved", "auto_resolved"),
    )
