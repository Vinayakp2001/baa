"""ORM models for quality scoring and sales layer tables (migration 004).

Tables: business_quality_score, data_quality_flag, province_coverage_gap, lead_flag
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class BusinessQualityScore(Base):
    __tablename__ = "business_quality_score"

    score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business.entity_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    identity_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    address_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    phone_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    email_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    employee_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    industry_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    contact_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    recency_confidence: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    source_reliability: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    lead_quality_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="quality_score")


class DataQualityFlag(Base):
    __tablename__ = "data_quality_flag"

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    flag_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    flag_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    business: Mapped["Business | None"] = relationship("Business", back_populates="data_quality_flags")

    __table_args__ = (
        Index("ix_data_quality_flag_entity_id", "entity_id"),
        Index("ix_data_quality_flag_resolved", "resolved"),
    )


class ProvinceCoverageGap(Base):
    __tablename__ = "province_coverage_gap"

    gap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    province: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    gap_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LeadFlag(Base):
    __tablename__ = "lead_flag"

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    flag_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    flag_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    set_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    set_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="lead_flags")

    __table_args__ = (
        Index("ix_lead_flag_entity_id", "entity_id"),
        Index("ix_lead_flag_flag_type", "flag_type"),
    )
