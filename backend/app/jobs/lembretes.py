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
from app.api.services.financas import orcamento_service
from app.api.services.financas.bot_service import mapa_chat_usuario
from app.config import settings
from app.db.models.financas.cartao import Cartao
from app.db.models.financas.fatura import Fatura
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


async def _faturas_a_vencer(
    session: AsyncSession, usuario_id: uuid.UUID, limite: date
) -> List[tuple]:
    """(Fatura, nome do cartão) das faturas não pagas que vencem até `limite`."""
    stmt = (
        select(Fatura, Cartao.nome)
        .join(Cartao, Cartao.id == Fatura.cartao_id)
        .where(
            Cartao.usuario_id == usuario_id,
            Fatura.status != "paga",
            Fatura.valor_total > 0,
            Fatura.vencimento <= limite,
        )
        .order_by(Fatura.vencimento.asc())
    )
    return list((await session.execute(stmt)).all())


def _montar_texto_faturas(linhas: List[tuple], hoje: date) -> Optional[str]:
    if not linhas:
        return None
    out: List[str] = []
    total = Decimal("0")
    for f, nome in linhas:
        total += Decimal(f.valor_total)
        venceu = f.vencimento < hoje
        out.append(
            f"• {nome} — {_brl(f.valor_total)} "
            f"({'venceu' if venceu else 'vence'} {_dm(f.vencimento)})"
        )
    return (
        "💳 <b>Faturas de cartão</b>\n"
        + "\n".join(out)
        + f"\n<b>Total: {_brl(total)}</b>"
    )


async def _texto_orcamento(usuario_id: str, ref: date) -> Optional[str]:
    """Categorias que já passaram de `orcamento_alerta_pct` do teto no mês."""
    pct_alerta = max(0, settings.orcamento_alerta_pct)
    comp = f"{ref.year:04d}-{ref.month:02d}"
    status = await orcamento_service.status_do_mes(usuario_id, comp)
    quentes = [i for i in status.items if i.percentual >= pct_alerta]
    if not quentes:
        return None
    linhas = []
    for i in sorted(quentes, key=lambda x: x.percentual, reverse=True):
        estouro = "🔴" if i.percentual >= 100 else "🟠"
        linhas.append(
            f"{estouro} {i.categoria_nome or 'categoria'} — "
            f"{_brl(i.consumido)} de {_brl(i.valor_mensal)} ({round(i.percentual)}%)"
        )
    return "📊 <b>Orçamentos no limite</b>\n" + "\n".join(linhas)


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
            uid = uuid.UUID(usuario_id)
            itens = await _contas_a_pagar(session, uid, limite)
            faturas = await _faturas_a_vencer(session, uid, limite)
            orcamento = await _texto_orcamento(usuario_id, hoje)
            blocos = [
                b for b in (
                    _montar_texto(itens, hoje),
                    _montar_texto_faturas(faturas, hoje),
                    orcamento,
                ) if b
            ]
            if not blocos:
                continue
            texto = "\n\n".join(blocos)
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
