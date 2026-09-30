"""Canonical entity tables: business, business_location, business_identifier,
business_contact, person, business_employee_data, business_industry

Revision ID: 002
Revises: 001
Create Date: 2026-09-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- business ---
    op.create_table(
        "business",
        sa.Column("entity_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("canonical_name", sa.String(500), nullable=False),
        sa.Column("legal_name", sa.String(500), nullable=True),
        sa.Column("trade_name", sa.String(500), nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=True),
        # CORPORATION | SOLE_PROPRIETOR | PARTNERSHIP | OTHER
        sa.Column("province", sa.CHAR(2), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE", "INACTIVE", "SUSPENDED", "DISSOLVED", "PENDING", "UNKNOWN",
                name="business_status_enum",
            ),
            nullable=True,
            server_default="UNKNOWN",
        ),
        sa.Column("sales_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("lead_quality_score", sa.SmallInteger(), nullable=True),
        sa.Column("province_gap_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("first_seen_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("entity_id"),
    )
    op.create_index("ix_business_province", "business", ["province"])
    op.create_index("ix_business_status", "business", ["status"])
    op.create_index("ix_business_sales_ready", "business", ["sales_ready"])

    # --- business_location ---
    op.create_table(
        "business_location",
        sa.Column("location_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("address_line1", sa.String(300), nullable=True),
        sa.Column("address_line2", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("province", sa.CHAR(2), nullable=True),
        sa.Column("postal_code", sa.CHAR(7), nullable=True),
        sa.Column("country", sa.CHAR(2), nullable=False, server_default="CA"),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("raw_address", sa.Text(), nullable=True),
        sa.Column("location_type", sa.String(50), nullable=True),
        # REGISTERED | OPERATING | MAILING
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("ingestion_run_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_run.run_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("location_id"),
    )
    op.create_index("ix_business_location_entity_id", "business_location", ["entity_id"])

    # --- business_identifier ---
    op.create_table(
        "business_identifier",
        sa.Column("identifier_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("id_type", sa.String(50), nullable=False),
        # CORP_NUMBER | BN | LICENCE_ID | BC_REG_ID | NNI_NUMBER | OTHER
        sa.Column("id_value", sa.String(200), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("identifier_id"),
        sa.UniqueConstraint("id_type", "id_value", name="uq_business_identifier_type_value"),
    )
    op.create_index("ix_business_identifier_type_value", "business_identifier", ["id_type", "id_value"])

    # --- business_contact ---
    op.create_table(
        "business_contact",
        sa.Column("contact_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("contact_type", sa.String(20), nullable=False),
        # PHONE | EMAIL | WEBSITE
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalised_value", sa.Text(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("enrichment_source", sa.String(100), nullable=True),
        sa.Column("confidence", sa.String(10), nullable=True),
        # HIGH | MEDIUM | LOW
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("contact_id"),
    )
    op.create_index("ix_business_contact_entity_contact_type", "business_contact", ["entity_id", "contact_type"])

    # --- person ---
    op.create_table(
        "person",
        sa.Column("person_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("person_name", sa.String(300), nullable=False),
        sa.Column("role_type", sa.String(50), nullable=True),
        # DIRECTOR | OWNER | PRESIDENT | GENERAL_MANAGER |
        # IT_CONTACT | PROCUREMENT_CONTACT | PRIMARY_CONTACT | OTHER
        sa.Column("role_label_raw", sa.String(200), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(10), nullable=True),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("person_id"),
    )
    op.create_index("ix_person_entity_id", "person", ["entity_id"])

    # --- business_employee_data ---
    op.create_table(
        "business_employee_data",
        sa.Column("employee_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("raw_employee_value", sa.Text(), nullable=False),
        sa.Column("employee_min", sa.Integer(), nullable=True),
        sa.Column("employee_max", sa.Integer(), nullable=True),
        # NULL if unbounded (500+)
        sa.Column("employee_bucket", sa.String(20), nullable=True),
        # 1-4|5-9|10-19|20-49|50-99|100-199|200-499|500-999|1000+|500+
        sa.Column("employee_exact", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("employee_source", sa.UUID(), nullable=True),
        sa.Column("source_record_id", sa.UUID(), nullable=True),
        sa.Column("data_quality_flag", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_source"], ["source.source_id"], ondelete="SET NULL"),
        # source_record FK deferred — source_record table created in migration 003
        sa.PrimaryKeyConstraint("employee_id"),
    )
    op.create_index("ix_business_employee_data_entity_id", "business_employee_data", ["entity_id"])

    # --- business_industry ---
    op.create_table(
        "business_industry",
        sa.Column("industry_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("source_naics", sa.String(20), nullable=True),
        sa.Column("naics_sector", sa.CHAR(2), nullable=True),
        sa.Column("source_industry_str", sa.Text(), nullable=True),
        sa.Column("industry_source", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["industry_source"], ["source.source_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("industry_id"),
    )
    op.create_index("ix_business_industry_entity_id", "business_industry", ["entity_id"])


def downgrade() -> None:
    op.drop_index("ix_business_industry_entity_id", "business_industry")
    op.drop_table("business_industry")

    op.drop_index("ix_business_employee_data_entity_id", "business_employee_data")
    op.drop_table("business_employee_data")

    op.drop_index("ix_person_entity_id", "person")
    op.drop_table("person")

    op.drop_index("ix_business_contact_entity_contact_type", "business_contact")
    op.drop_table("business_contact")

    op.drop_index("ix_business_identifier_type_value", "business_identifier")
    op.drop_table("business_identifier")

    op.drop_index("ix_business_location_entity_id", "business_location")
    op.drop_table("business_location")

    op.drop_index("ix_business_sales_ready", "business")
    op.drop_index("ix_business_status", "business")
    op.drop_index("ix_business_province", "business")
    op.drop_table("business")

    op.execute("DROP TYPE IF EXISTS business_status_enum")
