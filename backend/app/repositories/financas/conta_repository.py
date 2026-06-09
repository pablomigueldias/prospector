from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.financas.conta import Conta


class ContaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dados: dict) -> Conta:
        conta = Conta(**dados)
        self.session.add(conta)
        await self.session.commit()
        await self.session.refresh(conta)
        return conta

    async def get(self, conta_id: uuid.UUID) -> Optional[Conta]:
        return await self.session.get(Conta, conta_id)

    async def listar(
        self, usuario_id: uuid.UUID, *, apenas_ativas: bool = False
    ) -> List[Conta]:
        stmt = (
            select(Conta)
            .where(Conta.usuario_id == usuario_id)
            .order_by(Conta.nome)
        )
        if apenas_ativas:
            stmt = stmt.where(Conta.ativa.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, conta_id: uuid.UUID, dados: dict) -> Optional[Conta]:
        conta = await self.get(conta_id)
        if conta is None:
            return None
        for campo, valor in dados.items():
            setattr(conta, campo, valor)
        await self.session.commit()
        await self.session.refresh(conta)
        return conta

    async def delete(self, conta_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(Conta).where(Conta.id == conta_id)
        )
        await self.session.commit()
        return result.rowcount > 0
