from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.financas.categoria import Categoria
from app.db.models.financas.recorrencia import Recorrencia
from app.db.models.financas.transacao import Transacao
from app.db.models.financas.transacao_pagamento import TransacaoPagamento


class TransacaoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, transacao: Transacao) -> None:
        """Adiciona à sessão (commit/flush fica a cargo do service, que também
        ajusta o saldo da conta no mesmo commit)."""
        self.session.add(transacao)

    async def get(self, transacao_id: uuid.UUID) -> Transacao | None:
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
        linha_digitavel: str | None = None,
        beneficiario: str | None = None,
        vencimento: date | None = None,
        valor: Decimal | None = None,
    ) -> Transacao | None:
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
        self, usuario_id: uuid.UUID, descricao: str | None
    ) -> uuid.UUID | None:
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

    async def ultima_conta_por_descricao(
        self, usuario_id: uuid.UUID, descricao: str | None
    ) -> uuid.UUID | None:
        """Conta usada pra pagar a transação paga mais recente com essa
        descrição (beneficiário). Sugere a conta no pagamento de um boleto."""
        if not descricao or not descricao.strip():
            return None
        stmt = (
            select(TransacaoPagamento.conta_id)
            .join(Transacao, Transacao.id == TransacaoPagamento.transacao_id)
            .where(
                Transacao.usuario_id == usuario_id,
                func.lower(Transacao.descricao) == descricao.strip().lower(),
                Transacao.status == "paga",
            )
            .order_by(
                Transacao.data_pagamento.desc().nullslast(),
                Transacao.created_at.desc(),
            )
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def recorrencia_para_descricao(
        self, usuario_id: uuid.UUID, descricao: str | None
    ) -> uuid.UUID | None:
        """Qual recorrência (conta fixa) casa com esse beneficiário/descrição.

        Aprende como as outras features 'por beneficiário': primeiro pela
        recorrência que já foi usada na transação mais recente com a mesma
        descrição; senão, por uma recorrência ativa de nome igual. Serve pra
        ligar o boleto importado (ex.: aluguel) à conta fixa automaticamente."""
        if not descricao or not descricao.strip():
            return None
        alvo = descricao.strip().lower()
        # 1) histórico: recorrência da última transação com essa descrição
        do_historico = await self.session.scalar(
            select(Transacao.recorrencia_id)
            .where(
                Transacao.usuario_id == usuario_id,
                func.lower(Transacao.descricao) == alvo,
                Transacao.recorrencia_id.is_not(None),
            )
            .order_by(Transacao.created_at.desc())
            .limit(1)
        )
        if do_historico is not None:
            return do_historico
        # 2) nome igual a uma recorrência ativa
        return await self.session.scalar(
            select(Recorrencia.id)
            .where(
                Recorrencia.usuario_id == usuario_id,
                Recorrencia.ativa.is_(True),
                func.lower(Recorrencia.descricao) == alvo,
            )
            .order_by(Recorrencia.created_at.desc())
            .limit(1)
        )

    # ── Listagem filtrável (para a tela de transações no dashboard) ───
    async def listar(
        self,
        usuario_id: uuid.UUID,
        *,
        inicio: date | None = None,
        proximo_mes: date | None = None,
        conta_id: uuid.UUID | None = None,
        categoria_id: uuid.UUID | None = None,
        tipo: str | None = None,
        status: list[str] | None = None,
        busca: str | None = None,
        por_vencimento: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Transacao], int]:
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

    async def previstas_por_tipo(
        self, usuario_id: uuid.UUID, ate: date
    ) -> dict[str, Decimal]:
        """Soma por tipo das transações NÃO pagas (prevista/atrasada) com data
        efetiva (vencimento, ou competência se não tiver) anterior a ``ate``.
        Usado na projeção de fim de mês — inclui as vencidas que ainda devem."""
        efetiva = func.coalesce(Transacao.data_vencimento, Transacao.data_competencia)
        stmt = (
            select(
                Transacao.tipo,
                func.coalesce(func.sum(Transacao.valor_total), 0),
            )
            .where(
                Transacao.usuario_id == usuario_id,
                Transacao.status != "paga",
                efetiva < ate,
            )
            .group_by(Transacao.tipo)
        )
        rows = await self.session.execute(stmt)
        return {tipo: Decimal(total) for tipo, total in rows.all()}

    # ── Agregados do resumo do mês (filtro por data_competencia) ──────
    async def total_por_tipo(
        self, usuario_id: uuid.UUID, inicio: date, proximo_mes: date
    ) -> dict[str, Decimal]:
        stmt = (
            select(
                Transacao.tipo,
                func.coalesce(func.sum(Transacao.valor_total), 0),
            )
            .where(
                Transacao.usuario_id == usuario_id,
                Transacao.data_competencia >= inicio,
                Transacao.data_competencia < proximo_mes,
                Transacao.origem != "transferencia",
            )
            .group_by(Transacao.tipo)
        )
        rows = await self.session.execute(stmt)
        return {tipo: Decimal(total) for tipo, total in rows.all()}

    def _filtros_relatorio(
        self,
        conta_id: uuid.UUID | None,
        categoria_id: uuid.UUID | None,
    ) -> list:
        """Condições extras opcionais do relatório (recorte por conta/categoria).
        Conta usa EXISTS sobre os pagamentos (sem fanout de linhas em splits);
        previstas sem pagamento ficam de fora do recorte por conta — o que é
        correto, já que ainda não moveram nenhuma conta."""
        extra: list = []
        if categoria_id is not None:
            extra.append(Transacao.categoria_id == categoria_id)
        if conta_id is not None:
            extra.append(
                select(TransacaoPagamento.id)
                .where(
                    TransacaoPagamento.transacao_id == Transacao.id,
                    TransacaoPagamento.conta_id == conta_id,
                )
                .exists()
            )
        return extra

    async def totais_por_mes(
        self,
        usuario_id: uuid.UUID,
        inicio: date,
        proximo_mes: date,
        *,
        conta_id: uuid.UUID | None = None,
        categoria_id: uuid.UUID | None = None,
    ) -> list[tuple[int, int, str, Decimal]]:
        """(ano, mes, tipo, total) por mês de competência no intervalo, pra
        montar a série do relatório. Meses sem lançamento não aparecem (o
        service preenche zero). Aceita recorte por conta/categoria."""
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
                Transacao.origem != "transferencia",
                *self._filtros_relatorio(conta_id, categoria_id),
            )
            .group_by("ano", "mes", Transacao.tipo)
        )
        rows = await self.session.execute(stmt)
        return [
            (int(a), int(m), tipo, Decimal(total)) for a, m, tipo, total in rows.all()
        ]

    async def despesas_por_categoria(
        self,
        usuario_id: uuid.UUID,
        inicio: date,
        proximo_mes: date,
        *,
        conta_id: uuid.UUID | None = None,
        categoria_id: uuid.UUID | None = None,
    ) -> list[tuple[uuid.UUID | None, str | None, Decimal]]:
        """(categoria_id, categoria_nome, total) das despesas do mês,
        maior total primeiro. categoria_id null = sem categoria. Aceita
        recorte por conta/categoria."""
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
                Transacao.origem != "transferencia",
                *self._filtros_relatorio(conta_id, categoria_id),
            )
            .group_by(Transacao.categoria_id, Categoria.nome)
            .order_by(soma.desc())
        )
        rows = await self.session.execute(stmt)
        return [(cid, nome, Decimal(total)) for cid, nome, total in rows.all()]
