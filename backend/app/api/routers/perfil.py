from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import require_permission
from app.api.schemas.pessoal import PerfilMestreResponse, PerfilMestreUpsert
from app.api.services.pessoal import certificado_sync_service, perfil_service
from app.api.services.pessoal.certificado_sync_service import (
    CertificadoSyncError,
    SyncResultado,
)
from app.api.services.pessoal.perfil_service import PerfilError

# Área pessoal: exige pessoal.ver (segurança REAL — o front esconder a aba é
# só UX). Sem a permissão → 403 em qualquer rota deste router.
router = APIRouter(
    prefix="/api/pessoal/perfil",
    tags=["pessoal:perfil"],
    dependencies=[Depends(require_permission("pessoal.ver"))],
)


@router.get("", summary="Retorna o Perfil Mestre ativo (ou null)")
async def get_perfil() -> PerfilMestreResponse | None:
    return await perfil_service.get_perfil()


@router.put("", response_model=PerfilMestreResponse,
            summary="Cria ou atualiza o Perfil Mestre")
async def salvar_perfil(body: PerfilMestreUpsert) -> PerfilMestreResponse:
    try:
        return await perfil_service.salvar_perfil(body)
    except PerfilError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/certificados/sincronizar", response_model=SyncResultado,
             summary="Puxa certificados novos da pasta pública do Drive")
async def sincronizar_certificados() -> SyncResultado:
    try:
        return await certificado_sync_service.sincronizar()
    except CertificadoSyncError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
