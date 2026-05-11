from typing import Optional

from app.collectors.brasilapi.classifiers import classificar_tamanho
from app.models.lead import Contato, Empresa, Lead, Socio
from app.services.investigador.confianca import Investigacao
from app.services.investigador.input_model import InputInvestigacao
from app.services.investigador.pipeline import investigar
from app.services.investigador.revisor_interativo import (
    pedir_aprovacao,
    perguntar_qual_site,
)
from app.utils.logger import get_logger


logger = get_logger()


STATUS_INVESTIGACAO = "🔬 Em investigação"
STATUS_APROVADO = "🔵 Prospect"


def investigar_e_montar_lead(
    input_: InputInvestigacao,
    interativo: bool = True,
) -> tuple[Lead, Investigacao, bool]:
   
    if not input_.tem_algo():
        raise ValueError("Pelo menos um campo do input deve estar preenchido")

    logger.info(f"🔬 Investigando: {input_.descricao_curta()}")
    inv = investigar(input_)

    if interativo and not inv.site and inv.candidatos_site:
        url_escolhida = perguntar_qual_site(inv)
        if url_escolhida:
            from app.services.investigador.pipeline import _enriquecer_via_site
            inv.adicionar("site", url_escolhida, "usuario")
            _enriquecer_via_site(inv, url_escolhida)

    if interativo:
        aprovado = pedir_aprovacao(inv)
    else:
        aprovado = False

    status = STATUS_APROVADO if aprovado else STATUS_INVESTIGACAO
    lead = _investigacao_para_lead(inv, status=status)

    return lead, inv, aprovado


def _investigacao_para_lead(inv: Investigacao, status: str) -> Lead:

    def v(campo: str) -> Optional[str]:
        c = getattr(inv, campo, None)
        return c.valor if c else None

    capital = None
    if inv.capital_social:
        try:
            capital = float(inv.capital_social.valor)
        except ValueError:
            capital = None

    tamanho = classificar_tamanho(None, capital, opcao_mei=False)

    socios_modelo = [
        Socio(nome=s["nome"], qualificacao=s.get("qualificacao"))
        for s in inv.socios
    ]

    notas_partes = []
    if inv.cnae_descricao:
        notas_partes.append(f"CNAE: {inv.cnae_descricao.valor}")
    notas_partes.append("\n📊 Confiança por campo:")
    for campo, (valor, score, fontes) in inv.campos_com_score().items():
        notas_partes.append(f"  • {campo}: {score}% ({fontes})")
    notas = "\n".join(notas_partes) if notas_partes else None

    empresa = Empresa(
        nome=v("nome") or "Empresa sem nome",
        razao_social=v("razao_social"),
        cnpj=v("cnpj"),
        capital_social=capital,
        cidade=v("cidade"),
        estado=v("estado"),
        local=v("endereco"),
        site=v("site"),
        instagram=v("instagram"),
        facebook=v("facebook"),
        setor=None,
        tamanho=tamanho,
        socios=socios_modelo,
        status=status,
        notas=notas,
    )

    contatos = []
    if socios_modelo:
        principal = Contato(
            nome=socios_modelo[0].nome,
            cargo=socios_modelo[0].qualificacao or "Sócio",
            decisor=True,
            email=v("email"),
            whatsapp=v("whatsapp"),
            telefone=v("telefone"),
            linkedin=v("linkedin"),
        )
        contatos.append(principal)
        for s in socios_modelo[1:]:
            contatos.append(Contato(
                nome=s.nome,
                cargo=s.qualificacao or "Sócio",
                decisor=True,
            ))
    elif v("email") or v("whatsapp") or v("telefone"):
        contatos.append(Contato(
            nome=f"{empresa.nome} - Contato Comercial",
            cargo="Contato comercial",
            decisor=False,
            email=v("email"),
            whatsapp=v("whatsapp"),
            telefone=v("telefone"),
            linkedin=v("linkedin"),
            origem_contato="Site",
        ))

    return Lead(empresa=empresa, contatos=contatos)


__all__ = [
    "investigar_e_montar_lead",
    "InputInvestigacao",
    "Investigacao",
    "STATUS_INVESTIGACAO",
    "STATUS_APROVADO",
]
