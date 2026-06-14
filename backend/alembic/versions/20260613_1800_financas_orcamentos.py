"""financas: orçamento por categoria (teto mensal)

Revision ID: f6b2c8d4e7a9
Revises: e5a1b3c4d6f7
Create Date: 2026-06-13 18:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = 'f6b2c8d4e7a9'
down_revision: Union[str, None] = 'e5a1b3c4d6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'orcamentos',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('usuario_id', PG_UUID(as_uuid=True), nullable=False),
        sa.Column('categoria_id', PG_UUID(as_uuid=True), nullable=False),
        sa.Column('valor_mensal', sa.Numeric(12, 2), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['categoria_id'], ['financas.categorias.id'],
            ondelete='CASCADE',
        ),
        sa.UniqueConstraint(
            'usuario_id', 'categoria_id', name='uq_fin_orcamentos_usuario_categoria'
        ),
        schema='financas',
    )
    op.create_index(
        'ix_fin_orcamentos_usuario_id', 'orcamentos', ['usuario_id'],
        schema='financas',
    )


def downgrade() -> None:
    op.drop_index('ix_fin_orcamentos_usuario_id', table_name='orcamentos', schema='financas')
    op.drop_table('orcamentos', schema='financas')
