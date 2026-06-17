from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.financas.categoria import Categoria


class CategoriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dados: dict) -> Categoria:
        categoria = Categoria(**dados)
        self.session.add(categoria)
        await self.session.commit()
        await self.session.refresh(categoria)
        return categoria

    async def get(self, categoria_id: uuid.UUID) -> Categoria | None:
        return await self.session.get(Categoria, categoria_id)

    async def listar_todas(self) -> list[Categoria]:
        """Todas as categorias, flat (a árvore é montada no service)."""
        stmt = select(Categoria).order_by(Categoria.nome)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, categoria_id: uuid.UUID, dados: dict
    ) -> Categoria | None:
        categoria = await self.get(categoria_id)
        if categoria is None:
            return None
        for campo, valor in dados.items():
            setattr(categoria, campo, valor)
        await self.session.commit()
        await self.session.refresh(categoria)
        return categoria

    async def delete(self, categoria_id: uuid.UUID) -> bool:
        # Filhos somem por CASCADE (FK ondelete='CASCADE').
        result = await self.session.execute(
            delete(Categoria).where(Categoria.id == categoria_id)
        )
        await self.session.commit()
        return result.rowcount > 0
