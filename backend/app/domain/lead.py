from datetime import datetime

from pydantic import BaseModel, Field


class Socio(BaseModel):
    nome: str
    qualificacao: str | None = None


class Empresa(BaseModel):
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
    analise_json: dict | None = None

    socios: list[Socio] = Field(default_factory=list)

    notas: str | None = None

    como_conheceu: str = "Outbound"
    status: str = "🔵 Prospect"
    coletado_em: datetime = Field(default_factory=datetime.now)
    notion_page_id: str | None = None


class Contato(BaseModel):
    nome: str
    cargo: str | None = None
    decisor: bool = True

    email: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None
    linkedin: str | None = None

    empresa_notion_id: str | None = None
    origem_contato: str = "Network"

    coletado_em: datetime = Field(default_factory=datetime.now)
    notion_page_id: str | None = None

class Lead(BaseModel):

    empresa: Empresa
    contatos: list[Contato] = Field(default_factory=list)
