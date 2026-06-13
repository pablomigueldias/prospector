from __future__ import annotations

import asyncio
import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.analyzers.boleto import extrator
from app.api.main import app
from tests._financas_auth import usar_usuario
from app.config import settings
from app.utils.s3_storage import get_storage

IMPORTAR = "/api/financas/importar/boleto"
TX = "/api/financas/transacoes"
LEITURAS = "/api/financas/leituras"
CATS = "/api/financas/categorias"

# Boleto do condomínio: 7 verbas que somam 1107.52 + 2 leituras.
BOLETO_OK = {
    "beneficiario": "Condomínio Lello",
    "vencimento": "2026-06-10",
    "valor_total": 1107.52,
    "verbas": [
        {"descricao": "Taxa de condomínio", "valor": 800.00},
        {"descricao": "Consumo de gás", "valor": 50.00},
        {"descricao": "Fundo de reserva", "valor": 100.00},
        {"descricao": "Consumo de água", "valor": 80.00},
        {"descricao": "Consumo de luz (área comum)", "valor": 40.52},
        {"descricao": "Água área comum", "valor": 20.00},
        {"descricao": "Reforma infiltração (parcelada)", "valor": 17.00},
    ],
    "leituras": [
        {"tipo": "agua", "leitura_atual": 1234.5, "leitura_anterior": 1220.0, "consumo": 14.5, "valor": 80},
        {"tipo": "gas", "leitura_atual": 320.2, "leitura_anterior": 297.0, "consumo": 23.2, "valor": 50},
    ],
}
BOLETO_SOMA_ERRADA = {**BOLETO_OK, "verbas": [{"descricao": "Total", "valor": 1000.0}]}
BOLETO_SEM_VALOR = {**BOLETO_OK, "valor_total": 0, "verbas": []}


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.connect() as conn:
            objs = (await conn.execute(
                text("SELECT bucket, arquivo_path FROM financas.comprovantes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )).all()
        for bucket, key in objs:
            try:
                get_storage().client.delete_object(Bucket=bucket, Key=key)
            except Exception:
                pass
        async with eng.begin() as conn:
            for tbl in ("leituras_consumo", "transacoes", "comprovantes"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


def _condominio_id(client: TestClient) -> str:
    for raiz in client.get(CATS).json()["items"]:
        if raiz["nome"] == "Condomínio":
            return raiz["id"]
    raise AssertionError("Condomínio não achado no seed")


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 16 (importador de boleto)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    original = extrator.extrair_boleto_llm
    with TestClient(app) as client:
        usar_usuario(usuario_id)  # dono = sessão (override de auth)
        try:
            condominio = _condominio_id(client)

            # ── 1. Boleto que confere → cria despesa + itens + leituras ─
            print("\n→ Test 1: boleto confere (soma == total)")
            extrator.extrair_boleto_llm = lambda c, ct: json.dumps(BOLETO_OK)
            r = client.post(IMPORTAR, data={
                "usuario_id": usuario_id, "categoria_id": condominio,
            }, files={"file": ("condominio.pdf", b"%PDF fake", "application/pdf")})
            assert r.status_code == 200, r.text
            b = r.json()
            assert b["success"] and b["conferido"], b
            assert b["transacao_id"] and b["comprovante_id"]
            print(f"   {b['mensagem']}")

            # transação tem 7 itens, status prevista, vencimento e categoria certos
            tx = client.get(f"{TX}/{b['transacao_id']}").json()
            assert len(tx["itens"]) == 7, len(tx["itens"])
            assert tx["status"] == "prevista"
            assert tx["data_vencimento"] == "2026-06-10"
            assert tx["categoria_id"] == condominio
            soma = sum(float(i["valor"]) for i in tx["itens"])
            assert round(soma, 2) == 1107.52, soma
            print(f"   tx: {len(tx['itens'])} itens, soma {soma}, venc {tx['data_vencimento']}")

            # 2 leituras de consumo criadas e vinculadas
            leituras = client.get(LEITURAS, params={"usuario_id": usuario_id}).json()
            assert leituras["total"] == 2, leituras["total"]
            tipos = sorted(x["tipo"] for x in leituras["items"])
            assert tipos == ["agua", "gas"], tipos
            assert all(x["transacao_id"] == b["transacao_id"] for x in leituras["items"])
            print(f"   leituras: {tipos} vinculadas à transação")

            # ── 2. Soma não bate → cria a pagar (sem itens), pra não sumir ─
            print("\n→ Test 2: soma não bate → prevista sem itens (a pagar)")
            extrator.extrair_boleto_llm = lambda c, ct: json.dumps(BOLETO_SOMA_ERRADA)
            r2 = client.post(IMPORTAR, data={
                "usuario_id": usuario_id,
            }, files={"file": ("outro.pdf", b"%PDF fake 2", "application/pdf")})
            assert r2.status_code == 200, r2.text
            b2 = r2.json()
            assert b2["success"] and not b2["conferido"], b2
            assert b2["transacao_id"], "deveria criar a despesa a pagar mesmo sem conferir"
            assert b2["comprovante_id"]
            tx2 = client.get(f"{TX}/{b2['transacao_id']}").json()
            assert tx2["status"] == "prevista", tx2["status"]
            assert tx2["itens"] == [], tx2["itens"]  # verbas não confiáveis → sem itens
            assert float(tx2["valor_total"]) == 1107.52, tx2["valor_total"]
            print(f"   {b2['mensagem']}")

            # ── 3. Sem valor legível → nada criado (só o arquivo) ─────────
            print("\n→ Test 3: sem valor total → revisão manual (sem transação)")
            extrator.extrair_boleto_llm = lambda c, ct: json.dumps(BOLETO_SEM_VALOR)
            r3 = client.post(IMPORTAR, data={
                "usuario_id": usuario_id,
            }, files={"file": ("vazio.pdf", b"%PDF fake 3", "application/pdf")})
            assert r3.status_code == 200, r3.text
            b3 = r3.json()
            assert b3["success"] and not b3["conferido"], b3
            assert b3["transacao_id"] is None, b3
            assert b3["comprovante_id"]
            print(f"   {b3['mensagem']}")

        finally:
            extrator.extrair_boleto_llm = original
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 16 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
