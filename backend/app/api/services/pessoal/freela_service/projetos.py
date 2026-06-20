"""Projeto: CRUD (você cola o texto) + extração de campos por IA."""
from __future__ import annotations

import asyncio
from datetime import date

from app.analyzers.freela.extrator.parser import parse_resposta as parse_extracao
from app.analyzers.freela.extrator.prompt_builder import (
    construir_prompt as construir_prompt_extracao,
)
from app.collectors.website.pagina import texto_de_url
from app.api.schemas.freela import (
    ExtrairProjetoResponse,
    ProjetoCreate,
    ProjetoListItem,
    ProjetoListResponse,
    ProjetoResponse,
    ProjetoUpdate,
)
from app.api.services._helpers import iso as _iso
from app.config import settings
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from .metricas import contar_resposta_por_stack

from ._base import FreelaError, _chamar_llm, _projeto_to_resp, _uuid, _uuid_opt


def _parse_data(valor) -> date | None:
    """'2026-06-15' (ou ISO completo) → date; vazio/ inválido → None."""
    if not valor:
        return None
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


async def criar_projeto(payload: ProjetoCreate) -> ProjetoResponse:
    if not payload.titulo.strip():
        raise FreelaError("O projeto precisa de um título.")
    if not payload.descricao.strip():
        raise FreelaError("Cole a descrição do projeto.")
    dados = payload.model_dump()
    dados["plataforma_id"] = _uuid_opt(dados.get("plataforma_id"), "plataforma_id")
    dados["cliente_id"] = _uuid_opt(dados.get("cliente_id"), "cliente_id")
    dados["publicado_em"] = _parse_data(dados.get("publicado_em"))
    async with get_session() as session:
        projeto = await FreelaRepository(session).create_projeto(dados)
        return _projeto_to_resp(projeto)


async def listar_projetos() -> ProjetoListResponse:
    async with get_session() as session:
        repo = FreelaRepository(session)
        linhas = await repo.listar_projetos()
        comprometidas = await repo.soma_horas_comprometidas()
        envs, resps, _fech, tot_env, tot_resp = contar_resposta_por_stack(
            await repo.propostas_status_e_analise()
        )
    hoje = date.today()
    horas_livres = max(0.0, settings.freela_capacidade_horas_semana - comprometidas)
    # Prob. de resposta por stack (só com amostra mínima) + base global.
    prob_stack = {k: resps.get(k, 0) / v for k, v in envs.items() if v >= 2}
    prob_global = (tot_resp / tot_env) if tot_env else _PRIOR_RESPOSTA
    items = []
    for projeto, cliente_nome, qtd, pago_usd, pag_verificado in linhas:
        analise = projeto.analise_json or {}
        bom, motivos = _detectar_bom_primeiro(
            analise, projeto.n_propostas_concorrentes, pag_verificado
        )
        dias_pub = (hoje - projeto.publicado_em).days if projeto.publicado_em else None
        momento, momento_motivo = _veredito_momento(
            analise, bom, pago_usd > 0, dias_pub,
            projeto.n_propostas_concorrentes, horas_livres,
        )
        ticket = _ticket(projeto.faixa_orcamento_min, projeto.faixa_orcamento_max)
        prob = _prob_resposta(analise, prob_stack, prob_global)
        valor_esp = _valor_esperado(analise, ticket, prob)
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
                bom_primeiro=bom,
                bom_primeiro_motivos=motivos,
                publicado_em=projeto.publicado_em.isoformat() if projeto.publicado_em else None,
                dias_desde_publicacao=dias_pub,
                momento=momento,
                momento_motivo=momento_motivo,
                valor_esperado=valor_esp,
                prob_resposta=round(prob, 2) if valor_esp is not None else None,
                created_at=_iso(projeto.created_at),
            )
        )
    # Fila de oportunidades (cold start): cliente recorrente vale ouro (vem
    # primeiro), depois "bom 1º projeto", depois mais FRESCO (responder cedo é
    # vantagem). Por fim, maior VALOR ESPERADO (custo de oportunidade) — fit
    # entra nele; fit puro fica de último desempate.
    items.sort(
        key=lambda i: (
            not i.cliente_recorrente,
            not i.bom_primeiro,
            i.dias_desde_publicacao is None,
            i.dias_desde_publicacao or 0,
            i.valor_esperado is None,
            -(i.valor_esperado or 0),
            -(i.fit_score or 0),
        )
    )
    return ProjetoListResponse(items=items, total=len(items))


# Custo de oportunidade — ranquear por valor esperado da próxima proposta.
_PRIOR_RESPOSTA = 0.15   # base de prob. de resposta na fase sem dados (cold start)
_HORAS_PADRAO = 20       # estimativa de horas quando a análise não trouxe


def _ticket(pmin, pmax) -> float | None:
    """Ponto médio do orçamento (ou o único valor informado)."""
    vals = [float(v) for v in (pmin, pmax) if v is not None]
    return sum(vals) / len(vals) if vals else None


def _prob_resposta(analise: dict, prob_stack: dict[str, float], prob_global: float) -> float:
    """Prob. de resposta do projeto: média das stacks com histórico, senão a base
    global. Piso no prior pra a fase cold start (0% de amostra pequena não deve
    zerar o ranking inteiro)."""
    tags = [str(t).strip() for t in (analise.get("stack") or []) if str(t).strip()]
    rates = [prob_stack[t] for t in tags if t in prob_stack]
    prob = (sum(rates) / len(rates)) if rates else prob_global
    return max(prob, _PRIOR_RESPOSTA)


def _valor_esperado(analise: dict, ticket: float | None, prob: float) -> float | None:
    """`ticket × prob. resposta × fit ÷ horas` — R$/h esperado da próxima
    proposta. Precisa de orçamento e análise (fit); horas caem no padrão se a
    análise não estimou."""
    if not analise or ticket is None:
        return None
    fit = analise.get("fit_score")
    if not isinstance(fit, (int, float)):
        return None
    horas = (analise.get("estimativa") or {}).get("horas_estimadas")
    if not isinstance(horas, (int, float)) or horas <= 0:
        horas = _HORAS_PADRAO
    return round(ticket * prob * (fit / 100) / horas, 2)


# Limiares do detector de "bom 1º projeto" (fase cold start).
_FIT_MIN = 70
_CONCORRENTES_MAX = 10
_HORAS_ENXUTO = 20


def _detectar_bom_primeiro(
    analise: dict, n_concorrentes: int | None, pagamento_verificado: bool
) -> tuple[bool, list[str]]:
    """Selo determinístico p/ achar a 1ª nota 5★ na fase cold start.

    Pagamento verificado é pré-requisito (não dá pra arriscar a 1ª nota com
    cliente não-verificado). Acima disso, exige 3 de 4 sinais favoráveis.
    Só dispara em projeto já analisado (fit/quadrante/preço vêm da análise).
    """
    if not pagamento_verificado:
        return False, []
    motivos = ["pagamento verificado"]
    sinais = 0

    fit = analise.get("fit_score")
    if isinstance(fit, (int, float)) and fit >= _FIT_MIN:
        sinais += 1
        motivos.append("fit alto")

    if n_concorrentes is not None and n_concorrentes <= _CONCORRENTES_MAX:
        sinais += 1
        motivos.append("pouca concorrência")

    horas = (analise.get("estimativa") or {}).get("horas_estimadas")
    if analise.get("quadrante") == "quick_win" or (
        isinstance(horas, (int, float)) and horas <= _HORAS_ENXUTO
    ):
        sinais += 1
        motivos.append("escopo enxuto")

    if (analise.get("veredito_preco") or {}).get("status") in ("justo", "acima"):
        sinais += 1
        motivos.append("orçamento saudável")

    return sinais >= 3, motivos


_CONCORRENTES_DEMAIS = 20


def _veredito_momento(
    analise: dict,
    bom_primeiro: bool,
    recorrente: bool,
    dias_pub: int | None,
    n_concorrentes: int | None,
    horas_livres: float | None = None,
) -> tuple[str | None, str | None]:
    """"É o momento pra mim, agora?" — agora / espere / passe.

    Determinístico, sintetiza os sinais da fase cold start (fit, risco, frescor,
    concorrência, "bom 1º projeto") + a capacidade livre (anti-furada). Sem
    análise não dá pra julgar → None.
    """
    if not analise:
        return None, None

    fit = analise.get("fit_score")
    fit_num = fit if isinstance(fit, (int, float)) else None
    risco = (analise.get("risco") or "").lower()
    rec = (analise.get("recomendacao") or "").lower()
    quad = analise.get("quadrante")
    fresco = dias_pub is not None and dias_pub <= 3
    horas_proj = (analise.get("estimativa") or {}).get("horas_estimadas")
    sem_mao = (
        horas_livres is not None
        and isinstance(horas_proj, (int, float))
        and horas_proj > horas_livres
    )

    # PASSE — sinais claros de que não vale gastar proposta.
    if rec == "evite" or risco == "alto" or (fit_num is not None and fit_num < 40):
        return "passe", "fit baixo ou risco alto — não gaste proposta aqui"

    # ANTI-FURADA: mesmo com bom fit, não dá pra pegar o que você não entrega.
    # (cliente recorrente fura a fila — vale o esforço de remanejar.)
    if sem_mao and not recorrente:
        return "espere", (
            f"sem mão essa semana ({horas_proj:.0f}h vs {horas_livres:.0f}h livres) "
            "— pegaria e atrasaria o resto"
        )

    # AGORA — responder já (foco do cold start: cravar a 1ª nota).
    if recorrente:
        return "agora", "cliente recorrente — prioridade máxima"
    if bom_primeiro:
        return "agora", "bom 1º projeto — responda cedo"
    if fresco and fit_num is not None and fit_num >= _FIT_MIN:
        return "agora", "fresco + bom fit — responder cedo é vantagem"

    # ESPERE — dá, mas não corre / falta clareza / há melhores na fila.
    if quad == "escopo_vago":
        return "espere", "escopo vago — pergunte ao cliente antes de cotar"
    if n_concorrentes is not None and n_concorrentes > _CONCORRENTES_DEMAIS and not fresco:
        return "espere", "muita concorrência e já não tão fresco"
    return "espere", "ok, mas priorize os melhores da fila primeiro"


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
    if "publicado_em" in dados:
        dados["publicado_em"] = _parse_data(dados["publicado_em"])
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


async def extrair_projeto(
    texto: str | None = None, url: str | None = None
) -> ExtrairProjetoResponse:
    """Campos pré-preenchidos a partir do texto colado OU da URL (não salva).

    Com URL, busca a página (httpx/Playwright, em thread por ser bloqueante) e
    usa o texto visível como fonte. Devolve `descricao` (texto-fonte) e `url`
    pra o form já guardar a origem.
    """
    url = (url or "").strip() or None
    texto = (texto or "").strip() or None
    if not texto and not url:
        raise FreelaError("Cole o texto do projeto ou informe a URL.")

    if not texto and url:
        texto = await asyncio.to_thread(texto_de_url, url)
        if not texto:
            raise FreelaError(
                "Não consegui ler a página dessa URL. Cole o texto do projeto na mão."
            )

    prompt = construir_prompt_extracao(texto)
    resposta = _chamar_llm(prompt, operacao="extrair")
    dados = parse_extracao(resposta)
    if dados is None:
        raise FreelaError("A IA não conseguiu extrair os campos. Preencha na mão.")
    dados.descricao = texto
    dados.url = url
    return dados
