from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pessoal.perfil_mestre import PerfilMestre

# Campos do PerfilMestre que vêm do payload (o resto é gerado/automático).
_CAMPOS = (
    "nome", "titulo", "resumo", "tom_escrita",
    "habilidades", "projetos", "experiencias", "formacao",
    "certificacoes", "o_que_procuro", "blocos_curriculo", "contato",
)


class PerfilRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_ativo(self) -> PerfilMestre | None:
        stmt = (
            select(PerfilMestre)
            .where(PerfilMestre.ativo.is_(True))
            .order_by(PerfilMestre.updated_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def upsert(self, dados: dict) -> PerfilMestre:
        """Cria o perfil ativo, ou atualiza o existente."""
        perfil = await self.get_ativo()
        if perfil is None:
            perfil = PerfilMestre(ativo=True)
            self.session.add(perfil)

        for campo in _CAMPOS:
            if campo in dados:
                setattr(perfil, campo, dados[campo])

        await self.session.commit()
        await self.session.refresh(perfil)
        return perfil
