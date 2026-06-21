"""Freela §2.F: data de publicação do projeto (frescor / cold start)

Revision ID: d1f7a4c9e2b3
Revises: c4a9e7b21d68
Create Date: 2026-06-19 12:00:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd1f7a4c9e2b3'
down_revision: Union[str, None] = 'c4a9e7b21d68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'pessoal_freela_projeto',
        sa.Column('publicado_em', sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('pessoal_freela_projeto', 'publicado_em')
