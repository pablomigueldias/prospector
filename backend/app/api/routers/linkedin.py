"""API do agente LinkedIn (P5 §6.C) — CRUD/publicar pelo studio.

Autenticada (`linkedin.editar`). É a mesa de edição do Pablo: criar/editar
rascunho, marcar como publicado (depois de postar na mão), arquivar. O agente de
IA (L1+) escreve via estes mesmos services. NÃO auto-posta no LinkedIn.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies.auth import require_permission
from app.api.schemas.linkedin import (
    GerarImagemLinkedinRequest,
    LinkedinBriefRequest,
    LinkedinGerarRequest,
    LinkedinPostCreate,
    LinkedinPostOut,
    LinkedinPostUpdate,
    LinkedinRedacao,
    LinkedinStatusUpdate,
)
from app.api.services import linkedin_service
from app.api.services.linkedin_service import LinkedinError

router = APIRouter(
    prefix="/api/linkedin",
    tags=["linkedin"],
    dependencies=[Depends(require_permission("linkedin.editar"))],
)


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, LinkedinError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("/posts", response_model=list[LinkedinPostOut], summary="Lista posts (filtra por status/conta)")
async def listar(
    status: str | None = Query(None),
    conta: str | None = Query(None),
) -> list[LinkedinPostOut]:
    try:
        return await linkedin_service.admin.listar(status=status, conta=conta)
    except Exception as e:
        raise _handle(e)


@router.get("/posts/{post_id}", response_model=LinkedinPostOut, summary="Detalhe do post")
async def get(post_id: str) -> LinkedinPostOut:
    try:
        return await linkedin_service.admin.get(post_id)
    except Exception as e:
        raise _handle(e)


@router.post("/redigir", response_model=LinkedinRedacao, summary="IA: brief → post (rascunho pro drawer)")
async def redigir(brief: LinkedinBriefRequest) -> LinkedinRedacao:
    try:
        return await linkedin_service.agente.redigir(brief)
    except Exception as e:
        raise _handle(e)


@router.post("/gerar", response_model=list[LinkedinPostOut], summary="IA autônoma: gera rascunhos (projetos/tendências)")
async def gerar(req: LinkedinGerarRequest) -> list[LinkedinPostOut]:
    try:
        return await linkedin_service.coordenador.gerar(req)
    except Exception as e:
        raise _handle(e)


@router.post("/posts", response_model=LinkedinPostOut, status_code=201, summary="Cria post (rascunho)")
async def criar(payload: LinkedinPostCreate) -> LinkedinPostOut:
    try:
        return await linkedin_service.admin.criar(payload)
    except Exception as e:
        raise _handle(e)


@router.put("/posts/{post_id}", response_model=LinkedinPostOut, summary="Edita post (patch parcial)")
async def atualizar(post_id: str, payload: LinkedinPostUpdate) -> LinkedinPostOut:
    try:
        return await linkedin_service.admin.atualizar(post_id, payload)
    except Exception as e:
        raise _handle(e)


@router.post("/posts/{post_id}/midia/sugerir", response_model=LinkedinPostOut, summary="IA: sugere a mídia ideal (direção de arte)")
async def sugerir_midia(post_id: str) -> LinkedinPostOut:
    try:
        return await linkedin_service.midia.sugerir(post_id)
    except Exception as e:
        raise _handle(e)


@router.post("/posts/{post_id}/imagem", response_model=LinkedinPostOut, summary="IA: gera a imagem do post → MinIO")
async def gerar_imagem(post_id: str, req: GerarImagemLinkedinRequest) -> LinkedinPostOut:
    try:
        return await linkedin_service.midia.gerar_imagem(
            post_id, prompt=req.prompt, alt=req.alt, aspect_ratio=req.aspect_ratio
        )
    except Exception as e:
        raise _handle(e)


@router.patch("/posts/{post_id}/status", response_model=LinkedinPostOut, summary="Muda status (publicar/arquivar)")
async def mudar_status(post_id: str, payload: LinkedinStatusUpdate) -> LinkedinPostOut:
    try:
        return await linkedin_service.admin.mudar_status(post_id, payload.status)
    except Exception as e:
        raise _handle(e)


@router.delete("/posts/{post_id}", status_code=204, summary="Apaga post")
async def deletar(post_id: str) -> None:
    try:
        await linkedin_service.admin.deletar(post_id)
    except Exception as e:
        raise _handle(e)
