from app.db.models.empresa import Empresa
from app.db.models.contato import Contato
from app.db.models.socio import Socio
from app.db.models.ai_call import AiCall
from app.db.models.pipeline_event import PipelineEvent
from app.db.models.email_outreach import EmailOutreach

# ── Área pessoal (tabelas pessoal_*) — isolada da Reative ──────────
from app.db.models.pessoal.perfil_mestre import PerfilMestre
from app.db.models.pessoal.vaga import Vaga
from app.db.models.pessoal.candidatura_email import CandidaturaEmail

# ── Organizador Financeiro (schema financas) — domínio pessoal ─────
from app.db.models.financas.conta import Conta
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.transacao import Transacao
from app.db.models.financas.transacao_item import TransacaoItem
from app.db.models.financas.transacao_pagamento import TransacaoPagamento


__all__ = [
    "Empresa",
    "Contato",
    "Socio",
    "AiCall",
    "PipelineEvent",
    "EmailOutreach",
    # pessoal
    "PerfilMestre",
    "Vaga",
    "CandidaturaEmail",
    # financas
    "Conta",
    "Categoria",
    "Transacao",
    "TransacaoItem",
    "TransacaoPagamento",
]