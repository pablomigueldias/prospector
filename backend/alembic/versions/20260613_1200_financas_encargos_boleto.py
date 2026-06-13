"""financas: encargos de boleto (multa/juros por atraso)

Revision ID: a1c7e9d2b4f0
Revises: f504abb8fb1f
Create Date: 2026-06-13 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1c7e9d2b4f0'
down_revision: Union[str, None] = 'f504abb8fb1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'transacoes',
        sa.Column('multa_percentual', sa.Numeric(6, 4), nullable=True),
        schema='financas',
    )
    op.add_column(
        'transacoes',
        sa.Column('juros_mensal_percentual', sa.Numeric(6, 4), nullable=True),
        schema='financas',
    )
    op.add_column(
        'transacoes',
        sa.Column('encargos_pagos', sa.Numeric(12, 2), nullable=True),
        schema='financas',
    )


def downgrade() -> None:
    op.drop_column('transacoes', 'encargos_pagos', schema='financas')
    op.drop_column('transacoes', 'juros_mensal_percentual', schema='financas')
    op.drop_column('transacoes', 'multa_percentual', schema='financas')
