"""seed categorias financas

Revision ID: 3fe4d1c4a738
Revises: f1d8647d25f4
Create Date: 2026-06-07 19:08:53.517732+00:00

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3fe4d1c4a738'
down_revision: Union[str, None] = 'f1d8647d25f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Árvore base de categorias. Já inclui as subverbas do boleto do condomínio
# (Lello), que é o caso que motivou a hierarquia: uma despesa-pai com várias
# subverbas. {pai: [filhos]}.
SEED: dict[str, list[str]] = {
    "Condomínio": [
        "Taxa de condomínio",
        "Consumo de gás",
        "Fundo de reserva",
        "Consumo de água",
        "Consumo de luz (área comum)",
        "Água área comum",
        "Reforma infiltração (parcelada)",
    ],
    "Moradia": [
        "Aluguel",
        "Luz (Enel)",
    ],
    "Transporte": [
        "Gasolina",
    ],
    "Alimentação": [
        "Mercado",
    ],
    "Dívidas": [
        "Empréstimo",
        "Cartão de crédito",
        "Acordos",
    ],
}


def _categorias_table() -> sa.Table:
    return sa.table(
        "categorias",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("nome", sa.String),
        sa.column("categoria_pai_id", postgresql.UUID(as_uuid=True)),
        sa.column("ativa", sa.Boolean),
        schema="financas",
    )


def upgrade() -> None:
    cat = _categorias_table()
    rows: list[dict] = []
    # UUIDs gerados aqui pra ligar pai→filho; created_at/updated_at ficam
    # com os server_default do banco.
    for pai_nome, filhos in SEED.items():
        pai_id = uuid.uuid4()
        rows.append({"id": pai_id, "nome": pai_nome, "categoria_pai_id": None, "ativa": True})
        for filho_nome in filhos:
            rows.append({
                "id": uuid.uuid4(),
                "nome": filho_nome,
                "categoria_pai_id": pai_id,
                "ativa": True,
            })
    op.bulk_insert(cat, rows)


def downgrade() -> None:
    # Apaga as categorias-pai do seed; os filhos somem por CASCADE.
    pais = list(SEED.keys())
    op.execute(
        sa.text(
            "DELETE FROM financas.categorias "
            "WHERE categoria_pai_id IS NULL AND nome = ANY(:pais)"
        ).bindparams(sa.bindparam("pais", value=pais, type_=postgresql.ARRAY(sa.String)))
    )
