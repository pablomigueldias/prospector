"""Schemas do agente LinkedIn (P5 §6.C).

DTOs em snake_case (convenção da API). Um só modelo serve às duas contas
(Página da Reative e perfil pessoal do Pablo) via `conta`. *Para no rascunho*:
o agente preenche; o Pablo revisa e copia/cola no LinkedIn.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LinkedinPostBase(BaseModel):
    titulo: str | None = None
    conta: str | None = None       # reative | pessoal
    formato: str | None = None     # post | carrossel | artigo
    hook: str | None = None
    body: str | None = None
    cta: str | None = None
    hashtags: list[str] | None = None
    fonte: str | None = None
    notas: str | None = None
    scheduled_for: datetime | None = None


class LinkedinPostCreate(LinkedinPostBase):
    pass


class LinkedinPostUpdate(LinkedinPostBase):
    """Patch parcial — `None` não mexe no campo. `published_at` editável aqui
    pra o Pablo registrar quando postou na mão."""

    published_at: datetime | None = None


class LinkedinImagem(BaseModel):
    url: str
    alt: str | None = None
    prompt: str | None = None
    origem: str = "ia"  # ia | upload


class MidiaSugestao(BaseModel):
    """Direção de arte do post (o agente agindo como social media pro)."""

    recomendacao: str = "imagem_ia"  # imagem_ia|foto|carrossel|video_reel|screenshot|grafico|sem_midia
    justificativa: str | None = None     # por que esse formato pra este post
    passos: list[str] = Field(default_factory=list)   # roteiro passo a passo de produção
    dicas: list[str] = Field(default_factory=list)    # dicas de composição/copy visual
    prompt_imagem: str | None = None     # prompt EN pronto pra gerar imagem por IA
    alt: str | None = None               # alt em PT da imagem sugerida
    aspect_ratio: str = "1:1"            # 1:1 | 4:5 | 16:9 (LinkedIn favorece 1:1 / 4:5)


class LinkedinPostOut(BaseModel):
    """Visão completa pro studio."""

    id: str
    titulo: str | None = None
    conta: str
    formato: str
    hook: str | None = None
    body: str | None = None
    cta: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    status: str
    fonte: str
    origem_blog_post_id: str | None = None
    scheduled_for: str | None = None
    published_at: str | None = None
    midia: MidiaSugestao | None = None
    imagens: list[LinkedinImagem] = Field(default_factory=list)
    char_count: int | None = None
    notas: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LinkedinStatusUpdate(BaseModel):
    status: str  # rascunho | aprovado | publicado | arquivado


# ══════════════════════════════════════════════════════════════════
# Agente (L1) — redator (brief → post)
# ══════════════════════════════════════════════════════════════════

class LinkedinBriefRequest(BaseModel):
    tema: str
    conta: str | None = None       # reative | pessoal (muda o tom/voz)
    formato: str | None = None     # post | carrossel | artigo
    publico: str | None = None     # recrutador | cliente
    angulo: str | None = None      # ângulo/pontos que o post deve cobrir
    tom: str | None = None


class LinkedinRedacao(BaseModel):
    """Saída do redator — preenche o drawer pro Pablo revisar (checkpoint)."""

    titulo: str | None = None      # rótulo interno (organização)
    hook: str
    body: str
    cta: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    # Recursos/ofertas que o texto menciona mas que talvez não existam — pro
    # Pablo criar ou remover (anti-mentira).
    pendencias: list[str] = Field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# Coordenador (L2) — gera rascunhos prontos autonomamente
# ══════════════════════════════════════════════════════════════════

class LinkedinGerarRequest(BaseModel):
    fonte: str = "tendencia"       # projeto | tendencia
    quantidade: int = 3
    conta: str | None = None       # reative | pessoal (default: reative)
    publico: str | None = None     # recrutador | cliente


# ══════════════════════════════════════════════════════════════════
# Direção de arte (L5) — sugerir mídia + gerar imagem por IA
# ══════════════════════════════════════════════════════════════════

class GerarImagemLinkedinRequest(BaseModel):
    # Sem prompt → usa o `prompt_imagem` da sugestão de mídia salva no post.
    prompt: str | None = None
    alt: str | None = None
    aspect_ratio: str = "1:1"
