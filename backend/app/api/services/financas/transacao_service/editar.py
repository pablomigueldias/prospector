from __future__ import annotations

from ._base import *  # noqa: F401,F403  (imports/TransacaoError compartilhados)
from ._base import (  # noqa: F401  (helpers privados)
    _buscar_conta,
    _checar_status,
    _finalizar_transacao,
    _intervalo_mes,
    _iso,
    _to_response,
    _uuid,
    _validar_categoria,
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


async def editar_prevista(
    transacao_id: str, payload, usuario_id_sessao: str
) -> TransacaoResponse:
    """Edita uma conta **a pagar** (prevista/atrasada) sem tocar no saldo — ela
    ainda não foi paga. Serve pra detalhar/corrigir o que veio do boleto:
    descrição, valor, categoria, vencimento, encargos e as verbas (itens)."""
    if not payload.descricao.strip():
        raise TransacaoError("A conta a pagar precisa de uma descrição.")
    tid = _uuid(transacao_id)
    uid = _uuid(usuario_id_sessao, campo="usuario_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )

    async with get_session() as session:
        repo = TransacaoRepository(session)
        t = await repo.get(tid)
        if t is None:
            raise TransacaoError("Transação não encontrada.")
        if t.usuario_id != uid:
            raise TransacaoError("A transação não pertence a esse usuário.")
        if t.status == "paga":
            raise TransacaoError(
                "Essa transação já foi paga — não dá pra editar como conta a pagar."
            )
        if len(t.pagamentos) > 1:
            raise TransacaoError(
                "Essa conta é dividida em mais de uma conta — exclua e relance."
            )
        await _validar_categoria(session, categoria_id)

        t.descricao = payload.descricao.strip()
        t.valor_total = payload.valor_total
        t.categoria_id = categoria_id
        t.data_vencimento = payload.data_vencimento
        if payload.multa_percentual is not None:
            t.multa_percentual = payload.multa_percentual
        if payload.juros_mensal_percentual is not None:
            t.juros_mensal_percentual = payload.juros_mensal_percentual
        # Prevista lançada com conta: mantém a soma do pagamento == total.
        if len(t.pagamentos) == 1:
            t.pagamentos[0].valor = payload.valor_total
        # Substitui as verbas, se vieram (cascade delete-orphan limpa as antigas).
        if payload.itens is not None:
            t.itens.clear()
            for it in payload.itens:
                t.itens.append(
                    TransacaoItem(descricao=it.descricao, valor=it.valor)
                )
        # Vínculo com a conta fixa: só mexe se o campo foi enviado (None = solta).
        if "recorrencia_id" in payload.model_fields_set:
            rid = (
                _uuid(payload.recorrencia_id, campo="recorrencia_id")
                if payload.recorrencia_id else None
            )
            if rid is not None:
                rec = await session.get(Recorrencia, rid)
                if rec is None:
                    raise TransacaoError("Recorrência não encontrada.")
                if rec.usuario_id != uid:
                    raise TransacaoError("A recorrência não pertence a esse usuário.")
            t.recorrencia_id = rid

        await eventos.notificar(session, uid, "transacao_editada")
        await session.commit()
        return _to_response(await repo.get(tid))



