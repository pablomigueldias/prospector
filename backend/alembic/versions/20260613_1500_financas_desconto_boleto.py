"""financas: desconto por antecipação do boleto

Revision ID: c3e9a4d7b8f2
Revises: b2d8f1a3c6e1
Create Date: 2026-06-13 15:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3e9a4d7b8f2'
down_revision: Union[str, None] = 'b2d8f1a3c6e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'transacoes',
        sa.Column('desconto_valor', sa.Numeric(12, 2), nullable=True),
        schema='financas',
    )
    op.add_column(
        'transacoes',
        sa.Column('desconto_ate', sa.Date(), nullable=True),
        schema='financas',
    )


def downgrade() -> None:
    op.drop_column('transacoes', 'desconto_ate', schema='financas')
    op.drop_column('transacoes', 'desconto_valor', schema='financas')
