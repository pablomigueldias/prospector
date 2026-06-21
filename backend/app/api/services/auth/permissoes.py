"""Catálogo de permissões + consulta das permissões de um usuário.

As permissões são strings nomeadas ligadas a papéis (RBAC). O catálogo abaixo
é a fonte de verdade — o seed (``app.jobs.seed_admin``) cria exatamente estas.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.auth.papel_permissao import PapelPermissao
from app.db.models.auth.permissao import Permissao
from app.db.models.auth.usuario_papel import UsuarioPapel

# (codigo, descricao) — catálogo canônico.
CATALOGO: list[tuple[str, str]] = [
    ("pessoal.ver", "Ver a área pessoal (vagas, perfil mestre)"),
    ("financas.ver", "Ver o organizador financeiro"),
    ("financas.editar", "Lançar e editar no financeiro"),
    ("comprovantes.ver", "Ver comprovantes"),
    ("relatorios.ver", "Ver relatórios"),
    ("usuarios.gerenciar", "Criar e editar usuários (admin)"),
    ("blog.editar", "Criar, editar e publicar posts do blog"),
]

# Subconjunto seguro pro papel "padrao" (ex.: Sandra): SEM pessoal.ver nem
# usuarios.gerenciar.
PADRAO: set[str] = {
    "financas.ver",
    "financas.editar",
    "comprovantes.ver",
    "relatorios.ver",
}

NOME_ADMIN = "admin"
NOME_PADRAO = "padrao"


async def listar_codigos(session: AsyncSession, usuario_id: uuid.UUID) -> list[str]:
    """Todas as permissões (códigos) do usuário, via papéis. Lista ordenada."""
    stmt = (
        select(Permissao.codigo)
        .join(PapelPermissao, PapelPermissao.permissao_id == Permissao.id)
        .join(UsuarioPapel, UsuarioPapel.papel_id == PapelPermissao.papel_id)
        .where(UsuarioPapel.usuario_id == usuario_id)
        .distinct()
    )
    rows = await session.execute(stmt)
    return sorted(r[0] for r in rows.all())
