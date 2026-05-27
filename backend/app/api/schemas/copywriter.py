from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class CopywriterRequest(BaseModel):
    """Entrada para gerar um e-mail. Todos os campos do seu prompt."""
    empresa: str = Field(..., description="Nome da empresa alvo")
    segmento: Optional[str] = Field(None, description="Nicho/setor")
    nome_contato: Optional[str] = Field(None, description="Nome do decisor")
    cargo: Optional[str] = Field(None, description="Cargo do contato")
    canal: str = Field(
        "email",
        description="Canal de envio: email | whatsapp",
    )
    tipo: str = Field(
        "negocio",
        description="prospeccao | vaga | parceria | freelancer",
    )
    necessidade: Optional[str] = Field(None, description="Dor identificada")
    servico: Optional[str] = Field(
        None, description="O que está sendo ofertado")
    diferenciais: Optional[str] = Field(
        None, description="Diferenciais da Reative")
    contexto_extra: Optional[str] = Field(
        None,
        description="Texto livre — ex: descrição de vaga colada de um site de freelancer",
    )
    # Permite gerar a partir de um lead já existente no histórico
    lead_arquivo: Optional[str] = Field(
        None, description="Nome do arquivo em data/sent/ para puxar contexto"
    )


class EmailGerado(BaseModel):
    assunto: str
    corpo: str
    cta: str
    tom: str


class CopywriterResponse(BaseModel):
    success: bool = True
    email: EmailGerado
    variantes: List[EmailGerado] = Field(
        default_factory=list,
        description="Versões alternativas (A/B) do mesmo e-mail",
    )
