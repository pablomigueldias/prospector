"""Admin de usuários — criar/listar/editar e atribuir papéis.

Só quem tem ``usuarios.gerenciar`` chega aqui (checado no router). Não há
cadastro público: usuários nascem por aqui.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import (
    PapelItem,
    UsuarioAdminCreate,
    UsuarioAdminItem,
    UsuarioAdminListResponse,
    UsuarioAdminUpdate,
)
from app.api.services.auth import auditoria_service, senha_service
from app.api.services.auth.senha_service import SenhaFraca
from app.db.models.auth.papel import Papel
from app.db.models.auth.usuario import Usuario
from app.db.models.auth.usuario_papel import UsuarioPapel
from app.db.session import get_session


class AdminError(Exception):
    """Erro de negócio do admin de usuários — vira 400/404/409 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat() if dt else None


async def _papeis_por_usuario(session: AsyncSession) -> dict[uuid.UUID, list[str]]:
    rows = await session.execute(
        select(UsuarioPapel.usuario_id, Papel.nome).join(
            Papel, Papel.id == UsuarioPapel.papel_id
        )
    )
    mapa: dict[uuid.UUID, list[str]] = {}
    for uid, nome in rows.all():
        mapa.setdefault(uid, []).append(nome)
    return mapa


def _to_item(u: Usuario, papeis: list[str]) -> UsuarioAdminItem:
    return UsuarioAdminItem(
        id=str(u.id),
        email=u.email,
        nome=u.nome,
        ativo=u.ativo,
        twofa_ativado=u.twofa_ativado,
        papeis=sorted(papeis),
        ultimo_login=_iso(u.ultimo_login),
        created_at=_iso(u.created_at),
    )


async def listar_papeis() -> list[PapelItem]:
    async with get_session() as session:
        papeis = (await session.scalars(select(Papel).order_by(Papel.nome))).all()
        return [PapelItem(nome=p.nome, descricao=p.descricao) for p in papeis]


async def listar_usuarios() -> UsuarioAdminListResponse:
    async with get_session() as session:
        usuarios = (
            await session.scalars(select(Usuario).order_by(Usuario.created_at))
        ).all()
        mapa = await _papeis_por_usuario(session)
        items = [_to_item(u, mapa.get(u.id, [])) for u in usuarios]
        return UsuarioAdminListResponse(items=items, total=len(items))


async def _resolver_papeis(session: AsyncSession, nomes: list[str]) -> list[Papel]:
    nomes_unicos = sorted(set(nomes))
    papeis = (
        await session.scalars(select(Papel).where(Papel.nome.in_(nomes_unicos)))
    ).all()
    achados = {p.nome for p in papeis}
    faltando = set(nomes_unicos) - achados
    if faltando:
        raise AdminError(f"Papel(is) inexistente(s): {', '.join(sorted(faltando))}")
    return list(papeis)


async def criar_usuario(
    payload: UsuarioAdminCreate, *, ator_id, ip=None, user_agent=None
) -> UsuarioAdminItem:
    email_norm = (payload.email or "").strip().lower()
    if not email_norm or "@" not in email_norm:
        raise AdminError("Email inválido.")
    if not payload.nome.strip():
        raise AdminError("O nome é obrigatório.")
    try:
        senha_service.validar_forca(payload.senha)
    except SenhaFraca as e:
        raise AdminError(str(e))

    async with get_session() as session:
        existe = await session.scalar(
            select(Usuario).where(Usuario.email == email_norm)
        )
        if existe:
            raise AdminError("Já existe um usuário com esse email.")

        papeis = await _resolver_papeis(session, payload.papeis or ["padrao"])
        u = Usuario(
            email=email_norm,
            senha_hash=senha_service.hash_senha(payload.senha),
            nome=payload.nome.strip(),
        )
        session.add(u)
        await session.flush()
        for p in papeis:
            session.add(UsuarioPapel(usuario_id=u.id, papel_id=p.id))
        await auditoria_service.registrar(
            session, auditoria_service.USUARIO_CRIADO, usuario_id=ator_id,
            ip=ip, user_agent=user_agent,
            detalhe={"novo_usuario": str(u.id), "email": email_norm,
                     "papeis": [p.nome for p in papeis]},
        )
        await session.commit()
        return _to_item(u, [p.nome for p in papeis])


async def atualizar_usuario(
    usuario_id: str, payload: UsuarioAdminUpdate, *, ator_id, ip=None, user_agent=None
) -> UsuarioAdminItem:
    try:
        uid = uuid.UUID(usuario_id)
    except ValueError:
        raise AdminError("id inválido")

    async with get_session() as session:
        u = await session.get(Usuario, uid)
        if u is None:
            raise AdminError("Usuário não encontrado.")

        # Trava de segurança: não deixar o admin se trancar pra fora.
        eh_proprio = ator_id is not None and uid == ator_id
        if eh_proprio and payload.ativo is False:
            raise AdminError("Você não pode desativar a si mesmo.")

        if payload.nome is not None:
            if not payload.nome.strip():
                raise AdminError("O nome não pode ficar vazio.")
            u.nome = payload.nome.strip()
        if payload.ativo is not None:
            u.ativo = payload.ativo

        papeis_finais: Optional[list[str]] = None
        if payload.papeis is not None:
            papeis = await _resolver_papeis(session, payload.papeis)
            nomes = {p.nome for p in papeis}
            if eh_proprio and "admin" not in nomes:
                raise AdminError("Você não pode remover seu próprio papel admin.")
            await session.execute(
                delete(UsuarioPapel).where(UsuarioPapel.usuario_id == uid)
            )
            for p in papeis:
                session.add(UsuarioPapel(usuario_id=uid, papel_id=p.id))
            papeis_finais = sorted(nomes)
            await auditoria_service.registrar(
                session, auditoria_service.PAPEIS_ALTERADOS, usuario_id=ator_id,
                ip=ip, user_agent=user_agent,
                detalhe={"usuario": str(uid), "papeis": papeis_finais},
            )

        await session.commit()

        if papeis_finais is None:
            mapa = await _papeis_por_usuario(session)
            papeis_finais = sorted(mapa.get(uid, []))
        await session.refresh(u)
        return _to_item(u, papeis_finais)
