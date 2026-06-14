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
REC = "/api/financas/recorrencias"

# Boleto do condomínio: 7 verbas que somam 1107.52 + 2 leituras.
BOLETO_OK = {
    "beneficiario": "Condomínio Lello",
    "vencimento": "2026-06-10",
    "valor_total": 1107.52,
    "linha_digitavel": "34191.79001 01043.510047 91020.150008 9 99990000110752",
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
# Distintos do BOLETO_OK (outro beneficiário/vencimento/linha) pra não baterem
# no detector de duplicado.
BOLETO_SOMA_ERRADA = {
    **BOLETO_OK, "beneficiario": "Escola Alfa", "vencimento": "2026-07-15",
    "linha_digitavel": None, "verbas": [{"descricao": "Total", "valor": 1000.0}],
}
BOLETO_SEM_VALOR = {
    **BOLETO_OK, "beneficiario": "Loja Beta", "vencimento": "2026-08-01",
    "linha_digitavel": None, "valor_total": 0, "verbas": [],
}
# Mesmo beneficiário do BOLETO_OK, outro mês/valor/linha — pra testar a
# auto-categoria (deve herdar a categoria do BOLETO_OK sem informar).
BOLETO_MESMO_BENEF = {
    "beneficiario": "Condomínio Lello", "vencimento": "2026-07-10",
    "valor_total": 500, "linha_digitavel": "75691.23456 78901.234567 89012.345678 1 88880000050000",
    "verbas": [{"descricao": "Taxa", "valor": 500}], "leituras": [],
}
# Beneficiário com nome igual a uma recorrência ("Imobiliária Sá") — pra testar
# o auto-vínculo do boleto importado à conta fixa.
BOLETO_ALUGUEL = {
    "beneficiario": "Imobiliária Sá", "vencimento": "2026-06-05",
    "valor_total": 1800, "linha_digitavel": "11111.22222 33333.444444 55555.666666 7 99990000180000",
    "verbas": [{"descricao": "Aluguel", "valor": 1800}], "leituras": [],
}


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
            for tbl in ("leituras_consumo", "transacoes", "comprovantes", "recorrencias"):
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
            # linha digitável guardada só com dígitos
            assert tx["linha_digitavel"] == "34191790010104351004791020150008999990000110752", tx["linha_digitavel"]
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

            # ── 4. Reimportar o BOLETO_OK → detecta duplicado, não cria ──
            print("\n→ Test 4: reimportar boleto já lançado → duplicado")
            antes = client.get(f"{TX}?status=prevista").json()["total"]
            extrator.extrair_boleto_llm = lambda c, ct: json.dumps(BOLETO_OK)
            r4 = client.post(IMPORTAR, data={
                "usuario_id": usuario_id, "categoria_id": condominio,
            }, files={"file": ("repetido.pdf", b"%PDF dup", "application/pdf")})
            assert r4.status_code == 200, r4.text
            b4 = r4.json()
            assert b4["duplicado"] is True, b4
            assert b4["transacao_id"] == b["transacao_id"], b4  # aponta pro existente
            depois = client.get(f"{TX}?status=prevista").json()["total"]
            assert depois == antes, (antes, depois)  # nada novo criado
            print(f"   {b4['mensagem']}")

            # ── 5. Mesmo beneficiário, SEM categoria → herda do histórico ─
            print("\n→ Test 5: auto-categoria pelo beneficiário (sem informar)")
            extrator.extrair_boleto_llm = lambda c, ct: json.dumps(BOLETO_MESMO_BENEF)
            r5 = client.post(IMPORTAR, data={
                "usuario_id": usuario_id,  # SEM categoria_id
            }, files={"file": ("julho.pdf", b"%PDF jul", "application/pdf")})
            assert r5.status_code == 200, r5.text
            b5 = r5.json()
            assert b5["transacao_id"] and not b5["duplicado"], b5
            tx5 = client.get(f"{TX}/{b5['transacao_id']}").json()
            assert tx5["categoria_id"] == condominio, tx5["categoria_id"]
            assert "reaproveitada" in b5["mensagem"].lower(), b5["mensagem"]
            print(f"   {b5['mensagem']}")

            # ── 6. Boleto cujo beneficiário casa com uma conta fixa ───────
            print("\n→ Test 6: auto-vínculo do boleto à recorrência (conta fixa)")
            aluguel = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "Imobiliária Sá",
                "tipo": "despesa", "valor_estimado": 1800, "dia_vencimento": 5,
                "forma_pagamento": "boleto",
            }).json()["id"]
            extrator.extrair_boleto_llm = lambda c, ct: json.dumps(BOLETO_ALUGUEL)
            r6 = client.post(IMPORTAR, data={
                "usuario_id": usuario_id,
            }, files={"file": ("aluguel.pdf", b"%PDF alu", "application/pdf")})
            assert r6.status_code == 200, r6.text
            b6 = r6.json()
            assert b6["transacao_id"] and not b6["duplicado"], b6
            tx6 = client.get(f"{TX}/{b6['transacao_id']}").json()
            assert tx6["recorrencia_id"] == aluguel, tx6["recorrencia_id"]
            assert "conta fixa" in b6["mensagem"].lower(), b6["mensagem"]
            # e o status do mês da recorrência reflete (aparece como prevista)
            st = client.get(f"{REC}/status", params={"competencia": "2026-06"}).json()
            sit = {i["recorrencia_id"]: i["situacao"] for i in st["items"]}
            assert sit.get(aluguel) == "prevista", sit
            print(f"   {b6['mensagem']}")

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
