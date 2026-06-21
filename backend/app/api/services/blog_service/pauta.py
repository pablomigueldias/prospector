"""Motor de pauta (B3): gera/ranqueia o backlog editorial e gerencia o CRUD das
pautas. Gerar usa a LLM (3 fontes, ancorado no Perfil Mestre); o resto é CRUD."""
from app.analyzers.blog.pauta.parser import parse_resposta
from app.analyzers.blog.pauta.prompt_builder import construir_prompt
from app.api.schemas.blog import (
    BlogPautaGerarRequest,
    BlogPautaItem,
    BlogPautaManualCreate,
    BlogPautaUpdate,
)
from app.api.services.pessoal.perfil_service import get_perfil
from app.db.models.blog.pauta import STATUS_PAUTA
from app.db.session import get_session
from app.repositories.blog_repository import BlogRepository

from ._base import BlogError, _chamar_llm, _uuid, to_pauta_item


async def gerar(req: BlogPautaGerarRequest) -> list[BlogPautaItem]:
    qtd = max(1, min(req.quantidade or 6, 15))
    perfil = await get_perfil()
    async with get_session() as session:
        repo = BlogRepository(session)
        existentes = await repo.titulos_pauta_existentes()

    prompt = construir_prompt(
        quantidade=qtd,
        fontes=req.fontes,
        publico=req.publico,
        sementes=req.sementes,
        tendencias=req.tendencias,
        perfil=perfil,
        titulos_existentes=sorted(existentes),
    )
    cru = _chamar_llm(prompt, operacao="gerar_pautas")
    novas = parse_resposta(cru)
    if not novas:
        raise BlogError("A IA não retornou pautas válidas. Tente de novo.")

    # Dedup contra o que já existe (case-insensitive).
    novas = [p for p in novas if p["titulo"].casefold() not in existentes]
    if not novas:
        raise BlogError("As pautas geradas já existem no backlog. Tente outro foco.")

    async with get_session() as session:
        criadas = await BlogRepository(session).create_pautas(novas)
        return [to_pauta_item(p) for p in criadas]


async def listar(status: str | None = None) -> list[BlogPautaItem]:
    if status and status not in STATUS_PAUTA:
        raise BlogError(f"status inválido: {status!r}")
    async with get_session() as session:
        pautas = await BlogRepository(session).listar_pautas(status=status)
        return [to_pauta_item(p) for p in pautas]


async def criar_manual(payload: BlogPautaManualCreate) -> BlogPautaItem:
    if not (payload.titulo or "").strip():
        raise BlogError("Título da pauta é obrigatório.")
    dados = payload.model_dump(exclude_none=True)
    dados["fonte"] = "manual"
    async with get_session() as session:
        pauta = await BlogRepository(session).create_pauta(dados)
        return to_pauta_item(pauta)


async def atualizar(pauta_id: str, payload: BlogPautaUpdate) -> BlogPautaItem:
    pid = _uuid(pauta_id, "pauta_id")
    dados = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "status" in dados and dados["status"] not in STATUS_PAUTA:
        raise BlogError(f"status inválido: {dados['status']!r}")
    async with get_session() as session:
        pauta = await BlogRepository(session).update_pauta(pid, dados)
        if pauta is None:
            raise BlogError("Pauta não encontrada.")
        return to_pauta_item(pauta)


async def deletar(pauta_id: str) -> None:
    pid = _uuid(pauta_id, "pauta_id")
    async with get_session() as session:
        ok = await BlogRepository(session).delete_pauta(pid)
        if not ok:
            raise BlogError("Pauta não encontrada.")
