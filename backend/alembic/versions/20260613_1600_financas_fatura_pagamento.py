"""financas: vincula a fatura à despesa que a paga (transacao_id)

Revision ID: d4f0a1b2c3e5
Revises: c3e9a4d7b8f2
Create Date: 2026-06-13 16:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = 'd4f0a1b2c3e5'
down_revision: Union[str, None] = 'c3e9a4d7b8f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'faturas',
        sa.Column('transacao_id', PG_UUID(as_uuid=True), nullable=True),
        schema='financas',
    )
    op.create_foreign_key(
        'fk_fin_faturas_transacao',
        'faturas', 'transacoes',
        ['transacao_id'], ['id'],
        source_schema='financas', referent_schema='financas',
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_fin_faturas_transacao', 'faturas',
        schema='financas', type_='foreignkey',
    )
    op.drop_column('faturas', 'transacao_id', schema='financas')
