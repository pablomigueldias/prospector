from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.contato import Contato
from app.utils.logger import get_logger

logger = get_logger()


class ContatoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Reads ─────────────────────────────────────────────────────

    async def get_by_id(self, contato_id: uuid.UUID) -> Contato | None:
        return await self.session.get(Contato, contato_id)

    async def list_by_empresa(self, empresa_id: uuid.UUID) -> list[Contato]:
        stmt = (
            select(Contato)
            .where(Contato.empresa_id == empresa_id)
            .order_by(Contato.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _filtro_lista(
        self, *, busca: str | None, empresa_id: uuid.UUID | None,
        decisor: bool | None, origem: str | None,
    ):
        conds = []
        if empresa_id:
            conds.append(Contato.empresa_id == empresa_id)
        if decisor is not None:
            conds.append(Contato.decisor.is_(decisor))
        if origem:
            conds.append(Contato.origem_contato == origem)
        if busca and busca.strip():
            termo = f"%{busca.strip()}%"
            conds.append(or_(
                Contato.nome.ilike(termo),
                Contato.cargo.ilike(termo),
                Contato.email.ilike(termo),
            ))
        return conds

    async def listar(
        self, *, busca: str | None = None, empresa_id: uuid.UUID | None = None,
        decisor: bool | None = None, origem: str | None = None,
        limit: int = 100, offset: int = 0,
    ) -> list[Contato]:
        conds = self._filtro_lista(
            busca=busca, empresa_id=empresa_id, decisor=decisor, origem=origem
        )
        stmt = (
            select(Contato)
            .where(*conds)
            .options(selectinload(Contato.empresa))
            .order_by(Contato.nome)
            .limit(limit).offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def contar(
        self, *, busca: str | None = None, empresa_id: uuid.UUID | None = None,
        decisor: bool | None = None, origem: str | None = None,
    ) -> int:
        conds = self._filtro_lista(
            busca=busca, empresa_id=empresa_id, decisor=decisor, origem=origem
        )
        stmt = select(func.count(Contato.id)).where(*conds)
        return await self.session.scalar(stmt) or 0

    async def excluir(self, contato: Contato) -> None:
        await self.session.delete(contato)

    async def find_by_empresa_and_email(
        self, empresa_id: uuid.UUID, email: str
    ) -> Contato | None:
        if not email:
            return None
        stmt = select(Contato).where(
            Contato.empresa_id == empresa_id,
            Contato.email == email.lower(),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_empresa_and_nome(
        self, empresa_id: uuid.UUID, nome: str
    ) -> Contato | None:
        if not nome:
            return None
        stmt = select(Contato).where(
            Contato.empresa_id == empresa_id,
            Contato.nome == nome,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Writes ────────────────────────────────────────────────────

    def add(self, contato: Contato) -> Contato:
        self.session.add(contato)
        return contato

    async def upsert(self, contato: Contato) -> Contato:
        existing: Contato | None = None

        if contato.email:
            existing = await self.find_by_empresa_and_email(
                contato.empresa_id, contato.email
            )
        if existing is None and contato.nome:
            existing = await self.find_by_empresa_and_nome(
                contato.empresa_id, contato.nome
            )

        if existing is None:
            self.session.add(contato)
            logger.debug(f"Contato novo: {contato.nome}")
            return contato

        campos_atualizaveis = [
            "nome", "cargo", "decisor",
            "email", "telefone", "whatsapp", "linkedin",
            "origem_contato", "notion_page_id", "notion_synced_at",
        ]
        for campo in campos_atualizaveis:
            valor_novo = getattr(contato, campo, None)
            if valor_novo is not None:
                setattr(existing, campo, valor_novo)

        logger.debug(f"Contato atualizado: {existing.nome}")
        return existing
