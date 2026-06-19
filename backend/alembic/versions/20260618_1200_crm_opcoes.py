"""CRM: tabela crm_opcoes (opções de select gerenciáveis) + seed

Revision ID: a3d8f1c47e90
Revises: e2f5b8c1d934
Create Date: 2026-06-18 12:00:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'a3d8f1c47e90'
down_revision: Union[str, None] = 'e2f5b8c1d934'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Opções iniciais (espelham o config; a partir daqui o banco é a fonte).
SEED: dict[str, list[str]] = {
    "setor": ["Tech", "Saúde", "Educação", "Varejo", "Serviços", "Marketing",
              "Jurídico", "Financeiro", "Imobiliário", "Indústria"],
    "tamanho": ["MEI", "Pequena (1-10)", "Média (11-50)", "Grande (51-200)",
                "Corporativa (200+)"],
    "status": ["🔴 Não qualificado", "⚪ Cliente inativo", "🟡 Lead ativo",
               "🔵 Prospect", "🟢 Cliente ativo", "🔬 Em investigação"],
    "como_conheceu": ["LinkedIn", "Indicação", "Site", "Comunidade dev",
                      "Network pessoal", "Outbound", "Inbound"],
    "estado": ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF"],
    "origem_contato": ["LinkedIn", "Indicação", "Site", "Comunidade", "Evento",
                       "Network"],
    "estagio": ["⚪ Lead novo", "🔵 Primeiro contato", "🟣 Qualificado",
                "🟡 Briefing agendado", "🟠 Briefing realizado",
                "🔴 Proposta enviada", "🔴 Em negociação", "🟢 Ganho",
                "⚪ Perdido", "🟣 Standby"],
    "probabilidade": ["10%", "25%", "50%", "75%", "90%"],
    "origem_negocio": ["LinkedIn", "Indicação", "Site", "Comunidade", "Network",
                       "Inbound", "Outbound", "Evento"],
    "tipo_servico": ["Landing page", "Site institucional", "Sistema web",
                     "Automação", "Bot", "Manutenção", "Consultoria"],
    "atividade_status": ["🟡 Agendada", "🟢 Realizada", "🔴 Não compareceu",
                         "⚪ Cancelada"],
    "atividade_tipo": ["📞 Call", "💬 WhatsApp", "✉️ E-mail",
                       "🤝 Reunião presencial", "💼 LinkedIn DM", "🎥 Videocall"],
    "projeto_status": ["🆕 Onboarding", "🛠️ Em desenvolvimento", "🚀 Em produção",
                       "👀 Em revisão", "⏸️ Pausado", "✅ Concluído"],
    "forma_pagamento": ["À vista", "50/50", "40/30/30", "Mensal", "Outro"],
}

# Cor da pílula derivada do emoji-bolinha que prefixa o valor (estilo Notion).
_COR_POR_EMOJI = {
    "🔴": "red", "🟢": "green", "🟡": "yellow", "🔵": "blue",
    "🟠": "orange", "🟣": "purple", "⚪": "gray",
}


def _cor(valor: str) -> str | None:
    return _COR_POR_EMOJI.get(valor[:1])


def upgrade() -> None:
    tabela = op.create_table(
        'crm_opcoes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('grupo', sa.String(40), nullable=False),
        sa.Column('valor', sa.String(120), nullable=False),
        sa.Column('cor', sa.String(30)),
        sa.Column('ordem', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(),
                  nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                  nullable=False),
        sa.UniqueConstraint('grupo', 'valor', name='uq_crm_opcoes_grupo_valor'),
    )
    op.create_index('ix_crm_opcoes_grupo', 'crm_opcoes', ['grupo'])

    linhas = []
    for grupo, valores in SEED.items():
        for ordem, valor in enumerate(valores):
            linhas.append({
                "grupo": grupo, "valor": valor, "cor": _cor(valor),
                "ordem": ordem, "ativo": True,
            })
    op.bulk_insert(tabela, linhas)


def downgrade() -> None:
    op.drop_index('ix_crm_opcoes_grupo', table_name='crm_opcoes')
    op.drop_table('crm_opcoes')
