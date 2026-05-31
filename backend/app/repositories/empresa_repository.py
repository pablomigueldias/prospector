from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.empresa import Empresa
from app.utils.logger import get_logger


logger = get_logger()


class EmpresaRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Reads ─────────────────────────────────────────────────────

    async def get_by_id(self, empresa_id: uuid.UUID) -> Optional[Empresa]:
        """Busca empresa pelo UUID. Retorna None se não existir."""
        return await self.session.get(Empresa, empresa_id)

    async def find_by_cnpj(self, cnpj: str) -> Optional[Empresa]:
        """
        Busca empresa pelo CNPJ (só dígitos, sem máscara).
        """
        if not cnpj:
            return None

        digits = "".join(c for c in cnpj if c.isdigit())
        if len(digits) != 14:
            return None

        stmt = select(Empresa).where(Empresa.cnpj == digits)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> List[Empresa]:
        """Últimas N empresas, mais recente primeiro."""
        stmt = (
            select(Empresa)
            .order_by(Empresa.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Writes ────────────────────────────────────────────────────

    def add(self, empresa: Empresa) -> Empresa:

        self.session.add(empresa)
        return empresa

    async def upsert_by_cnpj(self, empresa: Empresa) -> Empresa:

        if not empresa.cnpj:
            self.session.add(empresa)
            return empresa

        existing = await self.find_by_cnpj(empresa.cnpj)
        if existing is None:
            self.session.add(empresa)
            logger.debug(f" Empresa nova: {empresa.nome}")
            return empresa

        campos_atualizaveis = [
            "nome", "razao_social", "cidade", "estado", "local",
            "site", "instagram", "facebook",
            "capital_social", "setor", "tamanho", "score", "analise_json"
            "como_conheceu", "status", "notas",
            "notion_page_id", "notion_synced_at",
        ]
        for campo in campos_atualizaveis:
            valor_novo = getattr(empresa, campo, None)
            if valor_novo is not None:
                setattr(existing, campo, valor_novo)

        logger.debug(f"🔄 Empresa atualizada: {existing.nome}")
        return existing
