from __future__ import annotations

from ._base import *  # noqa: F401,F403  (imports/TransacaoError compartilhados)
from ._base import (  # noqa: F401  (helpers privados)
    _uuid, _iso, _to_response, _buscar_conta, _validar_categoria,
    _finalizar_transacao, _checar_status, _intervalo_mes,
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
            vencimento=payload.data_vencimento,
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



