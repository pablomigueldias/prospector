from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class ProspectorManualRequest(BaseModel):

    cnpj: str = Field(..., description="CNPJ com ou sem máscara")
    site: str | None = Field(None, description="URL do site (opcional)")

    instagram: str | None = Field(None, description="@handle ou URL")
    facebook: str | None = Field(None, description="handle ou URL")
    linkedin: str | None = Field(
        None, description="LinkedIn do decisor (pessoa, não empresa)"
    )
    email: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None

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
    def _site_opcional_mas_se_vier_valido(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^(https?://)?[\w\-.]+\.[a-z]{2,}", v, re.IGNORECASE):
            raise ValueError(f"URL inválida: {v!r}")
        return v



class ContatoOut(BaseModel):
    nome: str | None = None
    cargo: str | None = None
    email: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None
    linkedin: str | None = None
    decisor: bool = False


class EmpresaOut(BaseModel):
    nome: str | None = None
    razao_social: str | None = None
    cnpj: str | None = None
    cidade: str | None = None
    estado: str | None = None
    setor: str | None = None
    tamanho: str | None = None
    capital_social: float | None = None
    site: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    notas: str | None = None
    notion_page_id: str | None = None


class LeadOut(BaseModel):
    empresa: EmpresaOut
    contatos: list[ContatoOut] = Field(default_factory=list)


class ProspectorPreviewResponse(BaseModel):

    success: bool = True
    fonte_cnpj: str | None = Field(
        None, description="Qual fonte resolveu o CNPJ: 'brasilapi' ou 'opencnpj'"
    )
    lead: LeadOut


class ProspectorRunResponse(BaseModel):

    success: bool = True
    fonte_cnpj: str | None = None
    lead: LeadOut
    notion_empresa_id: str | None = None
    notion_contatos_ids: list[str] = Field(default_factory=list)


class LeadHistoryItem(BaseModel):

    empresa_nome: str
    cnpj: str | None = None
    cidade: str | None = None
    estado: str | None = None
    setor: str | None = None
    qtd_contatos: int = 0
    notion_empresa_id: str | None = None
    enviado_em: str | None = Field(
        None, description="ISO 8601 — extraído do nome do arquivo"
    )
    arquivo: str = Field(..., description="Nome do arquivo de backup local")


class LeadHistoryResponse(BaseModel):
    items: list[LeadHistoryItem]
    total: int


class ApiError(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None
