"""Precificador: matemática da comissão Workana (sem IA)."""
from __future__ import annotations

from app.api.schemas.freela import PrecificarRequest, PrecificarResponse
from app.api.services._helpers import r2 as _r2
from app.db.models.pessoal.freela.plataforma import Plataforma
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import FreelaError, _uuid

# Faixas de comissão padrão (Workana) caso a plataforma não tenha config.
_COMISSAO_PADRAO = [
    {"ate_usd": 300, "pct": 0.20},
    {"ate_usd": 3000, "pct": 0.10},
    {"ate_usd": None, "pct": 0.05},
]
_CUSTO_SERVICO_PADRAO = 0.045


def _pct_comissao(config_comissao: dict | None, ja_me_pagou_usd: float) -> float:
    faixas = (config_comissao or {}).get("faixas") or _COMISSAO_PADRAO
    for faixa in faixas:
        ate = faixa.get("ate_usd")
        if ate is None or ja_me_pagou_usd < ate:
            return float(faixa["pct"])
    return float(faixas[-1]["pct"])


async def precificar(req: PrecificarRequest) -> PrecificarResponse:
    if req.liquido_desejado <= 0:
        raise FreelaError("Informe o líquido desejado (maior que zero).")

    plataforma: Plataforma | None = None
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

    # Orçamento incompatível: compara o LANCE (valor a cotar) com a faixa do
    # cliente/mercado informada. Acima = risco de perder por preço; abaixo =
    # provável subcotação (dá pra cobrar mais).
    orcamento_status = None
    alerta_orcamento = None
    omin, omax = req.orcamento_min, req.orcamento_max
    if omax is not None and valor_a_cotar > omax:
        orcamento_status = "acima"
        alerta_orcamento = (
            f"Lance R$ {valor_a_cotar:.0f} acima do teto do orçamento "
            f"(R$ {omax:.0f}) — risco de perder por preço. Reduza escopo/horas ou "
            f"justifique o valor."
        )
    elif omin is not None and valor_a_cotar < omin:
        orcamento_status = "abaixo"
        alerta_orcamento = (
            f"Lance R$ {valor_a_cotar:.0f} abaixo do piso do orçamento "
            f"(R$ {omin:.0f}) — você pode estar subcotando; dá pra cobrar mais."
        )
    elif omin is not None or omax is not None:
        orcamento_status = "dentro"

    return PrecificarResponse(
        pct_comissao=pct,
        valor_a_cotar=valor_a_cotar,
        cliente_paga=cliente_paga,
        lance_minimo=lance_min,
        abaixo_do_lance_minimo=abaixo_min,
        liquido_por_hora=liquido_por_hora,
        alerta=alerta,
        orcamento_status=orcamento_status,
        alerta_orcamento=alerta_orcamento,
    )
