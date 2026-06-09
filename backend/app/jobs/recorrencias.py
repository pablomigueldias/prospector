"""Job das recorrências (rodar diariamente).

Duas tarefas:
1. gerar as transações *previstas* do mês a partir das recorrências ativas
   (idempotente: uma prevista por recorrência por mês);
2. marcar como *atrasada* toda prevista cujo vencimento já passou.

Em produção é chamado por cron; também dá pra disparar via endpoint
POST /api/financas/recorrencias/processar.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.services.financas.compra_service import dia_valido
from app.db.models.financas.recorrencia import Recorrencia
from app.db.models.financas.transacao import Transacao
from app.db.session import get_session


async def _gerar_previstas(
    session: AsyncSession, usuario_id: Optional[uuid.UUID], ref: date
) -> int:
    mes_ref = date(ref.year, ref.month, 1)

    stmt = select(Recorrencia).where(Recorrencia.ativa.is_(True))
    if usuario_id is not None:
        stmt = stmt.where(Recorrencia.usuario_id == usuario_id)
    recorrencias = (await session.execute(stmt)).scalars().all()

    criadas = 0
    for r in recorrencias:
        # idempotência: já existe uma prevista desta recorrência neste mês?
        existe = await session.scalar(
            select(func.count())
            .select_from(Transacao)
            .where(
                Transacao.recorrencia_id == r.id,
                Transacao.data_competencia == mes_ref,
            )
        )
        if existe:
            continue

        venc = date(ref.year, ref.month, dia_valido(ref.year, ref.month, r.dia_vencimento))
        session.add(Transacao(
            usuario_id=r.usuario_id,
            tipo=r.tipo,
            descricao=r.descricao,
            valor_total=r.valor_estimado,
            data_competencia=mes_ref,
            data_vencimento=venc,
            status="prevista",
            origem="recorrencia",
            categoria_id=r.categoria_id,
            recorrencia_id=r.id,
        ))
        criadas += 1
    return criadas


async def _marcar_atrasadas(
    session: AsyncSession, usuario_id: Optional[uuid.UUID], ref: date
) -> int:
    stmt = (
        update(Transacao)
        .where(
            Transacao.status == "prevista",
            Transacao.data_vencimento.is_not(None),
            Transacao.data_vencimento < ref,
        )
        .values(status="atrasada")
    )
    if usuario_id is not None:
        stmt = stmt.where(Transacao.usuario_id == usuario_id)
    result = await session.execute(stmt)
    return result.rowcount or 0


async def processar_recorrencias(
    usuario_id: Optional[uuid.UUID] = None, ref: Optional[date] = None
) -> dict:
    ref = ref or date.today()
    async with get_session() as session:
        criadas = await _gerar_previstas(session, usuario_id, ref)
        # flush pra que o UPDATE de atrasadas enxergue as previstas recém-criadas
        # (autoflush está desligado na sessão).
        await session.flush()
        atrasadas = await _marcar_atrasadas(session, usuario_id, ref)
        await session.commit()
    return {"previstas_criadas": criadas, "marcadas_atrasadas": atrasadas}
