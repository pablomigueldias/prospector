"""Lembrete de vencimento das contas a pagar (boletos) + rotina diária.

Roda 1x/dia pelo agendador (APScheduler no container da API). Manda um digest
no Telegram com o que está vencido e o que vence nos próximos dias, já com os
juros/multa projetados. A `rotina_diaria` também processa as recorrências
(gera previstas + marca atrasadas), matando o "cron das recorrências".
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.services.financas import encargos as encargos_service
from app.api.services.financas.bot_service import mapa_chat_usuario
from app.config import settings
from app.db.models.financas.transacao import Transacao
from app.db.session import get_session
from app.integrations import telegram as tg
from app.jobs.recorrencias import processar_recorrencias
from app.utils.logger import get_logger

logger = get_logger()


def _brl(v) -> str:
    """1107.52 → 'R$1.107,52'."""
    s = f"{Decimal(v):,.2f}"
    return "R$" + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _dm(d: date) -> str:
    return d.strftime("%d/%m")


async def _contas_a_pagar(
    session: AsyncSession, usuario_id: uuid.UUID, limite: date
) -> List[Transacao]:
    stmt = (
        select(Transacao)
        .where(
            Transacao.usuario_id == usuario_id,
            Transacao.tipo == "despesa",
            Transacao.status.in_(["prevista", "atrasada"]),
            Transacao.data_vencimento.is_not(None),
            Transacao.data_vencimento <= limite,
        )
        .order_by(Transacao.data_vencimento.asc())
    )
    return list((await session.scalars(stmt)).all())


def _montar_texto(itens: List[Transacao], hoje: date) -> Optional[str]:
    if not itens:
        return None
    vencidas: List[str] = []
    proximas: List[str] = []
    total = Decimal("0")
    for t in itens:
        enc = encargos_service.calcular_encargos(
            t.valor_total, t.data_vencimento, t.multa_percentual,
            t.juros_mensal_percentual, hoje,
        )
        valor = Decimal(t.valor_total) + enc
        total += valor
        extra = f" +{_brl(enc)} juros/multa" if enc > 0 else ""
        venceu = t.data_vencimento < hoje
        linha = (
            f"• {t.descricao} — {_brl(valor)} "
            f"({'venceu' if venceu else 'vence'} {_dm(t.data_vencimento)}{extra})"
        )
        (vencidas if venceu else proximas).append(linha)

    partes = ["🔔 <b>Contas a pagar</b>"]
    if vencidas:
        partes.append("\n⚠️ <b>Vencidas</b>\n" + "\n".join(vencidas))
    if proximas:
        partes.append("\n📅 <b>Vencem em breve</b>\n" + "\n".join(proximas))
    partes.append(f"\n<b>Total: {_brl(total)}</b>")
    return "\n".join(partes)


async def enviar_lembretes(ref: Optional[date] = None) -> dict:
    """Manda o digest de contas a pagar pra cada chat configurado no Telegram.
    Pablo e Monique compartilham o usuario_id → ambos recebem (carteira junta)."""
    if not settings.lembretes_enabled:
        return {"enviados": 0, "motivo": "desligado"}
    hoje = ref or date.today()
    limite = hoje + timedelta(days=max(0, settings.lembretes_dias_antes))
    mapa = mapa_chat_usuario()
    if not mapa or not settings.telegram_bot_token:
        return {"enviados": 0, "motivo": "sem telegram configurado"}

    enviados = 0
    async with get_session() as session:
        for chat_id, usuario_id in mapa.items():
            itens = await _contas_a_pagar(session, uuid.UUID(usuario_id), limite)
            texto = _montar_texto(itens, hoje)
            if not texto:
                continue
            try:
                await asyncio.to_thread(tg.send_message, chat_id, texto)
                enviados += 1
            except Exception as e:  # nunca derruba a rotina por causa de envio
                logger.warning("Falha ao enviar lembrete pro chat %s: %s", chat_id, e)
    return {"enviados": enviados}


async def rotina_diaria() -> dict:
    """O que o agendador chama 1x/dia: recorrências + lembretes."""
    rec = await processar_recorrencias()
    lemb = await enviar_lembretes()
    logger.info("Rotina diária — recorrências=%s lembretes=%s", rec, lemb)
    return {"recorrencias": rec, "lembretes": lemb}
