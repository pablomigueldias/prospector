"""Seed da plataforma Workana (faixas de comissão + lance mínimo).

Idempotente: se já existir uma plataforma 'Workana', atualiza a config.

    source backend/venv/bin/activate
    python backend/scripts/seed_freela.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import asyncio

from sqlalchemy import select

from app.db.models.pessoal.freela.plataforma import Plataforma
from app.db.session import get_session

WORKANA = {
    "nome": "Workana",
    "url_base": "https://www.workana.com",
    # Comissão escalonada por cliente: 20% até US$300 acumulados, 10% até
    # US$3.000, 5% acima. O cliente ainda paga ~4,5% de custo de serviço.
    "config_comissao": {
        "faixas": [
            {"ate_usd": 300, "pct": 0.20},
            {"ate_usd": 3000, "pct": 0.10},
            {"ate_usd": None, "pct": 0.05},
        ],
        "custo_servico_cliente_pct": 0.045,
        # As faixas acima são em US$; ao fechar uma proposta, o líquido (R$) é
        # convertido por esta taxa pra somar no acumulado do cliente.
        "usd_brl": 5.20,
    },
    "lance_minimo_padrao": 760.0,
}


async def main() -> None:
    async with get_session() as session:
        existente = await session.scalar(
            select(Plataforma).where(Plataforma.nome == WORKANA["nome"])
        )
        if existente:
            existente.url_base = WORKANA["url_base"]
            existente.config_comissao = WORKANA["config_comissao"]
            existente.lance_minimo_padrao = WORKANA["lance_minimo_padrao"]
            acao = "atualizada"
        else:
            session.add(Plataforma(**WORKANA))
            acao = "criada"
        await session.commit()
    print(f"✓ Plataforma Workana {acao}.")


if __name__ == "__main__":
    asyncio.run(main())
