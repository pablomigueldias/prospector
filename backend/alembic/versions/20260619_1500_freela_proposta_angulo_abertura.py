"""Freela §2.F: ângulo de abertura da proposta (A/B — direto/prova/pergunta)

Revision ID: e2a8b5d1c9f4
Revises: d1f7a4c9e2b3
Create Date: 2026-06-19 15:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e2a8b5d1c9f4"
down_revision: Union[str, None] = "d1f7a4c9e2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pessoal_freela_proposta",
        sa.Column("angulo_abertura", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pessoal_freela_proposta", "angulo_abertura")
