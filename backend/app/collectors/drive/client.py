"""Enumera e baixa arquivos de uma pasta PÚBLICA do Google Drive.

Sem API key nem OAuth: faz scrape da página da pasta (que embute a lista de
arquivos no HTML) e baixa cada arquivo pelo endpoint público de download.

Limites conhecidos:
- Só funciona pra pastas com link "qualquer um com o link pode ver".
- O scrape depende do HTML do Drive; se o Google mudar o markup, ajustar os
  regexes abaixo (âncoras: `data-id="..."` por linha + `aria-label="<nome> PDF"`).
- Arquivos enormes caem no interstício de "scan de vírus"; certificados (<10MB)
  baixam direto.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from app.utils.logger import get_logger

logger = get_logger()

_FOLDER_URL = "https://drive.google.com/drive/folders/{folder_id}"
_DOWNLOAD_URL = "https://drive.google.com/uc?export=download&id={file_id}"
_TIMEOUT = 40.0

# Cada linha de arquivo traz um `data-id="<FILE_ID>"` e, adiante, um
# `aria-label="<NOME> PDF ..."`. Pareamos o nome ao data-id imediatamente
# anterior a ele no documento.
_RE_DATA_ID = re.compile(r'data-id="([-\w]{20,})"')
_RE_NOME = re.compile(r'aria-label="([^"]+?\.[A-Za-z0-9]+) (?:PDF|Shared|Arquivo)')


@dataclass(frozen=True)
class ArquivoDrive:
    file_id: str
    nome: str


def listar_pasta_publica(folder_id: str) -> list[ArquivoDrive]:
    """Lista (id, nome) dos arquivos de uma pasta pública. Ordem do Drive."""
    url = _FOLDER_URL.format(folder_id=folder_id)
    resp = httpx.get(url, follow_redirects=True, timeout=_TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    ids = [(m.start(), m.group(1)) for m in _RE_DATA_ID.finditer(html)]
    nomes = [(m.start(), m.group(1)) for m in _RE_NOME.finditer(html)]

    arquivos: list[ArquivoDrive] = []
    vistos: set[str] = set()
    for pos_nome, nome in nomes:
        anteriores = [fid for pos, fid in ids if pos < pos_nome]
        if not anteriores:
            continue
        fid = anteriores[-1]
        if fid in vistos:
            continue
        vistos.add(fid)
        arquivos.append(ArquivoDrive(file_id=fid, nome=nome))

    logger.info("Drive: {} arquivos na pasta {}", len(arquivos), folder_id)
    return arquivos


def baixar_arquivo(file_id: str) -> bytes:
    """Baixa o conteúdo bruto de um arquivo público pelo id."""
    url = _DOWNLOAD_URL.format(file_id=file_id)
    resp = httpx.get(url, follow_redirects=True, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.content
