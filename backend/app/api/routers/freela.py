"""Rotas do Agente Freelancer (Workana) — CRM de propostas + precificador.

A IA não toca na Workana: aqui é só a sua mesa de trabalho (organizar,
precificar, marcar status). As fases de IA (analisar/redigir/selecionar)
entram em endpoints próprios depois.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import require_permission
from app.api.schemas.freela import (
    AnalisarProjetoResponse,
    ChecklistResponse,
    ClienteCreate,
    ClienteResponse,
    ClienteUpdate,
    CorrigirRequest,
    ExtrairProjetoRequest,
    ExtrairProjetoResponse,
    KanbanResponse,
    MetricasResponse,
    NegociarRequest,
    NegociarResponse,
    PlanoMetaRequest,
    PlanoMetaResponse,
    PlataformaResponse,
    PrecificarRequest,
    PrecificarResponse,
    ProjetoCreate,
    ProjetoListResponse,
    ProjetoResponse,
    ProjetoUpdate,
    PropostaCreate,
    PropostaResponse,
    PropostaStatusUpdate,
    PropostaUpdate,
    CapacidadeResponse,
    RedigirRequest,
    RedigirResponse,
    TaxaPorStackResponse,
)
from app.api.services.pessoal import freela_service
from app.api.services.pessoal.freela_service import FreelaError

router = APIRouter(
    prefix="/api/pessoal/freela",
    tags=["pessoal:freela"],
    dependencies=[Depends(require_permission("pessoal.ver"))],
)


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, FreelaError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


# ── Plataformas ──────────────────────────────────────────────────
@router.get("/plataformas", response_model=list[PlataformaResponse],
            summary="Plataformas (Workana...) e suas faixas de comissão")
async def listar_plataformas() -> list[PlataformaResponse]:
    try:
        return await freela_service.listar_plataformas()
    except Exception as e:
        raise _handle(e)


# ── Painel ───────────────────────────────────────────────────────
@router.get("/kanban", response_model=KanbanResponse,
            summary="Board de propostas por status")
async def kanban() -> KanbanResponse:
    try:
        return await freela_service.kanban()
    except Exception as e:
        raise _handle(e)


@router.get("/metricas", response_model=MetricasResponse,
            summary="Taxas de resposta/fechamento e líquido total")
async def metricas() -> MetricasResponse:
    try:
        return await freela_service.metricas()
    except Exception as e:
        raise _handle(e)


@router.get("/metricas/por-stack", response_model=TaxaPorStackResponse,
            summary="Taxa de resposta por stack/categoria — onde insistir")
async def metricas_por_stack() -> TaxaPorStackResponse:
    try:
        return await freela_service.taxa_por_stack()
    except Exception as e:
        raise _handle(e)


@router.get("/capacidade", response_model=CapacidadeResponse,
            summary="Capacidade da semana vs horas comprometidas (anti-furada)")
async def capacidade() -> CapacidadeResponse:
    try:
        return await freela_service.capacidade()
    except Exception as e:
        raise _handle(e)


@router.post("/precificar", response_model=PrecificarResponse,
             summary="Líquido desejado → quanto cotar (embute a comissão)")
async def precificar(body: PrecificarRequest) -> PrecificarResponse:
    try:
        return await freela_service.precificar(body)
    except Exception as e:
        raise _handle(e)


@router.post("/meta/plano", response_model=PlanoMetaResponse,
             summary="Meta líquida → valor-hora alvo, propostas/semana, gargalo e fase da rampa")
async def plano_meta(body: PlanoMetaRequest) -> PlanoMetaResponse:
    try:
        return await freela_service.plano_meta(body)
    except Exception as e:
        raise _handle(e)


# ── Clientes ─────────────────────────────────────────────────────
@router.get("/clientes", response_model=list[ClienteResponse], summary="Lista clientes")
async def listar_clientes() -> list[ClienteResponse]:
    try:
        return await freela_service.listar_clientes()
    except Exception as e:
        raise _handle(e)


@router.post("/clientes", response_model=ClienteResponse, status_code=201,
             summary="Cadastra cliente")
async def criar_cliente(body: ClienteCreate) -> ClienteResponse:
    try:
        return await freela_service.criar_cliente(body)
    except Exception as e:
        raise _handle(e)


@router.get("/clientes/{cliente_id}", response_model=ClienteResponse, summary="Detalhe do cliente")
async def detalhe_cliente(cliente_id: str) -> ClienteResponse:
    try:
        return await freela_service.get_cliente(cliente_id)
    except Exception as e:
        raise _handle(e)


@router.patch("/clientes/{cliente_id}", response_model=ClienteResponse, summary="Atualiza cliente")
async def atualizar_cliente(cliente_id: str, body: ClienteUpdate) -> ClienteResponse:
    try:
        return await freela_service.atualizar_cliente(cliente_id, body)
    except Exception as e:
        raise _handle(e)


@router.delete("/clientes/{cliente_id}", status_code=204, summary="Remove cliente")
async def remover_cliente(cliente_id: str) -> None:
    try:
        await freela_service.deletar_cliente(cliente_id)
    except Exception as e:
        raise _handle(e)


# ── Projetos ─────────────────────────────────────────────────────
@router.get("/projetos", response_model=ProjetoListResponse,
            summary="Fila de oportunidades (ordenada por fit)")
async def listar_projetos() -> ProjetoListResponse:
    try:
        return await freela_service.listar_projetos()
    except Exception as e:
        raise _handle(e)


@router.post("/projetos", response_model=ProjetoResponse, status_code=201,
             summary="Registra um projeto (cola o texto)")
async def criar_projeto(body: ProjetoCreate) -> ProjetoResponse:
    try:
        return await freela_service.criar_projeto(body)
    except Exception as e:
        raise _handle(e)


@router.post("/projetos/extrair", response_model=ExtrairProjetoResponse,
             summary="Extrai campos do texto colado ou da URL (pré-preenche o form)")
async def extrair_projeto(body: ExtrairProjetoRequest) -> ExtrairProjetoResponse:
    try:
        return await freela_service.extrair_projeto(body.texto, body.url)
    except Exception as e:
        raise _handle(e)


@router.get("/projetos/{projeto_id}", response_model=ProjetoResponse, summary="Detalhe do projeto")
async def detalhe_projeto(projeto_id: str) -> ProjetoResponse:
    try:
        return await freela_service.get_projeto(projeto_id)
    except Exception as e:
        raise _handle(e)


@router.patch("/projetos/{projeto_id}", response_model=ProjetoResponse, summary="Atualiza projeto")
async def atualizar_projeto(projeto_id: str, body: ProjetoUpdate) -> ProjetoResponse:
    try:
        return await freela_service.atualizar_projeto(projeto_id, body)
    except Exception as e:
        raise _handle(e)


@router.delete("/projetos/{projeto_id}", status_code=204, summary="Remove projeto")
async def remover_projeto(projeto_id: str) -> None:
    try:
        await freela_service.deletar_projeto(projeto_id)
    except Exception as e:
        raise _handle(e)


@router.get("/projetos/{projeto_id}/propostas", response_model=list[PropostaResponse],
            summary="Propostas de um projeto")
async def propostas_do_projeto(projeto_id: str) -> list[PropostaResponse]:
    try:
        return await freela_service.listar_propostas_do_projeto(projeto_id)
    except Exception as e:
        raise _handle(e)


@router.post("/projetos/{projeto_id}/analisar", response_model=AnalisarProjetoResponse,
             summary="Analisa o projeto (fit + red flags + ganchos) com IA")
async def analisar_projeto(projeto_id: str) -> AnalisarProjetoResponse:
    try:
        return await freela_service.analisar_projeto(projeto_id)
    except Exception as e:
        raise _handle(e)


# ── Propostas ────────────────────────────────────────────────────
@router.post("/propostas", response_model=PropostaResponse, status_code=201,
             summary="Cria proposta (nasce rascunho)")
async def criar_proposta(body: PropostaCreate) -> PropostaResponse:
    try:
        return await freela_service.criar_proposta(body)
    except Exception as e:
        raise _handle(e)


@router.get("/propostas/{proposta_id}", response_model=PropostaResponse, summary="Detalhe da proposta")
async def detalhe_proposta(proposta_id: str) -> PropostaResponse:
    try:
        return await freela_service.get_proposta(proposta_id)
    except Exception as e:
        raise _handle(e)


@router.patch("/propostas/{proposta_id}", response_model=PropostaResponse,
              summary="Atualiza campos da proposta")
async def atualizar_proposta(proposta_id: str, body: PropostaUpdate) -> PropostaResponse:
    try:
        return await freela_service.atualizar_proposta(proposta_id, body)
    except Exception as e:
        raise _handle(e)


@router.post("/propostas/{proposta_id}/status", response_model=PropostaResponse,
             summary="Move a proposta no Kanban (registra evento)")
async def mudar_status(proposta_id: str, body: PropostaStatusUpdate) -> PropostaResponse:
    try:
        return await freela_service.mudar_status(proposta_id, body)
    except Exception as e:
        raise _handle(e)


@router.post("/propostas/{proposta_id}/redigir", response_model=RedigirResponse,
             summary="Rascunha a proposta com IA (PARA no rascunho, não envia)")
async def redigir_proposta(proposta_id: str, body: RedigirRequest) -> RedigirResponse:
    try:
        return await freela_service.redigir_proposta(proposta_id, body)
    except Exception as e:
        raise _handle(e)


@router.post("/propostas/{proposta_id}/negociar", response_model=NegociarResponse,
             summary="Sugestões de resposta à objeção do cliente (defende o valor)")
async def negociar_proposta(proposta_id: str, body: NegociarRequest) -> NegociarResponse:
    try:
        return await freela_service.negociar_proposta(proposta_id, body)
    except Exception as e:
        raise _handle(e)


@router.post("/propostas/{proposta_id}/checklist", response_model=ChecklistResponse,
             summary="Gate anti-genérico: pontua o rascunho antes de enviar")
async def checklist_proposta(proposta_id: str) -> ChecklistResponse:
    try:
        return await freela_service.avaliar_proposta(proposta_id)
    except Exception as e:
        raise _handle(e)


@router.post("/propostas/{proposta_id}/corrigir", response_model=RedigirResponse,
             summary="Reescreve a proposta corrigindo os pontos do checklist")
async def corrigir_proposta(proposta_id: str, body: CorrigirRequest) -> RedigirResponse:
    try:
        return await freela_service.corrigir_proposta(proposta_id, body.correcoes)
    except Exception as e:
        raise _handle(e)


@router.delete("/propostas/{proposta_id}", status_code=204, summary="Remove proposta")
async def remover_proposta(proposta_id: str) -> None:
    try:
        await freela_service.deletar_proposta(proposta_id)
    except Exception as e:
        raise _handle(e)
