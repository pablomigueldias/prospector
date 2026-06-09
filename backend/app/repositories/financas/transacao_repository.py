from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.financas.categoria import Categoria
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

    # ── Agregados do resumo do mês (filtro por data_competencia) ──────
    async def total_por_tipo(
        self, usuario_id: uuid.UUID, inicio: date, proximo_mes: date
    ) -> Dict[str, Decimal]:
        stmt = (
            select(
                Transacao.tipo,
                func.coalesce(func.sum(Transacao.valor_total), 0),
            )
            .where(
                Transacao.usuario_id == usuario_id,
                Transacao.data_competencia >= inicio,
                Transacao.data_competencia < proximo_mes,
            )
            .group_by(Transacao.tipo)
        )
        rows = await self.session.execute(stmt)
        return {tipo: Decimal(total) for tipo, total in rows.all()}

    async def despesas_por_categoria(
        self, usuario_id: uuid.UUID, inicio: date, proximo_mes: date
    ) -> List[Tuple[Optional[uuid.UUID], Optional[str], Decimal]]:
        """(categoria_id, categoria_nome, total) das despesas do mês,
        maior total primeiro. categoria_id null = sem categoria."""
        soma = func.coalesce(func.sum(Transacao.valor_total), 0)
        stmt = (
            select(Transacao.categoria_id, Categoria.nome, soma.label("total"))
            .select_from(Transacao)
            .outerjoin(Categoria, Categoria.id == Transacao.categoria_id)
            .where(
                Transacao.usuario_id == usuario_id,
                Transacao.tipo == "despesa",
                Transacao.data_competencia >= inicio,
                Transacao.data_competencia < proximo_mes,
            )
            .group_by(Transacao.categoria_id, Categoria.nome)
            .order_by(soma.desc())
        )
        rows = await self.session.execute(stmt)
        return [(cid, nome, Decimal(total)) for cid, nome, total in rows.all()]
