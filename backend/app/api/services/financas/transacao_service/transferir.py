from __future__ import annotations

from ._base import *  # noqa: F401,F403  (imports/TransacaoError compartilhados)
from ._base import (  # noqa: F401  (helpers privados)
    _uuid, _iso, _to_response, _buscar_conta, _validar_categoria,
    _finalizar_transacao, _checar_status, _intervalo_mes,
)


async def transferir(payload: TransferenciaCreate) -> TransferenciaResponse:
    """Move dinheiro entre contas (ex.: guardar na reserva). Cria duas pernas
    (saída na origem + entrada no destino) marcadas como ``origem=transferencia``
    pra NÃO contarem como receita/despesa no resumo. Ambas pagas."""
    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    origem_id = _uuid(payload.origem_conta_id, campo="origem_conta_id")
    destino_id = _uuid(payload.destino_conta_id, campo="destino_conta_id")
    if origem_id == destino_id:
        raise TransacaoError("A origem e o destino precisam ser contas diferentes.")
    if payload.valor <= 0:
        raise TransacaoError("O valor precisa ser maior que zero.")

    quando = payload.data or date.today()
    valor = payload.valor

    async with get_session() as session:
        origem = await _buscar_conta(session, origem_id, usuario_id)
        destino = await _buscar_conta(session, destino_id, usuario_id)
        desc = (payload.descricao or "").strip() or f"Transferência p/ {destino.nome}"

        saida = Transacao(
            usuario_id=usuario_id, tipo="despesa", descricao=desc,
            valor_total=valor, data_competencia=quando, data_pagamento=quando,
            status="paga", origem="transferencia",
            pagamentos=[TransacaoPagamento(conta_id=origem.id, valor=valor)],
        )
        entrada = Transacao(
            usuario_id=usuario_id, tipo="receita", descricao=desc,
            valor_total=valor, data_competencia=quando, data_pagamento=quando,
            status="paga", origem="transferencia",
            pagamentos=[TransacaoPagamento(conta_id=destino.id, valor=valor)],
        )
        session.add(saida)
        session.add(entrada)
        saldo_service.aplicar_movimento(origem, "despesa", valor)
        saldo_service.aplicar_movimento(destino, "receita", valor)
        await eventos.notificar(session, usuario_id, "transferencia")
        await session.commit()

    return TransferenciaResponse(
        origem_conta_id=str(origem_id),
        destino_conta_id=str(destino_id),
        valor=valor,
    )



