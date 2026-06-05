"""Schemas da área pessoal — Perfil Mestre, Vagas e Candidatura.

Isolado dos schemas da Reative (prospector/copywriter/outreach).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


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


class AnaliseVaga(BaseModel):
    requisitos_obrigatorios: List[str] = Field(default_factory=list)
    desejaveis: List[str] = Field(default_factory=list)
    stack: List[str] = Field(default_factory=list)
    senioridade: Optional[str] = None
    palavras_chave: List[str] = Field(default_factory=list)
    resumo: Optional[str] = None


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
