"""financas: meta (objetivo) na conta — reservas com objetivo

Revision ID: a7c3e1f9d2b8
Revises: f6b2c8d4e7a9
Create Date: 2026-06-13 19:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a7c3e1f9d2b8'
down_revision: Union[str, None] = 'f6b2c8d4e7a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Objetivo de valor da conta (ex.: reserva "viagem: R$ 5.000"). Nulo = sem meta.
    op.add_column(
        'contas',
        sa.Column('meta', sa.Numeric(12, 2), nullable=True),
        schema='financas',
    )


def downgrade() -> None:
    op.drop_column('contas', 'meta', schema='financas')
