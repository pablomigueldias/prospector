"""CRM: tabelas negocios, atividades e projetos (espelho do Notion)

Revision ID: e2f5b8c1d934
Revises: c7e1a9d4f2b8
Create Date: 2026-06-17 22:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'e2f5b8c1d934'
down_revision: Union[str, None] = 'c7e1a9d4f2b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'negocios',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nome', sa.String(500), nullable=False),
        sa.Column('estagio', sa.String(60)),
        sa.Column('valor_estimado', sa.Numeric(15, 2)),
        sa.Column('probabilidade', sa.String(20)),
        sa.Column('origem', sa.String(80)),
        sa.Column('tipo_servico', JSONB()),
        sa.Column('notas', sa.Text()),
        sa.Column('motivo_perda', sa.String(120)),
        sa.Column('previsao_fechamento', sa.Date()),
        sa.Column('data_fechamento_real', sa.Date()),
        sa.Column('proxima_acao', sa.Date()),
        sa.Column('empresa_id', UUID(as_uuid=True),
                  sa.ForeignKey('empresas.id', ondelete='SET NULL')),
        sa.Column('contato_id', UUID(as_uuid=True),
                  sa.ForeignKey('contatos.id', ondelete='SET NULL')),
        sa.Column('notion_page_id', sa.String(50)),
        sa.Column('notion_synced_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_negocios_estagio', 'negocios', ['estagio'])
    op.create_index('ix_negocios_empresa_id', 'negocios', ['empresa_id'])
    op.create_index('ix_negocios_notion_page_id', 'negocios', ['notion_page_id'])

    op.create_table(
        'projetos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nome', sa.String(500), nullable=False),
        sa.Column('status', sa.String(60)),
        sa.Column('tipo_servico', sa.String(120)),
        sa.Column('valor_total', sa.Numeric(15, 2)),
        sa.Column('valor_recebido', sa.Numeric(15, 2)),
        sa.Column('briefing', sa.Text()),
        sa.Column('link_producao', sa.String(500)),
        sa.Column('repo_github', sa.String(500)),
        sa.Column('forma_pagamento', sa.String(80)),
        sa.Column('prazo_entrega', sa.Date()),
        sa.Column('data_inicio', sa.Date()),
        sa.Column('data_entrega_real', sa.Date()),
        sa.Column('empresa_id', UUID(as_uuid=True),
                  sa.ForeignKey('empresas.id', ondelete='SET NULL')),
        sa.Column('negocio_id', UUID(as_uuid=True),
                  sa.ForeignKey('negocios.id', ondelete='SET NULL')),
        sa.Column('notion_page_id', sa.String(50)),
        sa.Column('notion_synced_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_projetos_status', 'projetos', ['status'])
    op.create_index('ix_projetos_empresa_id', 'projetos', ['empresa_id'])
    op.create_index('ix_projetos_notion_page_id', 'projetos', ['notion_page_id'])

    op.create_table(
        'atividades',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('titulo', sa.String(500), nullable=False),
        sa.Column('tipo', sa.String(60)),
        sa.Column('status', sa.String(60)),
        sa.Column('data', sa.DateTime()),
        sa.Column('resumo', sa.Text()),
        sa.Column('proximos_passos', sa.Text()),
        sa.Column('negocio_id', UUID(as_uuid=True),
                  sa.ForeignKey('negocios.id', ondelete='SET NULL')),
        sa.Column('contato_id', UUID(as_uuid=True),
                  sa.ForeignKey('contatos.id', ondelete='SET NULL')),
        sa.Column('notion_page_id', sa.String(50)),
        sa.Column('notion_synced_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_atividades_data', 'atividades', ['data'])
    op.create_index('ix_atividades_status', 'atividades', ['status'])
    op.create_index('ix_atividades_negocio_id', 'atividades', ['negocio_id'])
    op.create_index('ix_atividades_notion_page_id', 'atividades', ['notion_page_id'])


def downgrade() -> None:
    op.drop_table('atividades')
    op.drop_table('projetos')
    op.drop_table('negocios')
