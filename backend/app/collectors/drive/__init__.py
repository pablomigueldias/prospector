"""Collector de pasta pública do Google Drive (sem credencial/OAuth).

Lê a página pública da pasta e extrai os arquivos (id + nome), e baixa cada um
pelo endpoint `uc?export=download`. Serve o sync autônomo de certificados do
Perfil Mestre — o Pablo joga PDFs na pasta, o sistema puxa.
"""
from app.collectors.drive.client import (
    ArquivoDrive,
    baixar_arquivo,
    listar_pasta_publica,
)

__all__ = ["ArquivoDrive", "baixar_arquivo", "listar_pasta_publica"]
