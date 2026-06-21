"""Blog headless (P5 §6.B0): blog_post + blog_redirect

Revision ID: f3b9c1d4e7a2
Revises: e2a8b5d1c9f4
Create Date: 2026-06-20 10:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f3b9c1d4e7a2"
down_revision: Union[str, None] = "e2a8b5d1c9f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blog_post",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("excerpt", sa.Text()),
        sa.Column("category", sa.String(length=60)),
        sa.Column("body_md", sa.Text()),
        sa.Column("toc", postgresql.JSONB()),
        sa.Column("cover_url", sa.String(length=500)),
        sa.Column("cover_alt", sa.String(length=255)),
        sa.Column("cover_class", sa.String(length=60)),
        sa.Column("imagens", postgresql.JSONB()),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="rascunho",
            nullable=False,
        ),
        sa.Column(
            "author",
            sa.String(length=120),
            server_default="Pablo Dias",
            nullable=False,
        ),
        sa.Column(
            "lang", sa.String(length=10), server_default="pt-BR", nullable=False
        ),
        sa.Column("tags", postgresql.JSONB()),
        sa.Column("reading_time", sa.Integer()),
        sa.Column("word_count", sa.Integer()),
        sa.Column(
            "noindex", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("meta_description", sa.String(length=200)),
        sa.Column("keyword_alvo", sa.String(length=120)),
        sa.Column("keywords", postgresql.JSONB()),
        sa.Column("og_image", sa.String(length=500)),
        sa.Column("og_title", sa.String(length=200)),
        sa.Column("og_description", sa.String(length=300)),
        sa.Column("fonte", sa.String(length=20)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
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
    op.create_index("ix_blog_post_slug", "blog_post", ["slug"], unique=True)
    op.create_index("ix_blog_post_status", "blog_post", ["status"])
    op.create_index("ix_blog_post_published_at", "blog_post", ["published_at"])

    op.create_table(
        "blog_redirect",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("slug_antigo", sa.String(length=160), nullable=False),
        sa.Column("slug_novo", sa.String(length=160), nullable=False),
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
    op.create_index(
        "ix_blog_redirect_slug_antigo",
        "blog_redirect",
        ["slug_antigo"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_blog_redirect_slug_antigo", table_name="blog_redirect")
    op.drop_table("blog_redirect")
    op.drop_index("ix_blog_post_published_at", table_name="blog_post")
    op.drop_index("ix_blog_post_status", table_name="blog_post")
    op.drop_index("ix_blog_post_slug", table_name="blog_post")
    op.drop_table("blog_post")
