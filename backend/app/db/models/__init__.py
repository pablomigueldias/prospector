"""
Re-exporta todos os modelos ORM.

IMPORTANTE: pra Alembic descobrir as tabelas via `--autogenerate`,
todo modelo precisa ser importado em algum lugar que seja carregado
ANTES do Alembic rodar. Esse __init__.py é esse lugar.

Quando você criar um modelo novo (`evento.py`, `ai_call.py`, etc),
adiciona o import aqui. Senão a tabela some das migrations.
"""

from app.db.models.empresa import Empresa
from app.db.models.contato import Contato
from app.db.models.socio import Socio


__all__ = ["Empresa", "Contato", "Socio"]