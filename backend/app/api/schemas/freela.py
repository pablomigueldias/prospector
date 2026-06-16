"""Schemas do Agente Freelancer (Workana) — área pessoal.

CRM de propostas (Plataforma, Cliente, Projeto, Proposta) + precificador.
Isolado dos demais schemas pessoais.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ══════════════════════════════════════════════════════════════════
# Plataforma (read-only; seedada)
# ══════════════════════════════════════════════════════════════════

class PlataformaResponse(BaseModel):
    id: str
    nome: str
    url_base: Optional[str] = None
    config_comissao: Optional[dict] = None
    lance_minimo_padrao: Optional[float] = None


# ══════════════════════════════════════════════════════════════════
# Cliente
# ══════════════════════════════════════════════════════════════════

class ClienteBase(BaseModel):
    nome: str
    plataforma_id: Optional[str] = None
    rating: Optional[float] = None
    projetos_publicados: Optional[int] = None
    projetos_pagos: Optional[int] = None
    pagamento_verificado: bool = False
    membro_desde: Optional[str] = None
    ja_me_pagou_usd: float = 0
    notas: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    plataforma_id: Optional[str] = None
    rating: Optional[float] = None
    projetos_publicados: Optional[int] = None
    projetos_pagos: Optional[int] = None
    pagamento_verificado: Optional[bool] = None
    membro_desde: Optional[str] = None
    ja_me_pagou_usd: Optional[float] = None
    notas: Optional[str] = None


class ClienteResponse(ClienteBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
# Projeto (você cola o texto)
# ══════════════════════════════════════════════════════════════════

class ProjetoBase(BaseModel):
    titulo: str
    descricao: str
    plataforma_id: Optional[str] = None
    cliente_id: Optional[str] = None
    url: Optional[str] = None
    faixa_orcamento_min: Optional[float] = None
    faixa_orcamento_max: Optional[float] = None
    habilidades: List[str] = Field(default_factory=list)
    prazo_estimado: Optional[str] = None
    status_no_site: Optional[str] = None
    n_propostas_concorrentes: Optional[int] = None
    n_interessados: Optional[int] = None


class ProjetoCreate(ProjetoBase):
    pass


class ExtrairProjetoRequest(BaseModel):
    texto: str = Field(..., description="Texto do projeto colado da Workana")


class ExtrairProjetoResponse(BaseModel):
    """Campos pré-preenchidos a partir do texto colado (revisar antes de salvar)."""

    titulo: Optional[str] = None
    faixa_orcamento_min: Optional[float] = None
    faixa_orcamento_max: Optional[float] = None
    n_propostas_concorrentes: Optional[int] = None

    @field_validator(
        "faixa_orcamento_min", "faixa_orcamento_max", "n_propostas_concorrentes",
        mode="before",
    )
    @classmethod
    def _so_numero(cls, v):
        """Aceita 'R$ 1.500', '64 propostas' etc. → número; vazio → None."""
        if v is None or isinstance(v, (int, float)):
            return v
        digitos = "".join(c for c in str(v) if c.isdigit())
        return int(digitos) if digitos else None


class ProjetoUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    plataforma_id: Optional[str] = None
    cliente_id: Optional[str] = None
    url: Optional[str] = None
    faixa_orcamento_min: Optional[float] = None
    faixa_orcamento_max: Optional[float] = None
    habilidades: Optional[List[str]] = None
    prazo_estimado: Optional[str] = None
    status_no_site: Optional[str] = None
    n_propostas_concorrentes: Optional[int] = None
    n_interessados: Optional[int] = None


class ProjetoResponse(ProjetoBase):
    id: str
    analise_json: Optional[dict] = None
    coletado_em: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProjetoListItem(BaseModel):
    id: str
    titulo: str
    cliente_nome: Optional[str] = None
    status_no_site: Optional[str] = None
    faixa_orcamento_min: Optional[float] = None
    faixa_orcamento_max: Optional[float] = None
    n_propostas_concorrentes: Optional[int] = None
    fit_score: Optional[int] = None       # vem do analise_json (Fase 3)
    risco: Optional[str] = None           # baixo / medio / alto (scam radar)
    tem_analise: bool = False
    qtd_propostas: int = 0
    cliente_recorrente: bool = False      # cliente já me pagou (comissão menor)
    cliente_pago_usd: float = 0
    created_at: Optional[str] = None


class ProjetoListResponse(BaseModel):
    items: List[ProjetoListItem]
    total: int


# ══════════════════════════════════════════════════════════════════
# Proposta
# ══════════════════════════════════════════════════════════════════

class PropostaBase(BaseModel):
    valor_cotado: Optional[float] = None
    horas_estimadas: Optional[float] = None
    valor_liquido_estimado: Optional[float] = None
    texto_enviado: Optional[str] = None
    projetos_destacados: List[str] = Field(default_factory=list)
    habilidades_destacadas: List[str] = Field(default_factory=list)
    prazo_proposto: Optional[str] = None


class PropostaCreate(PropostaBase):
    projeto_id: str


class PropostaUpdate(PropostaBase):
    # status muda pelo endpoint dedicado /status (registra evento)
    pass


class PropostaResponse(PropostaBase):
    id: str
    projeto_id: str
    status: str
    enviada_em: Optional[str] = None
    data_resposta: Optional[str] = None
    data_fechamento: Optional[str] = None
    motivo_perda: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PropostaStatusUpdate(BaseModel):
    status: str
    motivo_perda: Optional[str] = None  # usado quando status="perdida"


class PropostaKanbanItem(BaseModel):
    id: str
    projeto_id: str
    projeto_titulo: str
    cliente_nome: Optional[str] = None
    valor_cotado: Optional[float] = None
    valor_liquido_estimado: Optional[float] = None
    status: str
    dias_desde_envio: Optional[int] = None
    created_at: Optional[str] = None


class KanbanColuna(BaseModel):
    status: str
    items: List[PropostaKanbanItem]


class KanbanResponse(BaseModel):
    colunas: List[KanbanColuna]


# ══════════════════════════════════════════════════════════════════
# Métricas do painel
# ══════════════════════════════════════════════════════════════════

class MetricasResponse(BaseModel):
    total_propostas: int
    enviadas: int
    respondidas: int
    fechadas: int
    perdidas: int
    em_aberto: int             # propostas aguardando decisão
    taxa_resposta: float       # respondidas / enviadas
    taxa_fechamento: float     # fechadas / enviadas
    liquido_total_fechado: float
    ticket_medio_fechado: float
    # Forecast: o que provavelmente entra do pipeline atual
    pipeline_aberto_liquido: float          # soma do líquido em aberto
    forecast_liquido: float                 # pipeline × taxa de fechamento
    # Calibração
    tempo_medio_resposta_horas: Optional[float] = None  # velocidade do cliente
    valor_hora_real: Optional[float] = None             # líquido/hora das fechadas


# ══════════════════════════════════════════════════════════════════
# Precificador (matemática da comissão — sem IA)
# ══════════════════════════════════════════════════════════════════

class PrecificarRequest(BaseModel):
    liquido_desejado: float
    cliente_id: Optional[str] = None          # puxa ja_me_pagou_usd do cliente
    ja_me_pagou_usd: Optional[float] = None    # ou passe direto (cliente novo = 0)
    plataforma_id: Optional[str] = None        # de onde vêm as faixas de comissão
    horas_estimadas: Optional[float] = None
    valor_hora_alvo: Optional[float] = None


class PrecificarResponse(BaseModel):
    pct_comissao: float          # 0.20 / 0.10 / 0.05
    valor_a_cotar: float         # o que você poe no campo "valor total"
    cliente_paga: float          # valor_a_cotar + custo de serviço do cliente
    lance_minimo: Optional[float] = None
    abaixo_do_lance_minimo: bool = False
    liquido_por_hora: Optional[float] = None
    alerta: Optional[str] = None  # ex: "abaixo do seu valor-hora alvo"


# ══════════════════════════════════════════════════════════════════
# Analisador de projeto (Fase 3 — IA) → grava em projeto.analise_json
# ══════════════════════════════════════════════════════════════════

class AnaliseFreela(BaseModel):
    fit_score: int = 0                 # 0-100: é a sua praia?
    recomendacao: Optional[str] = None  # vale / talvez / evite
    risco: Optional[str] = None         # baixo / medio / alto (scam radar)
    veredito: Optional[str] = None      # 1 frase: gasto proposta aqui?
    requisitos: List[str] = Field(default_factory=list)
    stack: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    sinais_cliente: List[str] = Field(default_factory=list)
    ganchos: List[str] = Field(default_factory=list)  # o que do perfil conversa


class AnalisarProjetoResponse(BaseModel):
    projeto_id: str
    analise: AnaliseFreela


# ══════════════════════════════════════════════════════════════════
# Redator + Seletor (Fase 5 — IA) → preenche a proposta
# ══════════════════════════════════════════════════════════════════

class RedacaoProposta(BaseModel):
    texto: str = ""                 # rascunho completo (estrutura Workana)
    prazo_sugerido: Optional[str] = None
    tom: Optional[str] = None       # técnico | institucional
    # Seletor: dos SEUS projetos/habilidades (max 3 / max 5)
    projetos_destacados: List[str] = Field(default_factory=list)
    habilidades_destacadas: List[str] = Field(default_factory=list)
    # A/B: 2-3 primeiras linhas alternativas pra testar qual converte mais
    variacoes_abertura: List[str] = Field(default_factory=list)


class RedigirRequest(BaseModel):
    instrucoes_extra: Optional[str] = None  # "cita o teste no Safari iOS" etc.


class RedigirResponse(BaseModel):
    proposta_id: str
    redacao: RedacaoProposta


# ══════════════════════════════════════════════════════════════════
# Assistente de negociação (IA) — não persiste, é conselho
# ══════════════════════════════════════════════════════════════════

class NegociarRequest(BaseModel):
    objecao: str  # o que o cliente falou (ex.: "tá caro", "consegue por R$1000?")


class NegociarResponse(BaseModel):
    proposta_id: str
    opcoes: List[str]  # 2-3 respostas com estratégias diferentes


class ChecklistItem(BaseModel):
    criterio: str
    ok: bool = False
    nota: Optional[str] = None


class ChecklistResponse(BaseModel):
    """Gate de qualidade do rascunho: pontua e diz o que faltou antes de enviar."""

    proposta_id: str
    score: int = 0                      # 0-100
    selo: Optional[str] = None          # "pronta" | "ajustar" | "fraca" (derivado)
    itens: List[ChecklistItem] = Field(default_factory=list)
    sugestoes: List[str] = Field(default_factory=list)
    # Conformidade Workana: setado se o texto tiver e-mail/telefone/link externo.
    alerta_conformidade: Optional[str] = None
