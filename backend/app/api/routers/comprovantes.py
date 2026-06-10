from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies.financas import exige_editar, financas_usuario_id
from app.api.schemas.financas import ComprovanteListResponse, ComprovanteResponse
from app.api.services.financas import comprovante_service
from app.api.services.financas.comprovante_service import ComprovanteError

router = APIRouter(prefix="/api/financas/comprovantes", tags=["financas:comprovantes"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, ComprovanteError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("", response_model=ComprovanteResponse, status_code=201,
             summary="Sobe um comprovante/boleto/nota (multipart) e vincula à transação",
             dependencies=[Depends(exige_editar)])
async def upload(
    tipo: str = Form(..., description="boleto/comprovante/nota_fiscal"),
    file: UploadFile = File(...),
    transacao_id: Optional[str] = Form(None),
    usuario_id: str = Depends(financas_usuario_id),
) -> ComprovanteResponse:
    try:
        conteudo = await file.read()
        return await comprovante_service.salvar_comprovante(
            usuario_id=usuario_id,
            tipo=tipo,
            conteudo=conteudo,
            nome_original=file.filename,
            content_type=file.content_type,
            transacao_id=transacao_id,
        )
    except Exception as e:
        raise _handle(e)


@router.get("", response_model=ComprovanteListResponse,
            summary="Lista comprovantes por transação OU do usuário logado (galeria)")
async def listar(
    transacao_id: Optional[str] = None,
    tipo: Optional[str] = None,
    usuario_id: str = Depends(financas_usuario_id),
) -> ComprovanteListResponse:
    try:
        if transacao_id:
            return await comprovante_service.listar_por_transacao(transacao_id)
        return await comprovante_service.listar_por_usuario(usuario_id, tipo=tipo)
    except HTTPException:
        raise
    except Exception as e:
        raise _handle(e)
