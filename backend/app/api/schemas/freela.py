"""Schemas do Agente Freelancer (Workana) — área pessoal.

CRM de propostas (Plataforma, Cliente, Projeto, Proposta) + precificador.
Isolado dos demais schemas pessoais.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

# ══════════════════════════════════════════════════════════════════
# Plataforma (read-only; seedada)
# ══════════════════════════════════════════════════════════════════

class PlataformaResponse(BaseModel):
    id: str
    nome: str
    url_base: str | None = None
    config_comissao: dict | None = None
    lance_minimo_padrao: float | None = None


# ══════════════════════════════════════════════════════════════════
# Cliente
# ══════════════════════════════════════════════════════════════════

class ClienteBase(BaseModel):
    nome: str
    plataforma_id: str | None = None
    rating: float | None = None
    projetos_publicados: int | None = None
    projetos_pagos: int | None = None
    pagamento_verificado: bool = False
    membro_desde: str | None = None
    ja_me_pagou_usd: float = 0
    notas: str | None = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: str | None = None
    plataforma_id: str | None = None
    rating: float | None = None
    projetos_publicados: int | None = None
    projetos_pagos: int | None = None
    pagamento_verificado: bool | None = None
    membro_desde: str | None = None
    ja_me_pagou_usd: float | None = None
    notas: str | None = None


class ClienteResponse(ClienteBase):
    id: str
    created_at: str | None = None
    updated_at: str | None = None


# ══════════════════════════════════════════════════════════════════
# Projeto (você cola o texto)
# ══════════════════════════════════════════════════════════════════

class ProjetoBase(BaseModel):
    titulo: str
    descricao: str
    plataforma_id: str | None = None
    cliente_id: str | None = None
    url: str | None = None
    faixa_orcamento_min: float | None = None
    faixa_orcamento_max: float | None = None
    habilidades: list[str] = Field(default_factory=list)
    prazo_estimado: str | None = None
    status_no_site: str | None = None
    n_propostas_concorrentes: int | None = None
    n_interessados: int | None = None
    publicado_em: str | None = None       # YYYY-MM-DD (data de publicação no site)


class ProjetoCreate(ProjetoBase):
    pass


class ExtrairProjetoRequest(BaseModel):
    """Origem da extração: texto colado OU url do projeto (ao menos um)."""

    texto: str | None = Field(None, description="Texto do projeto colado da Workana")
    url: str | None = Field(None, description="URL do projeto — busca e lê a página")

    @model_validator(mode="after")
    def _exige_origem(self):
        if not (self.texto and self.texto.strip()) and not (self.url and self.url.strip()):
            raise ValueError("Informe o texto colado ou a URL do projeto.")
        return self


class ExtrairProjetoResponse(BaseModel):
    """Campos pré-preenchidos a partir do texto/URL (revisar antes de salvar)."""

    titulo: str | None = None
    descricao: str | None = None  # texto-fonte (colado ou lido da URL)
    url: str | None = None        # eco da URL quando importado por link
    faixa_orcamento_min: float | None = None
    faixa_orcamento_max: float | None = None
    n_propostas_concorrentes: int | None = None
    n_interessados: int | None = None
    habilidades: list[str] = Field(default_factory=list)  # skills exigidas no texto

    @field_validator(
        "faixa_orcamento_min", "faixa_orcamento_max",
        "n_propostas_concorrentes", "n_interessados",
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
    titulo: str | None = None
    descricao: str | None = None
    plataforma_id: str | None = None
    cliente_id: str | None = None
    url: str | None = None
    faixa_orcamento_min: float | None = None
    faixa_orcamento_max: float | None = None
    habilidades: list[str] | None = None
    prazo_estimado: str | None = None
    status_no_site: str | None = None
    n_propostas_concorrentes: int | None = None
    n_interessados: int | None = None
    publicado_em: str | None = None


class ProjetoResponse(ProjetoBase):
    id: str
    analise_json: dict | None = None
    coletado_em: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProjetoListItem(BaseModel):
    id: str
    titulo: str
    cliente_nome: str | None = None
    status_no_site: str | None = None
    faixa_orcamento_min: float | None = None
    faixa_orcamento_max: float | None = None
    n_propostas_concorrentes: int | None = None
    fit_score: int | None = None       # vem do analise_json (Fase 3)
    risco: str | None = None           # baixo / medio / alto (scam radar)
    quadrante: str | None = None       # quick_win | dificil_longo | escopo_vago | padrao
    preco_status: str | None = None    # subcotado | justo | acima | sem_orcamento
    estimativa: EstimativaFreela | None = None  # esforço/preço pra pré-preencher
    tem_analise: bool = False
    qtd_propostas: int = 0
    cliente_recorrente: bool = False      # cliente já me pagou (comissão menor)
    cliente_pago_usd: float = 0
    bom_primeiro: bool = False            # selo cold start: bom candidato a 1ª nota 5★
    bom_primeiro_motivos: list[str] = Field(default_factory=list)
    publicado_em: str | None = None       # YYYY-MM-DD
    dias_desde_publicacao: int | None = None  # frescor (responder cedo é vantagem)
    momento: str | None = None            # veredito de timing: agora | espere | passe
    momento_motivo: str | None = None     # por que (1 linha)
    valor_esperado: float | None = None   # custo de oportunidade: R$/h esperado (ticket×prob×fit÷horas)
    prob_resposta: float | None = None    # prob. de resposta usada no cálculo (0..1)
    created_at: str | None = None


class ProjetoListResponse(BaseModel):
    items: list[ProjetoListItem]
    total: int


# ══════════════════════════════════════════════════════════════════
# Proposta
# ══════════════════════════════════════════════════════════════════

# Ângulo da 1ª linha da proposta (A/B) — qual abre melhor a conversa.
ANGULOS_ABERTURA = ("direto", "prova", "pergunta")


class PropostaBase(BaseModel):
    valor_cotado: float | None = None
    horas_estimadas: float | None = None
    valor_liquido_estimado: float | None = None
    texto_enviado: str | None = None
    projetos_destacados: list[str] = Field(default_factory=list)
    habilidades_destacadas: list[str] = Field(default_factory=list)
    prazo_proposto: str | None = None
    angulo_abertura: str | None = None    # direto | prova | pergunta (A/B)


class PropostaCreate(PropostaBase):
    projeto_id: str


class PropostaUpdate(PropostaBase):
    # status muda pelo endpoint dedicado /status (registra evento)
    pass


class PropostaResponse(PropostaBase):
    id: str
    projeto_id: str
    status: str
    enviada_em: str | None = None
    data_resposta: str | None = None
    data_fechamento: str | None = None
    motivo_perda: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PropostaStatusUpdate(BaseModel):
    status: str
    motivo_perda: str | None = None  # usado quando status="perdida"


class PropostaKanbanItem(BaseModel):
    id: str
    projeto_id: str
    projeto_titulo: str
    cliente_nome: str | None = None
    valor_cotado: float | None = None
    valor_liquido_estimado: float | None = None
    status: str
    dias_desde_envio: int | None = None
    created_at: str | None = None


class KanbanColuna(BaseModel):
    status: str
    items: list[PropostaKanbanItem]


class KanbanResponse(BaseModel):
    colunas: list[KanbanColuna]


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
    tempo_medio_resposta_horas: float | None = None  # velocidade do cliente
    valor_hora_real: float | None = None             # líquido/hora das fechadas


class TaxaPorStackItem(BaseModel):
    """Taxa de resposta de uma stack/categoria — onde insistir."""
    stack: str
    enviadas: int
    respondidas: int
    taxa_resposta: float       # respondidas / enviadas


class TaxaPorStackResponse(BaseModel):
    itens: list[TaxaPorStackItem] = Field(default_factory=list)


class TaxaPorAnguloItem(BaseModel):
    """Taxa de resposta por ângulo de abertura — qual 1ª linha converte mais."""
    angulo: str                # direto | prova | pergunta
    enviadas: int
    respondidas: int
    taxa_resposta: float       # respondidas / enviadas


class TaxaPorAnguloResponse(BaseModel):
    itens: list[TaxaPorAnguloItem] = Field(default_factory=list)


class CapacidadeResponse(BaseModel):
    """Anti-furada: quanto da semana ainda cabe (vs já comprometido)."""
    horas_semana: int                 # capacidade faturável/semana (config)
    horas_comprometidas: float        # soma das horas das propostas fechadas
    horas_livres: float               # o que sobra pra novos projetos


# ══════════════════════════════════════════════════════════════════
# Motor da meta (matemática reversa + rampa — sem IA)
# ══════════════════════════════════════════════════════════════════

class PlanoMetaRequest(BaseModel):
    meta_liquida: float = 10000           # R$ líquido/mês (o que entra no bolso)
    horas_dia: float = 5                  # capacidade diária
    dias_mes: int = 26                    # dias trabalhados no mês
    pct_faturavel: float = 0.7            # fração das horas que vira trabalho cobrado


class FaseRampa(BaseModel):
    nome: str          # ex.: "F1 — Cold start"
    meta_min: float
    meta_max: float
    foco: str


class ProgressoMes(BaseModel):
    """Progresso real do mês corrente vs ritmo linear necessário pra bater a meta."""
    realizado: float       # líquido fechado no mês (proposta fechada com data_resposta no mês)
    meta_ate_hoje: float   # ritmo linear esperado até hoje (meta × fração do mês decorrida)
    fechadas_mes: int      # nº de propostas fechadas no mês
    dia: int               # dia do mês corrente
    dias_no_mes: int
    pct_meta: float        # realizado ÷ meta (0..1+)
    status: str            # na_frente | no_caminho | atras | sem_dados
    resumo: str            # 1 linha pro card


class PlanoMetaResponse(BaseModel):
    meta_liquida: float
    horas_faturaveis_mes: float
    valor_hora_alvo: float                # meta ÷ horas faturáveis: o R$/h que fecha a conta
    valor_hora_real: float | None = None       # das fechadas (echo de métricas)
    ticket_medio: float | None = None          # echo de métricas
    projecao_liquida_mes: float | None = None  # valor_hora_real × horas (ritmo atual)
    projetos_necessarios_mes: float | None = None
    propostas_necessarias_mes: float | None = None
    propostas_por_semana: float | None = None
    alcancavel_por_volume: bool = False   # o ritmo atual de R$/h enche a meta?
    gargalo: str                          # ticket | conversao | volume | no_caminho | sem_dados
    diagnostico: str
    fase: FaseRampa
    progresso_mes: ProgressoMes | None = None  # realizado no mês vs ritmo necessário


# ══════════════════════════════════════════════════════════════════
# Precificador (matemática da comissão — sem IA)
# ══════════════════════════════════════════════════════════════════

class PrecificarRequest(BaseModel):
    liquido_desejado: float
    cliente_id: str | None = None          # puxa ja_me_pagou_usd do cliente
    ja_me_pagou_usd: float | None = None    # ou passe direto (cliente novo = 0)
    plataforma_id: str | None = None        # de onde vêm as faixas de comissão
    horas_estimadas: float | None = None
    valor_hora_alvo: float | None = None


class PrecificarResponse(BaseModel):
    pct_comissao: float          # 0.20 / 0.10 / 0.05
    valor_a_cotar: float         # o que você poe no campo "valor total"
    cliente_paga: float          # valor_a_cotar + custo de serviço do cliente
    lance_minimo: float | None = None
    abaixo_do_lance_minimo: bool = False
    liquido_por_hora: float | None = None
    alerta: str | None = None  # ex: "abaixo do seu valor-hora alvo"


# ══════════════════════════════════════════════════════════════════
# Analisador de projeto (Fase 3 — IA) → grava em projeto.analise_json
# ══════════════════════════════════════════════════════════════════

class EstimativaFreela(BaseModel):
    """Esforço + preço justo de mercado (BR) pra este escopo. R$/horas/dias."""

    horas_estimadas: int | None = None      # horas de trabalho realistas
    prazo_dias: int | None = None           # prazo de entrega em dias
    valor_mercado_min: int | None = None    # faixa honesta de mercado (R$)
    valor_mercado_max: int | None = None
    valor_sugerido: int | None = None       # quanto cotar (R$), dado fit/concorrência

    @field_validator(
        "horas_estimadas", "prazo_dias",
        "valor_mercado_min", "valor_mercado_max", "valor_sugerido",
        mode="before",
    )
    @classmethod
    def _so_numero(cls, v):
        if v is None or isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        digitos = "".join(c for c in str(v) if c.isdigit())
        return int(digitos) if digitos else None


class VereditoPreco(BaseModel):
    """Cruzamento determinístico orçamento do cliente × mercado (calculado no
    service, não pela IA). Responde 'o valor está justo?'."""

    status: str | None = None       # subcotado | justo | acima | sem_orcamento
    gap_texto: str | None = None    # frase legível ("cliente R$800; mercado R$1.5-2.5k → subcotado")
    rh_orcamento: float | None = None  # R$/hora efetivo do orçamento do cliente
    rh_vs_alvo: bool | None = None     # True se rh_orcamento abaixo do valor-hora alvo


class TarefaEstimada(BaseModel):
    """Uma entrega do escopo com horas — quebra o 'horas_estimadas' mágico."""

    nome: str
    horas: int | None = None

    @field_validator("horas", mode="before")
    @classmethod
    def _so_numero(cls, v):
        if v is None or isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        digitos = "".join(c for c in str(v) if c.isdigit())
        return int(digitos) if digitos else None


class AnaliseFreela(BaseModel):
    fit_score: int = 0                 # 0-100: é a sua praia?
    confianca_analise: str | None = None  # alta | media | baixa (texto pobre → baixa)
    confianca_motivo: str | None = None   # 1 linha: o que falta no texto pra cravar
    recomendacao: str | None = None  # vale / talvez / evite
    risco: str | None = None         # baixo / medio / alto (scam radar)
    complexidade_tecnica: str | None = None  # trivial | media | alta | incerta
    clareza_escopo: str | None = None        # claro | parcial | vago
    quadrante: str | None = None             # derivado: quick_win | dificil_longo | escopo_vago | padrao
    veredito: str | None = None      # 1 frase: gasto proposta aqui?
    veredito_preco: VereditoPreco | None = None  # calculado no service (orçamento × mercado)
    requisitos: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    tarefas: list[TarefaEstimada] = Field(default_factory=list)  # escopo quebrado em entregas + horas
    perguntas_cliente: list[str] = Field(default_factory=list)   # ambiguidades a esclarecer antes de cotar
    skills_faltando: list[str] = Field(default_factory=list)     # exige e NÃO está claro no seu perfil (gap)
    red_flags: list[str] = Field(default_factory=list)
    sinais_cliente: list[str] = Field(default_factory=list)
    ganchos: list[str] = Field(default_factory=list)  # o que do perfil conversa
    estimativa: EstimativaFreela | None = None     # esforço + preço de mercado


class AnalisarProjetoResponse(BaseModel):
    projeto_id: str
    analise: AnaliseFreela


# ══════════════════════════════════════════════════════════════════
# Redator + Seletor (Fase 5 — IA) → preenche a proposta
# ══════════════════════════════════════════════════════════════════

class VariacaoAbertura(BaseModel):
    """Uma 1ª linha alternativa pra A/B, rotulada pelo ângulo que ela usa."""
    angulo: str = "direto"   # direto | prova | pergunta
    texto: str


class RedacaoProposta(BaseModel):
    texto: str = ""                 # rascunho completo (estrutura Workana)
    prazo_sugerido: str | None = None
    tom: str | None = None       # técnico | institucional
    # Seletor: dos SEUS projetos/habilidades (max 3 / max 5)
    projetos_destacados: list[str] = Field(default_factory=list)
    habilidades_destacadas: list[str] = Field(default_factory=list)
    # A/B: 2-3 primeiras linhas alternativas (rotuladas) pra testar o que converte
    variacoes_abertura: list[VariacaoAbertura] = Field(default_factory=list)


class RedigirRequest(BaseModel):
    instrucoes_extra: str | None = None  # "cita o teste no Safari iOS" etc.


class RedigirResponse(BaseModel):
    proposta_id: str
    redacao: RedacaoProposta


# ══════════════════════════════════════════════════════════════════
# Assistente de negociação (IA) — não persiste, é conselho
# ══════════════════════════════════════════════════════════════════

class CorrigirRequest(BaseModel):
    correcoes: list[str] = Field(default_factory=list)  # pontos do checklist a corrigir


class NegociarRequest(BaseModel):
    objecao: str  # o que o cliente falou (ex.: "tá caro", "consegue por R$1000?")


class NegociarResponse(BaseModel):
    proposta_id: str
    opcoes: list[str]  # 2-3 respostas com estratégias diferentes


class ChecklistItem(BaseModel):
    criterio: str
    ok: bool = False
    nota: str | None = None


class ChecklistResponse(BaseModel):
    """Gate de qualidade do rascunho: pontua e diz o que faltou antes de enviar."""

    proposta_id: str
    score: int = 0                      # 0-100
    selo: str | None = None          # "pronta" | "ajustar" | "fraca" (derivado)
    itens: list[ChecklistItem] = Field(default_factory=list)
    sugestoes: list[str] = Field(default_factory=list)
    # Conformidade Workana: setado se o texto tiver e-mail/telefone/link externo.
    alerta_conformidade: str | None = None
