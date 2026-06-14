"""Pagar o mês — quita a fatura do cartão + os boletos/contas a pagar do mês
numa tacada. Orquestra os serviços que já existem (pagar_transacao e
pagar_fatura), cada item debitando a conta escolhida."""
from __future__ import annotations

import calendar
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select

from app.api.schemas.financas import (
    PagamentoMesItem,
    PagamentoMesPreview,
    PagamentoMesRequest,
    PagamentoMesResultado,
    PagarFaturaRequest,
)
from app.api.services.financas import (
    cartao_service,
    encargos as encargos_service,
    transacao_service,
)
from app.db.models.financas.cartao import Cartao
from app.db.models.financas.conta import Conta
from app.db.models.financas.fatura import Fatura
from app.db.models.financas.transacao import Transacao
from app.db.session import get_session
from app.repositories.financas.transacao_repository import TransacaoRepository


class PagamentoMesError(Exception):
    """Erro de negócio — vira HTTP 400 no router."""


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise PagamentoMesError(f"{campo} inválido: {valor!r}")


def _parse_competencia(s: Optional[str]) -> Tuple[int, int]:
    if not s:
        hoje = date.today()
        return hoje.year, hoje.month
    try:
        ano, mes = s.split("-")
        ano, mes = int(ano), int(mes)
        if not (1 <= mes <= 12):
            raise ValueError
        return ano, mes
    except (ValueError, AttributeError):
        raise PagamentoMesError(f"Competência inválida: {s!r} (use YYYY-MM).")


async def preview_mes(
    usuario_id: str, competencia: Optional[str] = None
) -> PagamentoMesPreview:
    """Tudo que está a pagar com vencimento até o fim do mês: boletos/contas a
    pagar (com encargos até hoje) + faturas de cartão em aberto."""
    uid = _uuid(usuario_id, campo="usuario_id")
    ano, mes = _parse_competencia(competencia)
    fim_mes = date(ano, mes, calendar.monthrange(ano, mes)[1])
    hoje = date.today()

    itens: List[PagamentoMesItem] = []
    total = Decimal("0")

    async with get_session() as session:
        repo = TransacaoRepository(session)

        boletos = (await session.scalars(
            select(Transacao).where(
                Transacao.usuario_id == uid,
                Transacao.tipo == "despesa",
                Transacao.status.in_(["prevista", "atrasada"]),
                Transacao.data_vencimento.is_not(None),
                Transacao.data_vencimento <= fim_mes,
            ).order_by(Transacao.data_vencimento.asc())
        )).all()

        for t in boletos:
            enc = encargos_service.calcular_encargos(
                t.valor_total, t.data_vencimento, t.multa_percentual,
                t.juros_mensal_percentual, hoje,
            )
            valor = Decimal(t.valor_total) + enc
            conta_id = await repo.ultima_conta_por_descricao(uid, t.descricao)
            conta_nome = None
            if conta_id is not None:
                conta = await session.get(Conta, conta_id)
                conta_nome = conta.nome if conta else None
            total += valor
            itens.append(PagamentoMesItem(
                tipo="boleto", id=str(t.id), descricao=t.descricao,
                valor=valor, vencimento=t.data_vencimento,
                conta_sugerida_id=str(conta_id) if conta_id else None,
                conta_sugerida_nome=conta_nome,
            ))

        faturas = (await session.execute(
            select(Fatura, Cartao.nome)
            .join(Cartao, Cartao.id == Fatura.cartao_id)
            .where(
                Cartao.usuario_id == uid,
                Fatura.status != "paga",
                Fatura.valor_total > 0,
                Fatura.vencimento <= fim_mes,
            ).order_by(Fatura.vencimento.asc())
        )).all()

        for f, nome in faturas:
            total += Decimal(f.valor_total)
            itens.append(PagamentoMesItem(
                tipo="fatura", id=str(f.id),
                descricao=f"Fatura {nome}",
                valor=Decimal(f.valor_total), vencimento=f.vencimento,
            ))

    return PagamentoMesPreview(
        competencia=f"{ano:04d}-{mes:02d}", itens=itens, total=total,
    )


async def pagar_mes(
    usuario_id: str, payload: PagamentoMesRequest
) -> PagamentoMesResultado:
    """Paga cada item (boleto via pagar_transacao, fatura via pagar_fatura).
    Erro num item não derruba os outros — volta na lista de falhas."""
    quando = payload.data_pagamento or date.today()
    pagos = 0
    total = Decimal("0")
    falhas: List[str] = []

    for item in payload.itens:
        try:
            if item.tipo == "fatura":
                r = await cartao_service.pagar_fatura(
                    item.id,
                    PagarFaturaRequest(conta_id=item.conta_id, data_pagamento=quando),
                    usuario_id_sessao=usuario_id,
                )
                total += Decimal(r.valor_total)
            elif item.tipo == "boleto":
                r = await transacao_service.pagar_transacao(
                    item.id, conta_id=item.conta_id, data_pagamento=quando,
                    usuario_id_sessao=usuario_id,
                )
                total += Decimal(r.valor_total)
            else:
                falhas.append(f"{item.id}: tipo inválido {item.tipo!r}")
                continue
            pagos += 1
        except Exception as e:  # não derruba o lote por causa de um item
            falhas.append(f"{item.tipo} {item.id}: {e}")

    return PagamentoMesResultado(pagos=pagos, total_pago=total, falhas=falhas)
