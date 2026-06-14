"""Schemas do Organizador Financeiro pessoal (domínio `financas`).

Isolado dos schemas da Reative (prospector/copywriter/outreach) e dos
pessoais (perfil/vagas).

Era um arquivo-deus de ~836 linhas; foi quebrado por subdomínio (ver
docs/ORGANIZACAO_REFATORACAO.md). Este `__init__` re-exporta tudo, então
`from app.api.schemas.financas import X` continua válido. Para mexer num
schema, vá direto no submódulo do domínio.
"""
from __future__ import annotations

from .boleto import *  # noqa: F401,F403
from .cartao import *  # noqa: F401,F403
from .categoria import *  # noqa: F401,F403
from .comprovante import *  # noqa: F401,F403
from .conta import *  # noqa: F401,F403
from .leitura import *  # noqa: F401,F403
from .nlu import *  # noqa: F401,F403
from .orcamento import *  # noqa: F401,F403
from .pagamento_mes import *  # noqa: F401,F403
from .recorrencia import *  # noqa: F401,F403
from .resumo import *  # noqa: F401,F403
from .transacao import *  # noqa: F401,F403
