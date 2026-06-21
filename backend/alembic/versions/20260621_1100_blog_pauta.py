"""Blog motor de pauta (P5 §6.B3): blog_pauta

Revision ID: a7c2e5f9b1d8
Revises: f3b9c1d4e7a2
Create Date: 2026-06-21 11:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a7c2e5f9b1d8"
down_revision: Union[str, None] = "f3b9c1d4e7a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blog_pauta",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("resumo", sa.Text()),
        sa.Column("keyword_alvo", sa.String(length=120)),
        sa.Column("intencao", sa.String(length=20)),
        sa.Column("publico", sa.String(length=20)),
        sa.Column("estagio_funil", sa.String(length=10)),
        sa.Column("fonte", sa.String(length=20), server_default="manual", nullable=False),
        sa.Column("score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ideia", nullable=False),
        sa.Column("notas", sa.Text()),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("blog_post.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_blog_pauta_status", "blog_pauta", ["status"])


def downgrade() -> None:
    op.drop_index("ix_blog_pauta_status", table_name="blog_pauta")
    op.drop_table("blog_pauta")
