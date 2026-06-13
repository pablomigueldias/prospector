"""financas: linha digitável do boleto (copiar/colar + dedup)

Revision ID: b2d8f1a3c6e1
Revises: a1c7e9d2b4f0
Create Date: 2026-06-13 13:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2d8f1a3c6e1'
down_revision: Union[str, None] = 'a1c7e9d2b4f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'transacoes',
        sa.Column('linha_digitavel', sa.String(length=64), nullable=True),
        schema='financas',
    )
    op.create_index(
        'ix_fin_transacoes_linha_digitavel',
        'transacoes',
        ['usuario_id', 'linha_digitavel'],
        unique=False,
        schema='financas',
    )


def downgrade() -> None:
    op.drop_index(
        'ix_fin_transacoes_linha_digitavel',
        table_name='transacoes',
        schema='financas',
    )
    op.drop_column('transacoes', 'linha_digitavel', schema='financas')
