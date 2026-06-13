"""Service de Transações — lançamento de despesa e cálculo de saldo.

Step 7: despesa simples (uma conta, uma categoria). Split de pagamento e
resumo do mês vêm nos próximos steps.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.financas import (
    DespesaAutoSplitCreate,
    DespesaCreate,
    DespesaDivididaCreate,
    ReceitaCreate,
    TransacaoItemResponse,
    TransacaoListItem,
    TransacaoListResponse,
    TransacaoPagamentoResponse,
    TransacaoResponse,
)
from app.api.services.financas import encargos as encargos_service
from app.api.services.financas import eventos, saldo_service
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.conta import Conta
from app.db.models.financas.transacao import STATUS_TRANSACAO, Transacao
from app.db.models.financas.transacao_pagamento import TransacaoPagamento
from app.db.session import get_session
from app.repositories.financas.transacao_repository import TransacaoRepository


class TransacaoError(Exception):
    """Erro de negócio de Transações — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise TransacaoError(f"{campo} inválido: {valor!r}")


def _to_response(t: Transacao) -> TransacaoResponse:
    return TransacaoResponse(
        id=str(t.id),
        usuario_id=str(t.usuario_id),
        tipo=t.tipo,
        descricao=t.descricao,
        valor_total=t.valor_total,
        data_competencia=t.data_competencia,
        data_pagamento=t.data_pagamento,
        data_vencimento=t.data_vencimento,
        multa_percentual=t.multa_percentual,
        juros_mensal_percentual=t.juros_mensal_percentual,
        encargos_pagos=t.encargos_pagos,
        linha_digitavel=t.linha_digitavel,
        status=t.status,
        origem=t.origem,
        categoria_id=str(t.categoria_id) if t.categoria_id else None,
        notas=t.notas,
        itens=[
            TransacaoItemResponse(
                id=str(i.id),
                categoria_id=str(i.categoria_id) if i.categoria_id else None,
                descricao=i.descricao,
                valor=i.valor,
            )
            for i in t.itens
        ],
        pagamentos=[
            TransacaoPagamentoResponse(
                id=str(p.id), conta_id=str(p.conta_id), valor=p.valor
            )
            for p in t.pagamentos
        ],
        created_at=_iso(t.created_at),
        updated_at=_iso(t.updated_at),
    )


async def _buscar_conta(
    session: AsyncSession, conta_id: uuid.UUID, usuario_id: uuid.UUID
) -> Conta:
    conta = await session.get(Conta, conta_id)
    if conta is None:
        raise TransacaoError("Conta não encontrada.")
    if conta.usuario_id != usuario_id:
        raise TransacaoError("A conta não pertence a esse usuário.")
    return conta


async def _validar_categoria(
    session: AsyncSession, categoria_id: Optional[uuid.UUID]
) -> None:
    if categoria_id is not None:
        if await session.get(Categoria, categoria_id) is None:
            raise TransacaoError("Categoria não encontrada.")


async def _finalizar_transacao(
    session: AsyncSession,
    *,
    tipo: str,
    usuario_id: uuid.UUID,
    descricao: str,
    valor_total: Decimal,
    categoria_id: Optional[uuid.UUID],
    competencia: date,
    pagamento_em: Optional[date],
    status: str,
    notas: Optional[str],
    pagamentos: List[Tuple[Conta, Decimal]],
) -> TransacaoResponse:
    """Núcleo: cria a transação (despesa/receita) com N pagamentos e ajusta o
    saldo de cada conta (só quando paga). Assume contas/categoria já validadas."""
    transacao = Transacao(
        usuario_id=usuario_id,
        tipo=tipo,
        descricao=descricao,
        valor_total=valor_total,
        data_competencia=competencia,
        data_pagamento=pagamento_em,
        status=status,
        origem="manual",
        categoria_id=categoria_id,
        notas=notas,
        pagamentos=[
            TransacaoPagamento(conta_id=conta.id, valor=valor)
            for conta, valor in pagamentos
        ],
    )
    repo = TransacaoRepository(session)
    repo.add(transacao)

    if status == "paga":
        for conta, valor in pagamentos:
            saldo_service.aplicar_movimento(conta, tipo, valor)

    # Avisa o dashboard em tempo real (entregue no commit).
    await eventos.notificar(session, usuario_id, "transacao_criada")
    await session.commit()
    return _to_response(await repo.get(transacao.id))


def _checar_status(status: str) -> None:
    if status not in STATUS_TRANSACAO:
        raise TransacaoError(
            f"Status inválido: {status!r}. "
            f"Use um de: {', '.join(STATUS_TRANSACAO)}."
        )


async def lancar_despesa(payload: DespesaCreate) -> TransacaoResponse:
    if not payload.descricao.strip():
        raise TransacaoError("A despesa precisa de uma descrição.")
    _checar_status(payload.status)

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    conta_id = _uuid(payload.conta_id, campo="conta_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )

    competencia = payload.data_competencia or date.today()
    paga = payload.status == "paga"
    pagamento_em = payload.data_pagamento or (date.today() if paga else None)

    async with get_session() as session:
        conta = await _buscar_conta(session, conta_id, usuario_id)
        await _validar_categoria(session, categoria_id)
        return await _finalizar_transacao(
            session,
            tipo="despesa",
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            categoria_id=categoria_id,
            competencia=competencia,
            pagamento_em=pagamento_em,
            status=payload.status,
            notas=payload.notas,
            pagamentos=[(conta, payload.valor_total)],
        )


async def lancar_receita(payload: ReceitaCreate) -> TransacaoResponse:
    if not payload.descricao.strip():
        raise TransacaoError("A receita precisa de uma descrição.")
    _checar_status(payload.status)

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    conta_id = _uuid(payload.conta_id, campo="conta_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    competencia = payload.data_competencia or date.today()
    paga = payload.status == "paga"
    pagamento_em = payload.data_pagamento or (date.today() if paga else None)

    async with get_session() as session:
        conta = await _buscar_conta(session, conta_id, usuario_id)
        await _validar_categoria(session, categoria_id)
        return await _finalizar_transacao(
            session,
            tipo="receita",
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            categoria_id=categoria_id,
            competencia=competencia,
            pagamento_em=pagamento_em,
            status=payload.status,
            notas=payload.notas,
            pagamentos=[(conta, payload.valor_total)],
        )


async def lancar_despesa_dividida(
    payload: DespesaDivididaCreate,
) -> TransacaoResponse:
    if not payload.descricao.strip():
        raise TransacaoError("A despesa precisa de uma descrição.")
    _checar_status(payload.status)

    soma = sum((p.valor for p in payload.pagamentos), Decimal("0"))
    if soma != payload.valor_total:
        raise TransacaoError(
            f"A soma dos pagamentos (R${soma}) não bate com o total "
            f"(R${payload.valor_total})."
        )

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    competencia = payload.data_competencia or date.today()
    paga = payload.status == "paga"
    pagamento_em = payload.data_pagamento or (date.today() if paga else None)

    async with get_session() as session:
        await _validar_categoria(session, categoria_id)
        pagamentos: List[Tuple[Conta, Decimal]] = []
        for p in payload.pagamentos:
            conta = await _buscar_conta(
                session, _uuid(p.conta_id, campo="conta_id"), usuario_id
            )
            pagamentos.append((conta, p.valor))

        return await _finalizar_transacao(
            session,
            tipo="despesa",
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            categoria_id=categoria_id,
            competencia=competencia,
            pagamento_em=pagamento_em,
            status=payload.status,
            notas=payload.notas,
            pagamentos=pagamentos,
        )


async def lancar_despesa_auto_split(
    payload: DespesaAutoSplitCreate,
) -> TransacaoResponse:
    """Esgota o VR/VA e joga o resto no dinheiro. Sempre paga (move o saldo)."""
    if not payload.descricao.strip():
        raise TransacaoError("A despesa precisa de uma descrição.")

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    vr_id = _uuid(payload.conta_vr_id, campo="conta_vr_id")
    fallback_id = _uuid(payload.conta_fallback_id, campo="conta_fallback_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    if vr_id == fallback_id:
        raise TransacaoError("As contas de VR e fallback precisam ser diferentes.")

    competencia = payload.data_competencia or date.today()
    total = payload.valor_total

    async with get_session() as session:
        vr = await _buscar_conta(session, vr_id, usuario_id)
        fallback = await _buscar_conta(session, fallback_id, usuario_id)
        await _validar_categoria(session, categoria_id)

        # Quanto o VR cobre (nunca negativo), o resto vai pro fallback.
        vr_disponivel = max(Decimal("0"), Decimal(vr.saldo_atual))
        parte_vr = min(total, vr_disponivel)
        parte_fallback = total - parte_vr

        pagamentos: List[Tuple[Conta, Decimal]] = []
        if parte_vr > 0:
            pagamentos.append((vr, parte_vr))
        if parte_fallback > 0:
            pagamentos.append((fallback, parte_fallback))

        return await _finalizar_transacao(
            session,
            tipo="despesa",
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=total,
            categoria_id=categoria_id,
            competencia=competencia,
            pagamento_em=date.today(),
            status="paga",
            notas=payload.notas,
            pagamentos=pagamentos,
        )


async def get_transacao(transacao_id: str) -> TransacaoResponse:
    async with get_session() as session:
        transacao = await TransacaoRepository(session).get(_uuid(transacao_id))
        if transacao is None:
            raise TransacaoError("Transação não encontrada.")
        return _to_response(transacao)


def _intervalo_mes(ano: Optional[int], mes: Optional[int]) -> Tuple[
    Optional[date], Optional[date]
]:
    """(inicio, proximo_mes) para filtrar por competência; (None, None) se
    ano/mes não vierem juntos."""
    if not ano or not mes:
        return None, None
    if mes < 1 or mes > 12:
        raise TransacaoError(f"Mês inválido: {mes}.")
    inicio = date(ano, mes, 1)
    proximo = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, proximo


async def listar_transacoes(
    usuario_id: str,
    *,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    conta_id: Optional[str] = None,
    categoria_id: Optional[str] = None,
    tipo: Optional[str] = None,
    status: Optional[List[str]] = None,
    busca: Optional[str] = None,
    por_vencimento: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> TransacaoListResponse:
    """Lista filtrável de transações para o dashboard (mais novas primeiro)."""
    uid = _uuid(usuario_id, campo="usuario_id")
    inicio, proximo = _intervalo_mes(ano, mes)
    cid = _uuid(conta_id, campo="conta_id") if conta_id else None
    catid = _uuid(categoria_id, campo="categoria_id") if categoria_id else None
    if tipo is not None and tipo not in ("despesa", "receita"):
        raise TransacaoError(f"Tipo inválido: {tipo!r}. Use despesa ou receita.")
    if status:
        invalidos = [s for s in status if s not in STATUS_TRANSACAO]
        if invalidos:
            raise TransacaoError(f"Status inválido: {', '.join(invalidos)}.")
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    termo = busca.strip() if busca and busca.strip() else None

    async with get_session() as session:
        repo = TransacaoRepository(session)
        itens, total = await repo.listar(
            uid,
            inicio=inicio,
            proximo_mes=proximo,
            conta_id=cid,
            categoria_id=catid,
            tipo=tipo,
            status=status,
            busca=termo,
            por_vencimento=por_vencimento,
            limit=limit,
            offset=offset,
        )

        conta_ids = {p.conta_id for t in itens for p in t.pagamentos}
        cat_ids = {t.categoria_id for t in itens if t.categoria_id}
        contas_nome: dict = {}
        if conta_ids:
            rows = await session.execute(
                select(Conta.id, Conta.nome).where(Conta.id.in_(conta_ids))
            )
            contas_nome = {cid_: nome for cid_, nome in rows.all()}
        cat_nome: dict = {}
        if cat_ids:
            rows = await session.execute(
                select(Categoria.id, Categoria.nome).where(Categoria.id.in_(cat_ids))
            )
            cat_nome = {cid_: nome for cid_, nome in rows.all()}

        items = [
            TransacaoListItem(
                id=str(t.id),
                tipo=t.tipo,
                descricao=t.descricao,
                valor_total=t.valor_total,
                data_competencia=t.data_competencia,
                data_pagamento=t.data_pagamento,
                data_vencimento=t.data_vencimento,
                multa_percentual=t.multa_percentual,
                juros_mensal_percentual=t.juros_mensal_percentual,
                encargos_pagos=t.encargos_pagos,
                linha_digitavel=t.linha_digitavel,
                status=t.status,
                categoria_id=str(t.categoria_id) if t.categoria_id else None,
                categoria_nome=cat_nome.get(t.categoria_id),
                contas=[contas_nome.get(p.conta_id, "?") for p in t.pagamentos],
            )
            for t in itens
        ]

    return TransacaoListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


async def editar_transacao(
    transacao_id: str, payload, usuario_id_sessao: str
) -> TransacaoResponse:
    """Edita uma transação simples (uma conta) reajustando o saldo: reverte o
    efeito antigo (se estava paga) e aplica o novo. Divididas/com itens não são
    suportadas aqui — a mensagem orienta a excluir e relançar."""
    if not payload.descricao.strip():
        raise TransacaoError("A transação precisa de uma descrição.")
    if payload.tipo not in ("despesa", "receita"):
        raise TransacaoError(f"Tipo inválido: {payload.tipo!r}. Use despesa ou receita.")
    _checar_status(payload.status)

    tid = _uuid(transacao_id)
    usuario_id = _uuid(usuario_id_sessao, campo="usuario_id")
    nova_conta_id = _uuid(payload.conta_id, campo="conta_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )

    async with get_session() as session:
        repo = TransacaoRepository(session)
        t = await repo.get(tid)
        if t is None:
            raise TransacaoError("Transação não encontrada.")
        if t.usuario_id != usuario_id:
            raise TransacaoError("A transação não pertence a esse usuário.")
        if len(t.pagamentos) != 1:
            raise TransacaoError(
                "Essa transação foi paga por mais de uma conta — exclua e "
                "relance pra alterar."
            )
        if t.itens:
            raise TransacaoError(
                "Essa transação tem itens detalhados — exclua e relance pra alterar."
            )

        nova_conta = await _buscar_conta(session, nova_conta_id, usuario_id)
        await _validar_categoria(session, categoria_id)

        # 1) desfaz o efeito antigo no saldo (se a transação estava paga).
        if t.status == "paga":
            conta_antiga = await session.get(Conta, t.pagamentos[0].conta_id)
            if conta_antiga is not None:
                saldo_service.reverter_movimento(
                    conta_antiga, t.tipo, t.pagamentos[0].valor
                )

        # 2) aplica os novos valores na transação e no único pagamento.
        paga = payload.status == "paga"
        t.tipo = payload.tipo
        t.descricao = payload.descricao.strip()
        t.valor_total = payload.valor_total
        t.categoria_id = categoria_id
        t.data_competencia = payload.data_competencia or t.data_competencia
        t.status = payload.status
        t.data_pagamento = (t.data_pagamento or date.today()) if paga else None
        t.pagamentos[0].conta_id = nova_conta.id
        t.pagamentos[0].valor = payload.valor_total

        # 3) aplica o efeito novo no saldo (se ficou paga).
        if paga:
            saldo_service.aplicar_movimento(nova_conta, t.tipo, payload.valor_total)

        await eventos.notificar(session, usuario_id, "transacao_editada")
        await session.commit()
        return _to_response(await repo.get(t.id))


async def pagar_transacao(
    transacao_id: str,
    *,
    conta_id: Optional[str] = None,
    data_pagamento: Optional[date] = None,
    multa_percentual: Optional[Decimal] = None,
    juros_mensal_percentual: Optional[Decimal] = None,
    usuario_id_sessao: str,
) -> TransacaoResponse:
    """Marca uma transação prevista/atrasada como **paga**, movendo o saldo.

    - Se já tem pagamento(s) (ex.: prevista lançada com conta), só efetiva:
      aplica no saldo o valor de cada pagamento existente.
    - Se não tem nenhum (ex.: boleto importado ou recorrência, que nascem sem
      conta), exige uma ``conta_id`` e cria o pagamento único com o valor total
      antes de mexer no saldo.
    """
    tid = _uuid(transacao_id)
    uid = _uuid(usuario_id_sessao, campo="usuario_id")
    quando = data_pagamento or date.today()

    async with get_session() as session:
        repo = TransacaoRepository(session)
        t = await repo.get(tid)
        if t is None:
            raise TransacaoError("Transação não encontrada.")
        if t.usuario_id != uid:
            raise TransacaoError("A transação não pertence a esse usuário.")
        if t.status == "paga":
            raise TransacaoError("Essa transação já está paga.")

        # Encargos informados na hora de pagar sobrescrevem (e salvam) os da
        # transação — corrige o que a IA leu / preenche boleto antigo sem essa info.
        if multa_percentual is not None:
            t.multa_percentual = multa_percentual
        if juros_mensal_percentual is not None:
            t.juros_mensal_percentual = juros_mensal_percentual

        # Multa + juros até a data do pagamento (0 se no prazo / sem encargos).
        # Não aplica em despesa dividida (mais de uma conta) — caso raro de boleto.
        enc = encargos_service.calcular_encargos(
            t.valor_total, t.data_vencimento, t.multa_percentual,
            t.juros_mensal_percentual, quando,
        )
        aplica_enc = enc > 0 and len(t.pagamentos) <= 1

        if t.pagamentos:
            if aplica_enc:
                t.pagamentos[0].valor = Decimal(t.pagamentos[0].valor) + enc
                t.valor_total = Decimal(t.valor_total) + enc
                t.encargos_pagos = enc
            for p in t.pagamentos:
                conta = await session.get(Conta, p.conta_id)
                if conta is not None:
                    saldo_service.aplicar_movimento(conta, t.tipo, p.valor)
        else:
            if not conta_id:
                raise TransacaoError("Escolha a conta pra registrar o pagamento.")
            conta = await _buscar_conta(
                session, _uuid(conta_id, campo="conta_id"), uid
            )
            total = Decimal(t.valor_total) + (enc if aplica_enc else Decimal("0"))
            t.pagamentos.append(
                TransacaoPagamento(conta_id=conta.id, valor=total)
            )
            if aplica_enc:
                t.valor_total = total
                t.encargos_pagos = enc
            saldo_service.aplicar_movimento(conta, t.tipo, total)

        t.status = "paga"
        t.data_pagamento = quando

        await eventos.notificar(session, uid, "transacao_paga")
        await session.commit()
        return _to_response(await repo.get(tid))


async def excluir_transacao(transacao_id: str) -> None:
    """Remove a transação e reverte o saldo das contas (se estava paga).
    Cascateia pagamentos/itens/comprovantes; zera leituras ligadas."""
    async with get_session() as session:
        repo = TransacaoRepository(session)
        transacao = await repo.get(_uuid(transacao_id))
        if transacao is None:
            raise TransacaoError("Transação não encontrada.")
        usuario_id = transacao.usuario_id
        if transacao.status == "paga":
            for p in transacao.pagamentos:
                conta = await session.get(Conta, p.conta_id)
                if conta is not None:
                    saldo_service.reverter_movimento(conta, transacao.tipo, p.valor)
        await session.delete(transacao)
        await eventos.notificar(session, usuario_id, "transacao_excluida")
        await session.commit()
