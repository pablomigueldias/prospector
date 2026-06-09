"""Service do resumo do mês — totais e quebra de despesas por categoria."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.api.schemas.financas import CategoriaResumoItem, ResumoMesResponse
from app.db.session import get_session
from app.repositories.financas.transacao_repository import TransacaoRepository


class ResumoError(Exception):
    """Erro de negócio do resumo — vira HTTP 400 no router."""


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise ResumoError(f"{campo} inválido: {valor!r}")


def _intervalo_mes(ano: int, mes: int) -> tuple[date, date]:
    inicio = date(ano, mes, 1)
    proximo = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, proximo


async def resumo_mes(usuario_id: str, ano: int, mes: int) -> ResumoMesResponse:
    if not 1 <= mes <= 12:
        raise ResumoError(f"Mês inválido: {mes}. Use 1..12.")
    uid = _uuid(usuario_id, campo="usuario_id")
    inicio, proximo = _intervalo_mes(ano, mes)

    async with get_session() as session:
        repo = TransacaoRepository(session)
        totais = await repo.total_por_tipo(uid, inicio, proximo)
        por_cat = await repo.despesas_por_categoria(uid, inicio, proximo)

    receitas = totais.get("receita", Decimal("0"))
    despesas = totais.get("despesa", Decimal("0"))

    return ResumoMesResponse(
        ano=ano,
        mes=mes,
        total_receitas=receitas,
        total_despesas=despesas,
        saldo=receitas - despesas,
        por_categoria=[
            CategoriaResumoItem(
                categoria_id=str(cid) if cid else None,
                categoria_nome=nome or "Sem categoria",
                total=total,
            )
            for cid, nome, total in por_cat
        ],
    )
