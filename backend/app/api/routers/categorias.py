from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import exige_editar, usuario_financas
from app.api.schemas.financas import (
    CategoriaCreate,
    CategoriaResponse,
    CategoriaTreeResponse,
    CategoriaUpdate,
)
from app.api.services.financas import categoria_service
from app.api.services.financas.categoria_service import CategoriaError

# Categorias são globais (árvore compartilhada); exigem login + financas.ver
# em tudo (router-level) e financas.editar nas mutações.
router = APIRouter(
    prefix="/api/financas/categorias",
    tags=["financas:categorias"],
    dependencies=[Depends(usuario_financas)],
)


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, CategoriaError):
        msg = str(e)
        status = 404 if "não encontrada" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=CategoriaTreeResponse,
            summary="Árvore de categorias (raízes com filhos aninhados)")
async def listar() -> CategoriaTreeResponse:
    try:
        return await categoria_service.listar_arvore()
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=CategoriaResponse, status_code=201,
             summary="Cria uma categoria (raiz ou subverba)",
             dependencies=[Depends(exige_editar)])
async def criar(body: CategoriaCreate) -> CategoriaResponse:
    try:
        return await categoria_service.criar_categoria(body)
    except Exception as e:
        raise _handle(e)


@router.get("/{categoria_id}", response_model=CategoriaResponse,
            summary="Detalhe da categoria")
async def detalhe(categoria_id: str) -> CategoriaResponse:
    try:
        return await categoria_service.get_categoria(categoria_id)
    except Exception as e:
        raise _handle(e)


@router.patch("/{categoria_id}", response_model=CategoriaResponse,
              summary="Atualiza nome/pai/ativa (com checagem de ciclo)",
              dependencies=[Depends(exige_editar)])
async def atualizar(categoria_id: str, body: CategoriaUpdate) -> CategoriaResponse:
    try:
        return await categoria_service.atualizar_categoria(categoria_id, body)
    except Exception as e:
        raise _handle(e)


@router.delete("/{categoria_id}", status_code=204,
               summary="Remove a categoria (filhos somem por cascata)",
               dependencies=[Depends(exige_editar)])
async def remover(categoria_id: str) -> None:
    try:
        await categoria_service.deletar_categoria(categoria_id)
    except Exception as e:
        raise _handle(e)
