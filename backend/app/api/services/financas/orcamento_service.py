"""Service de Orçamentos — teto mensal de despesa por categoria.

O consumido do mês não é guardado: vem das transações (mesma soma do resumo,
via ``despesas_por_categoria``). Match é por categoria exata (sem roll-up de
subcategorias por ora)."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import select

from app.api.schemas.financas import (
    OrcamentoCreate,
    OrcamentoListResponse,
    OrcamentoResponse,
    OrcamentoStatusItem,
    OrcamentoStatusResponse,
    OrcamentoUpdate,
)
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.orcamento import Orcamento
from app.db.session import get_session
from app.repositories.financas.categoria_repository import CategoriaRepository
from app.repositories.financas.transacao_repository import TransacaoRepository


class OrcamentoError(Exception):
    """Erro de negócio de Orçamentos — vira HTTP 400/404 no router."""


from app.api.services.financas._common import iso as _iso


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise OrcamentoError(f"{campo} inválido: {valor!r}")


def _parse_competencia(s: Optional[str]) -> Tuple[int, int]:
    if not s:
        hoje = date.today()
        return hoje.year, hoje.month
    try:
        ano, mes = s.split("-")
        ano, mes = int(ano), int(mes)
        if not (1 <= mes <= 12):
            raise ValueError
        return ano, mes
    except (ValueError, AttributeError):
        raise OrcamentoError(f"Competência inválida: {s!r} (use YYYY-MM).")


def _to_response(o: Orcamento, nome: Optional[str] = None) -> OrcamentoResponse:
    return OrcamentoResponse(
        id=str(o.id),
        usuario_id=str(o.usuario_id),
        categoria_id=str(o.categoria_id),
        categoria_nome=nome,
        valor_mensal=o.valor_mensal,
        ativo=o.ativo,
        created_at=_iso(o.created_at),
        updated_at=_iso(o.updated_at),
    )


async def criar_orcamento(payload: OrcamentoCreate) -> OrcamentoResponse:
    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    categoria_id = _uuid(payload.categoria_id, campo="categoria_id")
    async with get_session() as session:
        cat = await session.get(Categoria, categoria_id)
        if cat is None:
            raise OrcamentoError("Categoria não encontrada.")
        existe = await session.scalar(
            select(Orcamento).where(
                Orcamento.usuario_id == usuario_id,
                Orcamento.categoria_id == categoria_id,
            )
        )
        if existe is not None:
            raise OrcamentoError("Já existe um orçamento pra essa categoria.")
        orc = Orcamento(
            usuario_id=usuario_id,
            categoria_id=categoria_id,
            valor_mensal=payload.valor_mensal,
        )
        session.add(orc)
        await session.commit()
        await session.refresh(orc)
        return _to_response(orc, cat.nome)


async def atualizar_orcamento(
    orcamento_id: str, payload: OrcamentoUpdate
) -> OrcamentoResponse:
    dados = payload.model_dump(exclude_unset=True)
    async with get_session() as session:
        orc = await session.get(Orcamento, _uuid(orcamento_id))
        if orc is None:
            raise OrcamentoError("Orçamento não encontrado.")
        for campo, valor in dados.items():
            setattr(orc, campo, valor)
        await session.commit()
        await session.refresh(orc)
        cat = await session.get(Categoria, orc.categoria_id)
        return _to_response(orc, cat.nome if cat else None)


async def excluir_orcamento(orcamento_id: str) -> None:
    async with get_session() as session:
        orc = await session.get(Orcamento, _uuid(orcamento_id))
        if orc is None:
            raise OrcamentoError("Orçamento não encontrado.")
        await session.delete(orc)
        await session.commit()


async def listar_orcamentos(usuario_id: str) -> OrcamentoListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        stmt = (
            select(Orcamento, Categoria.nome)
            .outerjoin(Categoria, Categoria.id == Orcamento.categoria_id)
            .where(Orcamento.usuario_id == uid)
            .order_by(Categoria.nome)
        )
        rows = (await session.execute(stmt)).all()
        items = [_to_response(o, nome) for o, nome in rows]
    return OrcamentoListResponse(items=items, total=len(items))


async def status_do_mes(
    usuario_id: str, competencia: Optional[str] = None
) -> OrcamentoStatusResponse:
    """Por orçamento ativo, quanto já foi consumido no mês (das despesas da
    categoria) + restante e percentual."""
    uid = _uuid(usuario_id, campo="usuario_id")
    ano, mes = _parse_competencia(competencia)
    inicio = date(ano, mes, 1)
    proximo = date(ano + (mes // 12), (mes % 12) + 1, 1)

    async with get_session() as session:
        orcs = (await session.execute(
            select(Orcamento, Categoria.nome)
            .outerjoin(Categoria, Categoria.id == Orcamento.categoria_id)
            .where(Orcamento.usuario_id == uid, Orcamento.ativo.is_(True))
            .order_by(Categoria.nome)
        )).all()

        repo = TransacaoRepository(session)
        por_cat = await repo.despesas_por_categoria(uid, inicio, proximo)
        consumo = {cid: total for cid, _, total in por_cat if cid is not None}

        # Roll-up: o teto da categoria-mãe soma os gastos das subcategorias.
        todas = await CategoriaRepository(session).listar_todas()
        filhos: dict = {}
        for c in todas:
            if c.categoria_pai_id:
                filhos.setdefault(c.categoria_pai_id, []).append(c.id)

        def _gasto_com_descendentes(raiz) -> Decimal:
            total = Decimal(consumo.get(raiz, Decimal("0")))
            pilha = list(filhos.get(raiz, []))
            while pilha:
                n = pilha.pop()
                total += Decimal(consumo.get(n, Decimal("0")))
                pilha.extend(filhos.get(n, []))
            return total

        items = []
        total_orcado = Decimal("0")
        total_consumido = Decimal("0")
        for o, nome in orcs:
            gasto = _gasto_com_descendentes(o.categoria_id)
            orcado = Decimal(o.valor_mensal)
            total_orcado += orcado
            total_consumido += gasto
            pct = float(gasto / orcado * 100) if orcado > 0 else 0.0
            items.append(OrcamentoStatusItem(
                orcamento_id=str(o.id),
                categoria_id=str(o.categoria_id),
                categoria_nome=nome,
                valor_mensal=orcado,
                consumido=gasto,
                restante=orcado - gasto,
                percentual=round(pct, 1),
            ))

    return OrcamentoStatusResponse(
        competencia=f"{ano:04d}-{mes:02d}",
        items=items,
        total_orcado=total_orcado,
        total_consumido=total_consumido,
    )
