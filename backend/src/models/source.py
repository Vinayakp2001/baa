"""ORM models for source registry and ingestion tracking (migration 001)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, SmallInteger, String, Text
from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Source(Base):
    __tablename__ = "source"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    adapter_class: Mapped[str] = mapped_column(String(100), nullable=False)
    province: Mapped[str | None] = mapped_column(String(2), nullable=True)
    source_type: Mapped[str] = mapped_column(
        Enum("CSV", "JSON", "API", "HTML", "PDF", "GeoJSON", "XLSX", name="source_type_enum"),
        nullable=False,
    )
    source_class: Mapped[str] = mapped_column(
        Enum("A", "B", "C", "D", name="source_class_enum"),
        nullable=False,
    )
    licence: Mapped[str | None] = mapped_column(String(200), nullable=True)
    schedule_cron: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    rate_limit_rpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_header_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    terms_status: Mapped[str] = mapped_column(
        Enum("CLEARED", "UNRESOLVED", "BLOCKED", "NOT_SUITABLE", name="terms_status_enum"),
        nullable=False,
        server_default="CLEARED",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun", back_populates="source", cascade="all, delete-orphan"
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_run"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="RESTRICT"), nullable=False
    )
    run_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    run_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_status: Mapped[str] = mapped_column(
        Enum("RUNNING", "COMPLETED", "FAILED", "PARTIAL", name="run_status_enum"),
        nullable=False,
        server_default="RUNNING",
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieval_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_version_or_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    record_count_raw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    record_count_normalised: Mapped[int | None] = mapped_column(Integer, nullable=True)
    record_count_new: Mapped[int | None] = mapped_column(Integer, nullable=True)
    record_count_updated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    record_count_flagged: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="ingestion_runs")
    source_records: Mapped[list["SourceRecord"]] = relationship(
        "SourceRecord", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    field_observations: Mapped[list["FieldObservation"]] = relationship(
        "FieldObservation", back_populates="ingestion_run"
    )

    __table_args__ = (
        Index("ix_ingestion_run_source_id", "source_id"),
        Index("ix_ingestion_run_run_status", "run_status"),
    )
