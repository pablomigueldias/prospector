"""Núcleo compartilhado do service freela: erro de negócio, conversores de UUID,
conversores model→schema e o wrapper de chamada à LLM.

Tudo aqui é reusado pelos módulos por área (cadastro, projetos, propostas, …).
"""
from __future__ import annotations

import uuid

from app.analyzers.llm_provider import gerar_texto
from app.api.schemas.freela import (
    ClienteResponse,
    ProjetoResponse,
    PropostaResponse,
)
from app.api.services._helpers import iso as _iso
from app.api.services._helpers import parse_uuid
from app.db.models.pessoal.freela.cliente import Cliente
from app.db.models.pessoal.freela.projeto import Projeto
from app.db.models.pessoal.freela.proposta import Proposta
from app.utils.logger import get_logger

logger = get_logger()


class FreelaError(Exception):
    """Erro de negócio do agente freela — vira HTTP 400/404 no router."""


def _uuid(valor: str, label: str = "id") -> uuid.UUID:
    return parse_uuid(valor, erro=FreelaError, label=label)


def _uuid_opt(valor: str | None, label: str = "id") -> uuid.UUID | None:
    return _uuid(valor, label) if valor else None


# ── Conversores ──────────────────────────────────────────────────

def _cliente_to_resp(c: Cliente) -> ClienteResponse:
    return ClienteResponse(
        id=str(c.id),
        nome=c.nome,
        plataforma_id=str(c.plataforma_id) if c.plataforma_id else None,
        rating=float(c.rating) if c.rating is not None else None,
        projetos_publicados=c.projetos_publicados,
        projetos_pagos=c.projetos_pagos,
        pagamento_verificado=c.pagamento_verificado,
        membro_desde=c.membro_desde,
        ja_me_pagou_usd=float(c.ja_me_pagou_usd),
        notas=c.notas,
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


def _projeto_to_resp(p: Projeto) -> ProjetoResponse:
    return ProjetoResponse(
        id=str(p.id),
        titulo=p.titulo,
        descricao=p.descricao,
        plataforma_id=str(p.plataforma_id) if p.plataforma_id else None,
        cliente_id=str(p.cliente_id) if p.cliente_id else None,
        url=p.url,
        faixa_orcamento_min=float(p.faixa_orcamento_min) if p.faixa_orcamento_min is not None else None,
        faixa_orcamento_max=float(p.faixa_orcamento_max) if p.faixa_orcamento_max is not None else None,
        habilidades=p.habilidades or [],
        prazo_estimado=p.prazo_estimado,
        status_no_site=p.status_no_site,
        n_propostas_concorrentes=p.n_propostas_concorrentes,
        n_interessados=p.n_interessados,
        publicado_em=p.publicado_em.isoformat() if p.publicado_em else None,
        analise_json=p.analise_json,
        coletado_em=_iso(p.coletado_em),
        created_at=_iso(p.created_at),
        updated_at=_iso(p.updated_at),
    )


def _proposta_to_resp(p: Proposta) -> PropostaResponse:
    return PropostaResponse(
        id=str(p.id),
        projeto_id=str(p.projeto_id),
        valor_cotado=float(p.valor_cotado) if p.valor_cotado is not None else None,
        horas_estimadas=float(p.horas_estimadas) if p.horas_estimadas is not None else None,
        valor_liquido_estimado=float(p.valor_liquido_estimado) if p.valor_liquido_estimado is not None else None,
        texto_enviado=p.texto_enviado,
        projetos_destacados=p.projetos_destacados or [],
        habilidades_destacadas=p.habilidades_destacadas or [],
        prazo_proposto=p.prazo_proposto,
        angulo_abertura=p.angulo_abertura,
        status=p.status,
        enviada_em=_iso(p.enviada_em),
        data_resposta=_iso(p.data_resposta),
        data_fechamento=_iso(p.data_fechamento),
        motivo_perda=p.motivo_perda,
        created_at=_iso(p.created_at),
        updated_at=_iso(p.updated_at),
    )


def _chamar_llm(prompt: str, *, operacao: str) -> str:
    try:
        return gerar_texto(prompt, json_mode=True, agente="freela", operacao=operacao)
    except Exception as e:
        logger.error("freela: falha na LLM ({}): {}", operacao, e)
        raise FreelaError(
            "Não consegui falar com o modelo de IA. "
            "Verifique a conexão/configuração e tente de novo."
        )
