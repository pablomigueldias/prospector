from __future__ import annotations

from ._base import *  # noqa: F401,F403  (imports/TransacaoError compartilhados)
from ._base import (  # noqa: F401  (helpers privados)
    _uuid, _iso, _to_response, _buscar_conta, _validar_categoria,
    _finalizar_transacao, _checar_status, _intervalo_mes,
)


async def pagar_transacao(
    transacao_id: str,
    *,
    conta_id: Optional[str] = None,
    data_pagamento: Optional[date] = None,
    multa_percentual: Optional[Decimal] = None,
    juros_mensal_percentual: Optional[Decimal] = None,
    valor_pago: Optional[Decimal] = None,
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

        # Encargos/valor manual só fazem sentido num pagamento único (não em
        # despesa dividida em várias contas, caso raro de boleto).
        unico = len(t.pagamentos) <= 1

        # Conta destino: se ainda não tem pagamento (boleto/recorrência), exige.
        nova_conta = None
        if not t.pagamentos:
            if not conta_id:
                raise TransacaoError("Escolha a conta pra registrar o pagamento.")
            nova_conta = await _buscar_conta(
                session, _uuid(conta_id, campo="conta_id"), uid
            )

        if unico:
            enc = encargos_service.calcular_encargos(
                t.valor_total, t.data_vencimento, t.multa_percentual,
                t.juros_mensal_percentual, quando,
            )
            # Desconto por antecipação: abate se paga até a data limite.
            desc = Decimal("0")
            if (t.desconto_valor and t.desconto_ate and quando <= t.desconto_ate):
                desc = min(Decimal(t.desconto_valor), Decimal(t.valor_total))
            if valor_pago is not None and valor_pago > 0:
                # Valor manual manda — total exato que saiu da conta.
                total_final = Decimal(valor_pago)
                t.encargos_pagos = None
            elif enc > 0:
                total_final = Decimal(t.valor_total) + enc
                t.encargos_pagos = enc
            elif desc > 0:
                total_final = Decimal(t.valor_total) - desc
            else:
                total_final = Decimal(t.valor_total)
            t.valor_total = total_final
            if t.pagamentos:
                t.pagamentos[0].valor = total_final
            else:
                t.pagamentos.append(
                    TransacaoPagamento(conta_id=nova_conta.id, valor=total_final)
                )

        # Aplica no saldo o valor de cada pagamento (já com o ajuste acima).
        for p in t.pagamentos:
            conta = await session.get(Conta, p.conta_id)
            if conta is not None:
                saldo_service.aplicar_movimento(conta, t.tipo, p.valor)

        t.status = "paga"
        t.data_pagamento = quando

        await eventos.notificar(session, uid, "transacao_paga")
        await session.commit()
        return _to_response(await repo.get(tid))



