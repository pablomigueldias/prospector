"""Service do Agente Freelancer (Workana) — CRM de propostas + precificador.

Filosofia (igual ao agente de candidatura): é um COPILOTO. Nada aqui toca na
Workana nem envia proposta — a ferramenta organiza, precifica e (nas fases de
IA) rascunha; você revisa e envia na mão, e marca o status no painel.

Pacote dividido por área; este __init__ re-exporta a API pública pra manter
`from app.api.services.pessoal import freela_service` + `freela_service.<func>`.
"""
from __future__ import annotations

from ._base import FreelaError
from .analise import analisar_projeto
from .cadastro import (
    atualizar_cliente,
    criar_cliente,
    deletar_cliente,
    get_cliente,
    listar_clientes,
    listar_plataformas,
)
from .checklist import avaliar_proposta
from .meta import plano_meta
from .metricas import kanban, metricas
from .precificador import precificar
from .projetos import (
    atualizar_projeto,
    criar_projeto,
    deletar_projeto,
    extrair_projeto,
    get_projeto,
    listar_projetos,
)
from .propostas import (
    atualizar_proposta,
    corrigir_proposta,
    criar_proposta,
    deletar_proposta,
    get_proposta,
    listar_propostas_do_projeto,
    mudar_status,
    negociar_proposta,
    redigir_proposta,
)

__all__ = [
    "FreelaError",
    # cadastro
    "listar_plataformas",
    "criar_cliente",
    "listar_clientes",
    "get_cliente",
    "atualizar_cliente",
    "deletar_cliente",
    # projetos
    "criar_projeto",
    "listar_projetos",
    "get_projeto",
    "atualizar_projeto",
    "deletar_projeto",
    "extrair_projeto",
    # análise
    "analisar_projeto",
    # propostas
    "criar_proposta",
    "get_proposta",
    "atualizar_proposta",
    "mudar_status",
    "deletar_proposta",
    "listar_propostas_do_projeto",
    "redigir_proposta",
    "corrigir_proposta",
    "negociar_proposta",
    # checklist
    "avaliar_proposta",
    # métricas + kanban
    "kanban",
    "metricas",
    # meta
    "plano_meta",
    # precificador
    "precificar",
]
