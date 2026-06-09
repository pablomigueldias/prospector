"""Schemas (Pydantic) do módulo auth."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email do usuário")
    senha: str = Field(..., description="Senha em texto (vai por HTTPS)")


class UsuarioResponse(BaseModel):
    id: str
    email: str
    nome: str
    ativo: bool
    twofa_ativado: bool
    ultimo_login: Optional[str] = None
    # Preenchido quando o RBAC entrar (Step A5). Por ora vem vazio.
    permissoes: List[str] = Field(default_factory=list)


class MensagemResponse(BaseModel):
    ok: bool = True
    mensagem: str = ""
