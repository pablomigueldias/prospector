"""Service do Agente Freelancer (Workana) — CRM de propostas + precificador.

Filosofia (igual ao agente de candidatura): é um COPILOTO. Nada aqui toca na
Workana nem envia proposta — a ferramenta organiza, precifica e (nas fases de
IA) rascunha; você revisa e envia na mão, e marca o status no painel.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.analyzers.freela.analisador.parser import parse_resposta as parse_analise
from app.analyzers.freela.analisador.prompt_builder import (
    construir_prompt as construir_prompt_analise,
)
from app.analyzers.freela.negociador.parser import parse_resposta as parse_negociacao
from app.analyzers.freela.negociador.prompt_builder import (
    construir_prompt as construir_prompt_negociacao,
)
from app.analyzers.freela.checklist.parser import parse_resposta as parse_checklist
from app.analyzers.freela.checklist.prompt_builder import (
    construir_prompt as construir_prompt_checklist,
)
from app.analyzers.freela.extrator.parser import parse_resposta as parse_extracao
from app.analyzers.freela.extrator.prompt_builder import (
    construir_prompt as construir_prompt_extracao,
)
from app.analyzers.freela.redator.parser import parse_resposta as parse_redacao
from app.analyzers.freela.redator.prompt_builder import (
    construir_prompt as construir_prompt_redacao,
)
from app.analyzers._perfil_texto import perfil_para_texto
from app.analyzers.llm_provider import gerar_texto
from app.api.schemas.freela import (
    AnalisarProjetoResponse,
    AnaliseFreela,
    ChecklistItem,
    ChecklistResponse,
    ClienteCreate,
    ClienteResponse,
    ClienteUpdate,
    EstimativaFreela,
    ExtrairProjetoResponse,
    FaseRampa,
    NegociarRequest,
    NegociarResponse,
    RedigirRequest,
    RedigirResponse,
    KanbanColuna,
    KanbanResponse,
    MetricasResponse,
    PlanoMetaRequest,
    PlanoMetaResponse,
    PlataformaResponse,
    PrecificarRequest,
    PrecificarResponse,
    ProjetoCreate,
    ProjetoListItem,
    ProjetoListResponse,
    ProjetoResponse,
    ProjetoUpdate,
    PropostaCreate,
    PropostaKanbanItem,
    PropostaResponse,
    PropostaStatusUpdate,
    PropostaUpdate,
    VereditoPreco,
)
from app.db.models.pessoal.freela.cliente import Cliente
from app.db.models.pessoal.freela.plataforma import Plataforma
from app.db.models.pessoal.freela.projeto import Projeto
from app.db.models.pessoal.freela.proposta import STATUS_PROPOSTA, Proposta
from app.db.models.pipeline_event import PipelineEvent
from app.db.session import get_session
from app.api.services.pessoal.perfil_service import get_perfil
from app.repositories.pessoal.freela_repository import FreelaRepository
from app.utils.logger import get_logger

logger = get_logger()

# Faixas de comissão padrão (Workana) caso a plataforma não tenha config.
_COMISSAO_PADRAO = [
    {"ate_usd": 300, "pct": 0.20},
    {"ate_usd": 3000, "pct": 0.10},
    {"ate_usd": None, "pct": 0.05},
]
_CUSTO_SERVICO_PADRAO = 0.045
# As faixas de comissão são em US$, mas você cota em R$. Ao fechar, convertemos
# o líquido pra US$ por esta taxa (sobrescrevível em config_comissao.usd_brl).
_USD_BRL_PADRAO = 5.20

# Transições válidas que carimbam um timestamp na proposta.
_CARIMBO = {
    "enviada": "enviada_em",
    "respondida": "data_resposta",
    "fechada": "data_fechamento",
}


class FreelaError(Exception):
    """Erro de negócio do agente freela — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str, label: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, AttributeError):
        raise FreelaError(f"{label} inválido: {valor!r}")


def _uuid_opt(valor: Optional[str], label: str = "id") -> Optional[uuid.UUID]:
    return _uuid(valor, label) if valor else None


def _r2(x: float) -> float:
    return round(float(x), 2)


# ── Conversores ──────────────────────────────────────────────────

def _cliente_to_resp(c: Cliente) -> ClienteResponse:
    return ClienteResponse(
        id=str(c.id),
        nome=c.nome,
        plataforma_id=str(c.plataforma_id) if c.plataforma_id else None,
        rating=float(c.rating) if c.rating is not None else None,
        projetos_publicados=c.projetos_publicados,
        projetos_pagos=c.projetos_pagos,
        pagamento_verificado=c.pagamento_verificado,
        membro_desde=c.membro_desde,
        ja_me_pagou_usd=float(c.ja_me_pagou_usd),
        notas=c.notas,
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


def _projeto_to_resp(p: Projeto) -> ProjetoResponse:
    return ProjetoResponse(
        id=str(p.id),
        titulo=p.titulo,
        descricao=p.descricao,
        plataforma_id=str(p.plataforma_id) if p.plataforma_id else None,
        cliente_id=str(p.cliente_id) if p.cliente_id else None,
        url=p.url,
        faixa_orcamento_min=float(p.faixa_orcamento_min) if p.faixa_orcamento_min is not None else None,
        faixa_orcamento_max=float(p.faixa_orcamento_max) if p.faixa_orcamento_max is not None else None,
        habilidades=p.habilidades or [],
        prazo_estimado=p.prazo_estimado,
        status_no_site=p.status_no_site,
        n_propostas_concorrentes=p.n_propostas_concorrentes,
        n_interessados=p.n_interessados,
        analise_json=p.analise_json,
        coletado_em=_iso(p.coletado_em),
        created_at=_iso(p.created_at),
        updated_at=_iso(p.updated_at),
    )


def _proposta_to_resp(p: Proposta) -> PropostaResponse:
    return PropostaResponse(
        id=str(p.id),
        projeto_id=str(p.projeto_id),
        valor_cotado=float(p.valor_cotado) if p.valor_cotado is not None else None,
        horas_estimadas=float(p.horas_estimadas) if p.horas_estimadas is not None else None,
        valor_liquido_estimado=float(p.valor_liquido_estimado) if p.valor_liquido_estimado is not None else None,
        texto_enviado=p.texto_enviado,
        projetos_destacados=p.projetos_destacados or [],
        habilidades_destacadas=p.habilidades_destacadas or [],
        prazo_proposto=p.prazo_proposto,
        status=p.status,
        enviada_em=_iso(p.enviada_em),
        data_resposta=_iso(p.data_resposta),
        data_fechamento=_iso(p.data_fechamento),
        motivo_perda=p.motivo_perda,
        created_at=_iso(p.created_at),
        updated_at=_iso(p.updated_at),
    )


# ══════════════════════════════════════════════════════════════════
# Plataforma
# ══════════════════════════════════════════════════════════════════

async def listar_plataformas() -> List[PlataformaResponse]:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_plataformas()
        return [
            PlataformaResponse(
                id=str(p.id),
                nome=p.nome,
                url_base=p.url_base,
                config_comissao=p.config_comissao,
                lance_minimo_padrao=float(p.lance_minimo_padrao) if p.lance_minimo_padrao is not None else None,
            )
            for p in linhas
        ]


# ══════════════════════════════════════════════════════════════════
# Cliente
# ══════════════════════════════════════════════════════════════════

async def criar_cliente(payload: ClienteCreate) -> ClienteResponse:
    if not payload.nome.strip():
        raise FreelaError("O cliente precisa de um nome.")
    dados = payload.model_dump()
    dados["plataforma_id"] = _uuid_opt(dados.get("plataforma_id"), "plataforma_id")
    async with get_session() as session:
        cliente = await FreelaRepository(session).create_cliente(dados)
        return _cliente_to_resp(cliente)


async def listar_clientes() -> List[ClienteResponse]:
    async with get_session() as session:
        return [_cliente_to_resp(c) for c in await FreelaRepository(session).listar_clientes()]


async def get_cliente(cliente_id: str) -> ClienteResponse:
    async with get_session() as session:
        cliente = await FreelaRepository(session).get_cliente(_uuid(cliente_id))
        if cliente is None:
            raise FreelaError("Cliente não encontrado.")
        return _cliente_to_resp(cliente)


async def atualizar_cliente(cliente_id: str, payload: ClienteUpdate) -> ClienteResponse:
    dados = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if "plataforma_id" in dados:
        dados["plataforma_id"] = _uuid_opt(dados["plataforma_id"], "plataforma_id")
    async with get_session() as session:
        cliente = await FreelaRepository(session).update_cliente(_uuid(cliente_id), dados)
        if cliente is None:
            raise FreelaError("Cliente não encontrado.")
        return _cliente_to_resp(cliente)


async def deletar_cliente(cliente_id: str) -> None:
    async with get_session() as session:
        ok = await FreelaRepository(session).delete_cliente(_uuid(cliente_id))
        if not ok:
            raise FreelaError("Cliente não encontrado.")


# ══════════════════════════════════════════════════════════════════
# Projeto (você cola o texto)
# ══════════════════════════════════════════════════════════════════

async def criar_projeto(payload: ProjetoCreate) -> ProjetoResponse:
    if not payload.titulo.strip():
        raise FreelaError("O projeto precisa de um título.")
    if not payload.descricao.strip():
        raise FreelaError("Cole a descrição do projeto.")
    dados = payload.model_dump()
    dados["plataforma_id"] = _uuid_opt(dados.get("plataforma_id"), "plataforma_id")
    dados["cliente_id"] = _uuid_opt(dados.get("cliente_id"), "cliente_id")
    async with get_session() as session:
        projeto = await FreelaRepository(session).create_projeto(dados)
        return _projeto_to_resp(projeto)


async def listar_projetos() -> ProjetoListResponse:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_projetos()
    items = []
    for projeto, cliente_nome, qtd, pago_usd in linhas:
        analise = projeto.analise_json or {}
        items.append(
            ProjetoListItem(
                id=str(projeto.id),
                titulo=projeto.titulo,
                cliente_nome=cliente_nome,
                status_no_site=projeto.status_no_site,
                faixa_orcamento_min=float(projeto.faixa_orcamento_min) if projeto.faixa_orcamento_min is not None else None,
                faixa_orcamento_max=float(projeto.faixa_orcamento_max) if projeto.faixa_orcamento_max is not None else None,
                n_propostas_concorrentes=projeto.n_propostas_concorrentes,
                fit_score=analise.get("fit_score"),
                risco=analise.get("risco"),
                quadrante=analise.get("quadrante"),
                preco_status=(analise.get("veredito_preco") or {}).get("status"),
                estimativa=analise.get("estimativa"),
                tem_analise=projeto.analise_json is not None,
                qtd_propostas=qtd,
                cliente_recorrente=pago_usd > 0,
                cliente_pago_usd=round(pago_usd, 2),
                created_at=_iso(projeto.created_at),
            )
        )
    # Fila de oportunidades: cliente recorrente vale ouro (vem primeiro), depois
    # maior fit (sem análise vai pro fim).
    items.sort(
        key=lambda i: (not i.cliente_recorrente, i.fit_score is None, -(i.fit_score or 0))
    )
    return ProjetoListResponse(items=items, total=len(items))


async def get_projeto(projeto_id: str) -> ProjetoResponse:
    async with get_session() as session:
        projeto = await FreelaRepository(session).get_projeto(_uuid(projeto_id))
        if projeto is None:
            raise FreelaError("Projeto não encontrado.")
        return _projeto_to_resp(projeto)


async def atualizar_projeto(projeto_id: str, payload: ProjetoUpdate) -> ProjetoResponse:
    dados = dict(payload.model_dump(exclude_unset=True))
    if "plataforma_id" in dados:
        dados["plataforma_id"] = _uuid_opt(dados["plataforma_id"], "plataforma_id")
    if "cliente_id" in dados:
        dados["cliente_id"] = _uuid_opt(dados["cliente_id"], "cliente_id")
    async with get_session() as session:
        projeto = await FreelaRepository(session).update_projeto(_uuid(projeto_id), dados)
        if projeto is None:
            raise FreelaError("Projeto não encontrado.")
        return _projeto_to_resp(projeto)


async def deletar_projeto(projeto_id: str) -> None:
    async with get_session() as session:
        ok = await FreelaRepository(session).delete_projeto(_uuid(projeto_id))
        if not ok:
            raise FreelaError("Projeto não encontrado.")


# ── IA: análise de projeto (Fase 3) ──────────────────────────────

def _chamar_llm(prompt: str, *, operacao: str) -> str:
    try:
        return gerar_texto(prompt, json_mode=True, agente="freela", operacao=operacao)
    except Exception as e:
        logger.error("freela: falha na LLM (%s): %s", operacao, e)
        raise FreelaError(
            "Não consegui falar com o modelo de IA. "
            "Verifique a conexão/configuração e tente de novo."
        )


def _sinais_cliente_texto(cliente: Optional[Cliente]) -> Optional[str]:
    if cliente is None:
        return None
    partes = []
    partes.append("pagamento verificado" if cliente.pagamento_verificado else "pagamento NÃO verificado")
    if cliente.rating is not None:
        partes.append(f"rating {cliente.rating}")
    if cliente.projetos_pagos is not None:
        partes.append(f"{cliente.projetos_pagos} projetos pagos")
    if float(cliente.ja_me_pagou_usd) > 0:
        partes.append(f"já me pagou US$ {cliente.ja_me_pagou_usd} (recorrente)")
    return "; ".join(partes)


# Limiares do quadrante dificuldade × esforço.
_HORAS_LONGO = 40      # >= isto conta como projeto "longo"
_HORAS_QUICK = 16      # <= isto (e fácil) conta como "quick win"


def _quadrante(
    complexidade: Optional[str], clareza: Optional[str], horas: Optional[int]
) -> str:
    """Cruza dificuldade (complexidade) × esforço (horas) num rótulo acionável.

    escopo_vago vence tudo (risco de scope creep). Senão: alta+longo =
    dificil_longo; fácil+curto = quick_win (bom pra cravar reputação no cold
    start); o resto = padrao.
    """
    if clareza == "vago":
        return "escopo_vago"
    longo = bool(horas and horas >= _HORAS_LONGO)
    if complexidade == "alta" and longo:
        return "dificil_longo"
    if complexidade in ("trivial", "media") and horas and horas <= _HORAS_QUICK:
        return "quick_win"
    return "padrao"


def _veredito_preco(
    projeto: Projeto, estimativa: Optional["EstimativaFreela"]
) -> VereditoPreco:
    """Cruza o orçamento do cliente com a faixa de mercado da IA (determinístico).

    Responde 'o valor está justo?' sem deixar a IA inventar — usa os números
    reais do projeto.
    """
    orc_min = float(projeto.faixa_orcamento_min) if projeto.faixa_orcamento_min is not None else None
    orc_max = float(projeto.faixa_orcamento_max) if projeto.faixa_orcamento_max is not None else None
    vals = [v for v in (orc_min, orc_max) if v is not None]
    if not vals:
        return VereditoPreco(
            status="sem_orcamento",
            gap_texto="Cliente não informou orçamento — pergunte antes de cotar.",
        )
    orc_mid = sum(vals) / len(vals)

    rh = None
    if estimativa and estimativa.horas_estimadas:
        rh = _r2(orc_mid / estimativa.horas_estimadas)

    merc_min = estimativa.valor_mercado_min if estimativa else None
    merc_max = estimativa.valor_mercado_max if estimativa else None
    if merc_min is None or merc_max is None:
        return VereditoPreco(
            status=None,
            gap_texto="Sem faixa de mercado pra comparar (escopo vago demais).",
            rh_orcamento=rh,
        )

    if orc_mid < merc_min:
        status = "subcotado"
    elif orc_mid > merc_max:
        status = "acima"
    else:
        status = "justo"

    rotulo = {"subcotado": "subcotado", "justo": "dentro do mercado", "acima": "acima do mercado"}[status]
    gap = f"Cliente ~R$ {orc_mid:.0f}; mercado R$ {merc_min:.0f}–{merc_max:.0f} → {rotulo}."
    return VereditoPreco(status=status, gap_texto=gap, rh_orcamento=rh)


async def analisar_projeto(projeto_id: str) -> AnalisarProjetoResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise FreelaError(
            "Cadastre seu Perfil Mestre antes de analisar projetos — "
            "a análise cruza o projeto com quem você é."
        )

    pid = _uuid(projeto_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        projeto = await repo.get_projeto(pid)
        if projeto is None:
            raise FreelaError("Projeto não encontrado.")

        faixa = None
        if projeto.faixa_orcamento_min is not None or projeto.faixa_orcamento_max is not None:
            faixa = f"R$ {projeto.faixa_orcamento_min or '?'} – R$ {projeto.faixa_orcamento_max or '?'}"
        cliente = await repo.get_cliente(projeto.cliente_id) if projeto.cliente_id else None

        prompt = construir_prompt_analise(
            projeto.descricao,
            perfil,
            titulo=projeto.titulo,
            faixa_orcamento=faixa,
            n_propostas=projeto.n_propostas_concorrentes,
            n_interessados=projeto.n_interessados,
            sinais_cliente=_sinais_cliente_texto(cliente),
        )
        texto = _chamar_llm(prompt, operacao="analisar")

        analise = parse_analise(texto)
        if analise is None:
            raise FreelaError("A IA não retornou uma análise válida. Tente de novo.")

        # Garante a cotação: se o modelo deu faixa de mercado mas não o sugerido,
        # usa o ponto médio (assim o "+ Proposta" sempre vem com um valor).
        e = analise.estimativa
        if e and e.valor_sugerido is None and e.valor_mercado_min and e.valor_mercado_max:
            e.valor_sugerido = round((e.valor_mercado_min + e.valor_mercado_max) / 2)

        # Pós-processamento determinístico (não confia na IA pra cruzar números):
        # quadrante dificuldade × esforço e veredito de preço (orçamento × mercado).
        analise.quadrante = _quadrante(
            analise.complexidade_tecnica,
            analise.clareza_escopo,
            e.horas_estimadas if e else None,
        )
        analise.veredito_preco = _veredito_preco(projeto, e)

        await repo.salvar_analise_projeto(pid, analise.model_dump(mode="json"))

    return AnalisarProjetoResponse(projeto_id=projeto_id, analise=analise)


async def extrair_projeto(texto: str) -> ExtrairProjetoResponse:
    """Lê o texto colado da Workana e devolve campos pré-preenchidos (não salva)."""
    if not texto.strip():
        raise FreelaError("Cole o texto do projeto pra extrair.")

    prompt = construir_prompt_extracao(texto)
    resposta = _chamar_llm(prompt, operacao="extrair")
    dados = parse_extracao(resposta)
    if dados is None:
        raise FreelaError("A IA não conseguiu extrair os campos. Preencha na mão.")
    return dados


# ══════════════════════════════════════════════════════════════════
# Proposta
# ══════════════════════════════════════════════════════════════════

async def criar_proposta(payload: PropostaCreate) -> PropostaResponse:
    dados = payload.model_dump()
    projeto_id = _uuid(dados.pop("projeto_id"), "projeto_id")
    async with get_session() as session:
        repo = FreelaRepository(session)
        if await repo.get_projeto(projeto_id) is None:
            raise FreelaError("Projeto não encontrado.")
        dados["projeto_id"] = projeto_id
        proposta = await repo.create_proposta(dados)
        return _proposta_to_resp(proposta)


async def get_proposta(proposta_id: str) -> PropostaResponse:
    async with get_session() as session:
        proposta = await FreelaRepository(session).get_proposta(_uuid(proposta_id))
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        return _proposta_to_resp(proposta)


async def atualizar_proposta(proposta_id: str, payload: PropostaUpdate) -> PropostaResponse:
    dados = dict(payload.model_dump(exclude_unset=True))
    async with get_session() as session:
        proposta = await FreelaRepository(session).update_proposta(_uuid(proposta_id), dados)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        return _proposta_to_resp(proposta)


async def mudar_status(proposta_id: str, payload: PropostaStatusUpdate) -> PropostaResponse:
    novo = payload.status
    if novo not in STATUS_PROPOSTA:
        raise FreelaError(
            f"Status inválido: {novo!r}. Use um de: {', '.join(STATUS_PROPOSTA)}."
        )
    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")

        anterior = proposta.status
        dados: dict = {"status": novo}
        # Carimba o timestamp da transição se ainda não tiver.
        campo = _CARIMBO.get(novo)
        if campo and getattr(proposta, campo) is None:
            dados[campo] = datetime.now(timezone.utc)
        if novo == "perdida":
            dados["motivo_perda"] = payload.motivo_perda

        # Cliente recorrente vale ouro: ao FECHAR pela 1ª vez, soma o líquido
        # (convertido pra US$) ao acumulado do cliente → a comissão cai de faixa
        # sozinha e o precificador fica correto sem você lembrar.
        creditou_usd = 0.0
        if (
            novo == "fechada"
            and proposta.data_fechamento is None  # 1ª vez que fecha (não duplica)
            and proposta.valor_liquido_estimado
        ):
            projeto = await repo.get_projeto(proposta.projeto_id)
            if projeto and projeto.cliente_id:
                cliente = await repo.get_cliente(projeto.cliente_id)
                if cliente:
                    taxa = _USD_BRL_PADRAO
                    if projeto.plataforma_id:
                        plat = await repo.get_plataforma(projeto.plataforma_id)
                        if plat and plat.config_comissao:
                            taxa = float(plat.config_comissao.get("usd_brl", taxa))
                    creditou_usd = round(float(proposta.valor_liquido_estimado) / taxa, 2)
                    await repo.update_cliente(
                        cliente.id,
                        {"ja_me_pagou_usd": float(cliente.ja_me_pagou_usd) + creditou_usd},
                    )

        proposta = await repo.update_proposta(pid, dados)
        # Auditoria: reusa a tabela de eventos (pipeline_events).
        detalhe = json.dumps(
            {
                "proposta_id": proposta_id,
                "de": anterior,
                "para": novo,
                **({"creditou_usd": creditou_usd} if creditou_usd else {}),
            },
            ensure_ascii=False,
        )
        session.add(PipelineEvent(evento=f"freela_proposta_{novo}", detalhe=detalhe))
        await session.commit()
        return _proposta_to_resp(proposta)


async def deletar_proposta(proposta_id: str) -> None:
    async with get_session() as session:
        ok = await FreelaRepository(session).delete_proposta(_uuid(proposta_id))
        if not ok:
            raise FreelaError("Proposta não encontrada.")


async def listar_propostas_do_projeto(projeto_id: str) -> List[PropostaResponse]:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_propostas_do_projeto(_uuid(projeto_id))
        return [_proposta_to_resp(p) for p in linhas]


# ── IA: redator + seletor (Fase 5) ───────────────────────────────

async def redigir_proposta(proposta_id: str, payload: RedigirRequest) -> RedigirResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise FreelaError(
            "Cadastre seu Perfil Mestre antes de rascunhar — a proposta é "
            "ancorada nos seus projetos e habilidades."
        )

    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        projeto = await repo.get_projeto(proposta.projeto_id)
        if projeto is None:
            raise FreelaError("Projeto da proposta não encontrado.")

        # Cold start: sem nenhuma proposta fechada, ainda não há reputação na
        # plataforma — o redator compensa isso (prova descrita + redução de risco).
        _, qtd_fechadas = await repo.soma_liquido_fechado()

        prompt = construir_prompt_redacao(
            projeto.descricao,
            perfil,
            titulo=projeto.titulo,
            analise=projeto.analise_json,
            instrucoes_extra=payload.instrucoes_extra,
            cold_start=qtd_fechadas == 0,
        )
        texto = _chamar_llm(prompt, operacao="redigir")

        redacao = parse_redacao(texto)
        if redacao is None:
            raise FreelaError("A IA não retornou um rascunho válido. Tente de novo.")

        # PARA no rascunho: preenche a proposta, nada é enviado.
        await repo.update_proposta(
            pid,
            {
                "texto_enviado": redacao.texto,
                "projetos_destacados": redacao.projetos_destacados,
                "habilidades_destacadas": redacao.habilidades_destacadas,
                "prazo_proposto": redacao.prazo_sugerido or proposta.prazo_proposto,
            },
        )

    return RedigirResponse(proposta_id=proposta_id, redacao=redacao)


async def corrigir_proposta(
    proposta_id: str, correcoes: list[str]
) -> RedigirResponse:
    """Reescreve a proposta corrigindo os pontos apontados pelo checklist."""
    perfil = await get_perfil()
    if perfil is None:
        raise FreelaError("Cadastre seu Perfil Mestre antes de corrigir a proposta.")

    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        texto_atual = (proposta.texto_enviado or "").strip()
        if not texto_atual:
            raise FreelaError("Não há rascunho pra corrigir — gere a proposta antes.")
        projeto = await repo.get_projeto(proposta.projeto_id)
        if projeto is None:
            raise FreelaError("Projeto da proposta não encontrado.")

        _, qtd_fechadas = await repo.soma_liquido_fechado()
        prompt = construir_prompt_redacao(
            projeto.descricao,
            perfil,
            titulo=projeto.titulo,
            analise=projeto.analise_json,
            cold_start=qtd_fechadas == 0,
            texto_atual=texto_atual,
            correcoes=correcoes,
        )
        resposta = _chamar_llm(prompt, operacao="corrigir")
        redacao = parse_redacao(resposta)
        if redacao is None:
            raise FreelaError("A IA não retornou uma correção válida. Tente de novo.")

        await repo.update_proposta(
            pid,
            {
                "texto_enviado": redacao.texto,
                "projetos_destacados": redacao.projetos_destacados,
                "habilidades_destacadas": redacao.habilidades_destacadas,
                "prazo_proposto": redacao.prazo_sugerido or proposta.prazo_proposto,
            },
        )

    return RedigirResponse(proposta_id=proposta_id, redacao=redacao)


async def negociar_proposta(proposta_id: str, payload: NegociarRequest) -> NegociarResponse:
    if not payload.objecao.strip():
        raise FreelaError("Cole o que o cliente falou (a objeção).")

    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        projeto = await repo.get_projeto(proposta.projeto_id)

    perfil = await get_perfil()  # opcional: dá o tom; funciona sem
    prompt = construir_prompt_negociacao(
        payload.objecao,
        perfil=perfil,
        titulo=projeto.titulo if projeto else None,
        valor_cotado=float(proposta.valor_cotado) if proposta.valor_cotado is not None else None,
        descricao_projeto=projeto.descricao if projeto else None,
    )
    texto = _chamar_llm(prompt, operacao="negociar")

    opcoes = parse_negociacao(texto)
    if not opcoes:
        raise FreelaError("A IA não retornou respostas válidas. Tente de novo.")

    return NegociarResponse(proposta_id=proposta_id, opcoes=opcoes)


# Conformidade Workana: contato/link no texto da proposta é filtrado/penalizado.
# CUIDADO: só pega CONTATO real, não menção ao tema. Ex.: "sistema para WhatsApp"
# é o assunto do projeto, NÃO o seu contato — não pode flagar.
_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_RE_URL = re.compile(r"(https?://\S+|\bwww\.\S+|\b[\w-]+\.(?:com|net|io|dev|me|br)\b\S*)", re.I)
# telefone só quando tem cara de número de contato (DDD + 8/9 dígitos).
_RE_TEL = re.compile(r"(?:\+?55[\s-]*)?\(?\d{2}\)?[\s-]*9?\d{4}[\s-]?\d{4}")
# mensageria só por LINK explícito de contato (wa.me/t.me), não pela palavra solta.
_RE_ZAP = re.compile(r"\b(?:wa\.me|t\.me)/\S+", re.I)


def _scan_conformidade(texto: str) -> Optional[str]:
    """Acha CONTATO/link no texto da proposta (regra dura da Workana). None se limpo."""
    achados = []
    if _RE_EMAIL.search(texto):
        achados.append("e-mail")
    # tira e-mails antes de procurar URL (o domínio do e-mail não é "link").
    sem_email = _RE_EMAIL.sub(" ", texto)
    if _RE_TEL.search(sem_email):
        achados.append("telefone")
    if _RE_ZAP.search(texto) or _RE_URL.search(sem_email):
        achados.append("link externo")
    if not achados:
        return None
    return (
        "A proposta contém " + ", ".join(achados) + ". A Workana filtra/penaliza "
        "contato e link no texto antes do contrato — remova e remeta ao seu "
        "perfil/portfólio aqui na Workana."
    )


# Métrica "impressiva" inventada: a IA às vezes crava % / "Nx" que NÃO está no
# perfil (ex.: "90% de sucesso", "redução de 40%"). Pegamos números do texto que
# não aparecem no perfil pra alertar (anti-mentira determinístico). 100% é
# retórico ("100% focado") → ignorado pra reduzir falso-positivo.
_RE_METRICA = re.compile(r"\d{1,3}\s*%|\b\d+\s*x\b", re.I)


def _scan_metricas_inventadas(texto: str, perfil_texto: str) -> Optional[str]:
    """Acha número/percentual no texto que não está no perfil. None se limpo."""
    achados = _RE_METRICA.findall(texto)
    if not achados:
        return None
    perfil_digitos = set(re.findall(r"\d+", perfil_texto))
    suspeitos: list[str] = []
    for a in achados:
        nums = re.findall(r"\d+", a)
        if not nums or nums[0] in perfil_digitos:
            continue
        if a.rstrip().endswith("%") and nums[0] == "100":
            continue  # "100%" costuma ser retórico, não métrica fabricada
        token = a.strip().replace(" ", "")
        if token not in suspeitos:
            suspeitos.append(token)
    if not suspeitos:
        return None
    return (
        "Número(s) que NÃO encontrei no seu perfil: " + ", ".join(suspeitos) + ". "
        "A IA pode ter inventado — confirme que é real ou troque por descrição "
        "qualitativa (problema→solução→impacto, sem percentual fabricado)."
    )


def _selo(score: int) -> str:
    if score >= 80:
        return "pronta"
    if score >= 50:
        return "ajustar"
    return "fraca"


async def avaliar_proposta(proposta_id: str) -> ChecklistResponse:
    """Gate anti-genérico: pontua o rascunho e aponta o que falta antes de enviar."""
    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        projeto = await repo.get_projeto(proposta.projeto_id)

    texto = (proposta.texto_enviado or "").strip()
    if not texto:
        raise FreelaError("Rascunhe a proposta antes de conferir (texto vazio).")

    prompt = construir_prompt_checklist(
        texto,
        descricao_projeto=projeto.descricao if projeto else None,
        titulo=projeto.titulo if projeto else None,
    )
    resposta = _chamar_llm(prompt, operacao="checklist")
    resultado = parse_checklist(resposta)
    if resultado is None:
        raise FreelaError("A IA não retornou uma avaliação válida. Tente de novo.")

    resultado.proposta_id = proposta_id

    # Conformidade Workana (determinística): contato/link no texto é penalizado.
    alerta = _scan_conformidade(texto)
    if alerta:
        resultado.alerta_conformidade = alerta
        resultado.itens.append(
            ChecklistItem(
                criterio="Sem contato/link externo (regra da Workana)",
                ok=False,
                nota="Encontrei contato ou link no texto.",
            )
        )
        # Conformidade fura tudo: limita o selo enquanto não corrigir.
        resultado.score = min(resultado.score, 49)

    # Anti-mentira determinístico: número/percentual no texto que não está no
    # perfil cheira a invenção da IA. Não derruba pra "fraca" (pode ser falso-
    # positivo), mas impede o selo "pronta" e avisa explicitamente.
    perfil = await get_perfil()
    if perfil is not None:
        alerta_num = _scan_metricas_inventadas(texto, perfil_para_texto(perfil))
        if alerta_num:
            resultado.itens.append(
                ChecklistItem(
                    criterio="Sem número inventado (anti-mentira)",
                    ok=False,
                    nota=alerta_num,
                )
            )
            resultado.sugestoes.append(alerta_num)
            resultado.score = min(resultado.score, 79)

    resultado.selo = _selo(resultado.score)
    return resultado


# ══════════════════════════════════════════════════════════════════
# Kanban + Métricas
# ══════════════════════════════════════════════════════════════════

def _dias_desde(dt: Optional[datetime]) -> Optional[int]:
    if dt is None:
        return None
    agora = datetime.now(timezone.utc)
    base = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return (agora - base).days


async def kanban() -> KanbanResponse:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_propostas_kanban()

    por_status: dict[str, List[PropostaKanbanItem]] = {s: [] for s in STATUS_PROPOSTA}
    for proposta, projeto_titulo, cliente_nome in linhas:
        ref = proposta.enviada_em or proposta.created_at
        por_status.setdefault(proposta.status, []).append(
            PropostaKanbanItem(
                id=str(proposta.id),
                projeto_id=str(proposta.projeto_id),
                projeto_titulo=projeto_titulo,
                cliente_nome=cliente_nome,
                valor_cotado=float(proposta.valor_cotado) if proposta.valor_cotado is not None else None,
                valor_liquido_estimado=float(proposta.valor_liquido_estimado) if proposta.valor_liquido_estimado is not None else None,
                status=proposta.status,
                dias_desde_envio=_dias_desde(ref),
                created_at=_iso(proposta.created_at),
            )
        )
    colunas = [KanbanColuna(status=s, items=por_status.get(s, [])) for s in STATUS_PROPOSTA]
    return KanbanResponse(colunas=colunas)


async def metricas() -> MetricasResponse:
    async with get_session() as session:
        repo = FreelaRepository(session)
        contagem = await repo.contar_por_status()
        liquido_total, qtd_fechadas = await repo.soma_liquido_fechado()
        pipeline_aberto, qtd_aberto = await repo.soma_liquido_em_aberto()
        tempo_resposta = await repo.tempo_medio_resposta_horas()
        valor_hora_real = await repo.valor_hora_real_fechadas()

    total = sum(contagem.values())
    # "enviadas" = tudo que saiu da gaveta (qualquer status menos rascunho).
    enviadas = total - contagem.get("rascunho", 0)
    respondidas = (
        contagem.get("respondida", 0)
        + contagem.get("negociando", 0)
        + contagem.get("fechada", 0)
    )
    fechadas = contagem.get("fechada", 0)
    perdidas = contagem.get("perdida", 0)

    taxa_resposta = _r2(respondidas / enviadas) if enviadas else 0.0
    taxa_fechamento = _r2(fechadas / enviadas) if enviadas else 0.0
    ticket_medio = _r2(liquido_total / qtd_fechadas) if qtd_fechadas else 0.0

    # Forecast: o que provavelmente entra do pipeline em aberto. Ponderado pela
    # sua taxa de fechamento histórica; sem histórico ainda, assume 50% (chute
    # neutro) pra não mostrar R$0 e dar uma referência.
    prob = taxa_fechamento if fechadas else 0.5
    forecast = _r2(pipeline_aberto * prob)

    return MetricasResponse(
        total_propostas=total,
        enviadas=enviadas,
        respondidas=respondidas,
        fechadas=fechadas,
        perdidas=perdidas,
        em_aberto=qtd_aberto,
        taxa_resposta=taxa_resposta,
        taxa_fechamento=taxa_fechamento,
        liquido_total_fechado=_r2(liquido_total),
        ticket_medio_fechado=ticket_medio,
        pipeline_aberto_liquido=_r2(pipeline_aberto),
        forecast_liquido=forecast,
        tempo_medio_resposta_horas=tempo_resposta,
        valor_hora_real=valor_hora_real,
    )


# ══════════════════════════════════════════════════════════════════
# Motor da meta (matemática reversa + rampa — sem IA)
# ══════════════════════════════════════════════════════════════════

# Rampa de meta (líquido/mês). A fase é guiada pela REPUTAÇÃO (nº de fechadas),
# não por R$ — no cold start o gargalo é destravar avaliação, não faturar.
_RAMPA_META = [
    {"nome": "F1 — Cold start", "meta_min": 1500, "meta_max": 2000,
     "foco": "1–2 avaliações 5★ (R$ é secundário); aceitar quick wins"},
    {"nome": "F2 — Tração", "meta_min": 3500, "meta_max": 4500,
     "foco": "subir ticket, parar o fundo de poço, focar no núcleo"},
    {"nome": "F3 — Crescimento", "meta_min": 6500, "meta_max": 7500,
     "foco": "caçar recorrente + gringo/USD; nicho claro"},
    {"nome": "F4 — Meta cheia", "meta_min": 10000, "meta_max": 10000,
     "foco": "renda estável: base recorrente + ticket alto"},
]
# Conversão proposta→fechada baixa o bastante pra ser o gargalo.
_CONVERSAO_FRACA = 0.15
# Semanas por mês (média) pra transformar propostas/mês em propostas/semana.
_SEMANAS_MES = 4.3


def _fase_rampa(fechadas: int) -> dict:
    """Fase atual pela reputação: 0 nota = cold start; vai subindo com as fechadas."""
    if fechadas == 0:
        return _RAMPA_META[0]
    if fechadas <= 2:
        return _RAMPA_META[1]
    if fechadas <= 5:
        return _RAMPA_META[2]
    return _RAMPA_META[3]


async def plano_meta(req: PlanoMetaRequest) -> PlanoMetaResponse:
    """Matemática reversa: da meta líquida → valor-hora alvo, projetos e propostas
    necessárias, gargalo e fase da rampa. Reusa as métricas reais."""
    if req.meta_liquida <= 0:
        raise FreelaError("Informe a meta líquida (maior que zero).")
    if req.horas_dia <= 0 or req.dias_mes <= 0 or not (0 < req.pct_faturavel <= 1):
        raise FreelaError("Capacidade inválida (horas/dia, dias/mês, % faturável).")

    m = await metricas()

    horas_faturaveis = _r2(req.horas_dia * req.dias_mes * req.pct_faturavel)
    valor_hora_alvo = _r2(req.meta_liquida / horas_faturaveis) if horas_faturaveis else 0.0

    ticket = m.ticket_medio_fechado or None
    vhr = m.valor_hora_real  # das fechadas
    taxa_fech = m.taxa_fechamento or 0.0

    projetos_mes = _r2(req.meta_liquida / ticket) if ticket else None
    propostas_mes = (
        _r2(projetos_mes / taxa_fech) if (projetos_mes is not None and taxa_fech > 0) else None
    )
    propostas_sem = _r2(propostas_mes / _SEMANAS_MES) if propostas_mes is not None else None

    projecao = _r2(vhr * horas_faturaveis) if vhr else None
    alcancavel = bool(projecao is not None and projecao >= req.meta_liquida)

    # Diagnóstico do gargalo (honesto: prioriza o que mais trava a meta).
    if vhr is None and ticket is None:
        gargalo = "sem_dados"
        diagnostico = (
            f"Feche o 1º projeto pra eu calibrar com seus números. Por ora: pra "
            f"R$ {req.meta_liquida:.0f} líq/mês em {horas_faturaveis:.0f}h faturáveis, "
            f"mire um valor-hora ≥ R$ {valor_hora_alvo:.0f}/h."
        )
    elif vhr is not None and not alcancavel:
        gargalo = "ticket"
        diagnostico = (
            f"Seu valor-hora real (R$ {vhr:.0f}/h) × {horas_faturaveis:.0f}h dá só "
            f"~R$ {projecao:.0f}/mês — não fecha a meta por volume. O caminho é "
            f"SUBIR TICKET (nicho, gringo/USD, recorrente), não pegar mais projeto barato."
        )
    elif taxa_fech and taxa_fech < _CONVERSAO_FRACA:
        gargalo = "conversao"
        diagnostico = (
            f"O R$/h fecha a conta, mas sua conversão é baixa ({taxa_fech*100:.0f}%). "
            f"Foque proposta melhor (checklist) e nos projetos do seu núcleo."
        )
    elif propostas_sem is not None:
        gargalo = "volume"
        diagnostico = (
            f"No seu ritmo, mande ~{propostas_sem:.0f} propostas/semana "
            f"(~{projetos_mes:.0f} projetos/mês a R$ {ticket:.0f} de ticket) pra bater a meta."
        )
    else:
        gargalo = "no_caminho"
        diagnostico = (
            f"Pra R$ {req.meta_liquida:.0f} líq/mês, mire valor-hora ≥ "
            f"R$ {valor_hora_alvo:.0f}/h e mantenha o ritmo de propostas."
        )

    fase = _fase_rampa(m.fechadas)

    return PlanoMetaResponse(
        meta_liquida=_r2(req.meta_liquida),
        horas_faturaveis_mes=horas_faturaveis,
        valor_hora_alvo=valor_hora_alvo,
        valor_hora_real=vhr,
        ticket_medio=ticket,
        projecao_liquida_mes=projecao,
        projetos_necessarios_mes=projetos_mes,
        propostas_necessarias_mes=propostas_mes,
        propostas_por_semana=propostas_sem,
        alcancavel_por_volume=alcancavel,
        gargalo=gargalo,
        diagnostico=diagnostico,
        fase=FaseRampa(**fase),
    )


# ══════════════════════════════════════════════════════════════════
# Precificador (matemática da comissão — sem IA)
# ══════════════════════════════════════════════════════════════════

def _pct_comissao(config_comissao: Optional[dict], ja_me_pagou_usd: float) -> float:
    faixas = (config_comissao or {}).get("faixas") or _COMISSAO_PADRAO
    for faixa in faixas:
        ate = faixa.get("ate_usd")
        if ate is None or ja_me_pagou_usd < ate:
            return float(faixa["pct"])
    return float(faixas[-1]["pct"])


async def precificar(req: PrecificarRequest) -> PrecificarResponse:
    if req.liquido_desejado <= 0:
        raise FreelaError("Informe o líquido desejado (maior que zero).")

    plataforma: Optional[Plataforma] = None
    ja_pagou = req.ja_me_pagou_usd or 0.0

    async with get_session() as session:
        repo = FreelaRepository(session)
        if req.cliente_id:
            cliente = await repo.get_cliente(_uuid(req.cliente_id, "cliente_id"))
            if cliente is None:
                raise FreelaError("Cliente não encontrado.")
            ja_pagou = float(cliente.ja_me_pagou_usd)
            if cliente.plataforma_id:
                plataforma = await repo.get_plataforma(cliente.plataforma_id)
        if plataforma is None and req.plataforma_id:
            plataforma = await repo.get_plataforma(_uuid(req.plataforma_id, "plataforma_id"))

    config = plataforma.config_comissao if plataforma else None
    custo_servico = float((config or {}).get("custo_servico_cliente_pct", _CUSTO_SERVICO_PADRAO))
    lance_min = float(plataforma.lance_minimo_padrao) if plataforma and plataforma.lance_minimo_padrao is not None else None

    pct = _pct_comissao(config, ja_pagou)
    valor_a_cotar = _r2(req.liquido_desejado / (1 - pct))
    cliente_paga = _r2(valor_a_cotar * (1 + custo_servico))

    liquido_por_hora = None
    alerta = None
    if req.horas_estimadas and req.horas_estimadas > 0:
        liquido_por_hora = _r2(req.liquido_desejado / req.horas_estimadas)
        if req.valor_hora_alvo and liquido_por_hora < req.valor_hora_alvo:
            alerta = (
                f"Líquido/hora R$ {liquido_por_hora:.2f} abaixo do seu alvo "
                f"R$ {req.valor_hora_alvo:.2f} — considere cotar mais ou estimar menos horas."
            )

    abaixo_min = bool(lance_min and valor_a_cotar < lance_min)
    if abaixo_min and not alerta:
        alerta = f"Valor a cotar abaixo do lance mínimo (R$ {lance_min:.2f})."

    return PrecificarResponse(
        pct_comissao=pct,
        valor_a_cotar=valor_a_cotar,
        cliente_paga=cliente_paga,
        lance_minimo=lance_min,
        abaixo_do_lance_minimo=abaixo_min,
        liquido_por_hora=liquido_por_hora,
        alerta=alerta,
    )
