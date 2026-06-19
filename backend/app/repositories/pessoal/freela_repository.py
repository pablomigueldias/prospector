from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pessoal.freela.cliente import Cliente
from app.db.models.pessoal.freela.plataforma import Plataforma
from app.db.models.pessoal.freela.projeto import Projeto
from app.db.models.pessoal.freela.proposta import Proposta


class FreelaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Plataforma ───────────────────────────────────────────────
    async def listar_plataformas(self) -> list[Plataforma]:
        stmt = select(Plataforma).order_by(Plataforma.nome)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_plataforma(self, pid: uuid.UUID) -> Plataforma | None:
        return await self.session.get(Plataforma, pid)

    # ── Cliente ──────────────────────────────────────────────────
    async def create_cliente(self, dados: dict) -> Cliente:
        cliente = Cliente(**dados)
        self.session.add(cliente)
        await self.session.commit()
        await self.session.refresh(cliente)
        return cliente

    async def get_cliente(self, cid: uuid.UUID) -> Cliente | None:
        return await self.session.get(Cliente, cid)

    async def listar_clientes(self) -> list[Cliente]:
        stmt = select(Cliente).order_by(Cliente.nome)
        return list((await self.session.execute(stmt)).scalars().all())

    async def update_cliente(self, cid: uuid.UUID, dados: dict) -> Cliente | None:
        cliente = await self.get_cliente(cid)
        if cliente is None:
            return None
        for campo, valor in dados.items():
            setattr(cliente, campo, valor)
        await self.session.commit()
        await self.session.refresh(cliente)
        return cliente

    async def delete_cliente(self, cid: uuid.UUID) -> bool:
        result = await self.session.execute(delete(Cliente).where(Cliente.id == cid))
        await self.session.commit()
        return result.rowcount > 0

    # ── Projeto ──────────────────────────────────────────────────
    async def create_projeto(self, dados: dict) -> Projeto:
        projeto = Projeto(**dados)
        self.session.add(projeto)
        await self.session.commit()
        await self.session.refresh(projeto)
        return projeto

    async def get_projeto(self, pid: uuid.UUID) -> Projeto | None:
        return await self.session.get(Projeto, pid)

    async def listar_projetos(
        self,
    ) -> list[tuple[Projeto, str | None, int, float, bool]]:
        """Projetos + nome do cliente + nº de propostas + US$ já pago + pagamento verificado."""
        propostas = (
            select(
                Proposta.projeto_id,
                func.count(Proposta.id).label("qtd"),
            )
            .group_by(Proposta.projeto_id)
            .subquery()
        )
        stmt = (
            select(
                Projeto,
                Cliente.nome,
                func.coalesce(propostas.c.qtd, 0),
                func.coalesce(Cliente.ja_me_pagou_usd, 0),
                func.coalesce(Cliente.pagamento_verificado, False),
            )
            .outerjoin(Cliente, Cliente.id == Projeto.cliente_id)
            .outerjoin(propostas, propostas.c.projeto_id == Projeto.id)
            .order_by(Projeto.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [
            (row[0], row[1], int(row[2]), float(row[3]), bool(row[4]))
            for row in result.all()
        ]

    async def update_projeto(self, pid: uuid.UUID, dados: dict) -> Projeto | None:
        projeto = await self.get_projeto(pid)
        if projeto is None:
            return None
        for campo, valor in dados.items():
            setattr(projeto, campo, valor)
        await self.session.commit()
        await self.session.refresh(projeto)
        return projeto

    async def salvar_analise_projeto(
        self, pid: uuid.UUID, analise: dict
    ) -> Projeto | None:
        projeto = await self.get_projeto(pid)
        if projeto is None:
            return None
        projeto.analise_json = analise
        await self.session.commit()
        await self.session.refresh(projeto)
        return projeto

    async def delete_projeto(self, pid: uuid.UUID) -> bool:
        result = await self.session.execute(delete(Projeto).where(Projeto.id == pid))
        await self.session.commit()
        return result.rowcount > 0

    # ── Proposta ─────────────────────────────────────────────────
    async def create_proposta(self, dados: dict) -> Proposta:
        proposta = Proposta(**dados)
        self.session.add(proposta)
        await self.session.commit()
        await self.session.refresh(proposta)
        return proposta

    async def get_proposta(self, pid: uuid.UUID) -> Proposta | None:
        return await self.session.get(Proposta, pid)

    async def update_proposta(self, pid: uuid.UUID, dados: dict) -> Proposta | None:
        proposta = await self.get_proposta(pid)
        if proposta is None:
            return None
        for campo, valor in dados.items():
            setattr(proposta, campo, valor)
        await self.session.commit()
        await self.session.refresh(proposta)
        return proposta

    async def delete_proposta(self, pid: uuid.UUID) -> bool:
        result = await self.session.execute(delete(Proposta).where(Proposta.id == pid))
        await self.session.commit()
        return result.rowcount > 0

    async def listar_propostas_kanban(
        self,
    ) -> list[tuple[Proposta, str, str | None]]:
        """Todas as propostas + título do projeto + nome do cliente (pro board)."""
        stmt = (
            select(Proposta, Projeto.titulo, Cliente.nome)
            .join(Projeto, Projeto.id == Proposta.projeto_id)
            .outerjoin(Cliente, Cliente.id == Projeto.cliente_id)
            .order_by(Proposta.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def listar_propostas_do_projeto(
        self, projeto_id: uuid.UUID
    ) -> list[Proposta]:
        stmt = (
            select(Proposta)
            .where(Proposta.projeto_id == projeto_id)
            .order_by(Proposta.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def contar_por_status(self) -> dict[str, int]:
        stmt = select(Proposta.status, func.count(Proposta.id)).group_by(
            Proposta.status
        )
        result = await self.session.execute(stmt)
        return {status: int(qtd) for status, qtd in result.all()}

    async def propostas_status_e_analise(
        self,
    ) -> list[tuple[str, dict | None]]:
        """(status da proposta, analise_json do projeto) — pra taxa por stack."""
        stmt = select(Proposta.status, Projeto.analise_json).join(
            Projeto, Projeto.id == Proposta.projeto_id
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def soma_liquido_fechado(self) -> tuple[float, int]:
        """(soma do líquido das fechadas, quantidade de fechadas)."""
        stmt = select(
            func.coalesce(func.sum(Proposta.valor_liquido_estimado), 0),
            func.count(Proposta.id),
        ).where(Proposta.status == "fechada")
        soma, qtd = (await self.session.execute(stmt)).one()
        return float(soma), int(qtd)

    async def tempo_medio_resposta_horas(self) -> float | None:
        """Média de horas entre enviar e o cliente responder (onde houver ambos)."""
        stmt = select(
            func.avg(
                func.extract("epoch", Proposta.data_resposta - Proposta.enviada_em)
            )
        ).where(
            Proposta.data_resposta.isnot(None),
            Proposta.enviada_em.isnot(None),
        )
        v = (await self.session.execute(stmt)).scalar()
        return round(float(v) / 3600, 1) if v is not None else None

    async def valor_hora_real_fechadas(self) -> float | None:
        """Média do líquido/hora das propostas fechadas com horas estimadas."""
        stmt = select(
            func.avg(Proposta.valor_liquido_estimado / Proposta.horas_estimadas)
        ).where(
            Proposta.status == "fechada",
            Proposta.horas_estimadas.isnot(None),
            Proposta.horas_estimadas > 0,
            Proposta.valor_liquido_estimado.isnot(None),
        )
        v = (await self.session.execute(stmt)).scalar()
        return round(float(v), 2) if v is not None else None

    async def soma_liquido_em_aberto(self) -> tuple[float, int]:
        """(soma do líquido das propostas EM ABERTO, quantidade).

        Em aberto = enviada mas ainda não decidida (nem fechada, nem perdida,
        nem rascunho). É o que alimenta o forecast do pipeline.
        """
        abertos = ("enviada", "visualizada", "respondida", "negociando")
        stmt = select(
            func.coalesce(func.sum(Proposta.valor_liquido_estimado), 0),
            func.count(Proposta.id),
        ).where(Proposta.status.in_(abertos))
        soma, qtd = (await self.session.execute(stmt)).one()
        return float(soma), int(qtd)
