# Vertical slice "linkedin" (categoria Reative Systems — presença & conteúdo).
# Tabelas linkedin_* (NÃO pessoal_*): é presença da marca + do Pablo num só
# agente. O alvo (Página da Reative vs perfil pessoal) é o campo `conta`.
from app.db.models.linkedin.post import (
    CONTA_LINKEDIN,
    FONTE_LINKEDIN,
    FORMATO_LINKEDIN,
    STATUS_LINKEDIN,
    LinkedinPost,
)

__all__ = [
    "LinkedinPost",
    "STATUS_LINKEDIN",
    "FONTE_LINKEDIN",
    "FORMATO_LINKEDIN",
    "CONTA_LINKEDIN",
]
