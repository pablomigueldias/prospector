from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.prospector import (
    LeadHistoryResponse,
    LeadOut,
    ProspectorManualRequest,
    ProspectorPreviewResponse,
    ProspectorRunResponse,
)
from app.api.services import leads_reader
from app.api.services.prospector_service import (
    ProspectorError,
    executar_pipeline_completo,
    preview_lead,
)


router = APIRouter(prefix="/api/agents/prospector", tags=["prospector"])


@router.post(
    "/preview",
    response_model=ProspectorPreviewResponse,
    summary="Monta o Lead a partir do CNPJ sem enviar pro Notion",
)
def prospector_preview(body: ProspectorManualRequest) -> ProspectorPreviewResponse:
    try:
        lead, fonte = preview_lead(
            cnpj=body.cnpj,
            site=body.site,
            instagram=body.instagram,
            facebook=body.facebook,
            linkedin=body.linkedin,
            email=body.email,
            telefone=body.telefone,
            whatsapp=body.whatsapp,
            run_ai=False,
        )
    except ProspectorError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return ProspectorPreviewResponse(
        fonte_cnpj=fonte,
        lead=_lead_to_out(lead),
    )


@router.post(
    "/manual",
    response_model=ProspectorRunResponse,
    summary="Executa o pipeline completo e envia pro Notion",
)
def prospector_manual(body: ProspectorManualRequest) -> ProspectorRunResponse:
    try:
        lead, fonte = executar_pipeline_completo(
            cnpj=body.cnpj,
            site=body.site,
            instagram=body.instagram,
            facebook=body.facebook,
            linkedin=body.linkedin,
            email=body.email,
            telefone=body.telefone,
            whatsapp=body.whatsapp,
        )
    except ProspectorError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado no pipeline: {type(e).__name__}: {e}",
        )

    contato_ids = [c.notion_page_id for c in lead.contatos if c.notion_page_id]
    return ProspectorRunResponse(
        fonte_cnpj=fonte,
        lead=_lead_to_out(lead),
        notion_empresa_id=lead.empresa.notion_page_id,
        notion_contatos_ids=contato_ids,
    )


@router.get(
    "/leads",
    response_model=LeadHistoryResponse,
    summary="Lista os últimos leads enviados",
)
def prospector_history(
    limit: int = Query(20, ge=1, le=100, description="Quantos retornar"),
) -> LeadHistoryResponse:
    items = leads_reader.ler_historico(limit=limit)
    return LeadHistoryResponse(items=items, total=len(items))

@router.get(
        "/db-stats",
        summary="Contagem de registros no Postgres"
)
def prospector_db_stats() -> dict:
    from app.db.lead_persistence import db_stats_sync
    try:
        return {"success": True, "postgres": db_stats_sync()}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Postgress indispinível {type(e).__name__}: {e}",
        )


def _lead_to_out(lead) -> LeadOut:
    emp = lead.empresa
    return LeadOut.model_validate({
        "empresa": {
            "nome": emp.nome,
            "razao_social": emp.razao_social,
            "cnpj": emp.cnpj,
            "cidade": emp.cidade,
            "estado": emp.estado,
            "setor": emp.setor,
            "tamanho": emp.tamanho,
            "capital_social": emp.capital_social,
            "site": getattr(emp, "site", None),
            "instagram": getattr(emp, "instagram", None),
            "facebook": getattr(emp, "facebook", None),
            "notas": emp.notas,
            "notion_page_id": emp.notion_page_id,
        },
        "contatos": [
            {
                "nome": c.nome,
                "cargo": c.cargo,
                "email": c.email,
                "telefone": c.telefone,
                "whatsapp": c.whatsapp,
                "linkedin": c.linkedin,
                "decisor": c.decisor,
            }
            for c in lead.contatos
        ],
    })
