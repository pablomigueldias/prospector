from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Socio(BaseModel):
    nome: str
    qualificacao: Optional[str] = None


class Empresa(BaseModel):
    nome: str
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None

    cidade: Optional[str] = None
    estado: Optional[str] = None
    local: Optional[str] = None

    site: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None

    capital_social: Optional[float] = None
    setor: Optional[str] = None
    tamanho: Optional[str] = None
    score: Optional[int] = None
    analise_json: Optional[dict] = None

    socios: List[Socio] = Field(default_factory=list)

    notas: Optional[str] = None

    como_conheceu: str = "Outbound"
    status: str = "🔵 Prospect"
    coletado_em: datetime = Field(default_factory=datetime.now)
    notion_page_id: Optional[str] = None


class Contato(BaseModel):
    nome: str
    cargo: Optional[str] = None
    decisor: bool = True

    email: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None

    empresa_notion_id: Optional[str] = None
    origem_contato: str = "Network"

    coletado_em: datetime = Field(default_factory=datetime.now)
    notion_page_id: Optional[str] = None

class Lead(BaseModel):
   
    empresa: Empresa
    contatos: List[Contato] = Field(default_factory=list)