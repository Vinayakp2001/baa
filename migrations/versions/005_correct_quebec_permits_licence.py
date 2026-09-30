"""Correct the Québec City permits licence in the source registry.

Revision ID: 005
Revises: 004
Create Date: 2026-09-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE source SET licence = :licence "
            "WHERE source_key = :source_key"
        ).bindparams(
            licence="Creative Commons Attribution 4.0 (CC-BY 4.0)",
            source_key="quebec_city_permits",
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE source SET licence = :licence "
            "WHERE source_key = :source_key"
        ).bindparams(
            licence="OGL-Canada-2.0",
            source_key="quebec_city_permits",
        )
    )