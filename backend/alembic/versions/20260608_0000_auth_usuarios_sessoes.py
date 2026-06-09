"""auth: schema + usuarios + sessoes

Portão de entrada do app. Cria o schema ``auth`` (isolado de public/financas)
e as duas tabelas base: ``usuarios`` (senha em hash Argon2id) e ``sessoes``
(sessão opaca no servidor — guarda só o sha256 do token).

Revision ID: a1f0c0de0001
Revises: 233a2397398b
Create Date: 2026-06-08 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a1f0c0de0001"
down_revision: Union[str, None] = "233a2397398b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")

    op.create_table(
        "usuarios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column(
            "ativo", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "twofa_ativado",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_auth_usuarios_email"),
        schema="auth",
    )

    op.create_table(
        "sessoes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ultimo_uso",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "revogada", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=400), nullable=True),
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
            ["usuario_id"],
            ["auth.usuarios.id"],
            name="fk_auth_sessoes_usuario",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessoes_token_hash"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_sessoes_usuario_id", "sessoes", ["usuario_id"], schema="auth"
    )
    op.create_index(
        "ix_auth_sessoes_token_hash", "sessoes", ["token_hash"], schema="auth"
    )


def downgrade() -> None:
    op.drop_index("ix_auth_sessoes_token_hash", table_name="sessoes", schema="auth")
    op.drop_index("ix_auth_sessoes_usuario_id", table_name="sessoes", schema="auth")
    op.drop_table("sessoes", schema="auth")
    op.drop_table("usuarios", schema="auth")
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")
