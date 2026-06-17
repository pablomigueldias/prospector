from typing import Optional

from app.collectors import duckduckgo
from app.collectors.brasilapi.client import (
    CNPJInvalido,
    CNPJNaoEncontrado,
    buscar_cnpj,
)
from app.collectors.website import coletar_do_site
from app.collectors.website.extractors import formatar_telefone, normalizar_url
from app.prospector_engine.investigador.confianca import Investigacao
from app.prospector_engine.investigador.input_model import InputInvestigacao
from app.utils.logger import get_logger


logger = get_logger()


def investigar(input_: InputInvestigacao) -> Investigacao:
    inv = Investigacao()

    _aplicar_input_usuario(inv, input_)

    if input_.cnpj:
        _enriquecer_via_brasilapi(inv, input_.cnpj)

    site_inicial: Optional[str] = inv.site.valor if inv.site else None
    if site_inicial:
        _enriquecer_via_site(inv, site_inicial)

    nome_busca = inv.nome.valor if inv.nome else None
    cidade_busca = inv.cidade.valor if inv.cidade else None
    if nome_busca:
        _enriquecer_via_ddg(inv, nome_busca, cidade_busca)

    if not inv.site and inv.candidatos_site:
        melhor = inv.candidatos_site[0]
        url_candidato = melhor.get("url")
        if url_candidato:
            logger.info(
                f"   🔍 Scrape do melhor candidato a site: {url_candidato}")
            _enriquecer_via_site(inv, url_candidato)

    if not inv.cnpj and nome_busca:
        logger.info("   🔎 CNPJ não informado — buscando por nome no DDG...")
        candidatos_cnpj = duckduckgo.buscar_cnpj_por_nome(
            nome_busca, cidade_busca)
        if candidatos_cnpj:
            for cnpj_cand in candidatos_cnpj[:3]:
                _enriquecer_via_brasilapi(inv, cnpj_cand)
                if inv.cnpj:
                    logger.info(
                        f"   ✅ CNPJ confirmado via BrasilAPI: {cnpj_cand}")
                    break

    site_final = inv.site.valor if inv.site else None
    if site_final and site_final != site_inicial:
        pass
    return inv


def _aplicar_input_usuario(inv: Investigacao, input_: InputInvestigacao) -> None:
    if input_.nome:
        inv.adicionar("nome", input_.nome, "usuario")
    if input_.cnpj:
        inv.adicionar("cnpj", input_.cnpj, "usuario")
    if input_.cidade:
        inv.adicionar("cidade", input_.cidade, "usuario")
    if input_.estado:
        inv.adicionar("estado", input_.estado.upper(), "usuario")
    if input_.site:
        inv.adicionar("site", normalizar_url(input_.site), "usuario")
    if input_.instagram:
        inv.adicionar(
            "instagram",
            f"https://instagram.com/{input_.instagram}",
            "usuario",
        )
    if input_.telefone:
        if len(input_.telefone) == 11 and input_.telefone[2] == "9":
            inv.adicionar("whatsapp", formatar_telefone(
                input_.telefone), "usuario")
        else:
            inv.adicionar("telefone", formatar_telefone(
                input_.telefone), "usuario")


def _enriquecer_via_brasilapi(inv: Investigacao, cnpj: str) -> None:
    logger.info(f"📡 Consultando BrasilAPI: {cnpj}")
    try:
        data = buscar_cnpj(cnpj)
    except CNPJInvalido as e:
        logger.warning(f"   ⚠️  CNPJ inválido: {e}")
        return
    except CNPJNaoEncontrado:
        logger.warning(f"   ⚠️  CNPJ {cnpj} não encontrado na Receita")
        return
    except Exception as e:
        logger.error(f"   ❌ Erro BrasilAPI: {e}")
        return

    razao = data.get("razao_social")
    fantasia = data.get("nome_fantasia")
    nome = (fantasia or razao or "").strip()
    if nome and not inv.nome:
        inv.adicionar("nome", _capitalizar(nome), "brasilapi")
    if razao:
        inv.adicionar("razao_social", _capitalizar(razao), "brasilapi")

    inv.adicionar("cnpj", cnpj, "brasilapi")
    inv.adicionar("cidade", _capitalizar(data.get("municipio")), "brasilapi")
    inv.adicionar("estado", (data.get("uf") or "").upper(), "brasilapi")

    endereco = _montar_endereco(data)
    if endereco:
        inv.adicionar("endereco", endereco, "brasilapi")

    capital = data.get("capital_social")
    if capital is not None:
        inv.adicionar("capital_social", str(capital), "brasilapi")

    cnae_desc = data.get("cnae_fiscal_descricao")
    if cnae_desc:
        inv.adicionar("cnae_descricao", cnae_desc, "brasilapi")

    # Sócios
    qsa = data.get("qsa", []) or []
    for socio in qsa:
        nome_socio = socio.get("nome_socio") or socio.get("nome")
        if nome_socio:
            inv.socios.append({
                "nome": _capitalizar(nome_socio),
                "qualificacao": socio.get("qualificacao_socio")
                or socio.get("descricao_qualificacao_socio"),
                "fonte": "brasilapi",
            })


def _enriquecer_via_site(inv: Investigacao, url_site: str) -> None:

    try:
        contatos = coletar_do_site(url_site)
    except Exception as e:
        logger.warning(f"   ⚠️  Erro ao fazer scrape do site: {e}")
        return

    inv.adicionar("site", normalizar_url(url_site), "site_oficial")

    emails = contatos.get("emails") or []
    if emails:
        inv.adicionar("email", emails[0], "site_oficial")  # type: ignore

    whats = contatos.get("whatsapps") or []
    if whats:
        inv.adicionar("whatsapp", formatar_telefone(
            whats[0]), "site_oficial")  # type: ignore

    tels = contatos.get("telefones") or []
    if tels:
        inv.adicionar("telefone", formatar_telefone(
            tels[0]), "site_oficial")  # type: ignore

    if contatos.get("instagram"):
        # type: ignore
        inv.adicionar("instagram", contatos["instagram"], "site_oficial") #type: ignore
    if contatos.get("facebook"):
        # type: ignore
        inv.adicionar("facebook", contatos["facebook"], "site_oficial") #type: ignore
    if contatos.get("linkedin"):
        # type: ignore
        inv.adicionar("linkedin", contatos["linkedin"], "site_oficial") #type: ignore


def _enriquecer_via_ddg(
    inv: Investigacao, nome: str, cidade: Optional[str]
) -> None:
    achados = duckduckgo.buscar_redes_sociais(nome=nome, cidade=cidade)

    if achados.get("instagram"):
        inv.adicionar("instagram", achados["instagram"], "duckduckgo")
    if achados.get("facebook"):
        inv.adicionar("facebook", achados["facebook"], "duckduckgo")
    if achados.get("linkedin"):
        inv.adicionar("linkedin", achados["linkedin"], "duckduckgo")

    candidatos = achados.get("site_candidatos") or []
    if not inv.site:
        inv.candidatos_site = candidatos


def _capitalizar(texto: Optional[str]) -> Optional[str]:
    if not texto:
        return None
    texto = str(texto).strip()
    if not texto:
        return None
    if texto.isupper():
        return texto.title()
    return texto


def _montar_endereco(data: dict) -> Optional[str]:
    partes = []
    logradouro = data.get("logradouro")
    numero = data.get("numero")
    if logradouro:
        if numero:
            partes.append(f"{logradouro}, {numero}")
        else:
            partes.append(logradouro)
    for campo in ("complemento", "bairro", "municipio"):
        v = data.get(campo)
        if v:
            partes.append(v)
    uf = data.get("uf")
    cep = data.get("cep")
    if uf:
        partes.append(uf)
    if cep:
        partes.append(f"CEP {cep}")
    return ", ".join(partes) if partes else None
