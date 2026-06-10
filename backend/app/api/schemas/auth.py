"""Schemas (Pydantic) do módulo auth."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email do usuário")
    senha: str = Field(..., description="Senha em texto (vai por HTTPS)")
    codigo_2fa: Optional[str] = Field(
        None, description="Código TOTP ou backup code (2ª etapa, se 2FA ativo)"
    )


class TrocaSenhaRequest(BaseModel):
    senha_atual: str = Field(..., description="Senha atual (confirmação)")
    senha_nova: str = Field(..., description="Nova senha (validada por força)")


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


# ── 2FA (TOTP) ─────────────────────────────────────────────────────
class TwoFASetupResponse(BaseModel):
    secret: str = Field(..., description="Secret base32 (entrada manual no app)")
    otpauth_uri: str = Field(..., description="URI otpauth:// pro app autenticador")
    qr_data_uri: str = Field(..., description="PNG do QR em data: URI (mostrar no <img>)")


class TwoFACodigoRequest(BaseModel):
    codigo: str = Field(..., description="Código TOTP de 6 dígitos do app")


class TwoFAAtivarResponse(BaseModel):
    ok: bool = True
    backup_codes: List[str] = Field(
        ..., description="Códigos de backup — guarde agora; não aparecem de novo"
    )


class TwoFADesativarRequest(BaseModel):
    senha: str = Field(..., description="Senha atual (confirmação)")
    codigo: str = Field(..., description="Código TOTP ou backup code")


# ── Admin de usuários ──────────────────────────────────────────────
class PapelItem(BaseModel):
    nome: str
    descricao: Optional[str] = None


class UsuarioAdminItem(BaseModel):
    id: str
    email: str
    nome: str
    ativo: bool
    twofa_ativado: bool
    papeis: List[str]
    ultimo_login: Optional[str] = None
    created_at: Optional[str] = None


class UsuarioAdminListResponse(BaseModel):
    items: List[UsuarioAdminItem]
    total: int


class UsuarioAdminCreate(BaseModel):
    email: str
    nome: str
    senha: str = Field(..., description="Senha inicial (validada por força)")
    papeis: List[str] = Field(default_factory=lambda: ["padrao"])


class UsuarioAdminUpdate(BaseModel):
    nome: Optional[str] = None
    ativo: Optional[bool] = None
    papeis: Optional[List[str]] = None
