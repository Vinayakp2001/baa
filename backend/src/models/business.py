"""ORM models for canonical entity tables (migration 002).

Tables: business, business_location, business_identifier,
        business_contact, person, business_employee_data, business_industry
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, SmallInteger
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Business(Base):
    __tablename__ = "business"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trade_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(2), nullable=True)
    status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, server_default="UNKNOWN"
    )
    sales_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    lead_quality_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    province_gap_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    locations: Mapped[list["BusinessLocation"]] = relationship(
        "BusinessLocation", back_populates="business", cascade="all, delete-orphan"
    )
    identifiers: Mapped[list["BusinessIdentifier"]] = relationship(
        "BusinessIdentifier", back_populates="business", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["BusinessContact"]] = relationship(
        "BusinessContact", back_populates="business", cascade="all, delete-orphan"
    )
    persons: Mapped[list["Person"]] = relationship(
        "Person", back_populates="business", cascade="all, delete-orphan"
    )
    employee_data: Mapped[list["BusinessEmployeeData"]] = relationship(
        "BusinessEmployeeData", back_populates="business", cascade="all, delete-orphan"
    )
    industries: Mapped[list["BusinessIndustry"]] = relationship(
        "BusinessIndustry", back_populates="business", cascade="all, delete-orphan"
    )
    source_records: Mapped[list["SourceRecord"]] = relationship(
        "SourceRecord", back_populates="business"
    )
    field_observations: Mapped[list["FieldObservation"]] = relationship(
        "FieldObservation", back_populates="business", cascade="all, delete-orphan"
    )
    events: Mapped[list["BusinessEvent"]] = relationship(
        "BusinessEvent", back_populates="business", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["BusinessStatusHistory"]] = relationship(
        "BusinessStatusHistory", back_populates="business", cascade="all, delete-orphan"
    )
    merge_candidates_a: Mapped[list["MergeCandidate"]] = relationship(
        "MergeCandidate",
        foreign_keys="MergeCandidate.entity_id_a",
        back_populates="business_a",
        cascade="all, delete-orphan",
    )
    merge_candidates_b: Mapped[list["MergeCandidate"]] = relationship(
        "MergeCandidate",
        foreign_keys="MergeCandidate.entity_id_b",
        back_populates="business_b",
        cascade="all, delete-orphan",
    )
    quality_score: Mapped["BusinessQualityScore | None"] = relationship(
        "BusinessQualityScore", back_populates="business", uselist=False, cascade="all, delete-orphan"
    )
    data_quality_flags: Mapped[list["DataQualityFlag"]] = relationship(
        "DataQualityFlag", back_populates="business", cascade="all, delete-orphan"
    )
    lead_flags: Mapped[list["LeadFlag"]] = relationship(
        "LeadFlag", back_populates="business", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_business_province", "province"),
        Index("ix_business_status", "status"),
        Index("ix_business_sales_ready", "sales_ready"),
    )


class BusinessLocation(Base):
    __tablename__ = "business_location"

    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    address_line1: Mapped[str | None] = mapped_column(String(300), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(2), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(7), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, server_default="CA")
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    raw_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
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
    business: Mapped["Business"] = relationship("Business", back_populates="locations")

    __table_args__ = (Index("ix_business_location_entity_id", "entity_id"),)


class BusinessIdentifier(Base):
    __tablename__ = "business_identifier"

    identifier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    id_type: Mapped[str] = mapped_column(String(50), nullable=False)
    id_value: Mapped[str] = mapped_column(String(200), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="identifiers")

    __table_args__ = (
        Index("ix_business_identifier_type_value", "id_type", "id_value"),
    )


class BusinessContact(Base):
    __tablename__ = "business_contact"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    contact_type: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalised_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    enrichment_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="contacts")

    __table_args__ = (
        Index("ix_business_contact_entity_contact_type", "entity_id", "contact_type"),
    )


class Person(Base):
    __tablename__ = "person"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    person_name: Mapped[str] = mapped_column(String(300), nullable=False)
    role_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role_label_raw: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="persons")

    __table_args__ = (Index("ix_person_entity_id", "entity_id"),)


class BusinessEmployeeData(Base):
    __tablename__ = "business_employee_data"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    raw_employee_value: Mapped[str] = mapped_column(Text, nullable=False)
    employee_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_bucket: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employee_exact: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    employee_source: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_record.record_id", ondelete="SET NULL"), nullable=True
    )
    data_quality_flag: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="employee_data")

    __table_args__ = (Index("ix_business_employee_data_entity_id", "entity_id"),)


class BusinessIndustry(Base):
    __tablename__ = "business_industry"

    industry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.entity_id", ondelete="CASCADE"), nullable=False
    )
    source_naics: Mapped[str | None] = mapped_column(String(20), nullable=True)
    naics_sector: Mapped[str | None] = mapped_column(String(2), nullable=True)
    source_industry_str: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry_source: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.source_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="industries")

    __table_args__ = (Index("ix_business_industry_entity_id", "entity_id"),)
