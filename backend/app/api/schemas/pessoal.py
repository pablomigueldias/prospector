"""Schemas da área pessoal — Perfil Mestre, Vagas e Candidatura.

Isolado dos schemas da Reative (prospector/copywriter/outreach).
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

# ══════════════════════════════════════════════════════════════════
# Perfil Mestre (quem EU sou)
# ══════════════════════════════════════════════════════════════════

class Habilidade(BaseModel):
    nome: str
    nivel: str | None = None          # ex: "avançado"
    onde_usou: str | None = None      # ex: "front do Prospector"


class Projeto(BaseModel):
    nome: str
    descricao: str | None = None
    prova: str | None = None          # o que ESTE projeto prova
    stack: list[str] = Field(default_factory=list)
    link: str | None = None


class Experiencia(BaseModel):
    empresa: str | None = None
    cargo: str | None = None
    periodo: str | None = None
    descricao: str | None = None


class Formacao(BaseModel):
    instituicao: str | None = None
    curso: str | None = None
    periodo: str | None = None


class Certificacao(BaseModel):
    nome: str
    tema: str | None = None           # grupo, ex: "Frontend", "IA/ML", "Zoho/CRM"
    instituicao: str | None = None    # emissor, se conhecido
    ano: str | None = None            # data/ano de conclusão (YYYY ou YYYY-MM-DD)
    carga_horaria: str | None = None  # ex: "40h"
    prova: str | None = None          # o que ESTE certificado comprova
    arquivo: str | None = None        # nome do PDF de origem (chave do sync Drive)


class CertificadoExtraido(BaseModel):
    """Saída crua do extrator multimodal (1 PDF de certificado → campos)."""
    nome_curso: str | None = None
    instituicao: str | None = None
    carga_horaria: str | None = None
    data_conclusao: str | None = None
    aluno: str | None = None
    tema: str | None = None
    prova: str | None = None


class BlocoCurriculo(BaseModel):
    titulo: str
    conteudo: str
    tags: list[str] = Field(default_factory=list)


class OQueProcuro(BaseModel):
    stack: list[str] = Field(default_factory=list)
    modelo: str | None = None         # remoto / híbrido / presencial
    tipo_empresa: str | None = None
    pretensao: str | None = None
    observacoes: str | None = None


class ContatoPessoal(BaseModel):
    email: str | None = None
    telefone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None


class PerfilMestreBase(BaseModel):
    nome: str
    titulo: str | None = None
    resumo: str | None = None
    tom_escrita: str | None = None
    habilidades: list[Habilidade] = Field(default_factory=list)
    projetos: list[Projeto] = Field(default_factory=list)
    experiencias: list[Experiencia] = Field(default_factory=list)
    formacao: list[Formacao] = Field(default_factory=list)
    certificacoes: list[Certificacao] = Field(default_factory=list)
    o_que_procuro: OQueProcuro | None = None
    blocos_curriculo: list[BlocoCurriculo] = Field(default_factory=list)
    contato: ContatoPessoal | None = None


class PerfilMestreUpsert(PerfilMestreBase):
    """Payload de criação/atualização do perfil ativo."""


class PerfilMestreResponse(PerfilMestreBase):
    id: str
    ativo: bool = True
    created_at: str | None = None
    updated_at: str | None = None


# ══════════════════════════════════════════════════════════════════
# Vagas (vaga-alvo)
# ══════════════════════════════════════════════════════════════════

class VagaCreate(BaseModel):
    titulo: str
    descricao: str = Field(..., description="Descrição da vaga colada na mão")
    empresa: str | None = None
    link: str | None = None
    fonte: str | None = None
    contato_nome: str | None = None
    contato_email: str | None = None
    localizacao: str | None = None
    modelo: str | None = None
    senioridade: str | None = None
    notas: str | None = None


class VagaUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    empresa: str | None = None
    link: str | None = None
    fonte: str | None = None
    contato_nome: str | None = None
    contato_email: str | None = None
    localizacao: str | None = None
    modelo: str | None = None
    senioridade: str | None = None
    notas: str | None = None
    status: str | None = None


class ExtrairVagaRequest(BaseModel):
    """Origem da extração: texto colado OU url da vaga (ao menos um)."""

    texto: str | None = Field(None, description="Texto da vaga colado na mão")
    url: str | None = Field(None, description="URL da vaga — busca e lê a página")

    @model_validator(mode="after")
    def _exige_origem(self):
        if not (self.texto and self.texto.strip()) and not (self.url and self.url.strip()):
            raise ValueError("Informe o texto colado ou a URL da vaga.")
        return self


class ExtrairVagaResponse(BaseModel):
    """Campos pré-preenchidos a partir do texto/URL (revisar antes de salvar)."""

    titulo: str | None = None
    descricao: str | None = None  # texto-fonte (colado ou lido da URL)
    link: str | None = None       # eco da URL quando importado por link
    empresa: str | None = None
    localizacao: str | None = None
    modelo: str | None = None
    senioridade: str | None = None


class FaixaSalarial(BaseModel):
    """Estimativa honesta de mercado (BR) pra esta vaga, PJ e CLT, R$/mês."""

    pj_min: int | None = None         # faixa de mercado PJ (bruto/mês)
    pj_max: int | None = None
    clt_min: int | None = None        # faixa de mercado CLT (salário base/mês)
    clt_max: int | None = None
    pretensao_pj: int | None = None   # quanto pedir em PJ dado seu fit
    pretensao_clt: int | None = None  # quanto pedir em CLT dado seu fit
    base: str | None = None           # no que a estimativa se baseia
    observacao: str | None = None     # ressalva honesta sobre a estimativa

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
    requisitos_obrigatorios: list[str] = Field(default_factory=list)
    desejaveis: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    senioridade: str | None = None
    palavras_chave: list[str] = Field(default_factory=list)
    resumo: str | None = None
    salario: FaixaSalarial | None = None


class PlanoGap(BaseModel):
    """1 linha acionável pra fechar um gap do match (item #7 do MELHORIAS_VAGAS)."""
    gap: str                          # o requisito que falta
    acao: str                         # o que fazer (estudar X / virar prova num projeto)


class MatchVaga(BaseModel):
    aderencia: int = 0                   # 0-100
    tenho: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    destaques: list[str] = Field(default_factory=list)
    plano_gaps: list[PlanoGap] = Field(default_factory=list)  # ação por gap relevante
    veredito: str | None = None       # vale o esforço? (1 frase)


class VagaResponse(BaseModel):
    id: str
    titulo: str
    empresa: str | None = None
    link: str | None = None
    fonte: str | None = None
    contato_nome: str | None = None
    contato_email: str | None = None
    localizacao: str | None = None
    modelo: str | None = None
    senioridade: str | None = None
    descricao: str
    notas: str | None = None
    status: str
    analise_json: AnaliseVaga | None = None
    match_json: MatchVaga | None = None
    match_score: int | None = None
    curriculo: CurriculoVaga | None = None      # currículo ATS salvo
    curriculo_gerado_em: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class VagaListItem(BaseModel):
    id: str
    titulo: str
    empresa: str | None = None
    status: str
    modelo: str | None = None
    senioridade: str | None = None
    match_score: int | None = None
    tem_analise: bool = False
    tem_curriculo: bool = False
    qtd_rascunhos: int = 0
    created_at: str | None = None


class VagaListResponse(BaseModel):
    items: list[VagaListItem]
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
    taxa_resposta: int | None = None
    taxa_entrevista: int | None = None
    # Match médio (0-100) de todas com score e só das que viraram candidatura.
    match_medio: int | None = None
    match_medio_candidaturas: int | None = None


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
    para_estudar: list[SkillEstudo] = Field(default_factory=list)   # demandadas que você NÃO tem
    pontos_fortes: list[SkillEstudo] = Field(default_factory=list)  # demandadas que você JÁ tem (destacar no CV)


# ══════════════════════════════════════════════════════════════════
# Candidatura (Fase 4 — gera rascunho, PARA antes de enviar)
# ══════════════════════════════════════════════════════════════════

class EmailCandidatura(BaseModel):
    assunto: str | None = None
    corpo: str
    tom: str | None = None


class CartaCandidatura(BaseModel):
    corpo: str
    tom: str | None = None


class GerarCandidaturaRequest(BaseModel):
    gerar_carta: bool = Field(True, description="Gera também carta de apresentação")
    instrucoes_extra: str | None = Field(
        None, description="Ajustes pontuais de tom/ângulo pra esta candidatura"
    )


class GerarCandidaturaResponse(BaseModel):
    success: bool = True
    email: EmailCandidatura
    variantes_email: list[EmailCandidatura] = Field(default_factory=list)
    carta: CartaCandidatura | None = None
    rascunho_id: str | None = None    # id do CandidaturaEmail salvo (email principal)


class CandidaturaEmailItem(BaseModel):
    id: str
    vaga_id: str
    tipo: str
    destinatario: str | None = None
    assunto: str | None = None
    corpo: str
    tom: str | None = None
    status: str
    variantes: list[EmailCandidatura] = Field(default_factory=list)  # A/B salvas
    created_at: str | None = None


class RascunhoUpdate(BaseModel):
    """Edição manual de um rascunho (e-mail/carta) antes de baixar/enviar."""
    assunto: str | None = None
    corpo: str | None = None
    tom: str | None = None


# ══════════════════════════════════════════════════════════════════
# Currículo sob medida pra vaga (gera PDF no front)
# ══════════════════════════════════════════════════════════════════

class CurriculoExperiencia(BaseModel):
    cargo: str | None = None
    empresa: str | None = None
    periodo: str | None = None
    bullets: list[str] = Field(default_factory=list)  # realizações adaptadas


class CompetenciaGrupo(BaseModel):
    categoria: str                       # ex: "Linguagens", "Frameworks", "Backend"
    itens: list[str] = Field(default_factory=list)


class CurriculoProjeto(BaseModel):
    nome: str                            # nome EXATO do projeto no perfil
    descricao: str | None = None      # adaptada à vaga
    stack: list[str] = Field(default_factory=list)
    link: str | None = None


class CurriculoVaga(BaseModel):
    nome: str                             # factual (injetado do perfil)
    titulo: str | None = None          # headline adaptada à vaga
    contato: ContatoPessoal | None = None  # factual (injetado do perfil)
    resumo: str | None = None          # SOBRE: 2-4 frases adaptadas à vaga
    competencias: list[CompetenciaGrupo] = Field(default_factory=list)  # agrupadas
    experiencias: list[CurriculoExperiencia] = Field(default_factory=list)
    projetos: list[CurriculoProjeto] = Field(default_factory=list)
    formacao: list[Formacao] = Field(default_factory=list)  # factual (injetado)


class GerarCurriculoResponse(BaseModel):
    vaga_id: str
    curriculo: CurriculoVaga
    gerado_em: str | None = None


# VagaResponse referencia CurriculoVaga (definido acima); resolve o forward ref.
VagaResponse.model_rebuild()
