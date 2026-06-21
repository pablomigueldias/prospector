from __future__ import annotations

from pydantic import BaseModel, Field


class CopywriterRequest(BaseModel):
    """Entrada para gerar um e-mail. Todos os campos do seu prompt."""
    empresa: str = Field(..., description="Nome da empresa alvo")
    segmento: str | None = Field(default=None, description="Nicho/setor")
    nome_contato: str | None = Field(default=None, description="Nome do decisor")
    cargo: str | None = Field(default=None, description="Cargo do contato")
    canal: str = Field(
        "email",
        description="Canal de envio: email | whatsapp",
    )
    tipo: str = Field(
        "prospeccao",
        description="prospeccao | vaga | parceria | freelancer",
    )
    necessidade: str | None = Field(None, description="Dor identificada")
    servico: str | None = Field(
        None, description="O que está sendo ofertado")
    diferenciais: str | None = Field(
        None, description="Diferenciais da Reative")
    contexto_extra: str | None = Field(
        None,
        description="Texto livre — ex: descrição de vaga colada de um site de freelancer",
    )
    # Permite gerar a partir de um lead já existente no histórico
    lead_arquivo: str | None = Field(
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
    variantes: list[EmailGerado] = Field(
        default_factory=list,
        description="Versões alternativas (A/B) do mesmo e-mail",
    )
