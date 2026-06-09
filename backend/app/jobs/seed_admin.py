"""Seed do RBAC + usuário admin (você).

Idempotente — pode rodar quantas vezes quiser:
1. cria as permissões do catálogo;
2. cria os papéis ``admin`` (todas as permissões) e ``padrao`` (subconjunto seguro);
3. cria o usuário admin com id 00000000-0000-0000-0000-000000000001 (= dono do
   financas) a partir de ADMIN_EMAIL / ADMIN_SENHA_INICIAL do .env e dá o papel admin.

Rodar:  python -m app.jobs.seed_admin
Nunca hardcode senha aqui — só vem do .env. Troque a senha no primeiro acesso.
"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.api.services.auth import senha_service
from app.api.services.auth.permissoes import (
    CATALOGO,
    NOME_ADMIN,
    NOME_PADRAO,
    PADRAO,
)
from app.config import settings
from app.db.models.auth.papel import Papel
from app.db.models.auth.papel_permissao import PapelPermissao
from app.db.models.auth.permissao import Permissao
from app.db.models.auth.usuario import Usuario
from app.db.models.auth.usuario_papel import UsuarioPapel
from app.db.session import dispose_engine, get_session
from app.utils.logger import get_logger

logger = get_logger()

# Mesmo id que o financas usa como dono dos dados (NEXT_PUBLIC_FINANCAS_USUARIO_ID
# default). Casar os dois faz o login do Pablo enxergar os dados do financas.
ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _get_or_create_permissoes(session) -> dict[str, Permissao]:
    existentes = {
        p.codigo: p for p in (await session.scalars(select(Permissao))).all()
    }
    for codigo, descricao in CATALOGO:
        if codigo not in existentes:
            p = Permissao(codigo=codigo, descricao=descricao)
            session.add(p)
            existentes[codigo] = p
    await session.flush()
    return existentes


async def _get_or_create_papel(session, nome: str, descricao: str) -> Papel:
    papel = await session.scalar(select(Papel).where(Papel.nome == nome))
    if papel is None:
        papel = Papel(nome=nome, descricao=descricao)
        session.add(papel)
        await session.flush()
    return papel


async def _ligar(session, papel: Papel, permissoes: list[Permissao]) -> None:
    ja = {
        pp.permissao_id
        for pp in (
            await session.scalars(
                select(PapelPermissao).where(PapelPermissao.papel_id == papel.id)
            )
        ).all()
    }
    for perm in permissoes:
        if perm.id not in ja:
            session.add(PapelPermissao(papel_id=papel.id, permissao_id=perm.id))
    await session.flush()


async def seed() -> None:
    if not settings.admin_email or not settings.admin_senha_inicial:
        raise SystemExit(
            "Defina ADMIN_EMAIL e ADMIN_SENHA_INICIAL no .env antes de rodar o seed."
        )
    senha_service.validar_forca(settings.admin_senha_inicial)

    async with get_session() as session:
        perms = await _get_or_create_permissoes(session)
        logger.info(f"Permissões garantidas: {len(perms)}")

        papel_admin = await _get_or_create_papel(session, NOME_ADMIN, "Acesso total")
        papel_padrao = await _get_or_create_papel(
            session, NOME_PADRAO, "Usuário comum (sem área pessoal/admin)"
        )

        await _ligar(session, papel_admin, list(perms.values()))
        await _ligar(session, papel_padrao, [perms[c] for c in PADRAO])

        # Usuário admin (por id fixo OU por email, o que existir).
        email_norm = settings.admin_email.strip().lower()
        admin = await session.get(Usuario, ADMIN_ID)
        if admin is None:
            admin = await session.scalar(
                select(Usuario).where(Usuario.email == email_norm)
            )
        if admin is None:
            admin = Usuario(
                id=ADMIN_ID,
                email=email_norm,
                senha_hash=senha_service.hash_senha(settings.admin_senha_inicial),
                nome="Pablo",
            )
            session.add(admin)
            await session.flush()
            logger.info(f"Admin criado: {email_norm} (id={admin.id})")
        else:
            logger.info(f"Admin já existe: {admin.email} (id={admin.id}) — senha intacta")

        # Garante o papel admin (idempotente).
        tem = await session.scalar(
            select(UsuarioPapel).where(
                UsuarioPapel.usuario_id == admin.id,
                UsuarioPapel.papel_id == papel_admin.id,
            )
        )
        if tem is None:
            session.add(UsuarioPapel(usuario_id=admin.id, papel_id=papel_admin.id))

        await session.commit()

    logger.info("✅ Seed do admin concluído.")


async def _run() -> None:
    try:
        await seed()
    finally:
        await dispose_engine()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
