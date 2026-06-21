"""Service do Blog headless (P5 §6). Reexporta a API pública do pacote pra
``from app.api.services import blog_service`` funcionar como nos demais agentes.
"""
from app.api.services.blog_service import admin, agente, coordenador, pauta
from app.api.services.blog_service._base import (
    BlogError,
    contar_palavras,
    gerar_slug,
    tempo_de_leitura,
)
from app.api.services.blog_service.publico import (
    dados_sitemap,
    get,
    listar,
    resolver_redirect,
)

__all__ = [
    "BlogError",
    "gerar_slug",
    "contar_palavras",
    "tempo_de_leitura",
    "listar",
    "get",
    "resolver_redirect",
    "dados_sitemap",
    "admin",
    "agente",
    "pauta",
    "coordenador",
]
