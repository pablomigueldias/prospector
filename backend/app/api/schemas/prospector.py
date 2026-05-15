from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ProspectorManualRequest(BaseModel):

    cnpj: str = Field(..., description="CNPJ com ou sem máscara")
    site: Optional[str] = Field(None, description="URL do site (opcional)")

    instagram: Optional[str] = Field(None, description="@handle ou URL")
    facebook: Optional[str] = Field(None, description="handle ou URL")
    linkedin: Optional[str] = Field(
        None, description="LinkedIn do decisor (pessoa, não empresa)"
    )
    email: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None

    @field_validator("cnpj")
    @classmethod
    def _cnpj_so_digitos_validos(cls, v: str) -> str:
        if not v:
            raise ValueError("CNPJ é obrigatório")
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 14:
            raise ValueError(
                f"CNPJ deve ter 14 dígitos, veio com {len(digits)}"
            )
        return digits

    @field_validator("site")
    @classmethod
    def _site_opcional_mas_se_vier_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^(https?://)?[\w\-.]+\.[a-z]{2,}", v, re.IGNORECASE):
            raise ValueError(f"URL inválida: {v!r}")
        return v



class ContatoOut(BaseModel):
    nome: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None
    decisor: bool = False


class EmpresaOut(BaseModel):
    nome: Optional[str] = None
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    setor: Optional[str] = None
    tamanho: Optional[str] = None
    capital_social: Optional[float] = None
    site: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    notas: Optional[str] = None
    notion_page_id: Optional[str] = None


class LeadOut(BaseModel):
    empresa: EmpresaOut
    contatos: List[ContatoOut] = Field(default_factory=list)


class ProspectorPreviewResponse(BaseModel):

    success: bool = True
    fonte_cnpj: Optional[str] = Field(
        None, description="Qual fonte resolveu o CNPJ: 'brasilapi' ou 'opencnpj'"
    )
    lead: LeadOut


class ProspectorRunResponse(BaseModel):

    success: bool = True
    fonte_cnpj: Optional[str] = None
    lead: LeadOut
    notion_empresa_id: Optional[str] = None
    notion_contatos_ids: List[str] = Field(default_factory=list)


class LeadHistoryItem(BaseModel):

    empresa_nome: str
    cnpj: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    setor: Optional[str] = None
    qtd_contatos: int = 0
    notion_empresa_id: Optional[str] = None
    enviado_em: Optional[str] = Field(
        None, description="ISO 8601 — extraído do nome do arquivo"
    )
    arquivo: str = Field(..., description="Nome do arquivo de backup local")


class LeadHistoryResponse(BaseModel):
    items: List[LeadHistoryItem]
    total: int


class ApiError(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
