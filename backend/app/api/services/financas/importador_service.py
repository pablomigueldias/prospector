"""Importador de boleto — o 'pulo do gato'.

Recebe o arquivo (PDF/foto), sobe pro MinIO, manda pro LLM multimodal, valida
o JSON e — se a soma das verbas bate com o total — cria a despesa com os itens
(subverbas) e as leituras de consumo automaticamente. Se não bate, marca pra
revisão manual (não cria nada, só guarda o extraído).
"""
from __future__ import annotations

import asyncio
import re
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from app.analyzers.boleto import extrator
from app.analyzers.boleto.parser import parse_boleto
from app.api.schemas.financas import ImportarBoletoResponse
from app.api.services.financas.comprovante_service import salvar_comprovante
from app.db.models.financas.comprovante import Comprovante
from app.db.models.financas.leitura_consumo import TIPOS_CONSUMO, LeituraConsumo
from app.db.models.financas.transacao import Transacao
from app.db.models.financas.transacao_item import TransacaoItem
from app.db.session import get_session
from app.repositories.financas.transacao_repository import TransacaoRepository


class ImportadorError(Exception):
    """Erro de negócio do importador — vira HTTP 400/404 no router."""


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise ImportadorError(f"{campo} inválido: {valor!r}")


async def importar_boleto(
    *,
    usuario_id: str,
    conteudo: bytes,
    nome_original: Optional[str] = None,
    content_type: Optional[str] = None,
    categoria_id: Optional[str] = None,
) -> ImportarBoletoResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    cat_id = _uuid(categoria_id, campo="categoria_id") if categoria_id else None

    # 1. Guarda o arquivo (upload + dedup).
    comp = await salvar_comprovante(
        usuario_id=usuario_id, tipo="boleto", conteudo=conteudo,
        nome_original=nome_original, content_type=content_type,
    )

    # 2. Extrai via LLM multimodal (boto3/httpx síncrono → thread).
    texto = await asyncio.to_thread(extrator.extrair_boleto_llm, conteudo, content_type)
    extraido = parse_boleto(texto)
    if extraido is None:
        return ImportarBoletoResponse(
            success=False, conferido=False, comprovante_id=comp.id,
            mensagem="Não consegui ler o boleto. Tente uma foto mais nítida.",
        )

    soma = sum((v.valor for v in extraido.verbas), Decimal("0"))
    conferido = bool(extraido.verbas) and soma == extraido.valor_total

    competencia = (
        date(extraido.vencimento.year, extraido.vencimento.month, 1)
        if extraido.vencimento else date.today().replace(day=1)
    )

    # Linha digitável só com dígitos (chave forte de duplicata + copiar/colar).
    linha = re.sub(r"\D", "", extraido.linha_digitavel or "") or None

    # Sempre que houver um valor total, o boleto vira uma despesa **prevista**
    # (a pagar) — assim ele nunca some de vista. As verbas (itens) e as leituras
    # de consumo só entram quando a soma bate com o total (conferido); senão fica
    # só o total, pra você conferir/detalhar depois.
    criar = bool(extraido.valor_total and extraido.valor_total > 0)

    duplicado = False
    transacao_id = None
    async with get_session() as session:
        comp_row = await session.get(Comprovante, _uuid(comp.id))
        comp_row.extraido_json = extraido.model_dump(mode="json")

        repo = TransacaoRepository(session)
        # Antes de criar, vê se esse boleto já não foi lançado (não duplicar).
        existente = None
        if criar:
            existente = await repo.buscar_duplicado(
                uid,
                linha_digitavel=linha,
                beneficiario=extraido.beneficiario,
                vencimento=extraido.vencimento,
                valor=extraido.valor_total,
            )

        # Sem categoria explícita? Reaproveita a do último boleto desse mesmo
        # beneficiário (auto-categoriza recorrentes: condomínio, escola…).
        auto_categoria = False
        categoria_final = cat_id
        if existente is None and criar and categoria_final is None:
            categoria_final = await repo.ultima_categoria_por_descricao(
                uid, extraido.beneficiario
            )
            auto_categoria = categoria_final is not None

        if existente is not None:
            duplicado = True
            transacao_id = existente.id
            comp_row.transacao_id = existente.id
        elif criar:
            tx = Transacao(
                usuario_id=uid,
                tipo="despesa",
                descricao=extraido.beneficiario or "Boleto",
                valor_total=extraido.valor_total,
                data_competencia=competencia,
                data_vencimento=extraido.vencimento,
                multa_percentual=extraido.multa_percentual,
                juros_mensal_percentual=extraido.juros_mensal_percentual,
                linha_digitavel=linha,
                status="prevista",          # boleto importado = a pagar
                origem="importacao_boleto",
                categoria_id=categoria_final,
                itens=[
                    TransacaoItem(descricao=v.descricao, valor=v.valor)
                    for v in extraido.verbas
                ] if conferido else [],
            )
            session.add(tx)
            await session.flush()
            comp_row.transacao_id = tx.id
            transacao_id = tx.id

            if conferido:
                for le in extraido.leituras:
                    if le.tipo not in TIPOS_CONSUMO or le.leitura_atual is None:
                        continue
                    session.add(LeituraConsumo(
                        usuario_id=uid,
                        tipo=le.tipo,
                        mes_referencia=competencia,
                        leitura_atual=le.leitura_atual,
                        leitura_anterior=le.leitura_anterior,
                        consumo=le.consumo,
                        valor=le.valor,
                        transacao_id=tx.id,
                    ))

        await session.commit()

    if duplicado:
        msg = (
            f"Esse boleto já estava lançado (R${extraido.valor_total}"
            + (f", vence {extraido.vencimento}" if extraido.vencimento else "")
            + "). Não dupliquei."
        )
    elif conferido:
        msg = (
            f"Boleto importado: despesa de R${extraido.valor_total} "
            f"com {len(extraido.verbas)} verba(s)."
        )
    elif criar:
        msg = (
            f"Lancei R${extraido.valor_total} como a pagar, mas não consegui "
            "separar as verbas direito — confira/detalhe quando puder."
        )
    else:
        msg = (
            "Não consegui ler o valor do boleto. Guardei o arquivo pra "
            "revisão manual."
        )

    if auto_categoria:
        msg += " Categoria reaproveitada do último boleto desse beneficiário."

    return ImportarBoletoResponse(
        success=True,
        conferido=conferido,
        duplicado=duplicado,
        mensagem=msg,
        comprovante_id=comp.id,
        transacao_id=str(transacao_id) if transacao_id else None,
        extraido=extraido,
    )
