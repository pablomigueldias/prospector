from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies.financas import exige_editar, financas_usuario_id
from app.api.schemas.financas import ImportarBoletoResponse
from app.api.services.financas import importador_service
from app.api.services.financas.importador_service import ImportadorError

router = APIRouter(prefix="/api/financas/importar", tags=["financas:importador"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, ImportadorError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/boleto", response_model=ImportarBoletoResponse,
             summary="Lê um boleto (PDF/foto) e cria a despesa com as verbas",
             dependencies=[Depends(exige_editar)])
async def importar_boleto(
    file: UploadFile = File(...),
    categoria_id: Optional[str] = Form(None),
    usuario_id: str = Depends(financas_usuario_id),
) -> ImportarBoletoResponse:
    try:
        conteudo = await file.read()
        return await importador_service.importar_boleto(
            usuario_id=usuario_id,
            conteudo=conteudo,
            nome_original=file.filename,
            content_type=file.content_type,
            categoria_id=categoria_id,
        )
    except Exception as e:
        raise _handle(e)
