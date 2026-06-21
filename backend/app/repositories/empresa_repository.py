from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.empresa import Empresa
from app.utils.logger import get_logger

logger = get_logger()


class EmpresaRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Reads ─────────────────────────────────────────────────────

    async def get_by_id(self, empresa_id: uuid.UUID) -> Empresa | None:
        """Busca empresa pelo UUID. Retorna None se não existir."""
        return await self.session.get(Empresa, empresa_id)

    async def find_by_cnpj(self, cnpj: str) -> Empresa | None:
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

    async def find_by_notion_page_id(self, page_id: str) -> Empresa | None:
        """Busca empresa pelo id da página do Notion (chave estável do sync)."""
        if not page_id:
            return None
        stmt = select(Empresa).where(Empresa.notion_page_id == page_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> list[Empresa]:
        """Últimas N empresas, mais recente primeiro."""
        stmt = (
            select(Empresa)
            .order_by(Empresa.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    _ORDENAVEIS = {
        "nome": Empresa.nome,
        "score": Empresa.score,
        "cidade": Empresa.cidade,
        "status": Empresa.status,
        "setor": Empresa.setor,
        "criado": Empresa.created_at,
    }

    def _filtro(
        self, *, status: str | None = None, busca: str | None = None,
        setor: str | None = None, estado: str | None = None,
        cidade: str | None = None, tamanho: str | None = None,
        como_conheceu: str | None = None, score_min: int | None = None,
    ):
        """Monta as cláusulas WHERE compartilhadas por listar/contar."""
        conds = []
        if status:
            conds.append(Empresa.status == status)
        if setor:
            conds.append(Empresa.setor == setor)
        if estado:
            conds.append(Empresa.estado == estado)
        if tamanho:
            conds.append(Empresa.tamanho == tamanho)
        if como_conheceu:
            conds.append(Empresa.como_conheceu == como_conheceu)
        if cidade and cidade.strip():
            conds.append(Empresa.cidade.ilike(f"%{cidade.strip()}%"))
        if score_min is not None:
            conds.append(Empresa.score >= score_min)
        if busca and busca.strip():
            termo = f"%{busca.strip()}%"
            conds.append(or_(
                Empresa.nome.ilike(termo),
                Empresa.cnpj.ilike(termo),
                Empresa.cidade.ilike(termo),
                Empresa.setor.ilike(termo),
            ))
        return conds

    def _ordenacao(self, ordenar_por: str | None, desc: bool):
        col = self._ORDENAVEIS.get(ordenar_por or "", None)
        if col is None:
            # default: score desc, depois nome
            return (Empresa.score.desc().nullslast(), Empresa.nome)
        ordenado = col.desc().nullslast() if desc else col.asc().nullslast()
        return (ordenado,)

    async def listar(
        self, *, limit: int = 50, offset: int = 0,
        ordenar_por: str | None = None, desc: bool = False, **filtros,
    ) -> list[Empresa]:
        stmt = (
            select(Empresa)
            .where(*self._filtro(**filtros))
            .order_by(*self._ordenacao(ordenar_por, desc))
            .limit(limit).offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def contar(self, **filtros) -> int:
        stmt = select(func.count(Empresa.id)).where(*self._filtro(**filtros))
        return await self.session.scalar(stmt) or 0

    async def excluir(self, empresa: Empresa) -> None:
        await self.session.delete(empresa)

    async def _distintos(self, col) -> list[str]:
        stmt = select(col).where(col.isnot(None)).distinct().order_by(col)
        result = await self.session.execute(stmt)
        return [v for (v,) in result.all() if v]

    async def facetas(self) -> dict[str, list[str]]:
        """Valores distintos pros dropdowns de filtro."""
        return {
            "status": await self._distintos(Empresa.status),
            "setor": await self._distintos(Empresa.setor),
            "estado": await self._distintos(Empresa.estado),
            "tamanho": await self._distintos(Empresa.tamanho),
            "como_conheceu": await self._distintos(Empresa.como_conheceu),
        }

    async def listar_todas(self) -> list[Empresa]:
        """Todas as empresas (pro kanban), ordenadas por score."""
        stmt = select(Empresa).order_by(
            Empresa.score.desc().nullslast(), Empresa.nome
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
            "capital_social", "setor", "tamanho", "score", "analise_json",
            "como_conheceu", "status", "notas",
            "notion_page_id", "notion_synced_at",
        ]
        for campo in campos_atualizaveis:
            valor_novo = getattr(empresa, campo, None)
            if valor_novo is not None:
                setattr(existing, campo, valor_novo)

        logger.debug(f"🔄 Empresa atualizada: {existing.nome}")
        return existing
