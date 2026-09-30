"""Provenance tables: source_record, field_observation

Revision ID: 003
Revises: 002
Create Date: 2026-09-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- source_record ---
    op.create_table(
        "source_record",
        sa.Column("record_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("ingestion_run_id", sa.UUID(), nullable=False),
        sa.Column("source_record_id", sa.String(200), nullable=True),
        sa.Column("source_grain", sa.String(30), nullable=True),
        # CORPORATION | LICENCE | EVENT | REGISTRATION | ESTABLISHMENT
        sa.Column("raw_payload", JSONB(), nullable=False),
        sa.Column("normalised_payload", JSONB(), nullable=True),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        # NULL until resolved
        sa.Column("resolution_status", sa.String(20), nullable=True),
        # PENDING | MATCHED | NEW | CANDIDATE | SKIPPED
        sa.Column("resolution_confidence", sa.String(10), nullable=True),
        # HIGH | MEDIUM | LOW
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_run.run_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("record_id"),
    )
    op.create_index("ix_source_record_source_id", "source_record", ["source_id"])
    op.create_index("ix_source_record_ingestion_run_id", "source_record", ["ingestion_run_id"])
    op.create_index("ix_source_record_entity_id", "source_record", ["entity_id"])
    op.create_index("ix_source_record_resolution_status", "source_record", ["resolution_status"])

    # Now that source_record exists, add the FK from business_employee_data.source_record_id
    op.create_foreign_key(
        "fk_employee_data_source_record",
        "business_employee_data",
        "source_record",
        ["source_record_id"],
        ["record_id"],
        ondelete="SET NULL",
    )

    # --- field_observation ---
    op.create_table(
        "field_observation",
        sa.Column("observation_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("normalised_value", sa.Text(), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("ingestion_run_id", sa.UUID(), nullable=False),
        sa.Column("source_record_id", sa.UUID(), nullable=True),
        sa.Column("observed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("confidence", sa.String(10), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_run.run_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.record_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("observation_id"),
    )
    # Compound index per design.md requirement
    op.create_index(
        "ix_field_observation_entity_field_observed",
        "field_observation",
        ["entity_id", "field_name", "observed_at"],
    )
    op.create_index("ix_field_observation_entity_id", "field_observation", ["entity_id"])
    op.create_index("ix_field_observation_is_current", "field_observation", ["is_current"])


def downgrade() -> None:
    op.drop_index("ix_field_observation_is_current", "field_observation")
    op.drop_index("ix_field_observation_entity_id", "field_observation")
    op.drop_index("ix_field_observation_entity_field_observed", "field_observation")
    op.drop_table("field_observation")

    op.drop_constraint("fk_employee_data_source_record", "business_employee_data", type_="foreignkey")

    op.drop_index("ix_source_record_resolution_status", "source_record")
    op.drop_index("ix_source_record_entity_id", "source_record")
    op.drop_index("ix_source_record_ingestion_run_id", "source_record")
    op.drop_index("ix_source_record_source_id", "source_record")
    op.drop_table("source_record")
