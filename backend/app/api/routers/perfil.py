from fastapi import APIRouter, HTTPException

from app.api.schemas.pessoal import PerfilMestreResponse, PerfilMestreUpsert
from app.api.services.pessoal import perfil_service
from app.api.services.pessoal.perfil_service import PerfilError

router = APIRouter(prefix="/api/pessoal/perfil", tags=["pessoal:perfil"])


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
