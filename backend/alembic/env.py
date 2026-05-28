from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


from app.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db import models  # noqa: E402,F401  (efeito colateral: registrar modelos)


# Config do .ini (logging)
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Converte URL async → sync pro Alembic
# (Alembic não fala asyncpg, só psycopg)
def _sync_url(async_url: str) -> str:
    if async_url.startswith("postgresql+asyncpg://"):
        return async_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg://", 1
        )
    return async_url


# Sobrescreve a URL do .ini com a do .env
config.set_main_option("sqlalchemy.url", _sync_url(settings.database_url))

# Esse é o `Base.metadata` que o Alembic compara com o banco real
# pra detectar diferenças (autogenerate).
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Modo offline: gera SQL sem conectar no banco. Útil pra revisar
    a migration antes de aplicar.

    Como rodar:  alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Modo online (padrão): conecta no banco e aplica de fato.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()