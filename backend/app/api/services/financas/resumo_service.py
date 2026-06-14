"""Service do resumo do mês — totais e quebra de despesas por categoria."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.api.schemas.financas import (
    CategoriaResumoItem,
    RelatorioMesItem,
    RelatorioResponse,
    ResumoMesResponse,
)
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


def _passo_meses(ano: int, mes: int, delta: int) -> tuple[int, int]:
    """Soma ``delta`` meses a (ano, mes), tratando virada de ano. delta pode
    ser negativo."""
    indice = (ano * 12 + (mes - 1)) + delta
    return indice // 12, indice % 12 + 1


async def relatorio(
    usuario_id: str,
    ano: int,
    mes: int,
    meses: int = 6,
    *,
    conta_id: str | None = None,
    categoria_id: str | None = None,
) -> RelatorioResponse:
    """Série dos últimos ``meses`` (terminando em ano/mes): receita/despesa/saldo
    por mês, top categorias do período e totais consolidados. Meses sem
    lançamento entram zerados pra a série não ter buracos. Aceita recorte
    opcional por conta (ex.: "só Nubank") ou categoria (ex.: "só Mercado")."""
    if not 1 <= mes <= 12:
        raise ResumoError(f"Mês inválido: {mes}. Use 1..12.")
    meses = max(1, min(int(meses), 24))
    uid = _uuid(usuario_id, campo="usuario_id")
    cid = _uuid(conta_id, campo="conta_id") if conta_id else None
    catid = _uuid(categoria_id, campo="categoria_id") if categoria_id else None

    # Janela [inicio, proximo): do 1º dia do mês mais antigo até o 1º do mês
    # seguinte ao âncora.
    ano_ini, mes_ini = _passo_meses(ano, mes, -(meses - 1))
    inicio = date(ano_ini, mes_ini, 1)
    ano_fim, mes_fim = _passo_meses(ano, mes, 1)
    proximo = date(ano_fim, mes_fim, 1)

    async with get_session() as session:
        repo = TransacaoRepository(session)
        linhas = await repo.totais_por_mes(
            uid, inicio, proximo, conta_id=cid, categoria_id=catid
        )
        por_cat = await repo.despesas_por_categoria(
            uid, inicio, proximo, conta_id=cid, categoria_id=catid
        )

    # Indexa (ano, mes) → {receita, despesa}.
    por_mes: dict[tuple[int, int], dict[str, Decimal]] = {}
    for a, m, tipo, total in linhas:
        por_mes.setdefault((a, m), {})[tipo] = total

    itens: list[RelatorioMesItem] = []
    total_receitas = Decimal("0")
    total_despesas = Decimal("0")
    for i in range(meses):
        a, m = _passo_meses(ano_ini, mes_ini, i)
        dados = por_mes.get((a, m), {})
        rec = dados.get("receita", Decimal("0"))
        desp = dados.get("despesa", Decimal("0"))
        total_receitas += rec
        total_despesas += desp
        itens.append(
            RelatorioMesItem(
                ano=a, mes=m,
                total_receitas=rec, total_despesas=desp, saldo=rec - desp,
            )
        )

    media = (total_despesas / meses) if meses else Decimal("0")

    return RelatorioResponse(
        meses=itens,
        por_categoria=[
            CategoriaResumoItem(
                categoria_id=str(cid) if cid else None,
                categoria_nome=nome or "Sem categoria",
                total=total,
            )
            for cid, nome, total in por_cat
        ],
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo=total_receitas - total_despesas,
        media_despesas=media,
    )
