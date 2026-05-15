"""
Lê o backup local de leads enviados (`data/sent/*.json`) e devolve
itens resumidos pro histórico do dashboard.

Por que ler local em vez do Notion?
- Sem rate limit
- Sem latência (a tela carrega instantaneamente)
- Funciona offline
- Já tem todos os campos no JSON serializado (o pipeline salva tudo)

O Notion vira "fonte de verdade pra negócio"; o backup local é "fonte
de verdade pra histórico operacional".
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.api.schemas.prospector import LeadHistoryItem
from app.utils.logger import get_logger
from app.utils.storage import list_leads, load_lead


logger = get_logger()


_TIMESTAMP_RE = re.compile(r"^(\d{8}_\d{6})_")


def ler_historico(limit: int = 20) -> List[LeadHistoryItem]:
    """
    Devolve os últimos `limit` leads enviados, do mais recente pro mais antigo.
    """
    arquivos = list_leads(stage="sent")
    # `list_leads` já volta ordenado alfabeticamente, e como o nome começa
    # com timestamp, isso é cronológico. Pegamos os últimos N e invertemos.
    arquivos = arquivos[-limit:][::-1]

    items: List[LeadHistoryItem] = []
    for arq in arquivos:
        try:
            item = _arquivo_para_item(arq)
            if item:
                items.append(item)
        except Exception as e:
            logger.warning(f"Não consegui ler {arq.name}: {e}")

    return items


def _arquivo_para_item(arq: Path) -> Optional[LeadHistoryItem]:
    """Converte um arquivo JSON de lead salvo em LeadHistoryItem resumido."""
    lead = load_lead(arq)
    emp = lead.empresa

    return LeadHistoryItem(
        empresa_nome=emp.nome or "(sem nome)",
        cnpj=emp.cnpj,
        cidade=emp.cidade,
        estado=emp.estado,
        setor=emp.setor,
        qtd_contatos=len(lead.contatos),
        notion_empresa_id=emp.notion_page_id,
        enviado_em=_extrair_timestamp(arq.name),
        arquivo=arq.name,
    )


def _extrair_timestamp(filename: str) -> Optional[str]:
    """
    Extrai o timestamp do nome do arquivo (`20251112_143052_nome.json`)
    e devolve em formato ISO 8601 pro frontend.
    """
    match = _TIMESTAMP_RE.match(filename)
    if not match:
        return None
    try:
        dt = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
        return dt.isoformat(timespec="seconds")
    except ValueError:
        return None
