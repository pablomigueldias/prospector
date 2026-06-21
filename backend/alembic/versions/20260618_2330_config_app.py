"""S3: tabela config_app (overrides de settings pela UI / self-service)

Revision ID: c4a9e7b21d68
Revises: b7f2c9e14a05
Create Date: 2026-06-18 23:30:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'c4a9e7b21d68'
down_revision: Union[str, None] = 'b7f2c9e14a05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'config_app',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('chave', sa.String(80), nullable=False),
        sa.Column('valor', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(),
                  nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                  nullable=False),
        sa.UniqueConstraint('chave', name='uq_config_app_chave'),
    )


def downgrade() -> None:
    op.drop_table('config_app')
