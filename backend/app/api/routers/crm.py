from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.crm import (
    AtividadeListItem,
    AtividadeListResponse,
    AtividadeUpsert,
    ContatoListItem,
    ContatoListResponse,
    ContatoUpsert,
    CrmDashboard,
    CrmMetricas,
    EmpresaDetalhe,
    EmpresaListResponse,
    EmpresaRelacionados,
    EmpresaUpsert,
    KanbanResponse,
    NegocioListItem,
    NegociosPipeline,
    NegocioUpsert,
    OpcaoCreate,
    OpcaoOut,
    OpcaoReorder,
    OpcaoUpdate,
    ProjetoListItem,
    ProjetoListResponse,
    ProjetoUpsert,
    RecordDetalhe,
    RecordPatch,
)
from app.api.services import crm_service
from app.api.services.crm_service import CrmError
from app.exporters.notion.importer import ResultadoImport, importar

router = APIRouter(prefix="/api/crm", tags=["crm"])


@router.post("/sincronizar-notion", response_model=ResultadoImport,
             summary="Puxa as 5 bases do Notion pro Postgres (idempotente)")
async def sincronizar_notion() -> ResultadoImport:
    try:
        return await importar()
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Falha ao sincronizar: {type(e).__name__}: {e}"
        ) from e


def _erro(e: CrmError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(e))


# ── Empresas ─────────────────────────────────────────────────────────

@router.get("/empresas", response_model=EmpresaListResponse,
            summary="Lista empresas (filtros + ordenação)")
async def listar_empresas(
    status: str | None = Query(None),
    busca: str | None = Query(None),
    setor: str | None = Query(None),
    estado: str | None = Query(None),
    cidade: str | None = Query(None),
    tamanho: str | None = Query(None),
    como_conheceu: str | None = Query(None),
    score_min: int | None = Query(None),
    ordenar_por: str | None = Query(None),
    desc: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> EmpresaListResponse:
    return await crm_service.listar_empresas(
        status=status, busca=busca, setor=setor, estado=estado, cidade=cidade,
        tamanho=tamanho, como_conheceu=como_conheceu, score_min=score_min,
        ordenar_por=ordenar_por, desc=desc, limit=limit, offset=offset,
    )


@router.get("/empresas/facetas",
            summary="Valores distintos pros dropdowns de filtro")
async def facetas() -> dict[str, list[str]]:
    return await crm_service.facetas()


@router.get("/opcoes",
            summary="Opções dos selects do CRM (lidas da tabela gerenciável)")
async def opcoes() -> dict[str, list[str]]:
    return await crm_service.opcoes()


@router.get("/opcoes/cores",
            summary="Mapa grupo→valor→cor das opções (pra pintar as pílulas)")
async def opcoes_cores() -> dict[str, dict[str, str]]:
    return await crm_service.opcoes_cores()


@router.get("/opcoes/gerenciar", response_model=list[OpcaoOut],
            summary="Lista todas as opções (com cor/ordem/ativo) p/ gerenciar")
async def listar_opcoes() -> list[OpcaoOut]:
    return await crm_service.listar_opcoes()


@router.post("/opcoes", response_model=OpcaoOut, status_code=201,
             summary="Cria uma opção de select")
async def criar_opcao(body: OpcaoCreate) -> OpcaoOut:
    try:
        return await crm_service.criar_opcao(body)
    except CrmError as e:
        raise _erro(e) from e


@router.patch("/opcoes/{opcao_id}", response_model=OpcaoOut,
              summary="Edita uma opção (valor/cor/ativo)")
async def atualizar_opcao(opcao_id: str, body: OpcaoUpdate) -> OpcaoOut:
    try:
        return await crm_service.atualizar_opcao(opcao_id, body)
    except CrmError as e:
        raise _erro(e) from e


@router.delete("/opcoes/{opcao_id}", status_code=204,
               summary="Exclui uma opção")
async def excluir_opcao(opcao_id: str) -> None:
    try:
        await crm_service.excluir_opcao(opcao_id)
    except CrmError as e:
        raise _erro(e) from e


@router.post("/opcoes/reordenar", response_model=list[OpcaoOut],
             summary="Reordena as opções de um grupo")
async def reordenar_opcoes(body: OpcaoReorder) -> list[OpcaoOut]:
    try:
        return await crm_service.reordenar_opcoes(body)
    except CrmError as e:
        raise _erro(e) from e


@router.post("/empresas", response_model=EmpresaDetalhe, status_code=201,
             summary="Cria uma empresa")
async def criar_empresa(body: EmpresaUpsert) -> EmpresaDetalhe:
    try:
        return await crm_service.criar_empresa(body)
    except CrmError as e:
        raise _erro(e) from e


@router.get("/empresas/{empresa_id}", response_model=EmpresaDetalhe,
            summary="Detalhe de uma empresa (com contatos e sócios)")
async def get_empresa(empresa_id: str) -> EmpresaDetalhe:
    empresa = await crm_service.get_empresa(empresa_id)
    if empresa is None:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return empresa


@router.get("/empresas/{empresa_id}/relacionados", response_model=EmpresaRelacionados,
            summary="Negócios, projetos e atividades ligados à empresa (ficha 360)")
async def empresa_relacionados(empresa_id: str) -> EmpresaRelacionados:
    try:
        return await crm_service.empresa_relacionados(empresa_id)
    except CrmError as e:
        raise _erro(e) from e


@router.put("/empresas/{empresa_id}", response_model=EmpresaDetalhe,
            summary="Edita uma empresa")
async def atualizar_empresa(empresa_id: str, body: EmpresaUpsert) -> EmpresaDetalhe:
    try:
        return await crm_service.atualizar_empresa(empresa_id, body)
    except CrmError as e:
        raise _erro(e) from e


@router.delete("/empresas/{empresa_id}", status_code=204,
               summary="Exclui uma empresa")
async def excluir_empresa(empresa_id: str) -> None:
    try:
        await crm_service.excluir_empresa(empresa_id)
    except CrmError as e:
        raise _erro(e) from e


# ── Visões agregadas ─────────────────────────────────────────────────

@router.get("/kanban", response_model=KanbanResponse,
            summary="Empresas agrupadas por status (board do pipeline)")
async def kanban() -> KanbanResponse:
    return await crm_service.kanban()


@router.get("/metricas", response_model=CrmMetricas,
            summary="Totais do CRM (empresas, contatos, por status)")
async def metricas() -> CrmMetricas:
    return await crm_service.metricas()


@router.get("/dashboard", response_model=CrmDashboard,
            summary="Dashboard comercial (pipeline, atividades, projetos)")
async def dashboard() -> CrmDashboard:
    return await crm_service.dashboard()


@router.get("/record/{tipo}/{registro_id}", response_model=RecordDetalhe,
            summary="Detalhe navegável de qualquer registro (relações clicáveis)")
async def record_detalhe(tipo: str, registro_id: str) -> RecordDetalhe:
    try:
        return await crm_service.record_detalhe(tipo, registro_id)
    except CrmError as e:
        raise _erro(e) from e


@router.patch("/record/{tipo}/{registro_id}", response_model=RecordDetalhe,
              summary="Edita campos parciais de qualquer registro (edição inline)")
async def patch_record(
    tipo: str, registro_id: str, body: RecordPatch
) -> RecordDetalhe:
    try:
        return await crm_service.patch_record(tipo, registro_id, body.campos)
    except CrmError as e:
        raise _erro(e) from e


# ── Contatos ─────────────────────────────────────────────────────────

@router.get("/contatos", response_model=ContatoListResponse,
            summary="Lista contatos (filtros)")
async def listar_contatos(
    busca: str | None = Query(None),
    empresa_id: str | None = Query(None),
    decisor: bool | None = Query(None),
    origem: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ContatoListResponse:
    try:
        return await crm_service.listar_contatos(
            busca=busca, empresa_id=empresa_id, decisor=decisor,
            origem=origem, limit=limit, offset=offset,
        )
    except CrmError as e:
        raise _erro(e) from e


@router.post("/contatos", response_model=ContatoListItem, status_code=201,
             summary="Cria um contato")
async def criar_contato(body: ContatoUpsert) -> ContatoListItem:
    try:
        return await crm_service.criar_contato(body)
    except CrmError as e:
        raise _erro(e) from e


@router.put("/contatos/{contato_id}", response_model=ContatoListItem,
            summary="Edita um contato")
async def atualizar_contato(contato_id: str, body: ContatoUpsert) -> ContatoListItem:
    try:
        return await crm_service.atualizar_contato(contato_id, body)
    except CrmError as e:
        raise _erro(e) from e


@router.delete("/contatos/{contato_id}", status_code=204,
               summary="Exclui um contato")
async def excluir_contato(contato_id: str) -> None:
    try:
        await crm_service.excluir_contato(contato_id)
    except CrmError as e:
        raise _erro(e) from e


# ── Negócios (pipeline) · Atividades · Projetos ──────────────────────

@router.get("/negocios", response_model=list[NegocioListItem],
            summary="Lista os negócios do pipeline")
async def listar_negocios() -> list[NegocioListItem]:
    return await crm_service.listar_negocios()


@router.get("/negocios/pipeline", response_model=NegociosPipeline,
            summary="Negócios agrupados por estágio (com forecast ponderado)")
async def pipeline_negocios() -> NegociosPipeline:
    return await crm_service.pipeline_negocios()


@router.post("/negocios", response_model=NegocioListItem, status_code=201,
             summary="Cria um negócio")
async def criar_negocio(body: NegocioUpsert) -> NegocioListItem:
    try:
        return await crm_service.criar_negocio(body)
    except CrmError as e:
        raise _erro(e) from e


@router.put("/negocios/{negocio_id}", response_model=NegocioListItem,
            summary="Edita um negócio")
async def atualizar_negocio(negocio_id: str, body: NegocioUpsert) -> NegocioListItem:
    try:
        return await crm_service.atualizar_negocio(negocio_id, body)
    except CrmError as e:
        raise _erro(e) from e


@router.delete("/negocios/{negocio_id}", status_code=204, summary="Exclui um negócio")
async def excluir_negocio(negocio_id: str) -> None:
    try:
        await crm_service.excluir_negocio(negocio_id)
    except CrmError as e:
        raise _erro(e) from e


@router.patch("/negocios/{negocio_id}/estagio", response_model=NegocioListItem,
              summary="Move o negócio de estágio (drag no pipeline)")
async def mover_negocio_estagio(
    negocio_id: str, estagio: str = Query(...),
) -> NegocioListItem:
    try:
        return await crm_service.mover_negocio_estagio(negocio_id, estagio)
    except CrmError as e:
        raise _erro(e) from e


@router.get("/atividades", response_model=AtividadeListResponse,
            summary="Lista as atividades/follow-ups")
async def listar_atividades() -> AtividadeListResponse:
    return await crm_service.listar_atividades()


@router.post("/atividades", response_model=AtividadeListItem, status_code=201,
             summary="Cria uma atividade")
async def criar_atividade(body: AtividadeUpsert) -> AtividadeListItem:
    try:
        return await crm_service.criar_atividade(body)
    except CrmError as e:
        raise _erro(e) from e


@router.put("/atividades/{atividade_id}", response_model=AtividadeListItem,
            summary="Edita uma atividade")
async def atualizar_atividade(atividade_id: str, body: AtividadeUpsert) -> AtividadeListItem:
    try:
        return await crm_service.atualizar_atividade(atividade_id, body)
    except CrmError as e:
        raise _erro(e) from e


@router.delete("/atividades/{atividade_id}", status_code=204,
               summary="Exclui uma atividade")
async def excluir_atividade(atividade_id: str) -> None:
    try:
        await crm_service.excluir_atividade(atividade_id)
    except CrmError as e:
        raise _erro(e) from e


@router.get("/projetos", response_model=ProjetoListResponse,
            summary="Lista os projetos/entregas")
async def listar_projetos() -> ProjetoListResponse:
    return await crm_service.listar_projetos()


@router.post("/projetos", response_model=ProjetoListItem, status_code=201,
             summary="Cria um projeto")
async def criar_projeto(body: ProjetoUpsert) -> ProjetoListItem:
    try:
        return await crm_service.criar_projeto(body)
    except CrmError as e:
        raise _erro(e) from e


@router.put("/projetos/{projeto_id}", response_model=ProjetoListItem,
            summary="Edita um projeto")
async def atualizar_projeto(projeto_id: str, body: ProjetoUpsert) -> ProjetoListItem:
    try:
        return await crm_service.atualizar_projeto(projeto_id, body)
    except CrmError as e:
        raise _erro(e) from e


@router.delete("/projetos/{projeto_id}", status_code=204, summary="Exclui um projeto")
async def excluir_projeto(projeto_id: str) -> None:
    try:
        await crm_service.excluir_projeto(projeto_id)
    except CrmError as e:
        raise _erro(e) from e
