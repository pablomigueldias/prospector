"""S2 — Observabilidade & Custos de IA.

Agrega a tabela `ai_calls` pra a tela: totais do período, quebra por agente,
série diária (pra os gráficos) e as últimas chamadas. Leitura pura, no loop do
request (usa `get_session`, não o `bridge_session` de escrita).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import case, desc, func, select

from app.db.models.ai_call import AiCall
from app.db.session import get_session


def _f(v: Any) -> float:
    """Numeric/Decimal/None → float."""
    return float(v) if v is not None else 0.0


def _taxa_erro(chamadas: int, falhas: int) -> float:
    return round(falhas / chamadas, 4) if chamadas else 0.0


async def resumo(dias: int = 30) -> dict:
    dias = max(1, min(dias, 365))
    cutoff = datetime.now() - timedelta(days=dias)

    async with get_session() as session:
        # ── Totais do período ──
        chamadas = (
            await session.scalar(
                select(func.count(AiCall.id)).where(AiCall.created_at >= cutoff)
            )
        ) or 0
        falhas = (
            await session.scalar(
                select(func.count(AiCall.id)).where(
                    AiCall.created_at >= cutoff, AiCall.sucesso.is_(False)
                )
            )
        ) or 0
        tokens = await session.scalar(
            select(func.coalesce(func.sum(AiCall.tokens_total), 0)).where(
                AiCall.created_at >= cutoff
            )
        )
        custo = await session.scalar(
            select(func.coalesce(func.sum(AiCall.custo_usd), 0)).where(
                AiCall.created_at >= cutoff
            )
        )
        lat_media = await session.scalar(
            select(func.avg(AiCall.latencia_ms)).where(AiCall.created_at >= cutoff)
        )

        # ── Por agente ──
        rows_ag = (
            await session.execute(
                select(
                    AiCall.agente,
                    func.count(AiCall.id),
                    func.coalesce(
                        func.sum(case((AiCall.sucesso.is_(False), 1), else_=0)), 0
                    ),
                    func.coalesce(func.sum(AiCall.tokens_total), 0),
                    func.coalesce(func.sum(AiCall.custo_usd), 0),
                    func.avg(AiCall.latencia_ms),
                )
                .where(AiCall.created_at >= cutoff)
                .group_by(AiCall.agente)
                .order_by(desc(func.coalesce(func.sum(AiCall.custo_usd), 0)))
            )
        ).all()
        por_agente = [
            {
                "agente": ag or "—",
                "chamadas": int(ch),
                "falhas": int(fa or 0),
                "taxa_erro": _taxa_erro(int(ch), int(fa or 0)),
                "tokens": int(tk or 0),
                "custo_usd": round(_f(cu), 6),
                "latencia_media_ms": round(_f(lm)) if lm is not None else None,
            }
            for ag, ch, fa, tk, cu, lm in rows_ag
        ]

        # ── Série diária (pros gráficos) ──
        dia = func.date(AiCall.created_at).label("dia")
        rows_dia = (
            await session.execute(
                select(
                    dia,
                    func.count(AiCall.id),
                    func.coalesce(func.sum(AiCall.tokens_total), 0),
                    func.coalesce(func.sum(AiCall.custo_usd), 0),
                )
                .where(AiCall.created_at >= cutoff)
                .group_by(dia)
                .order_by(dia)
            )
        ).all()
        por_dia = [
            {
                "dia": str(d),
                "chamadas": int(ch),
                "tokens": int(tk or 0),
                "custo_usd": round(_f(cu), 6),
            }
            for d, ch, tk, cu in rows_dia
        ]

        # ── Últimas chamadas ──
        ultimas_rows = (
            await session.execute(
                select(AiCall)
                .order_by(desc(AiCall.created_at))
                .limit(20)
            )
        ).scalars().all()
        ultimas = [
            {
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "agente": c.agente,
                "operacao": c.operacao,
                "provider": c.provider,
                "modelo": c.modelo,
                "tokens_total": c.tokens_total,
                "custo_usd": round(_f(c.custo_usd), 6),
                "latencia_ms": c.latencia_ms,
                "sucesso": c.sucesso,
                "error_message": c.error_message,
            }
            for c in ultimas_rows
        ]

    return {
        "periodo_dias": dias,
        "totais": {
            "chamadas": int(chamadas),
            "falhas": int(falhas),
            "taxa_erro": _taxa_erro(int(chamadas), int(falhas)),
            "tokens": int(tokens or 0),
            "custo_usd": round(_f(custo), 6),
            "latencia_media_ms": round(_f(lat_media)) if lat_media is not None else None,
        },
        "por_agente": por_agente,
        "por_dia": por_dia,
        "ultimas": ultimas,
    }
