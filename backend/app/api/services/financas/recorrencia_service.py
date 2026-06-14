"""Service de Recorrências — cadastro e leitura das despesas/receitas fixas."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, select

from app.api.schemas.financas import (
    PagarMesRequest,
    RecorrenciaCreate,
    RecorrenciaListResponse,
    RecorrenciaResponse,
    RecorrenciaStatusItem,
    RecorrenciaStatusResponse,
    RecorrenciaUpdate,
)
from app.api.services.financas import compra_service, eventos, saldo_service
from app.api.services.financas.compra_service import dia_valido
from app.db.models.financas.cartao import Cartao
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.compra import Compra
from app.db.models.financas.conta import Conta
from app.db.models.financas.recorrencia import FORMAS_PAGAMENTO, Recorrencia
from app.db.models.financas.transacao import Transacao
from app.db.models.financas.transacao_pagamento import TransacaoPagamento
from app.db.session import get_session

TIPOS_RECORRENCIA = ("despesa", "receita")


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
        raise RecorrenciaError(f"Competência inválida: {s!r} (use YYYY-MM).")


class RecorrenciaError(Exception):
    """Erro de negócio de Recorrências — vira HTTP 400/404 no router."""


from app.api.services.financas._common import iso as _iso


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise RecorrenciaError(f"{campo} inválido: {valor!r}")


def _to_response(r: Recorrencia) -> RecorrenciaResponse:
    return RecorrenciaResponse(
        id=str(r.id),
        usuario_id=str(r.usuario_id),
        descricao=r.descricao,
        tipo=r.tipo,
        valor_estimado=r.valor_estimado,
        dia_vencimento=r.dia_vencimento,
        frequencia=r.frequencia,
        categoria_id=str(r.categoria_id) if r.categoria_id else None,
        conta_id=str(r.conta_id) if r.conta_id else None,
        forma_pagamento=r.forma_pagamento,
        cartao_id=str(r.cartao_id) if r.cartao_id else None,
        ativa=r.ativa,
        created_at=_iso(r.created_at),
        updated_at=_iso(r.updated_at),
    )


async def criar_recorrencia(payload: RecorrenciaCreate) -> RecorrenciaResponse:
    if not payload.descricao.strip():
        raise RecorrenciaError("A recorrência precisa de uma descrição.")
    if payload.tipo not in TIPOS_RECORRENCIA:
        raise RecorrenciaError(
            f"Tipo inválido: {payload.tipo!r}. Use 'despesa' ou 'receita'."
        )
    if payload.forma_pagamento not in FORMAS_PAGAMENTO:
        raise RecorrenciaError(
            f"Forma de pagamento inválida: {payload.forma_pagamento!r}."
        )

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    conta_id = _uuid(payload.conta_id, campo="conta_id") if payload.conta_id else None
    cartao_id = _uuid(payload.cartao_id, campo="cartao_id") if payload.cartao_id else None

    async with get_session() as session:
        if categoria_id and await session.get(Categoria, categoria_id) is None:
            raise RecorrenciaError("Categoria não encontrada.")
        if conta_id is not None:
            conta = await session.get(Conta, conta_id)
            if conta is None:
                raise RecorrenciaError("Conta não encontrada.")
            if conta.usuario_id != usuario_id:
                raise RecorrenciaError("A conta não pertence a esse usuário.")
        if cartao_id is not None:
            cartao = await session.get(Cartao, cartao_id)
            if cartao is None:
                raise RecorrenciaError("Cartão não encontrado.")
            if cartao.usuario_id != usuario_id:
                raise RecorrenciaError("O cartão não pertence a esse usuário.")

        rec = Recorrencia(
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            tipo=payload.tipo,
            valor_estimado=payload.valor_estimado,
            dia_vencimento=payload.dia_vencimento,
            frequencia=payload.frequencia,
            categoria_id=categoria_id,
            conta_id=conta_id,
            forma_pagamento=payload.forma_pagamento,
            cartao_id=cartao_id,
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return _to_response(rec)


async def tornar_recorrente(
    transacao_id: str, usuario_id_sessao: str, dia_vencimento: Optional[int] = None
) -> RecorrenciaResponse:
    """Cria uma conta fixa (recorrência) a partir de uma transação/boleto e
    liga a transação atual à recorrência, pra o cron não gerar uma 2ª prevista
    deste mês. O dia de vencimento vem do boleto (ou do informado)."""
    from datetime import date

    tid = _uuid(transacao_id)
    uid = _uuid(usuario_id_sessao, campo="usuario_id")
    async with get_session() as session:
        t = await session.get(Transacao, tid)
        if t is None:
            raise RecorrenciaError("Transação não encontrada.")
        if t.usuario_id != uid:
            raise RecorrenciaError("A transação não pertence a esse usuário.")

        dia = dia_vencimento or (
            t.data_vencimento.day if t.data_vencimento else date.today().day
        )
        dia = max(1, min(int(dia), 31))

        rec = Recorrencia(
            usuario_id=uid,
            descricao=t.descricao,
            tipo=t.tipo,
            valor_estimado=t.valor_total,
            dia_vencimento=dia,
            frequencia="mensal",
            categoria_id=t.categoria_id,
        )
        session.add(rec)
        await session.flush()
        # Liga a transação à recorrência → idempotência do cron neste mês.
        t.recorrencia_id = rec.id
        await session.commit()
        await session.refresh(rec)
        return _to_response(rec)


async def atualizar_recorrencia(
    recorrencia_id: str, payload: RecorrenciaUpdate
) -> RecorrenciaResponse:
    dados = payload.model_dump(exclude_unset=True)
    if "tipo" in dados and dados["tipo"] is not None:
        if dados["tipo"] not in TIPOS_RECORRENCIA:
            raise RecorrenciaError(
                f"Tipo inválido: {dados['tipo']!r}. Use 'despesa' ou 'receita'."
            )
    if "descricao" in dados and dados["descricao"] is not None:
        if not dados["descricao"].strip():
            raise RecorrenciaError("A descrição não pode ficar vazia.")
        dados["descricao"] = dados["descricao"].strip()
    if dados.get("forma_pagamento") and dados["forma_pagamento"] not in FORMAS_PAGAMENTO:
        raise RecorrenciaError(
            f"Forma de pagamento inválida: {dados['forma_pagamento']!r}."
        )

    async with get_session() as session:
        rec = await session.get(Recorrencia, _uuid(recorrencia_id))
        if rec is None:
            raise RecorrenciaError("Recorrência não encontrada.")

        if dados.get("categoria_id"):
            cid = _uuid(dados["categoria_id"], campo="categoria_id")
            if await session.get(Categoria, cid) is None:
                raise RecorrenciaError("Categoria não encontrada.")
            dados["categoria_id"] = cid
        if dados.get("conta_id"):
            coid = _uuid(dados["conta_id"], campo="conta_id")
            conta = await session.get(Conta, coid)
            if conta is None:
                raise RecorrenciaError("Conta não encontrada.")
            if conta.usuario_id != rec.usuario_id:
                raise RecorrenciaError("A conta não pertence a esse usuário.")
            dados["conta_id"] = coid
        if dados.get("cartao_id"):
            caid = _uuid(dados["cartao_id"], campo="cartao_id")
            cartao = await session.get(Cartao, caid)
            if cartao is None:
                raise RecorrenciaError("Cartão não encontrado.")
            if cartao.usuario_id != rec.usuario_id:
                raise RecorrenciaError("O cartão não pertence a esse usuário.")
            dados["cartao_id"] = caid

        for campo, valor in dados.items():
            setattr(rec, campo, valor)
        await session.commit()
        await session.refresh(rec)
        return _to_response(rec)


async def excluir_recorrencia(recorrencia_id: str) -> None:
    async with get_session() as session:
        rec = await session.get(Recorrencia, _uuid(recorrencia_id))
        if rec is None:
            raise RecorrenciaError("Recorrência não encontrada.")
        # Transações já geradas ficam (recorrencia_id vira NULL pela FK).
        await session.delete(rec)
        await session.commit()


async def listar_recorrencias(usuario_id: str) -> RecorrenciaListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        stmt = (
            select(Recorrencia)
            .where(Recorrencia.usuario_id == uid)
            .order_by(Recorrencia.dia_vencimento)
        )
        recs = (await session.execute(stmt)).scalars().all()
        items = [_to_response(r) for r in recs]
    return RecorrenciaListResponse(items=items, total=len(items))


def _status_item(r: Recorrencia, situacao: str, *, transacao_id=None, compra_id=None) -> RecorrenciaStatusItem:
    return RecorrenciaStatusItem(
        recorrencia_id=str(r.id),
        descricao=r.descricao,
        forma_pagamento=r.forma_pagamento,
        valor_estimado=r.valor_estimado,
        dia_vencimento=r.dia_vencimento,
        cartao_id=str(r.cartao_id) if r.cartao_id else None,
        situacao=situacao,
        transacao_id=transacao_id,
        compra_id=compra_id,
    )


async def _ocorrencia_no_mes(session, r: Recorrencia, mes_ref: date):
    """Devolve (situacao, transacao_id, compra_id) da recorrência naquele mês."""
    if r.forma_pagamento == "cartao":
        compra = await session.scalar(
            select(Compra).where(
                Compra.recorrencia_id == r.id,
                func.date_trunc("month", Compra.data_compra) == mes_ref,
            )
        )
        if compra is not None:
            return "lancada_cartao", None, str(compra.id)
        return "nenhuma", None, None
    t = await session.scalar(
        select(Transacao).where(
            Transacao.recorrencia_id == r.id,
            Transacao.data_competencia == mes_ref,
        )
    )
    if t is not None:
        return t.status, str(t.id), None
    return "nenhuma", None, None


async def status_do_mes(
    usuario_id: str, competencia: Optional[str] = None
) -> RecorrenciaStatusResponse:
    """Por recorrência, a situação no mês (paga/prevista/atrasada/lançada no
    cartão/nenhuma) + o vínculo com o lançamento."""
    uid = _uuid(usuario_id, campo="usuario_id")
    ano, mes = _parse_competencia(competencia)
    mes_ref = date(ano, mes, 1)
    async with get_session() as session:
        recs = (await session.execute(
            select(Recorrencia)
            .where(Recorrencia.usuario_id == uid)
            .order_by(Recorrencia.dia_vencimento)
        )).scalars().all()
        items = []
        for r in recs:
            situacao, tid, cid = await _ocorrencia_no_mes(session, r, mes_ref)
            items.append(_status_item(r, situacao, transacao_id=tid, compra_id=cid))
    return RecorrenciaStatusResponse(competencia=f"{ano:04d}-{mes:02d}", items=items)


async def pagar_mes(
    recorrencia_id: str, payload: PagarMesRequest, *, usuario_id_sessao: str
) -> RecorrenciaStatusItem:
    """Lança/quita a recorrência no mês, **ligando** o lançamento à recorrência.

    - Cartão: cria a compra à vista na fatura (não mexe no saldo agora).
    - Conta/boleto: paga a prevista do mês se existe (debitando a conta) ou cria
      uma despesa/receita já paga ligada à recorrência.
    """
    uid = _uuid(usuario_id_sessao, campo="usuario_id")
    ano, mes = _parse_competencia(payload.competencia)
    mes_ref = date(ano, mes, 1)
    quando = payload.data_pagamento or date.today()

    async with get_session() as session:
        r = await session.get(Recorrencia, _uuid(recorrencia_id))
        if r is None:
            raise RecorrenciaError("Recorrência não encontrada.")
        if r.usuario_id != uid:
            raise RecorrenciaError("A recorrência não pertence a esse usuário.")

        valor = Decimal(payload.valor_pago) if payload.valor_pago else Decimal(r.valor_estimado)

        # ── Cartão: vira compra na fatura ─────────────────────────────
        if r.forma_pagamento == "cartao":
            if r.cartao_id is None:
                raise RecorrenciaError("Defina o cartão da recorrência primeiro.")
            situacao, _, cid = await _ocorrencia_no_mes(session, r, mes_ref)
            if cid is not None:
                raise RecorrenciaError("Essa recorrência já foi lançada no cartão neste mês.")
            cartao = await session.get(Cartao, r.cartao_id)
            if cartao is None:
                raise RecorrenciaError("Cartão não encontrado.")
            compra = await compra_service.lancar_avista_na_sessao(
                session, cartao,
                usuario_id=uid,
                descricao=r.descricao,
                valor=valor,
                data_compra=quando,
                categoria_id=r.categoria_id,
                recorrencia_id=r.id,
            )
            await eventos.notificar(session, uid, "recorrencia_lancada")
            await session.commit()
            return _status_item(r, "lancada_cartao", compra_id=str(compra.id))

        # ── Conta / boleto: despesa/receita paga, debitando a conta ───
        t = await session.scalar(
            select(Transacao).where(
                Transacao.recorrencia_id == r.id,
                Transacao.data_competencia == mes_ref,
            )
        )
        if t is not None and t.status == "paga":
            raise RecorrenciaError("Essa recorrência já está paga neste mês.")

        conta_id = payload.conta_id or (str(r.conta_id) if r.conta_id else None)
        if not conta_id:
            raise RecorrenciaError("Escolha a conta que pagou (ou defina uma na recorrência).")
        conta = await session.get(Conta, _uuid(conta_id, campo="conta_id"))
        if conta is None or conta.usuario_id != uid:
            raise RecorrenciaError("Conta não encontrada.")

        venc = date(ano, mes, dia_valido(ano, mes, r.dia_vencimento))
        if t is None:
            t = Transacao(
                usuario_id=uid,
                tipo=r.tipo,
                descricao=r.descricao,
                valor_total=valor,
                data_competencia=mes_ref,
                data_vencimento=venc,
                status="paga",
                origem="recorrencia",
                categoria_id=r.categoria_id,
                recorrencia_id=r.id,
                data_pagamento=quando,
            )
            t.pagamentos.append(TransacaoPagamento(conta_id=conta.id, valor=valor))
            session.add(t)
        else:
            # paga a prevista/atrasada existente do mês
            t.valor_total = valor
            t.status = "paga"
            t.data_pagamento = quando
            if t.pagamentos:
                t.pagamentos[0].conta_id = conta.id
                t.pagamentos[0].valor = valor
            else:
                t.pagamentos.append(TransacaoPagamento(conta_id=conta.id, valor=valor))

        saldo_service.aplicar_movimento(conta, r.tipo, valor)
        await eventos.notificar(session, uid, "transacao_paga")
        await session.commit()
        await session.refresh(t)
        return _status_item(r, "paga", transacao_id=str(t.id))
