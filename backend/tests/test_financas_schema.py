from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import dispose_engine, get_session


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 1 (schema financas + Alembic)")
    print("━" * 60)

    # ── O schema 'financas' precisa existir (criado pela migration) ──
    print("\n→ Test 1: schema 'financas' existe")
    async with get_session() as session:
        existe = await session.scalar(
            text(
                "SELECT 1 FROM information_schema.schemata "
                "WHERE schema_name = 'financas'"
            )
        )
        assert existe == 1, (
            "schema 'financas' não encontrado — rode 'alembic upgrade head'"
        )
        print("   schema 'financas' presente")

    # ── O public continua intocado (a migration não mexeu nele) ──────
    print("\n→ Test 2: schema 'public' segue existindo")
    async with get_session() as session:
        publico = await session.scalar(
            text(
                "SELECT 1 FROM information_schema.schemata "
                "WHERE schema_name = 'public'"
            )
        )
        assert publico == 1
        print("   schema 'public' intacto")

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 1 funcionando!")
    print("━" * 60)


async def _run_with_cleanup() -> None:
    try:
        await smoke_test()
    finally:
        await dispose_engine()


def main() -> None:
    asyncio.run(_run_with_cleanup())


if __name__ == "__main__":
    main()
