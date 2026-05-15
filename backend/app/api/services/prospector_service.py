"""
Serviço do agente Prospector — orquestra o pipeline existente
(BrasilAPI/OpenCNPJ → site → IA → Notion) por trás de uma fachada
simples consumível pela API HTTP.

Esta camada existe pra:
- Isolar a API do pipeline (se o pipeline mudar, só este arquivo mexe)
- Capturar metadados úteis pra resposta HTTP (fonte do CNPJ, ids do Notion)
- Tratar erros com mensagens amigáveis pro frontend
"""

from __future__ import annotations

import contextlib
import io
import logging
from typing import Optional, Tuple

from app.analyzers.gemini import enriquecer_lead_com_analise
from app.collectors.brasilapi import (
    _consultar_com_fallback,
    map_to_lead,
)
from app.collectors.brasilapi import buscar_lead_por_cnpj as _orchestrate
from app.collectors.brasilapi.client import _digits_only, _validate_cnpj_digits
from app.collectors.website import enriquecer_lead_com_site
from app.exporters.notion import NotionExporter
from app.models.lead import Lead
from app.services.manual_overrides import aplicar_overrides_manuais
from app.utils.logger import get_logger
from app.utils.storage import save_lead


logger = get_logger()


# ─────────────────────────────────────────────────────────────────────
# Erros traduzíveis pro frontend
# ─────────────────────────────────────────────────────────────────────


class ProspectorError(Exception):
    """Erro de negócio do Prospector — vira HTTP 4xx/5xx com mensagem amigável."""

    def __init__(self, message: str, *, status_code: int = 400, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


class CnpjNaoEncontradoEmFonteAlguma(ProspectorError):
    def __init__(self, cnpj: str):
        super().__init__(
            message=(
                f"CNPJ {cnpj} não foi encontrado em nenhuma das fontes "
                f"(BrasilAPI e OpenCNPJ). Pode ser uma empresa baixada "
                f"ou cadastro muito recente."
            ),
            status_code=404,
        )


class CnpjInvalido(ProspectorError):
    def __init__(self, cnpj: str):
        super().__init__(
            message=f"CNPJ inválido: {cnpj}. Verifique os dígitos.",
            status_code=400,
        )


# ─────────────────────────────────────────────────────────────────────
# Preview — monta o Lead mas NÃO envia pro Notion
# ─────────────────────────────────────────────────────────────────────


def preview_lead(
    cnpj: str,
    *,
    site: Optional[str] = None,
    instagram: Optional[str] = None,
    facebook: Optional[str] = None,
    linkedin: Optional[str] = None,
    email: Optional[str] = None,
    telefone: Optional[str] = None,
    whatsapp: Optional[str] = None,
    run_ai: bool = False,
) -> Tuple[Lead, Optional[str]]:
    """
    Monta o Lead sem enviar pro Notion.

    Útil pro botão "Pré-visualizar lead" do dashboard — o usuário vê
    o que vai pro Notion antes de confirmar.

    `run_ai=False` por padrão pra preview ser barato e rápido.
    Devolve (lead, fonte_cnpj).
    """
    digits = _digits_only(cnpj)

    if not _validate_cnpj_digits(digits):
        raise CnpjInvalido(cnpj)

    data, fonte = _consultar_com_fallback(digits)
    if data is None:
        raise CnpjNaoEncontradoEmFonteAlguma(cnpj)

    lead = map_to_lead(data)

    # Extras OpenCNPJ (email/telefones da Receita) nas Notas
    extras = data.get("_extras_opencnpj") or {}
    if fonte == "opencnpj" and extras:
        from app.collectors.brasilapi import _anexar_extras_nas_notas
        _anexar_extras_nas_notas(lead, extras)

    # Enriquecer com site (se informado)
    if site:
        try:
            lead = enriquecer_lead_com_site(lead, site)
        except Exception as e:
            logger.warning(f"Falha no scraping do site (segue sem): {e}")

    # Overrides manuais (sempre prevalecem)
    overrides = _coletar_overrides(
        instagram=instagram,
        facebook=facebook,
        linkedin=linkedin,
        email=email,
        telefone=telefone,
        whatsapp=whatsapp,
    )
    if overrides:
        lead = aplicar_overrides_manuais(lead, **overrides)

    # Análise IA opcional
    if run_ai:
        try:
            lead = enriquecer_lead_com_analise(lead)
        except Exception as e:
            logger.warning(f"Falha na análise IA no preview (segue sem): {e}")

    return lead, fonte


# ─────────────────────────────────────────────────────────────────────
# Run completo — chama o pipeline e envia pro Notion
# ─────────────────────────────────────────────────────────────────────


def executar_pipeline_completo(
    cnpj: str,
    *,
    site: Optional[str] = None,
    instagram: Optional[str] = None,
    facebook: Optional[str] = None,
    linkedin: Optional[str] = None,
    email: Optional[str] = None,
    telefone: Optional[str] = None,
    whatsapp: Optional[str] = None,
) -> Tuple[Lead, Optional[str]]:
    """
    Pipeline completo: CNPJ + site + overrides + análise IA + Notion.

    Equivalente ao `cmd_prospectar_full` do CLI, mas com tratamento de
    erros adequado pra HTTP. Devolve (lead, fonte_cnpj).
    """
    digits = _digits_only(cnpj)

    if not _validate_cnpj_digits(digits):
        raise CnpjInvalido(cnpj)

    # 1. CNPJ via orquestrador (BrasilAPI → OpenCNPJ)
    # Usa a função pública pra ter o save_lead(raw) e os logs bonitos
    lead = _orchestrate(digits, salvar_raw=True)
    if lead is None:
        raise CnpjNaoEncontradoEmFonteAlguma(cnpj)

    # Recupera a fonte usada — pequena duplicação porque o orquestrador
    # não devolve isso, mas o overhead é zero (já está em cache da requisição)
    data, fonte = _consultar_com_fallback(digits)

    # 2. Site (opcional)
    if site:
        try:
            lead = enriquecer_lead_com_site(lead, site)
        except Exception as e:
            logger.warning(f"Falha no scraping do site (segue sem): {e}")

    # 3. Overrides manuais (após site, pra ganhar prioridade)
    overrides = _coletar_overrides(
        instagram=instagram,
        facebook=facebook,
        linkedin=linkedin,
        email=email,
        telefone=telefone,
        whatsapp=whatsapp,
    )
    if overrides:
        lead = aplicar_overrides_manuais(lead, **overrides)

    # 4. Análise IA
    try:
        lead = enriquecer_lead_com_analise(lead)
    except Exception as e:
        logger.warning(f"Falha na análise IA (segue sem): {e}")

    # 5. Salva backup
    save_lead(lead, stage="processed")

    # 6. Envia pro Notion
    exporter = NotionExporter()
    lead = exporter.send_lead(lead)
    save_lead(lead, stage="sent")

    return lead, fonte


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _coletar_overrides(**kwargs) -> dict:
    """Filtra Nones e devolve só os campos com valor — pra repassar
    como **kwargs ao aplicar_overrides_manuais sem injetar Nones."""
    return {k: v for k, v in kwargs.items() if v}
