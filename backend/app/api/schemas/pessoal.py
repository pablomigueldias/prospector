"""Schemas da área pessoal — Perfil Mestre, Vagas e Candidatura.

Isolado dos schemas da Reative (prospector/copywriter/outreach).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ══════════════════════════════════════════════════════════════════
# Perfil Mestre (quem EU sou)
# ══════════════════════════════════════════════════════════════════

class Habilidade(BaseModel):
    nome: str
    nivel: Optional[str] = None          # ex: "avançado"
    onde_usou: Optional[str] = None      # ex: "front do Prospector"


class Projeto(BaseModel):
    nome: str
    descricao: Optional[str] = None
    prova: Optional[str] = None          # o que ESTE projeto prova
    stack: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class Experiencia(BaseModel):
    empresa: Optional[str] = None
    cargo: Optional[str] = None
    periodo: Optional[str] = None
    descricao: Optional[str] = None


class Formacao(BaseModel):
    instituicao: Optional[str] = None
    curso: Optional[str] = None
    periodo: Optional[str] = None


class BlocoCurriculo(BaseModel):
    titulo: str
    conteudo: str
    tags: List[str] = Field(default_factory=list)


class OQueProcuro(BaseModel):
    stack: List[str] = Field(default_factory=list)
    modelo: Optional[str] = None         # remoto / híbrido / presencial
    tipo_empresa: Optional[str] = None
    pretensao: Optional[str] = None
    observacoes: Optional[str] = None


class ContatoPessoal(BaseModel):
    email: Optional[str] = None
    telefone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class PerfilMestreBase(BaseModel):
    nome: str
    titulo: Optional[str] = None
    resumo: Optional[str] = None
    tom_escrita: Optional[str] = None
    habilidades: List[Habilidade] = Field(default_factory=list)
    projetos: List[Projeto] = Field(default_factory=list)
    experiencias: List[Experiencia] = Field(default_factory=list)
    formacao: List[Formacao] = Field(default_factory=list)
    o_que_procuro: Optional[OQueProcuro] = None
    blocos_curriculo: List[BlocoCurriculo] = Field(default_factory=list)
    contato: Optional[ContatoPessoal] = None


class PerfilMestreUpsert(PerfilMestreBase):
    """Payload de criação/atualização do perfil ativo."""


class PerfilMestreResponse(PerfilMestreBase):
    id: str
    ativo: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
# Vagas (vaga-alvo)
# ══════════════════════════════════════════════════════════════════

class VagaCreate(BaseModel):
    titulo: str
    descricao: str = Field(..., description="Descrição da vaga colada na mão")
    empresa: Optional[str] = None
    link: Optional[str] = None
    fonte: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    localizacao: Optional[str] = None
    modelo: Optional[str] = None
    senioridade: Optional[str] = None
    notas: Optional[str] = None


class VagaUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    empresa: Optional[str] = None
    link: Optional[str] = None
    fonte: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    localizacao: Optional[str] = None
    modelo: Optional[str] = None
    senioridade: Optional[str] = None
    notas: Optional[str] = None
    status: Optional[str] = None


class FaixaSalarial(BaseModel):
    """Estimativa honesta de mercado (BR) pra esta vaga, PJ e CLT, R$/mês."""

    pj_min: Optional[int] = None         # faixa de mercado PJ (bruto/mês)
    pj_max: Optional[int] = None
    clt_min: Optional[int] = None        # faixa de mercado CLT (salário base/mês)
    clt_max: Optional[int] = None
    pretensao_pj: Optional[int] = None   # quanto pedir em PJ dado seu fit
    pretensao_clt: Optional[int] = None  # quanto pedir em CLT dado seu fit
    base: Optional[str] = None           # no que a estimativa se baseia
    observacao: Optional[str] = None     # ressalva honesta sobre a estimativa

    @field_validator(
        "pj_min", "pj_max", "clt_min", "clt_max",
        "pretensao_pj", "pretensao_clt",
        mode="before",
    )
    @classmethod
    def _so_digitos(cls, v):
        """Aceita 'R$ 8.000', '8000.0' etc. → 8000; vazio → None."""
        if v is None or isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        digitos = "".join(c for c in str(v) if c.isdigit())
        return int(digitos) if digitos else None


class AnaliseVaga(BaseModel):
    requisitos_obrigatorios: List[str] = Field(default_factory=list)
    desejaveis: List[str] = Field(default_factory=list)
    stack: List[str] = Field(default_factory=list)
    senioridade: Optional[str] = None
    palavras_chave: List[str] = Field(default_factory=list)
    resumo: Optional[str] = None
    salario: Optional[FaixaSalarial] = None


class MatchVaga(BaseModel):
    aderencia: int = 0                   # 0-100
    tenho: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    destaques: List[str] = Field(default_factory=list)
    veredito: Optional[str] = None       # vale o esforço? (1 frase)


class VagaResponse(BaseModel):
    id: str
    titulo: str
    empresa: Optional[str] = None
    link: Optional[str] = None
    fonte: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    localizacao: Optional[str] = None
    modelo: Optional[str] = None
    senioridade: Optional[str] = None
    descricao: str
    notas: Optional[str] = None
    status: str
    analise_json: Optional[AnaliseVaga] = None
    match_json: Optional[MatchVaga] = None
    match_score: Optional[int] = None
    curriculo: Optional["CurriculoVaga"] = None      # currículo ATS salvo
    curriculo_gerado_em: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class VagaListItem(BaseModel):
    id: str
    titulo: str
    empresa: Optional[str] = None
    status: str
    modelo: Optional[str] = None
    senioridade: Optional[str] = None
    match_score: Optional[int] = None
    tem_analise: bool = False
    tem_curriculo: bool = False
    qtd_rascunhos: int = 0
    created_at: Optional[str] = None


class VagaListResponse(BaseModel):
    items: List[VagaListItem]
    total: int


class AnalisarVagaResponse(BaseModel):
    success: bool = True
    analise: AnaliseVaga
    match: MatchVaga
    match_score: int


class VagasMetricas(BaseModel):
    """Funil + taxas do caçador de vagas (agrega todas, ignora filtros)."""

    total: int = 0
    por_status: dict = Field(default_factory=dict)  # status -> contagem
    candidaturas: int = 0          # saiu de 'quero_candidatar' (candidatei+…+fim)
    em_andamento: int = 0          # candidatei + respondeu + entrevista
    responderam: int = 0           # respondeu + entrevista
    entrevistas: int = 0           # entrevista
    # Taxas sobre 'em_andamento' (não conta 'fim' pra não inflar/honesto). 0-100.
    taxa_resposta: Optional[int] = None
    taxa_entrevista: Optional[int] = None
    # Match médio (0-100) de todas com score e só das que viraram candidatura.
    match_medio: Optional[int] = None
    match_medio_candidaturas: Optional[int] = None


# ══════════════════════════════════════════════════════════════════
# Estudo — o que a maioria das vagas pede e você ainda não tem
# ══════════════════════════════════════════════════════════════════

class SkillEstudo(BaseModel):
    skill: str                 # nome de exibição (forma mais comum nas vagas)
    n_vagas: int               # em quantas vagas analisadas aparece (demanda)
    pct_vagas: int             # % das vagas analisadas
    obrigatoria_em: int        # em quantas é requisito OBRIGATÓRIO
    tenho: bool                # já está no seu Perfil Mestre?


class EstudoVagasResponse(BaseModel):
    """Agrega as skills pedidas por TODAS as vagas analisadas e cruza com o perfil."""

    total_vagas: int = 0                          # vagas com análise consideradas
    para_estudar: List[SkillEstudo] = Field(default_factory=list)   # demandadas que você NÃO tem
    pontos_fortes: List[SkillEstudo] = Field(default_factory=list)  # demandadas que você JÁ tem (destacar no CV)


# ══════════════════════════════════════════════════════════════════
# Candidatura (Fase 4 — gera rascunho, PARA antes de enviar)
# ══════════════════════════════════════════════════════════════════

class EmailCandidatura(BaseModel):
    assunto: Optional[str] = None
    corpo: str
    tom: Optional[str] = None


class CartaCandidatura(BaseModel):
    corpo: str
    tom: Optional[str] = None


class GerarCandidaturaRequest(BaseModel):
    gerar_carta: bool = Field(True, description="Gera também carta de apresentação")
    instrucoes_extra: Optional[str] = Field(
        None, description="Ajustes pontuais de tom/ângulo pra esta candidatura"
    )


class GerarCandidaturaResponse(BaseModel):
    success: bool = True
    email: EmailCandidatura
    variantes_email: List[EmailCandidatura] = Field(default_factory=list)
    carta: Optional[CartaCandidatura] = None
    rascunho_id: Optional[str] = None    # id do CandidaturaEmail salvo (email principal)


class CandidaturaEmailItem(BaseModel):
    id: str
    vaga_id: str
    tipo: str
    destinatario: Optional[str] = None
    assunto: Optional[str] = None
    corpo: str
    tom: Optional[str] = None
    status: str
    created_at: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
# Currículo sob medida pra vaga (gera PDF no front)
# ══════════════════════════════════════════════════════════════════

class CurriculoExperiencia(BaseModel):
    cargo: Optional[str] = None
    empresa: Optional[str] = None
    periodo: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)  # realizações adaptadas


class CompetenciaGrupo(BaseModel):
    categoria: str                       # ex: "Linguagens", "Frameworks", "Backend"
    itens: List[str] = Field(default_factory=list)


class CurriculoProjeto(BaseModel):
    nome: str                            # nome EXATO do projeto no perfil
    descricao: Optional[str] = None      # adaptada à vaga
    stack: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class CurriculoVaga(BaseModel):
    nome: str                             # factual (injetado do perfil)
    titulo: Optional[str] = None          # headline adaptada à vaga
    contato: Optional[ContatoPessoal] = None  # factual (injetado do perfil)
    resumo: Optional[str] = None          # SOBRE: 2-4 frases adaptadas à vaga
    competencias: List[CompetenciaGrupo] = Field(default_factory=list)  # agrupadas
    experiencias: List[CurriculoExperiencia] = Field(default_factory=list)
    projetos: List[CurriculoProjeto] = Field(default_factory=list)
    formacao: List[Formacao] = Field(default_factory=list)  # factual (injetado)


class GerarCurriculoResponse(BaseModel):
    vaga_id: str
    curriculo: CurriculoVaga
    gerado_em: Optional[str] = None


# VagaResponse referencia CurriculoVaga (definido acima); resolve o forward ref.
VagaResponse.model_rebuild()
