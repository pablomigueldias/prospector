"""IA: análise de projeto (Fase 3) + pós-processamento determinístico
(quadrante dificuldade × esforço e veredito de preço orçamento × mercado)."""
from __future__ import annotations

from typing import Optional

from app.analyzers.freela.analisador.parser import parse_resposta as parse_analise
from app.analyzers.freela.analisador.prompt_builder import (
    construir_prompt as construir_prompt_analise,
)
from app.api.schemas.freela import (
    AnalisarProjetoResponse,
    EstimativaFreela,
    VereditoPreco,
)
from app.api.services._helpers import r2 as _r2
from app.api.services.pessoal.perfil_service import get_perfil
from app.db.models.pessoal.freela.cliente import Cliente
from app.db.models.pessoal.freela.projeto import Projeto
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import FreelaError, _chamar_llm, _uuid


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
