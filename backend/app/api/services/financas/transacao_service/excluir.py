from __future__ import annotations

from ._base import *  # noqa: F401,F403  (imports/TransacaoError compartilhados)
from ._base import (  # noqa: F401  (helpers privados)
    _uuid, _iso, _to_response, _buscar_conta, _validar_categoria,
    _finalizar_transacao, _checar_status, _intervalo_mes,
)


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

