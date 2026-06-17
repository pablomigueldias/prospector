from __future__ import annotations

import time
from datetime import datetime

from app.api.schemas.copywriter import CopywriterRequest
from app.api.services.copywriter_service import CopywriterError, gerar_email
from app.db.lead_persistence import bridge_session
from app.db.models.contato import Contato
from app.db.models.email_outreach import EmailOutreach
from app.mailer.client import MailerError, salvar_rascunho
from app.repositories.email_outreach_repository import EmailOutreachRepository
from app.utils.logger import get_logger

logger = get_logger()


PAUSA_ENTRE_RASCUNHOS_SEG = 8.0


async def _carregar_contato_com_empresa(session, contato_id):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    stmt = (
        select(Contato)
        .where(Contato.id == contato_id)
        .options(selectinload(Contato.empresa))
    )
    return (await session.execute(stmt)).scalar_one()


def _montar_request(contato: Contato) -> CopywriterRequest:
    empresa = contato.empresa
    contexto = _montar_contexto_analise(empresa) if empresa else None
    return CopywriterRequest(
        empresa=empresa.nome if empresa else "(empresa)",
        segmento=empresa.setor if empresa else None,
        nome_contato=contato.nome,
        cargo=contato.cargo,
        canal="email",
        tipo="prospeccao",
        necessidade=None,
        servico=None,
        diferenciais=None,
        contexto_extra=contexto,
        lead_arquivo=None,
    )

def _montar_contexto_analise(empresa) -> str | None:
    analise = getattr(empresa, "analise_json", None)
    if not analise:
        return None

    linhas = []

    dores = analise.get("dores") or []
    if dores:
        linhas.append("DORES IDENTIFICADAS NESTA EMPRESA:")
        for d in dores:
            texto = d.get("dor", "").strip()
            if texto:
                linhas.append(f"- {texto}")

    ganchos = analise.get("ganchos") or []
    if ganchos:
        linhas.append("")
        linhas.append("OPORTUNIDADES DE SERVIÇO:")
        for g in ganchos:
            servico = g.get("produto_servico", "").strip()
            porque = g.get("porque_faz_sentido", "").strip()
            if servico:
                linha = f"- {servico}"
                if porque:
                    linha += f" ({porque})"
                linhas.append(linha)

    return "\n".join(linhas) if linhas else None

def _montar_request_followup(original: EmailOutreach) -> CopywriterRequest:

    contexto = (
        "Este é um FOLLOW-UP (segundo contato). A pessoa recebeu o e-mail "
        "abaixo e não respondeu. Escreva uma mensagem curta e leve "
        "retomando o assunto, sem soar insistente nem repetir o texto.\n\n"
        f"--- E-MAIL ORIGINAL ---\n"
        f"Assunto: {original.assunto}\n\n"
        f"{original.corpo}"
    )
    return CopywriterRequest(
        empresa="(empresa)",
        segmento=None,
        nome_contato=None,
        cargo=None,
        canal="email",
        tipo="prospeccao",
        necessidade=None,
        servico=None,
        diferenciais=None,
        contexto_extra=contexto,
        lead_arquivo=None,
    )


async def gerar_rascunhos_pendentes(
    limit: int | None = None,
    pausa: float = PAUSA_ENTRE_RASCUNHOS_SEG,
) -> dict:
    resumo = {"gerados": 0, "falhas": 0, "pulados": 0}

    async with bridge_session() as session:
        repo = EmailOutreachRepository(session)
        pendentes = await repo.contatos_pendentes(limit=limit)

    if not pendentes:
        logger.info("Nenhum contato pendente. Tudo já tem rascunho.")
        return resumo

    logger.info(f"{len(pendentes)} contato(s) pendente(s) pra rascunho.")
    ids = [c.id for c in pendentes]

    for i, contato_id in enumerate(ids, 1):
        # Sessão curta por item: se um falhar, não derruba o resto.
        async with bridge_session() as session:
            repo = EmailOutreachRepository(session)

            if await repo.ja_tem_para_contato(contato_id):
                resumo["pulados"] += 1
                continue

            contato = await _carregar_contato_com_empresa(session, contato_id)
            nome_alvo = contato.email
            logger.info(f"[{i}/{len(ids)}] {nome_alvo} — gerando e-mail...")

            try:
                resp = gerar_email(_montar_request(contato))
            except CopywriterError as e:
                logger.error(f"IA falhou pra {nome_alvo}: {e}")
                resumo["falhas"] += 1
                continue
            except Exception as e:
                logger.error(f"Erro inesperado na IA ({type(e).__name__}): {e}")
                resumo["falhas"] += 1
                continue

            email = resp.email

            try:
                msg_id = salvar_rascunho(
                    para=contato.email,
                    assunto=email.assunto,
                    corpo=email.corpo,
                )
            except MailerError as e:
                logger.error(f"Rascunho falhou pra {nome_alvo}: {e}")
                resumo["falhas"] += 1
                continue

            registro = EmailOutreach(
                empresa_id=contato.empresa_id,
                contato_id=contato.id,
                destinatario=contato.email,
                assunto=email.assunto,
                corpo=email.corpo,
                tom=email.tom,
                canal="email",
                follow_up_num=0,
                status="rascunho",
                message_id=msg_id,
                draft_criado_em=datetime.now(),
                contexto={
                    "segmento": contato.empresa.setor if contato.empresa else None,
                    "tamanho": contato.empresa.tamanho if contato.empresa else None,
                    "cargo": contato.cargo,
                    "tom": email.tom,
                },
            )
            repo.add(registro)
            await session.commit()
            resumo["gerados"] += 1
            logger.success(f"Rascunho criado e registrado ({msg_id})")

        # Pausa só entre itens, não depois do último
        if i < len(ids):
            time.sleep(pausa)

    logger.success(
        f"Fim: {resumo['gerados']} gerados, "
        f"{resumo['falhas']} falhas, {resumo['pulados']} pulados."
    )
    return resumo

async def gerar_followups_pendentes(
    dias: int = 3,
    max_followups: int = 2,
    limit: int | None = None,
    pausa: float = PAUSA_ENTRE_RASCUNHOS_SEG,
) -> dict:
    resumo = {"gerados": 0, "falhas": 0}

    async with bridge_session() as session:
        repo = EmailOutreachRepository(session)
        candidatos = await repo.candidatos_followup(
            dias=dias, max_followups=max_followups, limit=limit
        )

    if not candidatos:
        logger.info("Nenhum e-mail aguardando follow-up.")
        return resumo

    logger.info(f"{len(candidatos)} e-mail(s) candidato(s) a follow-up.")
    ids = [c.id for c in candidatos]

    for i, original_id in enumerate(ids, 1):
        async with bridge_session() as session:
            repo = EmailOutreachRepository(session)

            # Recarrega o original nesta sessão
            original = await session.get(EmailOutreach, original_id)
            if original is None:
                continue

            logger.info(
                f"[{i}/{len(ids)}] follow-up pra {original.destinatario}..."
            )

            try:
                resp = gerar_email(_montar_request_followup(original))
            except CopywriterError as e:
                logger.error(f"IA falhou: {e}")
                resumo["falhas"] += 1
                continue
            except Exception as e:
                logger.error(f"Erro inesperado ({type(e).__name__}): {e}")
                resumo["falhas"] += 1
                continue

            email = resp.email

            try:
                msg_id = salvar_rascunho(
                    para=original.destinatario,
                    assunto=email.assunto,
                    corpo=email.corpo,
                )
            except MailerError as e:
                logger.error(f"Rascunho falhou: {e}")
                resumo["falhas"] += 1
                continue

            followup = EmailOutreach(
                empresa_id=original.empresa_id,
                contato_id=original.contato_id,
                parent_id=original.id,
                destinatario=original.destinatario,
                assunto=email.assunto,
                corpo=email.corpo,
                tom=email.tom,
                canal="email",
                follow_up_num=original.follow_up_num + 1,
                status="rascunho",
                message_id=msg_id,
                draft_criado_em=datetime.now(),
                contexto={"origem": "followup", "parent_id": str(original.id)},
            )
            repo.add(followup)
            await session.commit()
            resumo["gerados"] += 1
            logger.success(f"Follow-up criado ({msg_id})")

        if i < len(ids):
            time.sleep(pausa)

    logger.success(
        f"Fim: {resumo['gerados']} follow-up(s), {resumo['falhas']} falha(s)."
    )
    return resumo

