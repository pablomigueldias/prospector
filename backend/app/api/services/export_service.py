"""S8 — Export / Backup pela tela.

Exporta os domínios principais em CSV (um recurso por vez) ou um backup JSON
com tudo junto. Genérico: lê as colunas do próprio modelo SQLAlchemy, então não
precisa manter schema de export à mão. Leitura pura via `get_session`.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.db.models.contato import Contato
from app.db.models.empresa import Empresa
from app.db.models.financas.transacao import Transacao
from app.db.models.negocio import Negocio
from app.db.models.pessoal.vaga import Vaga
from app.db.session import get_session


class ExportError(ValueError):
    """Recurso desconhecido."""


# Recursos exportáveis (slug → modelo).
EXPORTS: dict[str, Any] = {
    "empresas": Empresa,
    "contatos": Contato,
    "negocios": Negocio,
    "vagas": Vaga,
    "transacoes": Transacao,
}

RECURSOS = tuple(EXPORTS.keys())


def _serial(v: Any) -> Any:
    if isinstance(v, datetime | date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, UUID):
        return str(v)
    return v


async def linhas(recurso: str) -> list[dict]:
    model = EXPORTS.get(recurso)
    if model is None:
        raise ExportError(f"recurso desconhecido: {recurso}")
    cols = [c.name for c in model.__table__.columns]
    async with get_session() as session:
        rows = (await session.execute(select(model))).scalars().all()
    return [{c: _serial(getattr(r, c)) for c in cols} for r in rows]


def to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for r in rows:
        # dict/list (JSONB) vira JSON pra não sair como repr do Python.
        writer.writerow(
            {
                k: json.dumps(v, ensure_ascii=False)
                if isinstance(v, dict | list)
                else v
                for k, v in r.items()
            }
        )
    return buf.getvalue()


async def backup() -> dict:
    recursos = {r: await linhas(r) for r in RECURSOS}
    return {
        "gerado_em": datetime.now().isoformat(),
        "totais": {r: len(v) for r, v in recursos.items()},
        "recursos": recursos,
    }
