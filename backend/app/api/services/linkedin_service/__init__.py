"""Service do agente LinkedIn (P5 §6.C). Reexporta a API pública do pacote pra
``from app.api.services import linkedin_service`` funcionar como nos demais.
"""
from app.api.services.linkedin_service import admin, agente, coordenador, midia
from app.api.services.linkedin_service._base import (
    LinkedinError,
    contar_chars,
    texto_final,
)

__all__ = [
    "LinkedinError",
    "texto_final",
    "contar_chars",
    "admin",
    "agente",
    "coordenador",
    "midia",
]
