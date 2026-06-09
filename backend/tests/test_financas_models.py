from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Categoria, Conta
from app.db.session import dispose_engine, get_session


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 2 (contas + categorias)")
    print("━" * 60)

    usuario_id = uuid.uuid4()  # multi-tenant leve: um "perfil" qualquer

    conta_id = None
    pai_id = None
    try:
        # ── 1. Conta: saldo nasce em 0, ativa por padrão ──────────────
        print("\n→ Test 1: cria conta (defaults de saldo/ativa)")
        async with get_session() as session:
            conta = Conta(usuario_id=usuario_id, nome="Nubank", tipo="corrente")
            session.add(conta)
            await session.commit()
            await session.refresh(conta)
            conta_id = conta.id
            assert isinstance(conta.id, uuid.UUID)
            assert conta.saldo_atual == Decimal("0.00"), conta.saldo_atual
            assert conta.ativa is True
            assert conta.created_at is not None
            print(f"   conta criada id={conta_id} saldo={conta.saldo_atual} ativa={conta.ativa}")

        # ── 2. Categoria hierárquica (Condomínio → Consumo de gás) ────
        print("\n→ Test 2: categoria pai + filho (auto-relacionamento)")
        async with get_session() as session:
            pai = Categoria(nome="Condomínio")
            session.add(pai)
            await session.commit()
            await session.refresh(pai)
            pai_id = pai.id

            filho = Categoria(nome="Consumo de gás", categoria_pai_id=pai_id)
            session.add(filho)
            await session.commit()
            await session.refresh(filho)
            filho_id = filho.id
            print(f"   pai={pai_id} filho={filho_id}")

        # ── 3. Navega pai ↔ filhos pelos relationships (eager) ────────
        print("\n→ Test 3: relationships pai/filhos")
        async with get_session() as session:
            pai = await session.scalar(
                select(Categoria)
                .options(selectinload(Categoria.filhos))
                .where(Categoria.id == pai_id)
            )
            assert pai is not None
            nomes_filhos = [f.nome for f in pai.filhos]
            assert "Consumo de gás" in nomes_filhos, nomes_filhos

            filho = await session.scalar(
                select(Categoria)
                .options(selectinload(Categoria.pai))
                .where(Categoria.id == filho_id)
            )
            assert filho.pai is not None
            assert filho.pai.nome == "Condomínio"
            print(f"   pai.filhos={nomes_filhos} ; filho.pai={filho.pai.nome!r}")

        # ── 4. CASCADE: deletar o pai leva o filho junto ──────────────
        print("\n→ Test 4: delete em cascata (pai → filhos)")
        async with get_session() as session:
            pai = await session.scalar(
                select(Categoria)
                .options(selectinload(Categoria.filhos))
                .where(Categoria.id == pai_id)
            )
            await session.delete(pai)
            await session.commit()
        pai_id = None
        async with get_session() as session:
            sumiu = await session.scalar(
                select(Categoria).where(Categoria.id == filho_id)
            )
            assert sumiu is None, "filho deveria ter sumido junto com o pai"
            print("   pai e filho removidos (CASCADE)")

    finally:
        # ── Limpeza (mesmo se um assert falhar no meio) ───────────────
        async with get_session() as session:
            if conta_id:
                c = await session.scalar(select(Conta).where(Conta.id == conta_id))
                if c:
                    await session.delete(c)
            if pai_id:
                p = await session.scalar(
                    select(Categoria)
                    .options(selectinload(Categoria.filhos))
                    .where(Categoria.id == pai_id)
                )
                if p:
                    await session.delete(p)
            await session.commit()

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 2 funcionando!")
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
