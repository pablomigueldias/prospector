"""Smoke test — quitar (marcar como paga) uma transação prevista.

Cobre o endpoint novo:
  POST /api/financas/transacoes/{id}/pagar

Dois caminhos:
  1. Prevista lançada COM conta (form): só efetiva, move o saldo da conta.
  2. Prevista SEM conta (boleto importado / recorrência): exige conta_id,
     cria o pagamento e move o saldo.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings
from tests._financas_auth import limpar_override, usar_usuario

CONTAS = "/api/financas/contas"
TX = "/api/financas/transacoes"


async def _inserir_prevista_sem_conta(
    usuario_id: str, tx_id: str, valor: float,
    *, vencimento=None, multa=None, juros=None,
) -> None:
    """Simula um boleto importado / recorrência: transação prevista sem
    nenhum pagamento (sem conta). Aceita encargos por atraso opcionais."""
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO financas.transacoes "
                    "(id, usuario_id, tipo, descricao, valor_total, "
                    " data_competencia, data_vencimento, multa_percentual, "
                    " juros_mensal_percentual, status, origem) "
                    "VALUES (:id, :uid, 'despesa', 'Condomínio', :v, "
                    " :comp, :venc, :multa, :juros, 'prevista', 'importacao_boleto')"
                ),
                {
                    "id": tx_id, "uid": usuario_id, "v": valor,
                    "comp": date.today().replace(day=1),
                    "venc": vencimento, "multa": multa, "juros": juros,
                },
            )
    finally:
        await eng.dispose()


async def _cleanup(conta_ids: list[str], tx_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tid in tx_ids:
                await conn.execute(
                    text("DELETE FROM financas.transacoes WHERE id = :id"),
                    {"id": tid},
                )
            for cid in conta_ids:
                await conn.execute(
                    text("DELETE FROM financas.contas WHERE id = :id"),
                    {"id": cid},
                )
    finally:
        await eng.dispose()


def _saldo(client: TestClient, conta_id: str) -> float:
    return float(client.get(f"{CONTAS}/{conta_id}").json()["saldo_atual"])


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — pagar (marcar prevista como paga)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    conta_ids: list[str] = []
    tx_ids: list[str] = []

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            # ── Conta com saldo de abertura 1000 ──────────────────────
            r = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 1000,
            })
            assert r.status_code == 201, r.text
            conta_id = r.json()["id"]
            conta_ids.append(conta_id)

            # ══ Caminho 1: prevista lançada COM conta ════════════════
            print("\n→ Test 1: lançar prevista com conta → saldo intacto (1000)")
            r1 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Luz",
                "valor_total": 200, "conta_id": conta_id,
                "status": "prevista",
            })
            assert r1.status_code == 201, r1.text
            tx1 = r1.json()["id"]
            tx_ids.append(tx1)
            assert r1.json()["status"] == "prevista"
            assert _saldo(client, conta_id) == 1000.0, _saldo(client, conta_id)

            # filtro "a pagar" (status=prevista) + ordenação por vencimento
            apagar = client.get(
                f"{TX}?status=prevista&por_vencimento=true&tipo=despesa"
            ).json()
            assert apagar["total"] == 1, apagar
            assert apagar["items"][0]["id"] == tx1
            assert "data_vencimento" in apagar["items"][0]
            # filtro de pagas ainda não traz nada
            assert client.get(f"{TX}?status=paga").json()["total"] == 0

            print("→ Test 2: pagar (sem conta no body) → paga, saldo 800")
            rp = client.post(f"{TX}/{tx1}/pagar", json={})
            assert rp.status_code == 200, rp.text
            assert rp.json()["status"] == "paga", rp.json()
            assert rp.json()["data_pagamento"], rp.json()
            assert _saldo(client, conta_id) == 800.0, _saldo(client, conta_id)

            print("→ Test 3: pagar de novo → 400 (já paga)")
            assert client.post(f"{TX}/{tx1}/pagar", json={}).status_code == 400

            # ══ Caminho 2: prevista SEM conta (boleto) ═══════════════
            print("\n→ Test 4: boleto sem conta → pagar sem conta_id → 400")
            tx2 = str(uuid.uuid4())
            asyncio.run(_inserir_prevista_sem_conta(usuario_id, tx2, 50))
            tx_ids.append(tx2)
            assert client.post(f"{TX}/{tx2}/pagar", json={}).status_code == 400

            print("→ Test 5: pagar com conta_id → paga, saldo 750, cria pagamento")
            rp2 = client.post(f"{TX}/{tx2}/pagar", json={"conta_id": conta_id})
            assert rp2.status_code == 200, rp2.text
            assert rp2.json()["status"] == "paga"
            assert len(rp2.json()["pagamentos"]) == 1, rp2.json()
            assert _saldo(client, conta_id) == 750.0, _saldo(client, conta_id)

            print("→ Test 6: pagar inexistente → 404")
            assert client.post(
                f"{TX}/{uuid.uuid4()}/pagar", json={"conta_id": conta_id}
            ).status_code == 404

            # ══ Caminho 3: boleto vencido com multa+juros ════════════
            print("\n→ Test 7: boleto R$100 vencido 10d, multa 2% + juros 1%/mês")
            from datetime import timedelta
            tx3 = str(uuid.uuid4())
            venc = date.today() - timedelta(days=10)
            asyncio.run(_inserir_prevista_sem_conta(
                usuario_id, tx3, 100, vencimento=venc, multa=2, juros=1,
            ))
            tx_ids.append(tx3)
            saldo_antes = _saldo(client, conta_id)  # 750
            rp3 = client.post(f"{TX}/{tx3}/pagar", json={"conta_id": conta_id})
            assert rp3.status_code == 200, rp3.text
            corpo = rp3.json()
            # multa 2,00 + juros 100*1%*10/30 = 0,33 → encargos 2,33; total 102,33
            assert float(corpo["encargos_pagos"]) == 2.33, corpo["encargos_pagos"]
            assert float(corpo["valor_total"]) == 102.33, corpo["valor_total"]
            assert round(saldo_antes - _saldo(client, conta_id), 2) == 102.33
            print(f"   encargos {corpo['encargos_pagos']}, total {corpo['valor_total']}")

            # ══ Editar conta a pagar: detalha verbas + ajusta valor ══
            print("\n→ Test 7b: editar prevista (detalhar verbas, sem mexer no saldo)")
            txe = str(uuid.uuid4())
            asyncio.run(_inserir_prevista_sem_conta(usuario_id, txe, 300))
            tx_ids.append(txe)
            saldo_pre = _saldo(client, conta_id)
            re_ = client.patch(f"{TX}/{txe}/conta-a-pagar", json={
                "descricao": "Condomínio detalhado",
                "valor_total": 300,
                "itens": [
                    {"descricao": "Taxa", "valor": 250},
                    {"descricao": "Fundo", "valor": 50},
                ],
            })
            assert re_.status_code == 200, re_.text
            ce = re_.json()
            assert ce["descricao"] == "Condomínio detalhado"
            assert len(ce["itens"]) == 2, ce["itens"]
            assert ce["status"] == "prevista"
            assert _saldo(client, conta_id) == saldo_pre, "editar prevista não mexe no saldo"
            print(f"   {len(ce['itens'])} verbas, saldo intacto")

            # ══ Caminho 4: boleto antigo SEM encargos → informa no pagamento ═
            print("\n→ Test 8: boleto antigo s/ encargos → multa/juros no body")
            tx4 = str(uuid.uuid4())
            venc4 = date.today() - timedelta(days=10)
            asyncio.run(_inserir_prevista_sem_conta(
                usuario_id, tx4, 100, vencimento=venc4,  # sem multa/juros
            ))
            tx_ids.append(tx4)
            rp4 = client.post(f"{TX}/{tx4}/pagar", json={
                "conta_id": conta_id, "multa_percentual": 2, "juros_mensal_percentual": 1,
            })
            assert rp4.status_code == 200, rp4.text
            c4 = rp4.json()
            assert float(c4["encargos_pagos"]) == 2.33, c4["encargos_pagos"]
            assert float(c4["valor_total"]) == 102.33, c4["valor_total"]
            assert float(c4["multa_percentual"]) == 2, c4  # persistiu
            print(f"   informado no pagamento → encargos {c4['encargos_pagos']}")

            # ══ Caminho 5: pagar valor diferente (acordo/desconto) ══════
            print("\n→ Test 9: pagar valor diferente do boleto (valor_pago)")
            tx5 = str(uuid.uuid4())
            asyncio.run(_inserir_prevista_sem_conta(usuario_id, tx5, 100))
            tx_ids.append(tx5)
            saldo5 = _saldo(client, conta_id)
            rp5 = client.post(f"{TX}/{tx5}/pagar", json={
                "conta_id": conta_id, "valor_pago": 90,  # pagou 90 em vez de 100
            })
            assert rp5.status_code == 200, rp5.text
            c5 = rp5.json()
            assert float(c5["valor_total"]) == 90, c5["valor_total"]
            assert round(saldo5 - _saldo(client, conta_id), 2) == 90.0
            print(f"   pagou {c5['valor_total']} (boleto era 100)")

            # ══ Conta sugerida pelo beneficiário ════════════════════════
            print("\n→ Test 10: sugestão de conta pelo último pago do beneficiário")
            # tx5 ('Condomínio') foi pago com conta_id acima; um novo boleto do
            # mesmo beneficiário deve sugerir essa conta.
            tx6 = str(uuid.uuid4())
            asyncio.run(_inserir_prevista_sem_conta(usuario_id, tx6, 80))  # 'Condomínio'
            tx_ids.append(tx6)
            sug = client.get(f"{TX}/{tx6}/sugestao-conta").json()
            assert sug["conta_id"] == conta_id, sug
            assert sug["conta_nome"] == "Nubank", sug
            print(f"   sugeriu {sug['conta_nome']}")

        finally:
            limpar_override()
            asyncio.run(_cleanup(conta_ids, tx_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — pagar prevista (com e sem conta) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
