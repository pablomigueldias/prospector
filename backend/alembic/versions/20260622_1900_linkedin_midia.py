"""Agente LinkedIn (P5 §6.C — L5): direção de arte (midia + imagens)

Revision ID: c1e8a4d7f3b2
Revises: b9d3f2a8c1e7
Create Date: 2026-06-22 19:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c1e8a4d7f3b2"
down_revision: Union[str, None] = "b9d3f2a8c1e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("linkedin_post", sa.Column("midia", postgresql.JSONB()))
    op.add_column("linkedin_post", sa.Column("imagens", postgresql.JSONB()))


def downgrade() -> None:
    op.drop_column("linkedin_post", "imagens")
    op.drop_column("linkedin_post", "midia")
