from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.db.models import Categoria
from app.db.session import dispose_engine, get_session


# Espelha o SEED da migration 3fe4d1c4a738.
ESPERADO: dict[str, set[str]] = {
    "Condomínio": {
        "Taxa de condomínio",
        "Consumo de gás",
        "Fundo de reserva",
        "Consumo de água",
        "Consumo de luz (área comum)",
        "Água área comum",
        "Reforma infiltração (parcelada)",
    },
    "Moradia": {"Aluguel", "Luz (Enel)"},
    "Transporte": {"Gasolina"},
    "Alimentação": {"Mercado"},
    "Dívidas": {"Empréstimo", "Cartão de crédito", "Acordos"},
}


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 3 (seed de categorias)")
    print("━" * 60)
    print("  (requer 'alembic upgrade head' aplicado)")

    async with get_session() as session:
        # ── Cada pai existe, é único e tem exatamente os filhos do seed ──
        for pai_nome, filhos_esperados in ESPERADO.items():
            print(f"\n→ {pai_nome}")
            n_pais = await session.scalar(
                select(func.count())
                .select_from(Categoria)
                .where(Categoria.nome == pai_nome)
                .where(Categoria.categoria_pai_id.is_(None))
            )
            assert n_pais == 1, f"esperava 1 '{pai_nome}' raiz, achei {n_pais}"

            pai = await session.scalar(
                select(Categoria)
                .where(Categoria.nome == pai_nome)
                .where(Categoria.categoria_pai_id.is_(None))
            )
            filhos = await session.scalars(
                select(Categoria).where(Categoria.categoria_pai_id == pai.id)
            )
            nomes = {f.nome for f in filhos}
            assert nomes == filhos_esperados, (
                f"{pai_nome}: esperava {filhos_esperados}, achei {nomes}"
            )
            print(f"   ok — {len(nomes)} subverbas")

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 3 funcionando!")
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
