"""Service do Perfil Mestre — o 'quem EU sou' dos agentes pessoais."""
from __future__ import annotations

from app.api.schemas.pessoal import PerfilMestreResponse, PerfilMestreUpsert
from app.api.services._helpers import iso as _iso
from app.db.models.pessoal.perfil_mestre import PerfilMestre
from app.db.session import get_session
from app.repositories.pessoal.perfil_repository import PerfilRepository


class PerfilError(Exception):
    """Erro de negócio do Perfil Mestre — vira HTTP 400 no router."""


def _to_response(p: PerfilMestre) -> PerfilMestreResponse:
    return PerfilMestreResponse(
        id=str(p.id),
        ativo=p.ativo,
        nome=p.nome,
        titulo=p.titulo,
        resumo=p.resumo,
        tom_escrita=p.tom_escrita,
        habilidades=p.habilidades or [],
        projetos=p.projetos or [],
        experiencias=p.experiencias or [],
        formacao=p.formacao or [],
        o_que_procuro=p.o_que_procuro,
        blocos_curriculo=p.blocos_curriculo or [],
        contato=p.contato,
        created_at=_iso(p.created_at),
        updated_at=_iso(p.updated_at),
    )


async def get_perfil() -> PerfilMestreResponse | None:
    async with get_session() as session:
        perfil = await PerfilRepository(session).get_ativo()
        return _to_response(perfil) if perfil else None


async def salvar_perfil(payload: PerfilMestreUpsert) -> PerfilMestreResponse:
    if not payload.nome or not payload.nome.strip():
        raise PerfilError("O perfil precisa de um nome.")

    # mode="json" serializa os sub-modelos em dict/list puros pro JSONB
    dados = payload.model_dump(mode="json")
    async with get_session() as session:
        perfil = await PerfilRepository(session).upsert(dados)
        return _to_response(perfil)
