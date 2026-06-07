from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

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
             summary="Sobe um comprovante/boleto/nota (multipart) e vincula à transação")
async def upload(
    usuario_id: str = Form(...),
    tipo: str = Form(..., description="boleto/comprovante/nota_fiscal"),
    file: UploadFile = File(...),
    transacao_id: Optional[str] = Form(None),
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
            summary="Lista comprovantes de uma transação (com URL pré-assinada)")
async def listar(transacao_id: str) -> ComprovanteListResponse:
    try:
        return await comprovante_service.listar_por_transacao(transacao_id)
    except Exception as e:
        raise _handle(e)
