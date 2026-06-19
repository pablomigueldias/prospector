"""perfil mestre: adiciona certificacoes (Fase 0 do plano MAS)

Revision ID: c7e1a9d4f2b8
Revises: d1f4a7c9e2b6
Create Date: 2026-06-17 21:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'c7e1a9d4f2b8'
down_revision: Union[str, None] = 'd1f4a7c9e2b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'pessoal_perfil_mestre',
        sa.Column('certificacoes', JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('pessoal_perfil_mestre', 'certificacoes')
