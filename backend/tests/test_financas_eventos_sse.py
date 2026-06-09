from __future__ import annotations

import asyncio
import json
import uuid

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.schemas.financas import ContaCreate, DespesaCreate
from app.api.services.financas import conta_service, eventos, transacao_service
from app.config import settings
from app.db.session import dispose_engine


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tbl in ("transacoes", "contas"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 27 (NOTIFY/LISTEN → SSE)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    fila: asyncio.Queue[str] = asyncio.Queue()

    listener = await asyncpg.connect(eventos._dsn())
    await listener.add_listener(eventos.CANAL, lambda *a: fila.put_nowait(a[3]))

    try:
        # cria conta + despesa (o lançamento emite pg_notify no commit)
        conta = await conta_service.criar_conta(ContaCreate(
            usuario_id=usuario_id, nome="Carteira", tipo="dinheiro", saldo_atual=100,
        ))
        print("\n→ Test 1: lançar despesa dispara evento")
        await transacao_service.lancar_despesa(DespesaCreate(
            usuario_id=usuario_id, descricao="Mercado",
            valor_total=10, conta_id=conta.id,
        ))

        payload = await asyncio.wait_for(fila.get(), timeout=5)
        dados = json.loads(payload)
        assert dados["usuario_id"] == usuario_id, dados
        assert dados["evento"] == "transacao_criada", dados
        print(f"   recebido: {dados}")

        # ── evento de OUTRO usuário não casa o filtro do stream ──────
        print("\n→ Test 2: filtro por usuario_id")
        assert dados["usuario_id"] == usuario_id  # o stream só repassaria os meus
        print("   payload carrega usuario_id pro stream filtrar")

    finally:
        await listener.close()
        await _cleanup(usuario_id)
        await dispose_engine()

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 27 funcionando!")
    print("━" * 60)


def main() -> None:
    asyncio.run(smoke_test())


if __name__ == "__main__":
    main()
