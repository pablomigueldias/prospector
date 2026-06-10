"""Segundo fator TOTP (D15–D17).

Fluxo:
1. ``gerar_setup`` cria um secret (cifrado, ainda **pendente**) e devolve a
   ``otpauth://`` URI + QR (PNG base64) pra plotar no app autenticador.
2. ``confirmar_ativacao`` valida o 1º código, marca ativo, gera 10 backup codes
   (devolvidos UMA vez; no banco só o hash, de uso único).
3. No login, ``validar_codigo`` aceita o TOTP atual OU consome um backup code.
4. ``desativar`` apaga os segredos.

O secret TOTP vai cifrado com Fernet (chave ``TOTP_ENC_KEY`` no ``.env``) — se
o banco vazar, sem a chave não dá pra gerar códigos. Backup codes são de alta
entropia, então sha256 (rápido) basta; senhas de usuário é que pedem Argon2.
"""
from __future__ import annotations

import base64
import hashlib
import io
import secrets
from typing import List, Optional

import pyotp
import qrcode
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.services.auth.sessao_service import _agora
from app.config import settings
from app.db.models.auth.usuario import Usuario
from app.db.models.auth.usuario_2fa import UsuarioTwoFA

ISSUER = "Reative"
N_BACKUP_CODES = 10


class TwoFAError(Exception):
    """Erro de configuração/estado do 2FA (vira HTTP 400)."""


# ── cifragem do secret ─────────────────────────────────────────────
def _fernet() -> Fernet:
    chave = (settings.totp_enc_key or "").strip()
    if not chave:
        raise TwoFAError("2FA indisponível: configure TOTP_ENC_KEY no servidor.")
    try:
        return Fernet(chave.encode())
    except (ValueError, TypeError) as e:
        raise TwoFAError("TOTP_ENC_KEY inválida (gere com Fernet.generate_key()).") from e


def _cifrar(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def _decifrar(cifrado: str) -> str:
    try:
        return _fernet().decrypt(cifrado.encode()).decode()
    except InvalidToken as e:
        raise TwoFAError("Segredo 2FA corrompido (chave trocada?).") from e


# ── backup codes ───────────────────────────────────────────────────
def _normalizar_backup(codigo: str) -> str:
    return (codigo or "").strip().upper().replace("-", "").replace(" ", "")


def _hash_backup(codigo: str) -> str:
    return hashlib.sha256(_normalizar_backup(codigo).encode()).hexdigest()


def _gerar_backup_codes() -> List[str]:
    """10 códigos no formato XXXX-XXXX (base32 sem caracteres ambíguos)."""
    alfabeto = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem I,O,0,1
    codes = []
    for _ in range(N_BACKUP_CODES):
        bruto = "".join(secrets.choice(alfabeto) for _ in range(8))
        codes.append(f"{bruto[:4]}-{bruto[4:]}")
    return codes


# ── QR ─────────────────────────────────────────────────────────────
def _qr_data_uri(otpauth_uri: str) -> str:
    img = qrcode.make(otpauth_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


# ── operações ──────────────────────────────────────────────────────
async def gerar_setup(session: AsyncSession, usuario: Usuario) -> dict:
    """Cria/renova o secret (pendente) e devolve URI + QR pra confirmar.

    Recusa se o 2FA já estiver ativo (desative antes pra re-chavear).
    """
    if usuario.twofa_ativado:
        raise TwoFAError("2FA já está ativo. Desative antes de gerar um novo.")

    secret = pyotp.random_base32()
    row = await session.get(UsuarioTwoFA, usuario.id)
    if row is None:
        row = UsuarioTwoFA(usuario_id=usuario.id)
        session.add(row)
    row.totp_secret_cifrado = _cifrar(secret)
    row.backup_codes_hash = []
    row.ativado_em = None
    await session.flush()

    otpauth = pyotp.TOTP(secret).provisioning_uri(name=usuario.email, issuer_name=ISSUER)
    return {"secret": secret, "otpauth_uri": otpauth, "qr_data_uri": _qr_data_uri(otpauth)}


async def confirmar_ativacao(
    session: AsyncSession, usuario: Usuario, codigo: str
) -> List[str]:
    """Valida o 1º código TOTP, ativa o 2FA e devolve os backup codes (uma vez)."""
    row = await session.get(UsuarioTwoFA, usuario.id)
    if row is None or usuario.twofa_ativado:
        raise TwoFAError("Nenhum setup de 2FA pendente. Comece pelo /setup.")
    secret = _decifrar(row.totp_secret_cifrado)
    if not pyotp.TOTP(secret).verify((codigo or "").strip(), valid_window=1):
        raise TwoFAError("Código inválido. Confira o relógio do app autenticador.")

    codes = _gerar_backup_codes()
    row.backup_codes_hash = [_hash_backup(c) for c in codes]
    row.ativado_em = _agora()
    usuario.twofa_ativado = True
    await session.flush()
    return codes


async def validar_codigo(
    session: AsyncSession, usuario_id, codigo: str
) -> bool:
    """No login: aceita o TOTP atual OU consome um backup code (uso único)."""
    codigo = (codigo or "").strip()
    if not codigo:
        return False
    row = await session.get(UsuarioTwoFA, usuario_id)
    if row is None or row.ativado_em is None:
        return False

    secret = _decifrar(row.totp_secret_cifrado)
    if pyotp.TOTP(secret).verify(codigo, valid_window=1):
        return True

    # backup code? consome (remove do array) se bater.
    alvo = _hash_backup(codigo)
    if alvo in (row.backup_codes_hash or []):
        row.backup_codes_hash = [h for h in row.backup_codes_hash if h != alvo]
        await session.flush()
        return True
    return False


async def desativar(session: AsyncSession, usuario: Usuario) -> None:
    """Apaga os segredos e desliga o 2FA do usuário."""
    row = await session.get(UsuarioTwoFA, usuario.id)
    if row is not None:
        await session.delete(row)
    usuario.twofa_ativado = False
    await session.flush()


def backup_codes_restantes(row: Optional[UsuarioTwoFA]) -> int:
    return len(row.backup_codes_hash) if row and row.backup_codes_hash else 0
