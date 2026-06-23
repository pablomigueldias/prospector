"""Agente LinkedIn (P5 §6.C — L0): tabela linkedin_post

Revision ID: b9d3f2a8c1e7
Revises: a7c2e5f9b1d8
Create Date: 2026-06-22 17:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b9d3f2a8c1e7"
down_revision: Union[str, None] = "a7c2e5f9b1d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "linkedin_post",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("titulo", sa.String(length=200)),
        sa.Column(
            "conta", sa.String(length=10), server_default="reative", nullable=False
        ),
        sa.Column(
            "formato", sa.String(length=12), server_default="post", nullable=False
        ),
        sa.Column("hook", sa.Text()),
        sa.Column("body", sa.Text()),
        sa.Column("cta", sa.Text()),
        sa.Column("hashtags", postgresql.JSONB()),
        sa.Column(
            "status", sa.String(length=20), server_default="rascunho", nullable=False
        ),
        sa.Column(
            "fonte", sa.String(length=20), server_default="manual", nullable=False
        ),
        sa.Column(
            "origem_blog_post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("blog_post.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scheduled_for", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("char_count", sa.Integer()),
        sa.Column("notas", sa.Text()),
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
    op.create_index("ix_linkedin_post_conta", "linkedin_post", ["conta"])
    op.create_index("ix_linkedin_post_status", "linkedin_post", ["status"])
    op.create_index(
        "ix_linkedin_post_scheduled_for", "linkedin_post", ["scheduled_for"]
    )


def downgrade() -> None:
    op.drop_index("ix_linkedin_post_scheduled_for", table_name="linkedin_post")
    op.drop_index("ix_linkedin_post_status", table_name="linkedin_post")
    op.drop_index("ix_linkedin_post_conta", table_name="linkedin_post")
    op.drop_table("linkedin_post")
