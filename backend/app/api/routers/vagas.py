
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import require_permission
from app.api.schemas.pessoal import (
    AnalisarVagaResponse,
    CandidaturaEmailItem,
    EstudoVagasResponse,
    ExtrairVagaRequest,
    ExtrairVagaResponse,
    GerarCandidaturaRequest,
    GerarCandidaturaResponse,
    GerarCurriculoResponse,
    VagaCreate,
    VagaListResponse,
    VagaResponse,
    VagasMetricas,
    VagaUpdate,
)
from app.api.services.pessoal import vaga_service
from app.api.services.pessoal.vaga_service import VagaError

router = APIRouter(
    prefix="/api/pessoal/vagas",
    tags=["pessoal:vagas"],
    dependencies=[Depends(require_permission("pessoal.ver"))],
)


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, VagaError):
        # "não encontrada" → 404; resto → 400
        msg = str(e)
        status = 404 if "não encontrada" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=VagaListResponse, summary="Lista as vagas")
async def listar(
    status: str | None = None,
    busca: str | None = None,
    match_min: int | None = None,
    modelo: str | None = None,
    fonte: str | None = None,
    tem_rascunho: bool | None = None,
    ordenar_por: str = "match",
) -> VagaListResponse:
    try:
        return await vaga_service.listar_vagas(
            status=status,
            busca=busca,
            match_min=match_min,
            modelo=modelo,
            fonte=fonte,
            tem_rascunho=tem_rascunho,
            ordenar_por=ordenar_por,
        )
    except Exception as e:
        raise _handle(e)


@router.get("/metricas", response_model=VagasMetricas,
            summary="Funil e taxas de resposta/entrevista")
async def metricas() -> VagasMetricas:
    try:
        return await vaga_service.metricas()
    except Exception as e:
        raise _handle(e)


@router.get("/estudo", response_model=EstudoVagasResponse,
            summary="O que a maioria das vagas pede e você ainda não tem (lista de estudo)")
async def estudo() -> EstudoVagasResponse:
    try:
        return await vaga_service.estudo_gaps()
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=VagaResponse, status_code=201,
             summary="Registra uma vaga (cola a descrição)")
async def criar(body: VagaCreate) -> VagaResponse:
    try:
        return await vaga_service.criar_vaga(body)
    except Exception as e:
        raise _handle(e)


@router.post("/extrair", response_model=ExtrairVagaResponse,
             summary="Extrai campos do texto colado ou da URL (pré-preenche o form)")
async def extrair(body: ExtrairVagaRequest) -> ExtrairVagaResponse:
    try:
        return await vaga_service.extrair_vaga(body.texto, body.url)
    except Exception as e:
        raise _handle(e)


@router.get("/{vaga_id}", response_model=VagaResponse, summary="Detalhe da vaga")
async def detalhe(vaga_id: str) -> VagaResponse:
    try:
        return await vaga_service.get_vaga(vaga_id)
    except Exception as e:
        raise _handle(e)


@router.patch("/{vaga_id}", response_model=VagaResponse,
              summary="Atualiza campos/status da vaga")
async def atualizar(vaga_id: str, body: VagaUpdate) -> VagaResponse:
    try:
        return await vaga_service.atualizar_vaga(vaga_id, body)
    except Exception as e:
        raise _handle(e)


@router.delete("/{vaga_id}", status_code=204, summary="Remove a vaga")
async def remover(vaga_id: str) -> None:
    try:
        await vaga_service.deletar_vaga(vaga_id)
    except Exception as e:
        raise _handle(e)


@router.post("/{vaga_id}/analisar", response_model=AnalisarVagaResponse,
             summary="Destrincha a vaga e cruza com o Perfil Mestre")
async def analisar(vaga_id: str) -> AnalisarVagaResponse:
    try:
        return await vaga_service.analisar_vaga(vaga_id)
    except Exception as e:
        raise _handle(e)


@router.post("/{vaga_id}/candidatura", response_model=GerarCandidaturaResponse,
             summary="Rascunha e-mail + carta (PARA no rascunho, não envia)")
async def gerar_candidatura(
    vaga_id: str, body: GerarCandidaturaRequest
) -> GerarCandidaturaResponse:
    try:
        return await vaga_service.gerar_candidatura(vaga_id, body)
    except Exception as e:
        raise _handle(e)


@router.post("/{vaga_id}/curriculo", response_model=GerarCurriculoResponse,
             summary="Gera currículo ATS sob medida pra vaga (PDF sai no front)")
async def gerar_curriculo(vaga_id: str) -> GerarCurriculoResponse:
    try:
        return await vaga_service.gerar_curriculo(vaga_id)
    except Exception as e:
        raise _handle(e)


@router.get("/{vaga_id}/rascunhos", response_model=list[CandidaturaEmailItem],
            summary="Rascunhos já gerados pra esta vaga")
async def rascunhos(vaga_id: str) -> list[CandidaturaEmailItem]:
    try:
        return await vaga_service.listar_rascunhos(vaga_id)
    except Exception as e:
        raise _handle(e)
