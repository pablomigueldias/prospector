from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.db.models.contato import Contato as ContatoORM
from app.db.models.empresa import Empresa as EmpresaORM
from app.db.models.socio import Socio as SocioORM
from app.domain.lead import Contato as ContatoPydantic
from app.domain.lead import Empresa as EmpresaPydantic
from app.domain.lead import Socio as SocioPydantic


def _cnpj_digits(cnpj: Optional[str]) -> Optional[str]:
    if not cnpj:
        return None
    digits  = ''.join(c for c in cnpj if c.isdigit())
    return digits or None

def empresa_to_orm(emp: EmpresaPydantic) -> EmpresaORM:
    sincronizado = datetime.now() if emp.notion_page_id else None
    return EmpresaORM(
        nome=emp.nome,
        razao_social=emp.razao_social,
        cnpj=_cnpj_digits(emp.cnpj),
        cidade=emp.cidade,
        estado=emp.estado,
        local=emp.local,
        site=emp.site,
        instagram=emp.instagram,
        facebook=emp.facebook,
        capital_social=emp.capital_social,
        setor=emp.setor,
        tamanho=emp.tamanho,
        score=emp.score,
        analise_json=emp.analise_json,
        como_conheceu=emp.como_conheceu,
        status=emp.status,
        notas=emp.notas,
        notion_page_id=emp.notion_page_id,
        notion_synced_at=sincronizado,
    )

def socio_to_orm(s:SocioPydantic) -> SocioORM:
    return SocioORM(
        nome=s.nome,
        qualificacao=s.qualificacao,
    )

def contato_to_orm(c:ContatoPydantic) -> ContatoORM:
    sincronizado = datetime.now() if c.notion_page_id else None
    email = c.email.strip().lower() if c.email else None
    return ContatoORM(
        nome=c.nome,
        cargo=c.cargo,
        decisor=c.decisor,
        email=email,
        telefone=c.telefone,
        whatsapp=c.whatsapp,
        linkedin=c.linkedin,
        origem_contato=c.origem_contato,
        notion_page_id=c.notion_page_id,
        notion_synced_at=sincronizado,
    )
