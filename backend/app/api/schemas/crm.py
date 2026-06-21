"""Schemas de leitura do CRM (empresas/contatos no Postgres).

O CRM dentro do sistema — substitui abrir o Notion pra consultar. Só leitura
por enquanto; a escrita continua pelo pipeline do Prospector (dual-write).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContatoOut(BaseModel):
    id: str
    nome: str
    cargo: str | None = None
    decisor: bool = False
    email: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None
    linkedin: str | None = None
    origem_contato: str | None = None


class SocioOut(BaseModel):
    id: str
    nome: str
    qualificacao: str | None = None


class EmpresaListItem(BaseModel):
    id: str
    nome: str
    cnpj: str | None = None
    site: str | None = None
    cidade: str | None = None
    estado: str | None = None
    setor: str | None = None
    tamanho: str | None = None
    status: str | None = None
    como_conheceu: str | None = None
    score: int | None = None
    n_contatos: int = 0


class EmpresaDetalhe(BaseModel):
    id: str
    nome: str
    razao_social: str | None = None
    cnpj: str | None = None
    cidade: str | None = None
    estado: str | None = None
    local: str | None = None
    site: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    capital_social: float | None = None
    setor: str | None = None
    tamanho: str | None = None
    score: int | None = None
    status: str | None = None
    como_conheceu: str | None = None
    notas: str | None = None
    analise_json: dict | None = None
    notion_page_id: str | None = None
    contatos: list[ContatoOut] = Field(default_factory=list)
    socios: list[SocioOut] = Field(default_factory=list)


class EmpresaListResponse(BaseModel):
    items: list[EmpresaListItem] = Field(default_factory=list)
    total: int = 0


class EmpresaUpsert(BaseModel):
    """Payload de criação/edição de empresa (CRUD do CRM)."""
    nome: str
    razao_social: str | None = None
    cnpj: str | None = None
    site: str | None = None
    cidade: str | None = None
    estado: str | None = None
    local: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    capital_social: float | None = None
    setor: str | None = None
    tamanho: str | None = None
    score: int | None = None
    status: str | None = None
    como_conheceu: str | None = None
    notas: str | None = None


# ── Contatos ─────────────────────────────────────────────────────────

class ContatoListItem(BaseModel):
    id: str
    nome: str
    cargo: str | None = None
    decisor: bool = False
    email: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None
    linkedin: str | None = None
    origem_contato: str | None = None
    empresa_id: str
    empresa_nome: str | None = None


class ContatoListResponse(BaseModel):
    items: list[ContatoListItem] = Field(default_factory=list)
    total: int = 0


class ContatoUpsert(BaseModel):
    """Payload de criação/edição de contato."""
    empresa_id: str
    nome: str
    cargo: str | None = None
    decisor: bool = False
    email: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None
    linkedin: str | None = None
    origem_contato: str | None = None


# ── Negócios (pipeline de vendas) ────────────────────────────────────

class NegocioListItem(BaseModel):
    id: str
    nome: str
    estagio: str | None = None
    valor_estimado: float | None = None
    valor_ponderado: float | None = None   # valor × probabilidade
    probabilidade: str | None = None
    origem: str | None = None
    tipo_servico: list[str] = Field(default_factory=list)
    previsao_fechamento: str | None = None
    proxima_acao: str | None = None
    empresa_id: str | None = None
    empresa_nome: str | None = None
    contato_nome: str | None = None
    notas: str | None = None


class NegocioColuna(BaseModel):
    estagio: str
    total: int
    valor_total: float
    valor_ponderado: float
    negocios: list[NegocioListItem] = Field(default_factory=list)


class NegociosPipeline(BaseModel):
    colunas: list[NegocioColuna] = Field(default_factory=list)
    valor_total: float = 0
    valor_ponderado: float = 0


# ── Atividades ───────────────────────────────────────────────────────

class AtividadeListItem(BaseModel):
    id: str
    titulo: str
    tipo: str | None = None
    status: str | None = None
    data: str | None = None
    resumo: str | None = None
    proximos_passos: str | None = None
    negocio_id: str | None = None
    negocio_nome: str | None = None
    contato_nome: str | None = None


class AtividadeListResponse(BaseModel):
    items: list[AtividadeListItem] = Field(default_factory=list)
    total: int = 0


# ── Projetos ─────────────────────────────────────────────────────────

class ProjetoListItem(BaseModel):
    id: str
    nome: str
    status: str | None = None
    tipo_servico: str | None = None
    valor_total: float | None = None
    valor_recebido: float | None = None
    a_receber: float | None = None
    prazo_entrega: str | None = None
    data_entrega_real: str | None = None
    link_producao: str | None = None
    repo_github: str | None = None
    empresa_nome: str | None = None
    negocio_nome: str | None = None
    briefing: str | None = None


class ProjetoListResponse(BaseModel):
    items: list[ProjetoListItem] = Field(default_factory=list)
    total: int = 0


class EmpresaRelacionados(BaseModel):
    """Tudo ligado a uma empresa — a ficha 360."""
    negocios: list[NegocioListItem] = Field(default_factory=list)
    projetos: list[ProjetoListItem] = Field(default_factory=list)
    atividades: list[AtividadeListItem] = Field(default_factory=list)


# ── Record universal (navegação relacional bidirecional) ─────────────

class RecordCampo(BaseModel):
    label: str
    valor: str                      # texto exibido (formatado)
    campo: str | None = None        # nome do campo no banco (None = não editável)
    kind: str = "text"              # text|num|date|select|bool
    opcoes_key: str | None = None   # chave em /crm/opcoes (quando kind=select)
    raw: str | None = None          # valor cru pra edição (default = valor)


class RecordLink(BaseModel):
    tipo: str           # empresa|contato|negocio|projeto|atividade
    id: str
    nome: str
    sub: str | None = None


class RecordGrupo(BaseModel):
    titulo: str
    itens: list[RecordLink] = Field(default_factory=list)


class RecordDetalhe(BaseModel):
    tipo: str
    id: str
    titulo: str
    campos: list[RecordCampo] = Field(default_factory=list)
    grupos: list[RecordGrupo] = Field(default_factory=list)
    notas: str | None = None


class RecordPatch(BaseModel):
    """Edição parcial: só os campos enviados são alterados (edição inline)."""
    campos: dict[str, Any]


# ── Opções de select gerenciáveis ────────────────────────────────────

class OpcaoOut(BaseModel):
    id: str
    grupo: str
    valor: str
    cor: str | None = None
    ordem: int
    ativo: bool


class OpcaoCreate(BaseModel):
    grupo: str
    valor: str
    cor: str | None = None


class OpcaoUpdate(BaseModel):
    valor: str | None = None
    cor: str | None = None
    ativo: bool | None = None


class OpcaoReorder(BaseModel):
    grupo: str
    ids: list[str] = Field(default_factory=list)


# ── Upserts (CRUD) ───────────────────────────────────────────────────

class NegocioUpsert(BaseModel):
    nome: str
    estagio: str | None = None
    valor_estimado: float | None = None
    probabilidade: str | None = None
    origem: str | None = None
    tipo_servico: list[str] = Field(default_factory=list)
    notas: str | None = None
    motivo_perda: str | None = None
    previsao_fechamento: str | None = None      # YYYY-MM-DD
    data_fechamento_real: str | None = None
    proxima_acao: str | None = None
    empresa_id: str | None = None
    contato_id: str | None = None


class AtividadeUpsert(BaseModel):
    titulo: str
    tipo: str | None = None
    status: str | None = None
    data: str | None = None                     # ISO (date ou datetime)
    resumo: str | None = None
    proximos_passos: str | None = None
    negocio_id: str | None = None
    contato_id: str | None = None


class ProjetoUpsert(BaseModel):
    nome: str
    status: str | None = None
    tipo_servico: str | None = None
    valor_total: float | None = None
    valor_recebido: float | None = None
    briefing: str | None = None
    link_producao: str | None = None
    repo_github: str | None = None
    forma_pagamento: str | None = None
    prazo_entrega: str | None = None
    data_inicio: str | None = None
    data_entrega_real: str | None = None
    empresa_id: str | None = None
    negocio_id: str | None = None


class KanbanColuna(BaseModel):
    status: str
    total: int
    empresas: list[EmpresaListItem] = Field(default_factory=list)


class KanbanResponse(BaseModel):
    colunas: list[KanbanColuna] = Field(default_factory=list)


class CrmMetricas(BaseModel):
    total_empresas: int = 0
    total_contatos: int = 0
    total_decisores: int = 0
    por_status: dict[str, int] = Field(default_factory=dict)


class EstagioResumo(BaseModel):
    estagio: str
    total: int
    valor: float


class CrmDashboard(BaseModel):
    # Pipeline
    pipeline_valor: float = 0
    pipeline_ponderado: float = 0
    negocios_abertos: int = 0
    por_estagio: list[EstagioResumo] = Field(default_factory=list)
    # Atividades
    atividades_total: int = 0
    atividades_pendentes: int = 0
    atividades_atrasadas: int = 0
    # Projetos (entrega/financeiro)
    projetos_total: int = 0
    projetos_valor_total: float = 0
    projetos_recebido: float = 0
    projetos_a_receber: float = 0
    # Contas
    empresas_total: int = 0
    clientes_ativos: int = 0
    contatos_total: int = 0
