# ── Autenticação/Autorização (schema auth) — portão de entrada ─────
from app.db.models.agente_evento import AgenteEvento
from app.db.models.ai_call import AiCall
from app.db.models.auth.auditoria import Auditoria
from app.db.models.auth.papel import Papel
from app.db.models.auth.papel_permissao import PapelPermissao
from app.db.models.auth.permissao import Permissao
from app.db.models.auth.sessao import Sessao
from app.db.models.auth.tentativa_login import TentativaLogin
from app.db.models.auth.usuario import Usuario
from app.db.models.auth.usuario_2fa import UsuarioTwoFA
from app.db.models.auth.usuario_papel import UsuarioPapel
from app.db.models.atividade import Atividade

# ── Blog headless (tabelas blog_*) — conteúdo do site Reative ──────
from app.db.models.blog.pauta import BlogPauta
from app.db.models.blog.post import BlogPost
from app.db.models.blog.redirect import BlogRedirect
from app.db.models.config_app import ConfigApp
from app.db.models.contato import Contato
from app.db.models.crm_opcao import CrmOpcao
from app.db.models.email_outreach import EmailOutreach
from app.db.models.empresa import Empresa
from app.db.models.financas.bot_rascunho import BotRascunho
from app.db.models.financas.cartao import Cartao
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.compra import Compra
from app.db.models.financas.comprovante import Comprovante

# ── Organizador Financeiro (schema financas) — domínio pessoal ─────
from app.db.models.financas.conta import Conta
from app.db.models.financas.fatura import Fatura
from app.db.models.financas.leitura_consumo import LeituraConsumo
from app.db.models.financas.orcamento import Orcamento
from app.db.models.financas.parcela import Parcela
from app.db.models.financas.recorrencia import Recorrencia
from app.db.models.financas.transacao import Transacao
from app.db.models.financas.transacao_item import TransacaoItem
from app.db.models.financas.transacao_pagamento import TransacaoPagamento
from app.db.models.pessoal.candidatura_email import CandidaturaEmail
from app.db.models.pessoal.freela.cliente import Cliente as FreelaCliente

# ── Agente Freelancer / Workana (tabelas pessoal_freela_*) ─────────
from app.db.models.pessoal.freela.plataforma import Plataforma
from app.db.models.pessoal.freela.projeto import Projeto as FreelaProjeto
from app.db.models.pessoal.freela.proposta import Proposta as FreelaProposta

# ── Área pessoal (tabelas pessoal_*) — isolada da Reative ──────────
from app.db.models.pessoal.perfil_mestre import PerfilMestre
from app.db.models.pessoal.vaga import Vaga
from app.db.models.negocio import Negocio
from app.db.models.pipeline_event import PipelineEvent
from app.db.models.projeto import ProjetoCRM
from app.db.models.socio import Socio

__all__ = [
    # auth
    "Usuario",
    "Sessao",
    "Papel",
    "Permissao",
    "UsuarioPapel",
    "PapelPermissao",
    "TentativaLogin",
    "Auditoria",
    "UsuarioTwoFA",
    "Empresa",
    "Contato",
    "Socio",
    "Negocio",
    "Atividade",
    "ProjetoCRM",
    "AiCall",
    "AgenteEvento",
    "PipelineEvent",
    "EmailOutreach",
    "CrmOpcao",
    "ConfigApp",
    # blog (site headless)
    "BlogPost",
    "BlogRedirect",
    "BlogPauta",
    # pessoal
    "PerfilMestre",
    "Vaga",
    "CandidaturaEmail",
    # freela (Workana)
    "Plataforma",
    "FreelaCliente",
    "FreelaProjeto",
    "FreelaProposta",
    # financas
    "Conta",
    "Categoria",
    "Transacao",
    "TransacaoItem",
    "TransacaoPagamento",
    "Cartao",
    "Fatura",
    "Compra",
    "Parcela",
    "Recorrencia",
    "Orcamento",
    "LeituraConsumo",
    "Comprovante",
    "BotRascunho",
]
