"""Service de Compras parceladas — gera N parcelas a partir de uma compra.

Step 10 cobre o cartão (parcelas caem em faturas mensais). Os helpers de
distribuição e de meses são puros, pra o boleto parcelado (Step 11) reaproveitar.
"""
from __future__ import annotations

import calendar
import uuid
from datetime import date
from decimal import ROUND_DOWN, Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.financas import (
    BoletoParceladoCreate,
    CompraCategoriaSugestao,
    CompraParceladaCreate,
    CompraResponse,
    ParcelaResponse,
)
from app.api.services.financas import eventos
from app.db.models.financas.cartao import Cartao
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.compra import Compra
from app.db.models.financas.fatura import Fatura
from app.db.models.financas.parcela import Parcela
from app.db.session import get_session


class CompraError(Exception):
    """Erro de negócio de Compras — vira HTTP 400/404 no router."""


_CENTAVO = Decimal("0.01")


from app.api.services.financas._common import iso as _iso


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise CompraError(f"{campo} inválido: {valor!r}")


def distribuir(total: Decimal, n: int) -> List[Decimal]:
    """Divide ``total`` em ``n`` partes de centavo certo; a última absorve o
    resto (ex.: 100/3 = 33.33, 33.33, 33.34)."""
    base = (total / n).quantize(_CENTAVO, rounding=ROUND_DOWN)
    valores = [base] * n
    valores[-1] = total - base * (n - 1)
    return valores


def add_meses(ano: int, mes: int, k: int) -> Tuple[int, int]:
    idx = ano * 12 + (mes - 1) + k
    return idx // 12, idx % 12 + 1


def dia_valido(ano: int, mes: int, dia: int) -> int:
    return min(dia, calendar.monthrange(ano, mes)[1])


def competencia_inicial(data_compra: date, dia_fechamento: int) -> Tuple[int, int]:
    """Em qual mês cai a 1ª fatura: se a compra entrou até o fechamento, no
    próprio mês; senão, no mês seguinte."""
    if data_compra.day <= dia_fechamento:
        return data_compra.year, data_compra.month
    return add_meses(data_compra.year, data_compra.month, 1)


def vencimento_fatura(
    ano: int, mes: int, dia_fechamento: int, dia_vencimento: int
) -> date:
    """Data de vencimento da fatura que FECHA em (ano, mes). O vencimento vem
    depois do fechamento: se o dia de vencimento é menor/igual ao de
    fechamento, cai no mês seguinte."""
    if dia_vencimento > dia_fechamento:
        vy, vm = ano, mes
    else:
        vy, vm = add_meses(ano, mes, 1)
    return date(vy, vm, dia_valido(vy, vm, dia_vencimento))


async def _carregar_compra(session: AsyncSession, compra_id: uuid.UUID) -> Optional[Compra]:
    return await session.scalar(
        select(Compra)
        .options(selectinload(Compra.parcelas))
        .where(Compra.id == compra_id)
    )


def _to_response(c: Compra) -> CompraResponse:
    return CompraResponse(
        id=str(c.id),
        usuario_id=str(c.usuario_id),
        cartao_id=str(c.cartao_id) if c.cartao_id else None,
        descricao=c.descricao,
        valor_total=c.valor_total,
        total_parcelas=c.total_parcelas,
        data_compra=c.data_compra,
        origem=c.origem,
        categoria_id=str(c.categoria_id) if c.categoria_id else None,
        parcelas=[
            ParcelaResponse(
                id=str(p.id),
                numero=p.numero,
                total_parcelas=p.total_parcelas,
                valor=p.valor,
                tem_juros=p.tem_juros,
                valor_juros=p.valor_juros,
                vencimento=p.vencimento,
                fatura_id=str(p.fatura_id) if p.fatura_id else None,
            )
            for p in c.parcelas
        ],
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


async def _fatura_do_mes(
    session: AsyncSession, cartao: Cartao, ano: int, mes: int,
    cache: dict[tuple[int, int], Fatura],
) -> Fatura:
    """Get-or-create da fatura do cartão naquele mês (cacheada na chamada)."""
    chave = (ano, mes)
    if chave in cache:
        return cache[chave]
    mes_ref = date(ano, mes, 1)
    fatura = await session.scalar(
        select(Fatura).where(
            Fatura.cartao_id == cartao.id, Fatura.mes_referencia == mes_ref
        )
    )
    if fatura is None:
        fatura = Fatura(
            cartao_id=cartao.id,
            mes_referencia=mes_ref,
            vencimento=vencimento_fatura(
                ano, mes, cartao.dia_fechamento, cartao.dia_vencimento
            ),
            valor_total=Decimal("0"),
        )
        session.add(fatura)
        await session.flush()  # garante fatura.id pra ligar na parcela
    cache[chave] = fatura
    return fatura


async def lancar_avista_na_sessao(
    session: AsyncSession,
    cartao: Cartao,
    *,
    usuario_id: uuid.UUID,
    descricao: str,
    valor: Decimal,
    data_compra: date,
    categoria_id: Optional[uuid.UUID] = None,
    recorrencia_id: Optional[uuid.UUID] = None,
) -> Compra:
    """Lança uma compra à vista (1 parcela) na fatura do mês, dentro da sessão
    dada (não commita). Usado pelo cron e pelo "marcar pago" das recorrências
    de cartão — a despesa só pesa no saldo quando a fatura é paga."""
    compra = Compra(
        usuario_id=usuario_id,
        descricao=descricao,
        valor_total=valor,
        total_parcelas=1,
        data_compra=data_compra,
        origem="cartao",
        cartao_id=cartao.id,
        categoria_id=categoria_id,
        recorrencia_id=recorrencia_id,
    )
    session.add(compra)
    await session.flush()

    ano0, mes0 = competencia_inicial(data_compra, cartao.dia_fechamento)
    fatura = await _fatura_do_mes(session, cartao, ano0, mes0, {})
    session.add(Parcela(
        compra_id=compra.id,
        numero=1,
        total_parcelas=1,
        valor=valor,
        tem_juros=False,
        valor_juros=Decimal("0"),
        vencimento=fatura.vencimento,
        fatura_id=fatura.id,
    ))
    fatura.valor_total = Decimal(fatura.valor_total) + Decimal(valor)
    return compra


async def criar_compra_parcelada(
    payload: CompraParceladaCreate, *, recorrencia_id: Optional[uuid.UUID] = None
) -> CompraResponse:
    if not payload.descricao.strip():
        raise CompraError("A compra precisa de uma descrição.")
    if payload.valor_juros_total > payload.valor_total:
        raise CompraError("O juro não pode ser maior que o total.")

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    cartao_id = _uuid(payload.cartao_id, campo="cartao_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    data_compra = payload.data_compra or date.today()
    n = payload.total_parcelas

    valores = distribuir(payload.valor_total, n)
    juros = distribuir(payload.valor_juros_total, n) if payload.valor_juros_total > 0 \
        else [Decimal("0")] * n

    async with get_session() as session:
        cartao = await session.get(Cartao, cartao_id)
        if cartao is None:
            raise CompraError("Cartão não encontrado.")
        if cartao.usuario_id != usuario_id:
            raise CompraError("O cartão não pertence a esse usuário.")
        if categoria_id is not None and await session.get(Categoria, categoria_id) is None:
            raise CompraError("Categoria não encontrada.")

        compra = Compra(
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            total_parcelas=n,
            data_compra=data_compra,
            origem="cartao",
            cartao_id=cartao_id,
            categoria_id=categoria_id,
            recorrencia_id=recorrencia_id,
        )
        session.add(compra)
        await session.flush()

        ano0, mes0 = competencia_inicial(data_compra, cartao.dia_fechamento)
        cache: dict[tuple[int, int], Fatura] = {}
        for i in range(n):
            ano_i, mes_i = add_meses(ano0, mes0, i)
            fatura = await _fatura_do_mes(session, cartao, ano_i, mes_i, cache)
            parcela = Parcela(
                compra_id=compra.id,
                numero=i + 1,
                total_parcelas=n,
                valor=valores[i],
                tem_juros=juros[i] > 0,
                valor_juros=juros[i],
                vencimento=fatura.vencimento,  # a parcela vence junto com a fatura
                fatura_id=fatura.id,
            )
            session.add(parcela)
            fatura.valor_total = Decimal(fatura.valor_total) + valores[i]

        await session.commit()

        return _to_response(await _carregar_compra(session, compra.id))


async def criar_compra_boleto_parcelada(
    payload: BoletoParceladoCreate,
) -> CompraResponse:
    """Boleto parcelado (sem cartão/fatura): parcelas vencem mês a mês a partir
    de primeiro_vencimento. Mesmo conceito de parcela do cartão."""
    if not payload.descricao.strip():
        raise CompraError("A compra precisa de uma descrição.")
    if payload.valor_juros_total > payload.valor_total:
        raise CompraError("O juro não pode ser maior que o total.")

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    n = payload.total_parcelas
    primeiro = payload.primeiro_vencimento

    valores = distribuir(payload.valor_total, n)
    juros = distribuir(payload.valor_juros_total, n) if payload.valor_juros_total > 0 \
        else [Decimal("0")] * n

    async with get_session() as session:
        if categoria_id is not None and await session.get(Categoria, categoria_id) is None:
            raise CompraError("Categoria não encontrada.")

        compra = Compra(
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            total_parcelas=n,
            data_compra=date.today(),
            origem="boleto",
            cartao_id=None,
            categoria_id=categoria_id,
        )
        session.add(compra)
        await session.flush()

        for i in range(n):
            ano_i, mes_i = add_meses(primeiro.year, primeiro.month, i)
            session.add(Parcela(
                compra_id=compra.id,
                numero=i + 1,
                total_parcelas=n,
                valor=valores[i],
                tem_juros=juros[i] > 0,
                valor_juros=juros[i],
                vencimento=date(ano_i, mes_i, dia_valido(ano_i, mes_i, primeiro.day)),
                fatura_id=None,  # boleto não tem fatura
            ))

        await session.commit()
        return _to_response(await _carregar_compra(session, compra.id))


async def get_compra(compra_id: str) -> CompraResponse:
    async with get_session() as session:
        compra = await _carregar_compra(session, _uuid(compra_id))
        if compra is None:
            raise CompraError("Compra não encontrada.")
        return _to_response(compra)


async def sugerir_categoria(
    usuario_id: str, descricao: str
) -> CompraCategoriaSugestao:
    """Categoria usada na última compra com a mesma descrição (reaproveita pra
    auto-categorizar compras que se repetem). Nula quando não há histórico."""
    vazia = CompraCategoriaSugestao(categoria_id=None, categoria_nome=None)
    if not descricao or not descricao.strip():
        return vazia
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        row = (await session.execute(
            select(Compra.categoria_id, Categoria.nome)
            .join(Categoria, Categoria.id == Compra.categoria_id)
            .where(
                Compra.usuario_id == uid,
                func.lower(Compra.descricao) == descricao.strip().lower(),
                Compra.categoria_id.is_not(None),
            )
            .order_by(Compra.created_at.desc())
            .limit(1)
        )).first()
    if row is None:
        return vazia
    return CompraCategoriaSugestao(categoria_id=str(row[0]), categoria_nome=row[1])


async def excluir_compra(compra_id: str, *, usuario_id: str) -> None:
    """Estorna uma compra parcelada: remove as parcelas (cascade) e abate o
    valor delas das faturas em que caíram. Bloqueia se alguma parcela já entrou
    numa fatura paga (aí o certo é desfazer o pagamento da fatura primeiro).
    Faturas que ficam sem parcela são removidas."""
    cid = _uuid(compra_id)
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        compra = await _carregar_compra(session, cid)
        if compra is None:
            raise CompraError("Compra não encontrada.")
        if compra.usuario_id != uid:
            raise CompraError("A compra não pertence a esse usuário.")

        # Faturas afetadas (parcelas de cartão); boleto parcelado não tem.
        faturas: dict[uuid.UUID, Fatura] = {}
        for p in compra.parcelas:
            if p.fatura_id and p.fatura_id not in faturas:
                f = await session.get(Fatura, p.fatura_id)
                if f is not None:
                    faturas[p.fatura_id] = f

        for f in faturas.values():
            if f.status == "paga":
                raise CompraError(
                    "Uma das parcelas já entrou numa fatura paga. "
                    "Desfaça o pagamento da fatura antes de estornar a compra."
                )

        # Abate cada parcela da sua fatura antes de remover.
        for p in compra.parcelas:
            if p.fatura_id and p.fatura_id in faturas:
                f = faturas[p.fatura_id]
                novo = Decimal(f.valor_total) - Decimal(p.valor)
                f.valor_total = novo if novo > 0 else Decimal("0")

        await session.delete(compra)  # parcelas saem por cascade
        await session.flush()

        # Faturas que ficaram sem nenhuma parcela viram lixo — remove.
        for fid, f in faturas.items():
            restam = await session.scalar(
                select(func.count()).select_from(Parcela).where(Parcela.fatura_id == fid)
            )
            if not restam:
                await session.delete(f)

        await eventos.notificar(session, uid, "compra_excluida")
        await session.commit()
