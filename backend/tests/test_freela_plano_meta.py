"""Smoke/unit do motor da meta do freela (matemática reversa + rampa).

Puro: faz patch de `metricas` (não toca API nem DB). Roda standalone com
`python -m tests.test_freela_plano_meta`.
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

from app.api.services.pessoal import freela_service as s
from app.api.schemas.freela import MetricasResponse, PlanoMetaRequest


def _metricas(**kw) -> MetricasResponse:
    base = dict(
        total_propostas=0, enviadas=0, respondidas=0, fechadas=0, perdidas=0,
        em_aberto=0, taxa_resposta=0.0, taxa_fechamento=0.0,
        liquido_total_fechado=0.0, ticket_medio_fechado=0.0,
        pipeline_aberto_liquido=0.0, forecast_liquido=0.0,
        tempo_medio_resposta_horas=None, valor_hora_real=None,
    )
    base.update(kw)
    return MetricasResponse(**base)


def _plano(metrics: MetricasResponse, **req_kw):
    async def _fake():
        return metrics

    async def _run():
        with patch.object(s, "metricas", _fake):
            return await s.plano_meta(PlanoMetaRequest(**req_kw))

    return asyncio.run(_run())


def main() -> None:
    print("━" * 60)
    print("Smoke — motor da meta do freela (plano_meta)")
    print("━" * 60)

    # ── 1. Valor-hora alvo = meta ÷ horas faturáveis ─────────────────
    print("\n→ Test 1: matemática reversa do valor-hora alvo")
    r = _plano(_metricas(), meta_liquida=10000, horas_dia=5, dias_mes=26, pct_faturavel=0.7)
    assert abs(r.horas_faturaveis_mes - 91.0) < 0.01, r.horas_faturaveis_mes
    assert abs(r.valor_hora_alvo - 109.89) < 0.5, r.valor_hora_alvo
    print(f"   91h faturáveis → alvo R$ {r.valor_hora_alvo}/h ✓")

    # ── 2. Sem fechadas → fase F1 (cold start) + gargalo sem_dados ────
    print("\n→ Test 2: cold start (0 fechadas)")
    assert r.fase.nome.startswith("F1"), r.fase.nome
    assert r.gargalo == "sem_dados", r.gargalo
    print(f"   fase={r.fase.nome}, gargalo={r.gargalo} ✓")

    # ── 3. Valor-hora baixo → gargalo TICKET (volume não fecha) ──────
    print("\n→ Test 3: valor-hora baixo → ticket")
    r3 = _plano(_metricas(fechadas=2, valor_hora_real=50, ticket_medio_fechado=900, taxa_fechamento=0.3))
    assert r3.gargalo == "ticket", r3.gargalo
    assert r3.alcancavel_por_volume is False
    assert r3.projecao_liquida_mes is not None and r3.projecao_liquida_mes < 10000
    assert r3.fase.nome.startswith("F2"), r3.fase.nome  # 1–2 fechadas
    print(f"   projeção R$ {r3.projecao_liquida_mes}/mês < meta → gargalo ticket ✓")

    # ── 4. Conversão fraca → gargalo CONVERSAO ───────────────────────
    print("\n→ Test 4: conversão baixa → conversao")
    r4 = _plano(_metricas(fechadas=4, valor_hora_real=150, ticket_medio_fechado=2500, taxa_fechamento=0.08))
    assert r4.gargalo == "conversao", r4.gargalo
    assert r4.fase.nome.startswith("F3"), r4.fase.nome  # 3–5 fechadas
    print(f"   conversão 8% → gargalo conversao, fase {r4.fase.nome} ✓")

    # ── 5. Tudo saudável → gargalo VOLUME + propostas/semana ─────────
    print("\n→ Test 5: saudável → volume com propostas/semana")
    r5 = _plano(_metricas(fechadas=7, valor_hora_real=150, ticket_medio_fechado=2500, taxa_fechamento=0.3))
    assert r5.gargalo == "volume", r5.gargalo
    assert r5.propostas_por_semana and r5.propostas_por_semana > 0
    assert r5.fase.nome.startswith("F4"), r5.fase.nome  # 6+ fechadas
    print(f"   ~{r5.propostas_por_semana} propostas/sem, fase {r5.fase.nome} ✓")

    # ── 6. Inputs inválidos viram erro de negócio ────────────────────
    print("\n→ Test 6: validação de entrada")
    for bad in (dict(meta_liquida=0), dict(horas_dia=0), dict(pct_faturavel=1.5)):
        try:
            _plano(_metricas(), **bad)
            raise AssertionError(f"deveria ter falhado: {bad}")
        except s.FreelaError:
            pass
    print("   meta<=0 / horas<=0 / pct>1 → FreelaError ✓")

    print("\n" + "━" * 60)
    print("✅ motor da meta OK")
    print("━" * 60)


if __name__ == "__main__":
    main()
