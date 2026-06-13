"""Service de Cartões — cadastro e leitura."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select

from app.api.schemas.financas import (
    CartaoCreate,
    CartaoListResponse,
    CartaoResponse,
    CartaoUpdate,
    FaturaExtratoItem,
    FaturaExtratoResponse,
    FaturaResponse,
    FaturasCartaoResponse,
    PagarFaturaRequest,
)
from app.api.services.financas import eventos, saldo_service
from app.db.models.financas.cartao import Cartao
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.compra import Compra
from app.db.models.financas.conta import Conta
from app.db.models.financas.fatura import Fatura
from app.db.models.financas.parcela import Parcela
from app.db.models.financas.transacao import Transacao
from app.db.models.financas.transacao_pagamento import TransacaoPagamento
from app.db.session import get_session


class CartaoError(Exception):
    """Erro de negócio de Cartões — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise CartaoError(f"{campo} inválido: {valor!r}")


def _to_response(c: Cartao) -> CartaoResponse:
    return CartaoResponse(
        id=str(c.id),
        usuario_id=str(c.usuario_id),
        nome=c.nome,
        bandeira=c.bandeira,
        dia_fechamento=c.dia_fechamento,
        dia_vencimento=c.dia_vencimento,
        limite=c.limite,
        ativo=c.ativo,
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


async def criar_cartao(payload: CartaoCreate) -> CartaoResponse:
    if not payload.nome.strip():
        raise CartaoError("O cartão precisa de um nome.")
    async with get_session() as session:
        cartao = Cartao(
            usuario_id=_uuid(payload.usuario_id, campo="usuario_id"),
            nome=payload.nome.strip(),
            bandeira=payload.bandeira,
            dia_fechamento=payload.dia_fechamento,
            dia_vencimento=payload.dia_vencimento,
            limite=payload.limite,
        )
        session.add(cartao)
        await session.commit()
        await session.refresh(cartao)
        return _to_response(cartao)


async def get_cartao(cartao_id: str) -> CartaoResponse:
    async with get_session() as session:
        cartao = await session.get(Cartao, _uuid(cartao_id))
        if cartao is None:
            raise CartaoError("Cartão não encontrado.")
        return _to_response(cartao)


async def atualizar_cartao(
    cartao_id: str, payload: CartaoUpdate
) -> CartaoResponse:
    dados = payload.model_dump(exclude_unset=True)
    if "nome" in dados and dados["nome"] is not None:
        if not dados["nome"].strip():
            raise CartaoError("O nome do cartão não pode ficar vazio.")
        dados["nome"] = dados["nome"].strip()
    async with get_session() as session:
        cartao = await session.get(Cartao, _uuid(cartao_id))
        if cartao is None:
            raise CartaoError("Cartão não encontrado.")
        for campo, valor in dados.items():
            setattr(cartao, campo, valor)
        await session.commit()
        await session.refresh(cartao)
        return _to_response(cartao)


async def excluir_cartao(cartao_id: str) -> None:
    """Remove o cartão. As faturas vão junto (cascade); as compras parceladas
    ficam, perdendo o vínculo com o cartão (FK ondelete=SET NULL)."""
    async with get_session() as session:
        cartao = await session.get(Cartao, _uuid(cartao_id))
        if cartao is None:
            raise CartaoError("Cartão não encontrado.")
        await session.delete(cartao)
        await session.commit()


async def listar_cartoes(usuario_id: str) -> CartaoListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        stmt = (
            select(Cartao)
            .where(Cartao.usuario_id == uid)
            .order_by(Cartao.nome)
        )
        cartoes = (await session.execute(stmt)).scalars().all()
        items = [_to_response(c) for c in cartoes]
    return CartaoListResponse(items=items, total=len(items))


async def faturas_do_cartao(cartao_id: str) -> FaturasCartaoResponse:
    cid = _uuid(cartao_id)
    async with get_session() as session:
        if await session.get(Cartao, cid) is None:
            raise CartaoError("Cartão não encontrado.")

        faturas = (await session.execute(
            select(Fatura)
            .where(Fatura.cartao_id == cid)
            .order_by(Fatura.mes_referencia.desc())
        )).scalars().all()

        em_aberto = await session.scalar(
            select(func.coalesce(func.sum(Fatura.valor_total), 0))
            .where(Fatura.cartao_id == cid, Fatura.status != "paga")
        )
        # juros: parcelas das compras desse cartão
        juros = await session.scalar(
            select(func.coalesce(func.sum(Parcela.valor_juros), 0))
            .select_from(Parcela)
            .join(Compra, Compra.id == Parcela.compra_id)
            .where(Compra.cartao_id == cid)
        )

    return FaturasCartaoResponse(
        cartao_id=str(cid),
        faturas=[
            FaturaResponse(
                id=str(f.id),
                cartao_id=str(f.cartao_id),
                mes_referencia=f.mes_referencia,
                valor_total=f.valor_total,
                vencimento=f.vencimento,
                status=f.status,
            )
            for f in faturas
        ],
        total_em_aberto=Decimal(em_aberto),
        total_juros=Decimal(juros),
    )


async def extrato_fatura(fatura_id: str) -> FaturaExtratoResponse:
    """Detalha uma fatura item a item: as parcelas que caem nela, com a
    descrição/categoria da compra de origem."""
    fid = _uuid(fatura_id)
    async with get_session() as session:
        fatura = await session.get(Fatura, fid)
        if fatura is None:
            raise CartaoError("Fatura não encontrada.")
        cartao = await session.get(Cartao, fatura.cartao_id)

        linhas = (await session.execute(
            select(Parcela, Compra, Categoria)
            .join(Compra, Compra.id == Parcela.compra_id)
            .outerjoin(Categoria, Categoria.id == Compra.categoria_id)
            .where(Parcela.fatura_id == fid)
            .order_by(Parcela.vencimento, Compra.descricao)
        )).all()

        itens = [
            FaturaExtratoItem(
                parcela_id=str(p.id),
                compra_id=str(c.id),
                descricao=c.descricao,
                numero=p.numero,
                total_parcelas=p.total_parcelas,
                valor=p.valor,
                valor_juros=p.valor_juros,
                vencimento=p.vencimento,
                categoria_id=str(cat.id) if cat else None,
                categoria_nome=cat.nome if cat else None,
            )
            for p, c, cat in linhas
        ]
        total_juros = sum((p.valor_juros for p, _, _ in linhas), Decimal("0"))

    return FaturaExtratoResponse(
        fatura=FaturaResponse(
            id=str(fatura.id),
            cartao_id=str(fatura.cartao_id),
            mes_referencia=fatura.mes_referencia,
            valor_total=fatura.valor_total,
            vencimento=fatura.vencimento,
            status=fatura.status,
        ),
        cartao_nome=cartao.nome if cartao else "",
        itens=itens,
        total_juros=Decimal(total_juros),
    )


def _fatura_response(f: Fatura) -> FaturaResponse:
    return FaturaResponse(
        id=str(f.id),
        cartao_id=str(f.cartao_id),
        mes_referencia=f.mes_referencia,
        valor_total=f.valor_total,
        vencimento=f.vencimento,
        status=f.status,
    )


async def pagar_fatura(
    fatura_id: str, payload: PagarFaturaRequest, *, usuario_id_sessao: str
) -> FaturaResponse:
    """Baixa a fatura: cria uma despesa paga (move o saldo da conta) e marca a
    fatura como paga, ligando-a a esse lançamento (``transacao_id``). A despesa
    aparece no resumo/lista do mês como a saída real de dinheiro."""
    fid = _uuid(fatura_id)
    uid = _uuid(usuario_id_sessao, campo="usuario_id")
    quando = payload.data_pagamento or date.today()

    async with get_session() as session:
        fatura = await session.get(Fatura, fid)
        if fatura is None:
            raise CartaoError("Fatura não encontrada.")
        cartao = await session.get(Cartao, fatura.cartao_id)
        if cartao is None or cartao.usuario_id != uid:
            raise CartaoError("A fatura não pertence a esse usuário.")
        if fatura.status == "paga":
            raise CartaoError("Essa fatura já está paga.")

        conta = await session.get(Conta, _uuid(payload.conta_id, campo="conta_id"))
        if conta is None or conta.usuario_id != uid:
            raise CartaoError("Conta não encontrada.")

        categoria_id = None
        if payload.categoria_id:
            categoria_id = _uuid(payload.categoria_id, campo="categoria_id")
            if await session.get(Categoria, categoria_id) is None:
                raise CartaoError("Categoria não encontrada.")

        total = Decimal(payload.valor_pago) if payload.valor_pago else Decimal(fatura.valor_total)
        competencia = fatura.mes_referencia
        rotulo = competencia.strftime("%m/%Y")

        despesa = Transacao(
            usuario_id=uid,
            tipo="despesa",
            descricao=f"Fatura {cartao.nome} {rotulo}",
            valor_total=total,
            data_competencia=quando,
            data_pagamento=quando,
            status="paga",
            origem="manual",
            categoria_id=categoria_id,
        )
        despesa.pagamentos.append(TransacaoPagamento(conta_id=conta.id, valor=total))
        session.add(despesa)
        await session.flush()  # garante despesa.id pra ligar na fatura

        saldo_service.aplicar_movimento(conta, "despesa", total)
        fatura.status = "paga"
        fatura.transacao_id = despesa.id

        await eventos.notificar(session, uid, "fatura_paga")
        await session.commit()
        await session.refresh(fatura)
        return _fatura_response(fatura)
