"""API ADMIN do blog (P5 §6.B1) — CRUD/publicar pelo studio.

Autenticada (`blog.editar`) e separada da pública (`/api/public/blog`). Aqui é a
mesa de edição do Pablo: criar/editar rascunho, publicar (checkpoint humano),
arquivar. O agente de IA (B2+) escreve via estes mesmos services.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.api.dependencies.auth import require_permission
from app.api.schemas.blog import (
    BlogBriefRequest,
    BlogPautaGerarRequest,
    BlogPautaItem,
    BlogPautaManualCreate,
    BlogPautaUpdate,
    BlogPostAdmin,
    BlogPostCreate,
    BlogPostUpdate,
    BlogRedacao,
    BlogStatusUpdate,
    ChecklistSeoRequest,
    ChecklistSeoResponse,
    GerarImagemRequest,
)
from app.api.services import blog_service
from app.api.services.blog_service import BlogError

router = APIRouter(
    prefix="/api/blog",
    tags=["blog"],
    dependencies=[Depends(require_permission("blog.editar"))],
)


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, BlogError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("/posts", response_model=list[BlogPostAdmin], summary="Lista posts (todos os status)")
async def listar(status: str | None = Query(None)) -> list[BlogPostAdmin]:
    try:
        return await blog_service.admin.listar(status=status)
    except Exception as e:
        raise _handle(e)


@router.get("/posts/{post_id}", response_model=BlogPostAdmin, summary="Detalhe do post")
async def get(post_id: str) -> BlogPostAdmin:
    try:
        return await blog_service.admin.get(post_id)
    except Exception as e:
        raise _handle(e)


@router.post("/redigir", response_model=BlogRedacao, summary="IA: brief → artigo (rascunho pro editor)")
async def redigir(brief: BlogBriefRequest) -> BlogRedacao:
    try:
        return await blog_service.agente.redigir(brief)
    except Exception as e:
        raise _handle(e)


@router.post("/checklist", response_model=ChecklistSeoResponse, summary="Score SEO do conteúdo (determinístico)")
async def checklist(payload: ChecklistSeoRequest) -> ChecklistSeoResponse:
    try:
        return blog_service.agente.checklist(payload)
    except Exception as e:
        raise _handle(e)


# ── Motor de pauta (B3) ──────────────────────────────────────────
@router.get("/pautas", response_model=list[BlogPautaItem], summary="Backlog de pautas (por score)")
async def listar_pautas(status: str | None = Query(None)) -> list[BlogPautaItem]:
    try:
        return await blog_service.pauta.listar(status)
    except Exception as e:
        raise _handle(e)


@router.post("/pautas/gerar", response_model=list[BlogPautaItem], summary="IA: gera pautas (3 fontes)")
async def gerar_pautas(req: BlogPautaGerarRequest) -> list[BlogPautaItem]:
    try:
        return await blog_service.pauta.gerar(req)
    except Exception as e:
        raise _handle(e)


@router.post("/pautas/{pauta_id}/escrever", response_model=BlogPostAdmin, summary="1 clique: pauta → rascunho (IA)")
async def escrever_pauta(pauta_id: str) -> BlogPostAdmin:
    try:
        return await blog_service.coordenador.escrever_pauta(pauta_id)
    except Exception as e:
        raise _handle(e)


@router.post("/pautas", response_model=BlogPautaItem, status_code=201, summary="Cria pauta manual")
async def criar_pauta(payload: BlogPautaManualCreate) -> BlogPautaItem:
    try:
        return await blog_service.pauta.criar_manual(payload)
    except Exception as e:
        raise _handle(e)


@router.put("/pautas/{pauta_id}", response_model=BlogPautaItem, summary="Edita pauta (status/score/…)")
async def atualizar_pauta(pauta_id: str, payload: BlogPautaUpdate) -> BlogPautaItem:
    try:
        return await blog_service.pauta.atualizar(pauta_id, payload)
    except Exception as e:
        raise _handle(e)


@router.delete("/pautas/{pauta_id}", status_code=204, summary="Apaga pauta")
async def deletar_pauta(pauta_id: str) -> None:
    try:
        await blog_service.pauta.deletar(pauta_id)
    except Exception as e:
        raise _handle(e)


@router.post("/posts", response_model=BlogPostAdmin, status_code=201, summary="Cria post (rascunho)")
async def criar(payload: BlogPostCreate) -> BlogPostAdmin:
    try:
        return await blog_service.admin.criar(payload)
    except Exception as e:
        raise _handle(e)


@router.put("/posts/{post_id}", response_model=BlogPostAdmin, summary="Edita post (patch parcial)")
async def atualizar(post_id: str, payload: BlogPostUpdate) -> BlogPostAdmin:
    try:
        return await blog_service.admin.atualizar(post_id, payload)
    except Exception as e:
        raise _handle(e)


@router.post("/posts/{post_id}/imagem", response_model=BlogPostAdmin, summary="IA: gera imagem (capa/seção) → MinIO")
async def gerar_imagem(post_id: str, req: GerarImagemRequest) -> BlogPostAdmin:
    try:
        return await blog_service.imagens.gerar(
            post_id, papel=req.papel, prompt=req.prompt, aspect_ratio=req.aspect_ratio
        )
    except Exception as e:
        raise _handle(e)


@router.post("/posts/{post_id}/imagem/upload", response_model=BlogPostAdmin, summary="Sobe a imagem final (editada fora)")
async def upload_imagem(
    post_id: str,
    arquivo: UploadFile = File(...),
    papel: str = Form("cover"),
    alt: str | None = Form(None),
) -> BlogPostAdmin:
    try:
        data = await arquivo.read()
        return await blog_service.imagens.upload(
            post_id,
            papel=papel,
            data=data,
            content_type=arquivo.content_type or "image/png",
            alt=alt,
        )
    except Exception as e:
        raise _handle(e)


@router.patch("/posts/{post_id}/status", response_model=BlogPostAdmin, summary="Muda status (publicar/arquivar)")
async def mudar_status(post_id: str, payload: BlogStatusUpdate) -> BlogPostAdmin:
    try:
        return await blog_service.admin.mudar_status(post_id, payload.status)
    except Exception as e:
        raise _handle(e)


@router.delete("/posts/{post_id}", status_code=204, summary="Apaga post")
async def deletar(post_id: str) -> None:
    try:
        await blog_service.admin.deletar(post_id)
    except Exception as e:
        raise _handle(e)
