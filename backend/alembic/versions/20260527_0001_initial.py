"""initial schema: empresas, contatos, socios + pgvector extension

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-27 00:00:00

Cria a estrutura mínima da Reative:
- extensão pgvector (preparado pra embeddings futuros)
- tabela `empresas` com índices em estado, setor, cidade
- tabela `socios` (FK pra empresas, CASCADE)
- tabela `contatos` (FK pra empresas, CASCADE)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensões do Postgres ────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── empresas ─────────────────────────────────────────────────
    op.create_table(
        "empresas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(length=500), nullable=False),
        sa.Column("razao_social", sa.String(length=500), nullable=True),
        sa.Column("cnpj", sa.String(length=14), nullable=True),
        sa.Column("cidade", sa.String(length=200), nullable=True),
        sa.Column("estado", sa.String(length=2), nullable=True),
        sa.Column("local", sa.Text(), nullable=True),
        sa.Column("site", sa.String(length=500), nullable=True),
        sa.Column("instagram", sa.String(length=300), nullable=True),
        sa.Column("facebook", sa.String(length=300), nullable=True),
        sa.Column(
            "capital_social",
            sa.Numeric(precision=15, scale=2),
            nullable=True,
        ),
        sa.Column("setor", sa.String(length=100), nullable=True),
        sa.Column("tamanho", sa.String(length=50), nullable=True),
        sa.Column(
            "como_conheceu",
            sa.String(length=50),
            server_default="Outbound",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="🔵 Prospect",
            nullable=False,
        ),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("notion_page_id", sa.String(length=50), nullable=True),
        sa.Column("notion_synced_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj", name="uq_empresas_cnpj"),
    )
    op.create_index("ix_empresas_estado", "empresas", ["estado"])
    op.create_index(
        "ix_empresas_cidade_estado", "empresas", ["cidade", "estado"]
    )
    op.create_index("ix_empresas_setor", "empresas", ["setor"])
    op.create_index(
        "ix_empresas_notion_page_id", "empresas", ["notion_page_id"]
    )

    # ── socios ───────────────────────────────────────────────────
    op.create_table(
        "socios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("nome", sa.String(length=300), nullable=False),
        sa.Column("qualificacao", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresas.id"],
            ondelete="CASCADE",
            name="fk_socios_empresa_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_socios_empresa_id", "socios", ["empresa_id"])

    # ── contatos ─────────────────────────────────────────────────
    op.create_table(
        "contatos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("nome", sa.String(length=300), nullable=False),
        sa.Column("cargo", sa.String(length=200), nullable=True),
        sa.Column(
            "decisor",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=300), nullable=True),
        sa.Column("telefone", sa.String(length=50), nullable=True),
        sa.Column("whatsapp", sa.String(length=50), nullable=True),
        sa.Column("linkedin", sa.String(length=500), nullable=True),
        sa.Column(
            "origem_contato",
            sa.String(length=50),
            server_default="Network",
            nullable=False,
        ),
        sa.Column("notion_page_id", sa.String(length=50), nullable=True),
        sa.Column("notion_synced_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["empresa_id"],
            ["empresas.id"],
            ondelete="CASCADE",
            name="fk_contatos_empresa_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contatos_empresa_id", "contatos", ["empresa_id"])
    op.create_index("ix_contatos_email", "contatos", ["email"])
    op.create_index("ix_contatos_decisor", "contatos", ["decisor"])


def downgrade() -> None:
    # Ordem reversa: contatos e socios primeiro (FK), depois empresas.
    # Extensões a gente NÃO dropa — outros bancos podem usar.
    op.drop_index("ix_contatos_decisor", table_name="contatos")
    op.drop_index("ix_contatos_email", table_name="contatos")
    op.drop_index("ix_contatos_empresa_id", table_name="contatos")
    op.drop_table("contatos")

    op.drop_index("ix_socios_empresa_id", table_name="socios")
    op.drop_table("socios")

    op.drop_index("ix_empresas_notion_page_id", table_name="empresas")
    op.drop_index("ix_empresas_setor", table_name="empresas")
    op.drop_index("ix_empresas_cidade_estado", table_name="empresas")
    op.drop_index("ix_empresas_estado", table_name="empresas")
    op.drop_table("empresas")
