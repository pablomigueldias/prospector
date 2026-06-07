from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.financas.transacao import Transacao


class TransacaoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, transacao: Transacao) -> None:
        """Adiciona à sessão (commit/flush fica a cargo do service, que também
        ajusta o saldo da conta no mesmo commit)."""
        self.session.add(transacao)

    async def get(self, transacao_id: uuid.UUID) -> Optional[Transacao]:
        stmt = (
            select(Transacao)
            .options(
                selectinload(Transacao.itens),
                selectinload(Transacao.pagamentos),
            )
            .where(Transacao.id == transacao_id)
        )
        return await self.session.scalar(stmt)
