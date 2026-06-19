"""MAS-1: tabela agente_eventos (memória compartilhada / blackboard)

Revision ID: b7f2c9e14a05
Revises: a3d8f1c47e90
Create Date: 2026-06-18 15:00:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'b7f2c9e14a05'
down_revision: Union[str, None] = 'a3d8f1c47e90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agente_eventos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('agente', sa.String(50), nullable=False),
        sa.Column('alvo_tipo', sa.String(30), nullable=False),
        sa.Column('alvo_id', sa.String(100), nullable=False),
        sa.Column('tipo', sa.String(40), nullable=False),
        sa.Column('resumo', sa.Text()),
        sa.Column('payload', JSONB()),
        sa.Column('origem', sa.String(20), nullable=False,
                  server_default='manual'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index('ix_agente_eventos_alvo', 'agente_eventos',
                    ['alvo_tipo', 'alvo_id'])
    op.create_index('ix_agente_eventos_created_at', 'agente_eventos',
                    ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_agente_eventos_created_at', table_name='agente_eventos')
    op.drop_index('ix_agente_eventos_alvo', table_name='agente_eventos')
    op.drop_table('agente_eventos')
