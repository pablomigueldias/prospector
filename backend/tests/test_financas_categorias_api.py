from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.api.main import app
from tests._financas_auth import usar_usuario

BASE = "/api/financas/categorias"


def _acha(items: list[dict], nome: str) -> dict | None:
    for it in items:
        if it["nome"] == nome:
            return it
    return None


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 5 (CRUD de categorias)")
    print("━" * 60)

    raiz_id = filho_id = None
    with TestClient(app) as client:
        usar_usuario(str(uuid.uuid4()))  # categorias são globais; só precisa logar
        try:
            # ── 1. Árvore do seed: Condomínio com 7 subverbas ─────────
            print("\n→ Test 1: GET árvore (seed)")
            r = client.get(BASE)
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["total"] >= 19, body["total"]
            cond = _acha(body["items"], "Condomínio")
            assert cond is not None, "Condomínio não está nas raízes"
            assert len(cond["filhos"]) == 7, len(cond["filhos"])
            print(f"   total={body['total']} ; Condomínio tem {len(cond['filhos'])} subverbas")

            # ── 2. Cria raiz + filho ──────────────────────────────────
            print("\n→ Test 2: POST raiz + filho")
            rr = client.post(BASE, json={"nome": "ZZ Teste Raiz"})
            assert rr.status_code == 201, rr.text
            raiz_id = rr.json()["id"]
            assert rr.json()["categoria_pai_id"] is None

            rf = client.post(BASE, json={
                "nome": "ZZ Teste Filho", "categoria_pai_id": raiz_id,
            })
            assert rf.status_code == 201, rf.text
            filho_id = rf.json()["id"]
            assert rf.json()["categoria_pai_id"] == raiz_id
            print(f"   raiz={raiz_id} filho={filho_id}")

            # ── 3. Pai inexistente → 404 ──────────────────────────────
            print("\n→ Test 3: pai inexistente → 404")
            rbad = client.post(BASE, json={
                "nome": "X", "categoria_pai_id": str(uuid.uuid4()),
            })
            assert rbad.status_code == 404, rbad.status_code
            print(f"   barrou: {rbad.json()['detail']}")

            # ── 4. PATCH renomeia filho ───────────────────────────────
            print("\n→ Test 4: PATCH renomeia")
            rp = client.patch(f"{BASE}/{filho_id}", json={"nome": "ZZ Filho Renomeado"})
            assert rp.status_code == 200, rp.text
            assert rp.json()["nome"] == "ZZ Filho Renomeado"
            print("   renomeado")

            # ── 5. Anti-ciclo: pai = si mesmo, e pai = descendente ────
            print("\n→ Test 5: checagem de ciclo → 400")
            rself = client.patch(f"{BASE}/{raiz_id}", json={"categoria_pai_id": raiz_id})
            assert rself.status_code == 400, rself.status_code
            rcycle = client.patch(f"{BASE}/{raiz_id}", json={"categoria_pai_id": filho_id})
            assert rcycle.status_code == 400, rcycle.status_code
            print(f"   self={rself.json()['detail']!r}")
            print(f"   ciclo={rcycle.json()['detail']!r}")

            # ── 6. DELETE raiz → filho some por cascata ───────────────
            print("\n→ Test 6: DELETE raiz (cascata no filho)")
            rdel = client.delete(f"{BASE}/{raiz_id}")
            assert rdel.status_code == 204, rdel.status_code
            assert client.get(f"{BASE}/{filho_id}").status_code == 404
            raiz_id = filho_id = None
            print("   raiz e filho removidos (CASCADE)")

            # ── 7. Seed intacto após a brincadeira ────────────────────
            print("\n→ Test 7: seed continua intacto")
            r2 = client.get(BASE)
            assert _acha(r2.json()["items"], "Condomínio") is not None
            print("   Condomínio segue lá")

        finally:
            for cid in (filho_id, raiz_id):
                if cid:
                    client.delete(f"{BASE}/{cid}")

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 5 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
