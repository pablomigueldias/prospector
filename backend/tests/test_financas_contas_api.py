from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.api.main import app
from tests._financas_auth import limpar_override, usar_usuario

BASE = "/api/financas/contas"


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 4 (CRUD de contas via HTTP)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    criadas: list[str] = []

    with TestClient(app) as client:
        usar_usuario(usuario_id)  # dono dos dados = sessão (override de auth)
        try:
            # ── 1. Cria duas contas ───────────────────────────────────
            print("\n→ Test 1: POST cria contas")
            r = client.post(BASE, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 150.50,
            })
            assert r.status_code == 201, (r.status_code, r.text)
            conta = r.json()
            criadas.append(conta["id"])
            assert conta["nome"] == "Nubank"
            assert conta["tipo"] == "corrente"
            assert float(conta["saldo_atual"]) == 150.50, conta["saldo_atual"]
            assert conta["ativa"] is True
            print(f"   conta1 id={conta['id']} saldo={conta['saldo_atual']}")

            r2 = client.post(BASE, json={
                "usuario_id": usuario_id, "nome": "Carteira", "tipo": "dinheiro",
            })
            assert r2.status_code == 201, r2.text
            criadas.append(r2.json()["id"])
            assert float(r2.json()["saldo_atual"]) == 0.0  # default
            print("   conta2 criada (saldo default 0)")

            # ── 2. Tipo inválido → 400 ────────────────────────────────
            print("\n→ Test 2: tipo inválido → 400")
            rbad = client.post(BASE, json={
                "usuario_id": usuario_id, "nome": "X", "tipo": "bitcoin",
            })
            assert rbad.status_code == 400, rbad.status_code
            print(f"   barrou: {rbad.json()['detail']}")

            # ── 3. Lista do usuário (isola por usuario_id) ────────────
            print("\n→ Test 3: GET lista")
            rl = client.get(BASE, params={"usuario_id": usuario_id})
            assert rl.status_code == 200
            body = rl.json()
            assert body["total"] == 2, body["total"]
            nomes = sorted(c["nome"] for c in body["items"])
            assert nomes == ["Carteira", "Nubank"], nomes
            print(f"   {body['total']} contas: {nomes}")

            # outro usuário (outra sessão) não enxerga essas contas
            usar_usuario(str(uuid.uuid4()))
            ro = client.get(BASE)
            assert ro.json()["total"] == 0
            usar_usuario(usuario_id)  # volta pro dono
            print("   isolamento por usuario_id (sessão) ok")

            # ── 4. Detalhe ────────────────────────────────────────────
            print("\n→ Test 4: GET detalhe")
            rd = client.get(f"{BASE}/{criadas[0]}")
            assert rd.status_code == 200
            assert rd.json()["nome"] == "Nubank"
            # id inexistente → 404
            assert client.get(f"{BASE}/{uuid.uuid4()}").status_code == 404
            print("   detalhe ok; inexistente → 404")

            # ── 5. PATCH (renomeia + desativa) ────────────────────────
            print("\n→ Test 5: PATCH")
            rp = client.patch(f"{BASE}/{criadas[0]}", json={
                "nome": "Nubank PJ", "ativa": False,
            })
            assert rp.status_code == 200, rp.text
            assert rp.json()["nome"] == "Nubank PJ"
            assert rp.json()["ativa"] is False
            # lista só ativas deve esconder essa
            rla = client.get(BASE, params={"usuario_id": usuario_id, "apenas_ativas": True})
            assert rla.json()["total"] == 1
            print("   renomeou/desativou; apenas_ativas filtra ok")

            # ── 6. DELETE ─────────────────────────────────────────────
            print("\n→ Test 6: DELETE")
            rdel = client.delete(f"{BASE}/{criadas[0]}")
            assert rdel.status_code == 204, rdel.status_code
            assert client.get(f"{BASE}/{criadas[0]}").status_code == 404
            criadas.remove(criadas[0])
            print("   removida; volta 404")

        finally:
            for cid in criadas:
                client.delete(f"{BASE}/{cid}")
            limpar_override()

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 4 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
