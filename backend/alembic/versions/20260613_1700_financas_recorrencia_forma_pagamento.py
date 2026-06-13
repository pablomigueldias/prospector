"""financas: forma de pagamento da recorrência + vínculo com compra

Revision ID: e5a1b3c4d6f7
Revises: d4f0a1b2c3e5
Create Date: 2026-06-13 17:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = 'e5a1b3c4d6f7'
down_revision: Union[str, None] = 'd4f0a1b2c3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'recorrencias',
        sa.Column(
            'forma_pagamento', sa.String(20),
            nullable=False, server_default='conta',
        ),
        schema='financas',
    )
    op.add_column(
        'recorrencias',
        sa.Column('cartao_id', PG_UUID(as_uuid=True), nullable=True),
        schema='financas',
    )
    op.create_foreign_key(
        'fk_fin_recorrencias_cartao',
        'recorrencias', 'cartoes',
        ['cartao_id'], ['id'],
        source_schema='financas', referent_schema='financas',
        ondelete='SET NULL',
    )
    op.add_column(
        'compras',
        sa.Column('recorrencia_id', PG_UUID(as_uuid=True), nullable=True),
        schema='financas',
    )
    op.create_foreign_key(
        'fk_fin_compras_recorrencia',
        'compras', 'recorrencias',
        ['recorrencia_id'], ['id'],
        source_schema='financas', referent_schema='financas',
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_fin_compras_recorrencia', 'compras',
        schema='financas', type_='foreignkey',
    )
    op.drop_column('compras', 'recorrencia_id', schema='financas')
    op.drop_constraint(
        'fk_fin_recorrencias_cartao', 'recorrencias',
        schema='financas', type_='foreignkey',
    )
    op.drop_column('recorrencias', 'cartao_id', schema='financas')
    op.drop_column('recorrencias', 'forma_pagamento', schema='financas')
