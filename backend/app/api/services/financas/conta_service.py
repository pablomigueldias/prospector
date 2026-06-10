"""Service de Contas — CRUD de 'onde o dinheiro mora'.

Validação de negócio aqui (vira HTTP 400/404 no router); acesso a dados no
ContaRepository.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.api.schemas.financas import (
    ContaCreate,
    ContaListResponse,
    ContaResponse,
    ContaUpdate,
)
from app.db.models.financas.conta import TIPOS_CONTA, Conta
from app.db.session import get_session
from app.repositories.financas.conta_repository import ContaRepository


class ContaError(Exception):
    """Erro de negócio de Contas — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise ContaError(f"{campo} inválido: {valor!r}")


def _valida_tipo(tipo: str) -> None:
    if tipo not in TIPOS_CONTA:
        raise ContaError(
            f"Tipo de conta inválido: {tipo!r}. "
            f"Use um de: {', '.join(TIPOS_CONTA)}."
        )


def _to_response(c: Conta) -> ContaResponse:
    return ContaResponse(
        id=str(c.id),
        usuario_id=str(c.usuario_id),
        nome=c.nome,
        tipo=c.tipo,
        saldo_atual=c.saldo_atual,
        ativa=c.ativa,
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


async def criar_conta(payload: ContaCreate) -> ContaResponse:
    if not payload.nome.strip():
        raise ContaError("A conta precisa de um nome.")
    _valida_tipo(payload.tipo)

    dados = {
        "usuario_id": _uuid(payload.usuario_id, campo="usuario_id"),
        "nome": payload.nome.strip(),
        "tipo": payload.tipo,
        "saldo_atual": payload.saldo_atual,
    }
    async with get_session() as session:
        conta = await ContaRepository(session).create(dados)
        return _to_response(conta)


async def listar_contas(
    usuario_id: str, *, apenas_ativas: bool = False
) -> ContaListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        contas = await ContaRepository(session).listar(
            uid, apenas_ativas=apenas_ativas
        )
        items = [_to_response(c) for c in contas]
    return ContaListResponse(items=items, total=len(items))


async def get_conta(conta_id: str) -> ContaResponse:
    async with get_session() as session:
        conta = await ContaRepository(session).get(_uuid(conta_id))
        if conta is None:
            raise ContaError("Conta não encontrada.")
        return _to_response(conta)


async def atualizar_conta(conta_id: str, payload: ContaUpdate) -> ContaResponse:
    dados = payload.model_dump(exclude_unset=True)
    if "tipo" in dados and dados["tipo"] is not None:
        _valida_tipo(dados["tipo"])
    if "nome" in dados and dados["nome"] is not None:
        if not dados["nome"].strip():
            raise ContaError("O nome da conta não pode ficar vazio.")
        dados["nome"] = dados["nome"].strip()

    async with get_session() as session:
        conta = await ContaRepository(session).update(_uuid(conta_id), dados)
        if conta is None:
            raise ContaError("Conta não encontrada.")
        return _to_response(conta)


async def deletar_conta(conta_id: str) -> bool:
    async with get_session() as session:
        try:
            ok = await ContaRepository(session).delete(_uuid(conta_id))
        except IntegrityError:
            # Tem transações/pagamentos apontando pra essa conta (FK).
            raise ContaError(
                "Essa conta tem lançamentos. Exclua ou mova as transações "
                "antes de remover a conta (ou inative-a)."
            )
        if not ok:
            raise ContaError("Conta não encontrada.")
        return True
