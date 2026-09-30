"""Event, quality, and sales layer tables:
business_event, business_status_history, merge_candidate,
business_quality_score, data_quality_flag, province_coverage_gap, lead_flag

Revision ID: 004
Revises: 003
Create Date: 2026-09-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- business_event ---
    op.create_table(
        "business_event",
        sa.Column("event_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        # FEDERAL_INCORPORATION | PROVINCIAL_REGISTRATION | MUNICIPAL_LICENCE_FIRST_ISSUE
        # MUNICIPAL_LICENCE_RENEWAL | LICENCE_STATUS_CHANGE | REGISTRY_FILING
        # NNI_REGISTRATION_RENEWAL | BUSINESS_DISCOVERED | BUSINESS_UPDATED
        # STATUS_CHANGED | LOCATION_ADDED | LOCATION_CHANGED | NAME_CHANGED
        # LICENCE_ISSUED | LICENCE_EXPIRED
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("event_source", sa.UUID(), nullable=True),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("ingestion_run_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_source"], ["source.source_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_run.run_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_business_event_entity_id", "business_event", ["entity_id"])
    op.create_index("ix_business_event_event_type", "business_event", ["event_type"])
    op.create_index("ix_business_event_event_date", "business_event", ["event_date"])

    # --- business_status_history ---
    op.create_table(
        "business_status_history",
        sa.Column("history_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("old_status", sa.String(20), nullable=True),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("changed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("ingestion_run_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_run.run_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("history_id"),
    )
    op.create_index("ix_business_status_history_entity_id", "business_status_history", ["entity_id"])

    # --- merge_candidate ---
    op.create_table(
        "merge_candidate",
        sa.Column("candidate_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id_a", sa.UUID(), nullable=False),
        sa.Column("entity_id_b", sa.UUID(), nullable=False),
        sa.Column("confidence", sa.String(10), nullable=False),
        # MEDIUM | LOW
        sa.Column("match_method", sa.String(100), nullable=True),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("auto_resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolved_by", sa.String(100), nullable=True),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        # MERGED | REJECTED | DEFERRED
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id_a"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entity_id_b"], ["business.entity_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("candidate_id"),
    )
    op.create_index("ix_merge_candidate_entity_id_a", "merge_candidate", ["entity_id_a"])
    op.create_index("ix_merge_candidate_entity_id_b", "merge_candidate", ["entity_id_b"])
    op.create_index("ix_merge_candidate_auto_resolved", "merge_candidate", ["auto_resolved"])

    # --- business_quality_score ---
    op.create_table(
        "business_quality_score",
        sa.Column("score_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("identity_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("address_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("phone_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("email_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("employee_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("industry_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("contact_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("recency_confidence", sa.SmallInteger(), nullable=True),
        sa.Column("source_reliability", sa.SmallInteger(), nullable=True),
        sa.Column("lead_quality_score", sa.SmallInteger(), nullable=True),
        sa.Column("scored_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("score_id"),
        sa.UniqueConstraint("entity_id", name="uq_business_quality_score_entity_id"),
    )

    # --- data_quality_flag ---
    op.create_table(
        "data_quality_flag",
        sa.Column("flag_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("flag_type", sa.String(100), nullable=True),
        # EMPLOYEE_RANGE_AMBIGUITY | MULTI_LICENCE_CONFLICT | etc.
        sa.Column("flag_detail", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("flag_id"),
    )
    op.create_index("ix_data_quality_flag_entity_id", "data_quality_flag", ["entity_id"])
    op.create_index("ix_data_quality_flag_resolved", "data_quality_flag", ["resolved"])

    # --- province_coverage_gap ---
    op.create_table(
        "province_coverage_gap",
        sa.Column("gap_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("province", sa.CHAR(2), nullable=False),
        sa.Column("gap_level", sa.String(20), nullable=True),
        # CONFIRMED | PARTIAL | DEFERRED
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("gap_id"),
        sa.UniqueConstraint("province", name="uq_province_coverage_gap_province"),
    )

    # Seed the 8 confirmed gap rows (VR20)
    op.execute("""
        INSERT INTO province_coverage_gap (province, gap_level, reason) VALUES
        ('NS', 'CONFIRMED', 'RJSC WAF-blocked; no open-data alternative found (VR20)'),
        ('NB', 'CONFIRMED', 'No municipal open-data source found (VR20)'),
        ('PE', 'CONFIRMED', 'OCBR auth required — NOT SUITABLE'),
        ('NL', 'CONFIRMED', 'CADO explicitly prohibits value-added use'),
        ('ON', 'PARTIAL', 'No general discovery source; regulated-sector enrichment only (VR20)'),
        ('QC', 'PARTIAL', 'Montréal city only; no provincial master (VR20)'),
        ('YT', 'DEFERRED', 'Supplier Directory 403; OGL confirmed; manual download needed'),
        ('NT', 'DEFERRED', 'CROS URL confirmed; basic info free; browser-only access')
    """)

    # --- lead_flag (sales/DNC layer — separate from canonical data) ---
    op.create_table(
        "lead_flag",
        sa.Column("flag_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("flag_type", sa.String(50), nullable=True),
        # DNC | CONTACTED | QUALIFIED | DISQUALIFIED | IN_PROGRESS
        sa.Column("flag_value", sa.Text(), nullable=True),
        sa.Column("set_by", sa.String(100), nullable=True),
        sa.Column("set_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["entity_id"], ["business.entity_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("flag_id"),
    )
    op.create_index("ix_lead_flag_entity_id", "lead_flag", ["entity_id"])
    op.create_index("ix_lead_flag_flag_type", "lead_flag", ["flag_type"])


def downgrade() -> None:
    op.drop_index("ix_lead_flag_flag_type", "lead_flag")
    op.drop_index("ix_lead_flag_entity_id", "lead_flag")
    op.drop_table("lead_flag")

    op.drop_table("province_coverage_gap")

    op.drop_index("ix_data_quality_flag_resolved", "data_quality_flag")
    op.drop_index("ix_data_quality_flag_entity_id", "data_quality_flag")
    op.drop_table("data_quality_flag")

    op.drop_table("business_quality_score")

    op.drop_index("ix_merge_candidate_auto_resolved", "merge_candidate")
    op.drop_index("ix_merge_candidate_entity_id_b", "merge_candidate")
    op.drop_index("ix_merge_candidate_entity_id_a", "merge_candidate")
    op.drop_table("merge_candidate")

    op.drop_index("ix_business_status_history_entity_id", "business_status_history")
    op.drop_table("business_status_history")

    op.drop_index("ix_business_event_event_date", "business_event")
    op.drop_index("ix_business_event_event_type", "business_event")
    op.drop_index("ix_business_event_entity_id", "business_event")
    op.drop_table("business_event")
