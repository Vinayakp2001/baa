"""Source registry and ingestion tracking tables

Revision ID: 001
Revises:
Create Date: 2026-09-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- source table ---
    op.create_table(
        "source",
        sa.Column("source_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_key", sa.String(100), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("adapter_class", sa.String(100), nullable=False),
        sa.Column("province", sa.CHAR(2), nullable=True),  # NULL = federal
        sa.Column(
            "source_type",
            sa.Enum("CSV", "JSON", "API", "HTML", "PDF", "GeoJSON", "XLSX", name="source_type_enum"),
            nullable=False,
        ),
        sa.Column(
            "source_class",
            sa.Enum("A", "B", "C", "D", name="source_class_enum"),
            nullable=False,
        ),
        sa.Column("licence", sa.String(200), nullable=True),
        sa.Column("schedule_cron", sa.String(50), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rate_limit_rpm", sa.Integer(), nullable=True),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("auth_header_key", sa.String(100), nullable=True),
        sa.Column(
            "terms_status",
            sa.Enum("CLEARED", "UNRESOLVED", "BLOCKED", "NOT_SUITABLE", name="terms_status_enum"),
            nullable=False,
            server_default="CLEARED",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("source_key"),
    )

    # --- ingestion_run table ---
    op.create_table(
        "ingestion_run",
        sa.Column("run_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("run_started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("run_completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "run_status",
            sa.Enum("RUNNING", "COMPLETED", "FAILED", "PARTIAL", name="run_status_enum"),
            nullable=False,
            server_default="RUNNING",
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("retrieval_timestamp", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("source_version_or_date", sa.String(100), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("record_count_raw", sa.Integer(), nullable=True),
        sa.Column("record_count_normalised", sa.Integer(), nullable=True),
        sa.Column("record_count_new", sa.Integer(), nullable=True),
        sa.Column("record_count_updated", sa.Integer(), nullable=True),
        sa.Column("record_count_flagged", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index("ix_ingestion_run_source_id", "ingestion_run", ["source_id"])
    op.create_index("ix_ingestion_run_run_status", "ingestion_run", ["run_status"])

    # --- Seed source table with all 17 sources ---
    op.execute("""
        INSERT INTO source (
            source_key, source_name, adapter_class, province,
            source_type, source_class, licence, schedule_cron,
            is_enabled, rate_limit_rpm, base_url, terms_status, notes
        ) VALUES
        (
            'corporations_canada_csv',
            'Corporations Canada — CBCA Active CSV',
            'CorporationsCanadaCSVAdapter',
            NULL,
            'CSV', 'A',
            'OGL-Canada-2.0',
            '0 4 * * 1',
            true, NULL,
            'https://ised-isde.canada.ca/cc/lgcy/fdrlCrpSrch.html',
            'CLEARED',
            'Federal CBCA active corporations, 645,005 rows. Weekly refresh sufficient.'
        ),
        (
            'corporations_canada_html',
            'Corporations Canada — Monthly Incorporations HTML',
            'CorporationsCanadaHTMLAdapter',
            NULL,
            'HTML', 'B',
            'OGL-Canada-2.0',
            '0 8 1 * *',
            true, NULL,
            'https://ised-isde.canada.ca/cc/lgcy/fdrlCrpSrch.html',
            'CLEARED',
            'Monthly new CBCA incorporations HTML page (VR03).'
        ),
        (
            'corporations_canada_api',
            'Corporations Canada — Directors API',
            'CorporationsCanadaAPIAdapter',
            NULL,
            'API', 'C',
            'OGL-Canada-2.0',
            NULL,
            true, 60,
            'https://api.ic.gc.ca/cc/api/corporations',
            'CLEARED',
            'Event-triggered director enrichment. 60 req/min rate limit. CBCA corps only.'
        ),
        (
            'calgary',
            'City of Calgary — Business Licences',
            'CalgaryAdapter',
            'AB',
            'CSV', 'A',
            'OGL-Canada-2.0',
            '0 6 * * *',
            true, NULL,
            'https://data.calgary.ca/resource/business-licences.csv',
            'CLEARED',
            'Socrata CSV, 23,178 rows, incremental via first_iss_dt.'
        ),
        (
            'edmonton',
            'City of Edmonton — Business Licences',
            'EdmontonAdapter',
            'AB',
            'CSV', 'A',
            'OGL-Canada-2.0',
            '0 6 * * *',
            true, NULL,
            'https://data.edmonton.ca/resource/business-licences.csv',
            'CLEARED',
            'Socrata CSV, 43,719 rows, incremental via originalissuedate.'
        ),
        (
            'vancouver',
            'City of Vancouver — Business Licences',
            'VancouverAdapter',
            'BC',
            'CSV', 'A',
            'OGL-Canada-2.0',
            '0 5 * * *',
            true, NULL,
            'https://opendata.vancouver.ca/explore/dataset/business-licences/download/',
            'CLEARED',
            'OpenDataSoft CSV, 206,024 rows, daily. Preserve LicenceRSN. Employee as float-string.'
        ),
        (
            'winnipeg',
            'City of Winnipeg — Business Licences',
            'WinnipegAdapter',
            'MB',
            'CSV', 'B',
            'OGL-Canada-2.0',
            '0 7 * * *',
            true, NULL,
            'https://data.winnipeg.ca/resource/business-licences.csv',
            'CLEARED',
            'Class B event-only. 84.7% rows Closed. Do NOT use as Class A discovery.'
        ),
        (
            'manitoba_weekly_pdf',
            'Manitoba Companies Office — Weekly Incorporations PDF',
            'ManitobaWeeklyPDFAdapter',
            'MB',
            'PDF', 'B',
            'OGL-Canada-2.0',
            '0 9 * * 5',
            true, NULL,
            'https://companiesoffice.gov.mb.ca/gazette/',
            'CLEARED',
            '14 weekly PDFs confirmed. Parse Incorporations category only. De-dup by file_no.'
        ),
        (
            'saskatoon_all_biz',
            'City of Saskatoon — All Business Licences',
            'SaskatoonAllBizAdapter',
            'SK',
            'XLSX', 'A',
            'OGL-Canada-2.0',
            '0 8 * * 1',
            true, NULL,
            'https://opendata.saskatoon.ca/',
            'CLEARED',
            'XLSX 7,472 rows. Parse Bus_Lic_Acct_Id, name, address, NAICS sub-sector.'
        ),
        (
            'saskatoon_new_biz',
            'City of Saskatoon — New Business Licences',
            'SaskatoonNewBizAdapter',
            'SK',
            'XLSX', 'B',
            'OGL-Canada-2.0',
            '0 8 * * 1',
            true, NULL,
            'https://opendata.saskatoon.ca/',
            'CLEARED',
            'XLSX 51 rows. Explicit new-licence signal. Event type: MUNICIPAL_LICENCE_FIRST_ISSUE.'
        ),
        (
            'ontario_select_licence',
            'Ontario Select Licence Registry',
            'OntarioSelectLicenceAdapter',
            'ON',
            'CSV', 'C',
            'OGL-Ontario-1.0',
            '0 8 1 * *',
            true, NULL,
            'https://data.ontario.ca/dataset/ontario-select-licence',
            'CLEARED',
            '674 rows. Phone/email enrichment. Treat N/A as NULL.'
        ),
        (
            'ontario_dairy',
            'Ontario — Dairy Processor Licences',
            'OntarioDairyAdapter',
            'ON',
            'CSV', 'C',
            'OGL-Ontario-1.0',
            '0 8 1 * *',
            true, NULL,
            'https://data.ontario.ca/dataset/dairy-processor-licences',
            'CLEARED',
            'Regulated sector enrichment: phone/postal for ON dairy processors.'
        ),
        (
            'ontario_meat',
            'Ontario — Meat Plant Licences',
            'OntarioMeatAdapter',
            'ON',
            'CSV', 'C',
            'OGL-Ontario-1.0',
            '0 8 1 * *',
            true, NULL,
            'https://data.ontario.ca/dataset/meat-plant-licences',
            'CLEARED',
            'Regulated sector enrichment: phone/postal for ON meat plants.'
        ),
        (
            'ontario_tobacco',
            'Ontario — Tobacco Retail Dealer Registrations',
            'OntarioTobaccoAdapter',
            'ON',
            'CSV', 'C',
            'OGL-Ontario-1.0',
            '0 8 1 * *',
            true, NULL,
            'https://data.ontario.ca/dataset/tobacco-retail-dealer-registrations',
            'CLEARED',
            'Regulated sector enrichment.'
        ),
        (
            'ontario_fuel',
            'Ontario — Fuel Licence Registrations',
            'OntarioFuelAdapter',
            'ON',
            'CSV', 'C',
            'OGL-Ontario-1.0',
            '0 8 1 * *',
            true, NULL,
            'https://data.ontario.ca/dataset/fuel-licence-registrations',
            'CLEARED',
            'Regulated sector enrichment.'
        ),
        (
            'ontario_csbif',
            'Ontario — CSBIF (Community Small Business Investment Funds)',
            'OntarioCSBIFAdapter',
            'ON',
            'CSV', 'C',
            'OGL-Ontario-1.0',
            '0 8 1 * *',
            true, NULL,
            'https://data.ontario.ca/dataset/community-small-business-investment-funds',
            'CLEARED',
            'Regulated sector enrichment.'
        ),
        (
            'ontario_dairy_plants',
            'Ontario — Dairy Plants Licences',
            'OntarioDairyPlantsAdapter',
            'ON',
            'CSV', 'C',
            'OGL-Ontario-1.0',
            '0 8 1 * *',
            true, NULL,
            'https://data.ontario.ca/dataset/dairy-plants-licences',
            'CLEARED',
            'Regulated sector enrichment.'
        ),
        (
            'montreal_commercial',
            'Ville de Montréal — Commercial Premises',
            'MontrealCommercialPremisesAdapter',
            'QC',
            'GeoJSON', 'A',
            'OGL-Canada-2.0',
            '0 8 1 1 *',
            true, NULL,
            'https://donnees.montreal.ca/dataset/commercial-premises',
            'CLEARED',
            'Annual dataset (updated Dec 2025). SCIAN codes map to NAICS.'
        ),
        (
            'quebec_city_permits',
            'Ville de Québec — Building/Business Permits',
            'QuebecCityPermitsAdapter',
            'QC',
            'CSV', 'B',
            'OGL-Canada-2.0',
            '0 9 * * 5',
            true, NULL,
            'https://www.donneesquebec.ca/recherche/dataset/vdq-permis',
            'CLEARED',
            'Weekly CSV. Event signal only — permit issuance. No canonical employee/contact data.'
        ),
        (
            'bc_indigenous',
            'BC Indigenous Business Listings',
            'BCIndigenousAdapter',
            'BC',
            'CSV', 'C',
            'OGL-BC-2.0',
            '0 8 1 * *',
            true, NULL,
            'https://bcbusiness.ca/indigenous/',
            'CLEARED',
            '~3,000+ rows. phone/email/contact/employee_range. "55 to 99" ambiguity flag.'
        ),
        (
            'bc_orgbook',
            'BC OrgBook API',
            'BCOrgBookAPIAdapter',
            'BC',
            'API', 'C',
            'OGL-BC-2.0',
            NULL,
            true, NULL,
            'https://orgbook.gov.bc.ca/api/v4',
            'CLEARED',
            'Targeted lookups only. Bulk enumeration prohibited by BC Gov Terms (VR09).'
        ),
        (
            'nni',
            'Nunavut Nunavummi Nanminiqaqtuniliririnirmut Ikajuqtiit (NNI)',
            'NNIAdapter',
            'NU',
            'HTML', 'C',
            'UNRESOLVED',
            NULL,
            false, NULL,
            'https://nni.nu.ca/',
            'UNRESOLVED',
            'Terms unresolved — NNI Regulations PDF not yet reviewed. Do NOT process into canonical layer.'
        )
    """)


def downgrade() -> None:
    op.drop_index("ix_ingestion_run_run_status", "ingestion_run")
    op.drop_index("ix_ingestion_run_source_id", "ingestion_run")
    op.drop_table("ingestion_run")
    op.drop_table("source")

    op.execute("DROP TYPE IF EXISTS run_status_enum")
    op.execute("DROP TYPE IF EXISTS source_type_enum")
    op.execute("DROP TYPE IF EXISTS source_class_enum")
    op.execute("DROP TYPE IF EXISTS terms_status_enum")
