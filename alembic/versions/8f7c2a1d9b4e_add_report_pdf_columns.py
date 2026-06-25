"""add report pdf columns

Revision ID: 8f7c2a1d9b4e
Revises: 0b361c8f9a05
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f7c2a1d9b4e"
down_revision: Union[str, Sequence[str], None] = "0b361c8f9a05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("simulation_results", sa.Column("report_pdf_path", sa.Text(), nullable=True))
    op.add_column("simulation_results", sa.Column("report_pdf_filename", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("simulation_results", "report_pdf_filename")
    op.drop_column("simulation_results", "report_pdf_path")
