"""cria schema financas

Revision ID: a5d6d0ad5b73
Revises: 8e0abc9aabf2
Create Date: 2026-06-07 19:00:19.954219+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5d6d0ad5b73'
down_revision: Union[str, None] = '8e0abc9aabf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema próprio do Organizador Financeiro pessoal. Isola o domínio
    # pessoal do B2B (Prospector) sem precisar de um segundo banco.
    # As tabelas (contas, categorias, transacoes...) entram aqui nos
    # próximos steps via schema='financas'.
    op.execute("CREATE SCHEMA IF NOT EXISTS financas")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS financas CASCADE")
