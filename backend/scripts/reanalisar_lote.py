import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
import asyncio
import time

from sqlalchemy import select

from app.analyzers.gemini import enriquecer_lead_com_analise
from app.db.sync_bridge import bridge_session
from app.db.models.empresa import Empresa as EmpresaORM
from app.domain.lead import Empresa as EmpresaPyd, Lead, Socio, Contato
from app.repositories.empresa_repository import EmpresaRepository
from app.utils.logger import get_logger

logger = get_logger()


def _orm_para_lead(emp: EmpresaORM) -> Lead:
    """Reconstrói um Lead Pydantic a partir da Empresa ORM (caminho inverso
    do converters.py). Mínimo necessário pra IA analisar."""
    empresa = EmpresaPyd(
        nome=emp.nome,
        razao_social=emp.razao_social,
        cnpj=emp.cnpj,
        cidade=emp.cidade,
        estado=emp.estado,
        local=emp.local,
        site=emp.site,
        instagram=emp.instagram,
        facebook=emp.facebook,
        capital_social=float(emp.capital_social) if emp.capital_social is not None else None,
        setor=emp.setor,
        tamanho=emp.tamanho,
        socios=[Socio(nome=s.nome, qualificacao=s.qualificacao) for s in emp.socios],
        notas=emp.notas,
    )
    contatos = [
        Contato(
            nome=c.nome, cargo=c.cargo, decisor=c.decisor,
            email=c.email, telefone=c.telefone,
            whatsapp=c.whatsapp, linkedin=c.linkedin,
        )
        for c in emp.contatos
    ]
    return Lead(empresa=empresa, contatos=contatos)


async def _reanalisar(limit, pausa):
    resumo = {"ok": 0, "falhas": 0}

    async with bridge_session() as session:
        stmt = select(EmpresaORM).where(EmpresaORM.analise_json.is_(None))
        if limit:
            stmt = stmt.limit(limit)
        empresas = list((await session.execute(stmt)).scalars().all())

    if not empresas:
        logger.info("Nenhuma empresa pendente de análise.")
        return resumo

    logger.info(f"{len(empresas)} empresa(s) pra re-analisar.")
    ids = [e.id for e in empresas]

    for i, emp_id in enumerate(ids, 1):
        async with bridge_session() as session:
            repo = EmpresaRepository(session)
            emp = await repo.get_by_id(emp_id)
            if emp is None:
                continue

            logger.info(f"[{i}/{len(ids)}] {emp.nome}...")
            lead = _orm_para_lead(emp)

            try:
                lead = enriquecer_lead_com_analise(lead)
            except Exception as e:
                logger.error(f"IA falhou pra {emp.nome}: {type(e).__name__}: {e}")
                resumo["falhas"] += 1
                continue

            if lead.empresa.score is None:
                logger.warning(f"{emp.nome} segue sem score (análise falhou)")
                resumo["falhas"] += 1
                continue

            emp.score = lead.empresa.score
            emp.analise_json = lead.empresa.analise_json
            emp.notas = lead.empresa.notas
            await session.commit()
            resumo["ok"] += 1
            logger.success(f"  → score {lead.empresa.score}")

        if i < len(ids):
            time.sleep(pausa)

    logger.success(f"Fim: {resumo['ok']} ok, {resumo['falhas']} falhas.")
    return resumo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--pausa", type=float, default=8.0)
    args = p.parse_args()
    asyncio.run(_reanalisar(args.limit, args.pausa))


if __name__ == "__main__":
    main()