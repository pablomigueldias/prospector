"""Cadastro: plataformas e clientes (CRM)."""
from __future__ import annotations

from typing import List

from app.api.schemas.freela import (
    ClienteCreate,
    ClienteResponse,
    ClienteUpdate,
    PlataformaResponse,
)
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import FreelaError, _cliente_to_resp, _uuid, _uuid_opt

# ══════════════════════════════════════════════════════════════════
# Plataforma
# ══════════════════════════════════════════════════════════════════

async def listar_plataformas() -> List[PlataformaResponse]:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_plataformas()
        return [
            PlataformaResponse(
                id=str(p.id),
                nome=p.nome,
                url_base=p.url_base,
                config_comissao=p.config_comissao,
                lance_minimo_padrao=float(p.lance_minimo_padrao) if p.lance_minimo_padrao is not None else None,
            )
            for p in linhas
        ]


# ══════════════════════════════════════════════════════════════════
# Cliente
# ══════════════════════════════════════════════════════════════════

async def criar_cliente(payload: ClienteCreate) -> ClienteResponse:
    if not payload.nome.strip():
        raise FreelaError("O cliente precisa de um nome.")
    dados = payload.model_dump()
    dados["plataforma_id"] = _uuid_opt(dados.get("plataforma_id"), "plataforma_id")
    async with get_session() as session:
        cliente = await FreelaRepository(session).create_cliente(dados)
        return _cliente_to_resp(cliente)


async def listar_clientes() -> List[ClienteResponse]:
    async with get_session() as session:
        return [_cliente_to_resp(c) for c in await FreelaRepository(session).listar_clientes()]


async def get_cliente(cliente_id: str) -> ClienteResponse:
    async with get_session() as session:
        cliente = await FreelaRepository(session).get_cliente(_uuid(cliente_id))
        if cliente is None:
            raise FreelaError("Cliente não encontrado.")
        return _cliente_to_resp(cliente)


async def atualizar_cliente(cliente_id: str, payload: ClienteUpdate) -> ClienteResponse:
    dados = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if "plataforma_id" in dados:
        dados["plataforma_id"] = _uuid_opt(dados["plataforma_id"], "plataforma_id")
    async with get_session() as session:
        cliente = await FreelaRepository(session).update_cliente(_uuid(cliente_id), dados)
        if cliente is None:
            raise FreelaError("Cliente não encontrado.")
        return _cliente_to_resp(cliente)


async def deletar_cliente(cliente_id: str) -> None:
    async with get_session() as session:
        ok = await FreelaRepository(session).delete_cliente(_uuid(cliente_id))
        if not ok:
            raise FreelaError("Cliente não encontrado.")
