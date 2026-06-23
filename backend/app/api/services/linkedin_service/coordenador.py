"""Coordenador autônomo do LinkedIn (P5 §6.C — L2): gera RASCUNHOS PRONTOS.

Encadeia o que já existe (redator L1 + CRUD L0): a partir de uma fonte (projetos
do Perfil Mestre ou tendências do setor), redige posts completos e salva como
RASCUNHO na fila. PARA no rascunho — o Pablo revisa, copia e publica (não
auto-postamos). É o que torna o agente "autônomo no sistema": uma chamada enche a
fila sozinha."""
from __future__ import annotations

import uuid

from app.analyzers.linkedin.temas.parser import parse_temas
from app.analyzers.linkedin.temas.prompt_builder import construir_prompt as prompt_temas
from app.api.schemas.linkedin import (
    LinkedinBriefRequest,
    LinkedinGerarRequest,
    LinkedinPostCreate,
    LinkedinPostOut,
)
from app.api.services.pessoal.perfil_service import get_perfil
from app.config import settings
from app.db.models.linkedin.post import CONTA_LINKEDIN
from app.db.session import get_session
from app.repositories.linkedin_repository import LinkedinRepository
from app.utils.logger import get_logger

from . import admin, agente
from ._base import LinkedinError, _chamar_llm, contar_chars, to_out

logger = get_logger()


def _conta_valida(conta: str | None) -> str:
    c = conta or "reative"
    if c not in CONTA_LINKEDIN:
        raise LinkedinError(f"conta inválida: {conta!r}")
    return c


async def _salvar_rascunho(
    red, *, conta: str, fonte: str, titulo_fallback: str
) -> LinkedinPostOut:
    return await admin.criar(
        LinkedinPostCreate(
            titulo=red.titulo or titulo_fallback,
            conta=conta,
            formato="post",
            hook=red.hook,
            body=red.body,
            cta=red.cta,
            hashtags=red.hashtags or None,
            fonte=fonte,
        )
    )


async def gerar_de_projetos(
    quantidade: int, *, conta: str, publico: str | None = None
) -> list[LinkedinPostOut]:
    """Cada projeto do Perfil Mestre vira um post de case/bastidor."""
    perfil = await get_perfil()
    projetos = list(perfil.projetos) if perfil else []
    if not projetos:
        raise LinkedinError(
            "Sem projetos no Perfil Mestre pra gerar posts. Preencha o Perfil "
            "Mestre primeiro."
        )

    out: list[LinkedinPostOut] = []
    for proj in projetos[: max(1, quantidade)]:
        partes = [proj.descricao, proj.prova]
        if proj.stack:
            partes.append("stack: " + ", ".join(proj.stack))
        angulo = " — ".join(p for p in partes if p)
        try:
            red = await agente.redigir(
                LinkedinBriefRequest(
                    tema=proj.nome, conta=conta, formato="post",
                    publico=publico, angulo=angulo or None,
                )
            )
        except LinkedinError as e:
            logger.warning("linkedin coordenador (projeto {}): {}", proj.nome, e)
            continue
        out.append(
            await _salvar_rascunho(
                red, conta=conta, fonte="projeto", titulo_fallback=proj.nome
            )
        )
    return out


async def gerar_de_tendencias(
    quantidade: int, *, conta: str, publico: str | None = None
) -> list[LinkedinPostOut]:
    """IA propõe N temas de tendência → redige cada um → salva rascunho."""
    perfil = await get_perfil()

    # Evitar repetir o que já está na fila desta conta.
    async with get_session() as session:
        existentes = await LinkedinRepository(session).listar(conta=conta, limit=100)
    evitar = [p.titulo or p.hook or "" for p in existentes if (p.titulo or p.hook)]

    cru = _chamar_llm(
        prompt_temas(
            quantidade=max(1, quantidade), conta=conta, publico=publico,
            evitar=evitar, perfil=perfil,
        ),
        operacao="temas",
    )
    temas = parse_temas(cru)
    if not temas:
        raise LinkedinError("A IA não retornou temas válidos. Tente de novo.")

    out: list[LinkedinPostOut] = []
    for t in temas[: max(1, quantidade)]:
        try:
            red = await agente.redigir(
                LinkedinBriefRequest(
                    tema=t["tema"], conta=conta, formato="post",
                    publico=publico, angulo=t.get("angulo") or None,
                )
            )
        except LinkedinError as e:
            logger.warning("linkedin coordenador (tendência {}): {}", t.get("tema"), e)
            continue
        out.append(
            await _salvar_rascunho(
                red, conta=conta, fonte="tendencia", titulo_fallback=t["tema"]
            )
        )
    return out


async def do_blog(
    *, blog_post_id: uuid.UUID, slug: str, title: str, excerpt: str | None
) -> LinkedinPostOut | None:
    """Cross-agent (L3 = B5): post de blog publicado → rascunho de divulgação no
    LinkedIn da Página da Reative, já ligado ao post (`origem_blog_post_id`).

    Determinístico e idempotente (NÃO chama LLM — não trava nem encarece a
    publicação do blog). O Pablo pode lapidar depois com o botão "Escrever com
    IA". Devolve None se já existia (idempotência) ou se faltar dado."""
    conta = "reative"
    link = f"{settings.site_url.rstrip('/')}/blog/{slug}"
    hook = title.strip()
    if not hook:
        return None
    body = (excerpt or "").strip()
    cta = f"Leia o artigo completo no nosso blog: {link}"

    async with get_session() as session:
        repo = LinkedinRepository(session)
        if await repo.existe_do_blog(blog_post_id, conta):
            return None  # já divulgado — não duplica
        post = await repo.create(
            {
                "titulo": f"[Blog] {title}"[:200],
                "conta": conta,
                "formato": "post",
                "hook": hook,
                "body": body or None,
                "cta": cta,
                "fonte": "blog",
                "origem_blog_post_id": blog_post_id,
                "char_count": contar_chars(hook, body, cta),
            }
        )
        return to_out(post)


async def gerar(req: LinkedinGerarRequest) -> list[LinkedinPostOut]:
    conta = _conta_valida(req.conta)
    if req.fonte == "projeto":
        return await gerar_de_projetos(req.quantidade, conta=conta, publico=req.publico)
    if req.fonte == "tendencia":
        return await gerar_de_tendencias(req.quantidade, conta=conta, publico=req.publico)
    raise LinkedinError(f"fonte inválida: {req.fonte!r} (use projeto|tendencia)")
