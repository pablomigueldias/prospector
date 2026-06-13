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
from app.db.models.financas.transacao_pagamento import TransacaoPagamento


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

    async def buscar_duplicado(
        self,
        usuario_id: uuid.UUID,
        *,
        linha_digitavel: Optional[str] = None,
        beneficiario: Optional[str] = None,
        vencimento: Optional[date] = None,
        valor: Optional[Decimal] = None,
    ) -> Optional[Transacao]:
        """Acha um boleto já lançado que pareça o mesmo. Prioriza a linha
        digitável (chave forte); senão, cai no trio beneficiário+vencimento+
        valor de um boleto importado. Retorna a transação existente ou None."""
        cond = [Transacao.usuario_id == usuario_id]
        if linha_digitavel:
            cond.append(Transacao.linha_digitavel == linha_digitavel)
        elif beneficiario and vencimento is not None and valor is not None:
            cond.append(Transacao.origem == "importacao_boleto")
            cond.append(Transacao.descricao == beneficiario)
            cond.append(Transacao.data_vencimento == vencimento)
            cond.append(Transacao.valor_total == valor)
        else:
            return None
        stmt = (
            select(Transacao)
            .options(selectinload(Transacao.pagamentos))
            .where(*cond)
            .order_by(Transacao.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def ultima_categoria_por_descricao(
        self, usuario_id: uuid.UUID, descricao: Optional[str]
    ) -> Optional[uuid.UUID]:
        """Categoria usada na transação mais recente com essa descrição
        (beneficiário). Serve pra auto-categorizar boletos recorrentes."""
        if not descricao or not descricao.strip():
            return None
        stmt = (
            select(Transacao.categoria_id)
            .where(
                Transacao.usuario_id == usuario_id,
                func.lower(Transacao.descricao) == descricao.strip().lower(),
                Transacao.categoria_id.is_not(None),
            )
            .order_by(Transacao.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    # ── Listagem filtrável (para a tela de transações no dashboard) ───
    async def listar(
        self,
        usuario_id: uuid.UUID,
        *,
        inicio: Optional[date] = None,
        proximo_mes: Optional[date] = None,
        conta_id: Optional[uuid.UUID] = None,
        categoria_id: Optional[uuid.UUID] = None,
        tipo: Optional[str] = None,
        status: Optional[List[str]] = None,
        busca: Optional[str] = None,
        por_vencimento: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Transacao], int]:
        """Transações do usuário aplicando os filtros, mais novas primeiro.
        Retorna ``(itens, total)`` — total ignora limit/offset (paginação).

        ``status`` filtra por uma lista (ex.: previstas+atrasadas = a pagar).
        ``por_vencimento`` ordena pela data de vencimento crescente (vencidas
        primeiro) — usado no painel "A pagar"."""
        cond = [Transacao.usuario_id == usuario_id]
        if inicio is not None:
            cond.append(Transacao.data_competencia >= inicio)
        if proximo_mes is not None:
            cond.append(Transacao.data_competencia < proximo_mes)
        if categoria_id is not None:
            cond.append(Transacao.categoria_id == categoria_id)
        if tipo is not None:
            cond.append(Transacao.tipo == tipo)
        if status:
            cond.append(Transacao.status.in_(status))
        if busca:
            cond.append(Transacao.descricao.ilike(f"%{busca}%"))
        if conta_id is not None:
            sub = select(TransacaoPagamento.transacao_id).where(
                TransacaoPagamento.conta_id == conta_id
            )
            cond.append(Transacao.id.in_(sub))

        total = await self.session.scalar(
            select(func.count()).select_from(
                select(Transacao.id).where(*cond).subquery()
            )
        )
        ordem = (
            [Transacao.data_vencimento.asc().nullslast(),
             Transacao.data_competencia.desc()]
            if por_vencimento
            else [Transacao.data_competencia.desc(), Transacao.created_at.desc()]
        )
        stmt = (
            select(Transacao)
            .options(selectinload(Transacao.pagamentos))
            .where(*cond)
            .order_by(*ordem)
            .limit(limit)
            .offset(offset)
        )
        itens = list((await self.session.scalars(stmt)).all())
        return itens, int(total or 0)

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

    async def totais_por_mes(
        self, usuario_id: uuid.UUID, inicio: date, proximo_mes: date
    ) -> List[Tuple[int, int, str, Decimal]]:
        """(ano, mes, tipo, total) por mês de competência no intervalo, pra
        montar a série do relatório. Meses sem lançamento não aparecem (o
        service preenche zero)."""
        ano = func.extract("year", Transacao.data_competencia)
        mes = func.extract("month", Transacao.data_competencia)
        stmt = (
            select(
                ano.label("ano"),
                mes.label("mes"),
                Transacao.tipo,
                func.coalesce(func.sum(Transacao.valor_total), 0).label("total"),
            )
            .where(
                Transacao.usuario_id == usuario_id,
                Transacao.data_competencia >= inicio,
                Transacao.data_competencia < proximo_mes,
            )
            .group_by("ano", "mes", Transacao.tipo)
        )
        rows = await self.session.execute(stmt)
        return [
            (int(a), int(m), tipo, Decimal(total)) for a, m, tipo, total in rows.all()
        ]

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
