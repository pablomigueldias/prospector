"""Smoke test — lembrete de vencimento das contas a pagar (Telegram).

Mocka o envio do Telegram e o mapa chat→usuário; cria 3 contas a pagar (uma
vencida, uma vencendo dentro da janela, uma fora) e confere que o digest sai
com as duas primeiras (e com juros na vencida), e a de fora fica de quarentena.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.jobs import lembretes


async def _inserir(uid: str, desc: str, valor, venc, *, multa=None, juros=None,
                   status="prevista") -> str:
    tid = str(uuid.uuid4())
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "INSERT INTO financas.transacoes "
                "(id, usuario_id, tipo, descricao, valor_total, data_competencia, "
                " data_vencimento, multa_percentual, juros_mensal_percentual, status, origem) "
                "VALUES (:id,:uid,'despesa',:d,:v,:c,:venc,:m,:j,:s,'importacao_boleto')"
            ), {"id": tid, "uid": uid, "d": desc, "v": valor,
                "c": date.today().replace(day=1), "venc": venc,
                "m": multa, "j": juros, "s": status})
    finally:
        await eng.dispose()
    return tid


async def _inserir_fatura(uid: str, nome: str, valor, venc) -> str:
    """Cria um cartão do usuário + uma fatura não paga vencendo em `venc`."""
    cid = str(uuid.uuid4())
    fid = str(uuid.uuid4())
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "INSERT INTO financas.cartoes "
                "(id, usuario_id, nome, dia_fechamento, dia_vencimento, ativo) "
                "VALUES (:id,:uid,:n,20,10,true)"
            ), {"id": cid, "uid": uid, "n": nome})
            await conn.execute(text(
                "INSERT INTO financas.faturas "
                "(id, cartao_id, mes_referencia, valor_total, vencimento, status) "
                "VALUES (:id,:cid,:mr,:v,:venc,'fechada')"
            ), {"id": fid, "cid": cid, "mr": venc.replace(day=1), "v": valor, "venc": venc})
    finally:
        await eng.dispose()
    return fid


async def _inserir_orcamento_estourado(uid: str) -> None:
    """Cria um orçamento e uma despesa paga na mesma categoria que estoura o
    teto neste mês (pra disparar o alerta de orçamento no digest)."""
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            cat_id = (await conn.execute(
                text("SELECT id FROM financas.categorias LIMIT 1")
            )).scalar()
            await conn.execute(text(
                "INSERT INTO financas.transacoes "
                "(id, usuario_id, tipo, descricao, valor_total, data_competencia, "
                " categoria_id, status, origem) "
                "VALUES (:id,:uid,'despesa','Mercado',:v,:c,:cat,'paga','manual')"
            ), {"id": str(uuid.uuid4()), "uid": uid, "v": 900,
                "c": date.today().replace(day=1), "cat": cat_id})
            await conn.execute(text(
                "INSERT INTO financas.orcamentos "
                "(usuario_id, categoria_id, valor_mensal, ativo) "
                "VALUES (:uid,:cat,:v,true)"
            ), {"uid": uid, "cat": cat_id, "v": 800})
    finally:
        await eng.dispose()


async def _cleanup(uid: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tbl in ("orcamentos", "transacoes", "cartoes"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(uid)},
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — lembrete de vencimento (Telegram)")
    print("━" * 60)

    uid = str(uuid.uuid4())
    hoje = date.today()
    enviados: list[tuple[str, str]] = []

    # Mocks: captura o envio e fixa o mapa chat→usuário e o token.
    orig_send = lembretes.tg.send_message
    orig_mapa = lembretes.mapa_chat_usuario
    orig_token = settings.telegram_bot_token
    orig_enabled = settings.lembretes_enabled
    lembretes.tg.send_message = lambda chat, texto, *a, **k: enviados.append((chat, texto)) or {"ok": True}
    lembretes.mapa_chat_usuario = lambda: {"99999": uid}
    settings.telegram_bot_token = "fake-token"
    settings.lembretes_enabled = True

    try:
        asyncio.run(_inserir(uid, "Condomínio", 100, hoje - timedelta(days=10),
                             multa=2, juros=1))                       # vencida + juros
        asyncio.run(_inserir(uid, "Luz", 200, hoje + timedelta(days=2)))  # vence em breve
        asyncio.run(_inserir(uid, "Escola", 900, hoje + timedelta(days=30)))  # fora da janela
        asyncio.run(_inserir_fatura(uid, "Nubank", 1500, hoje + timedelta(days=3)))  # fatura na janela
        asyncio.run(_inserir_orcamento_estourado(uid))  # categoria a 112% do teto

        print("\n→ Test 1: envia digest com vencida + próxima + fatura, ignora a distante")
        r = asyncio.run(lembretes.enviar_lembretes(ref=hoje))
        assert r["enviados"] == 1, r
        assert len(enviados) == 1
        chat, texto = enviados[0]
        assert chat == "99999"
        assert "Condomínio" in texto and "Luz" in texto, texto
        assert "Escola" not in texto, "boleto fora da janela não devia entrar"
        assert "Vencidas" in texto and "Vencem em breve" in texto
        # vencida 10 dias: 100 + multa 2 + juros 0,33 = 102,33
        assert "R$102,33" in texto, texto
        assert "juros/multa" in texto
        # seção de faturas de cartão
        assert "Faturas de cartão" in texto and "Nubank" in texto and "R$1.500,00" in texto, texto
        # seção de orçamento estourado (900 de 800 = 112%)
        assert "Orçamentos no limite" in texto and "112%" in texto, texto
        print("   " + texto.replace("\n", " | "))

        print("\n→ Test 2: desligado → não envia")
        settings.lembretes_enabled = False
        enviados.clear()
        r2 = asyncio.run(lembretes.enviar_lembretes(ref=hoje))
        assert r2["enviados"] == 0 and enviados == [], r2
        print("   ok, respeitou o desligado")

    finally:
        lembretes.tg.send_message = orig_send
        lembretes.mapa_chat_usuario = orig_mapa
        settings.telegram_bot_token = orig_token
        settings.lembretes_enabled = orig_enabled
        asyncio.run(_cleanup(uid))

    print("\n" + "━" * 60)
    print("TUDO OK — lembrete de vencimento funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
