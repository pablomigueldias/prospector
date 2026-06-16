"""vagas: persiste o currículo ATS gerado por vaga

Revision ID: d1f4a7c9e2b6
Revises: a09c2bcb4148
Create Date: 2026-06-15 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'd1f4a7c9e2b6'
down_revision: Union[str, None] = 'a09c2bcb4148'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'pessoal_vagas',
        sa.Column('curriculo_json', JSONB(), nullable=True),
    )
    op.add_column(
        'pessoal_vagas',
        sa.Column('curriculo_gerado_em', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('pessoal_vagas', 'curriculo_gerado_em')
    op.drop_column('pessoal_vagas', 'curriculo_json')
