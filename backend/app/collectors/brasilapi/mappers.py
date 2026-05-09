from typing import Any, Dict, List, Optional

from app.collectors.brasilapi.classifiers import (
    classificar_setor,
    classificar_tamanho,
)
from app.config import ESTADO_OPCOES
from app.models.lead import Contato, Empresa, Lead, Socio
from app.utils.logger import get_logger


logger = get_logger()


def _montar_endereco(data: Dict[str, Any]) -> Optional[str]:
    parts = []
    logradouro = data.get("logradouro")
    numero = data.get("numero")
    if logradouro:
        if numero:
            parts.append(f"{logradouro}, {numero}")
        else:
            parts.append(logradouro)

    for campo in ("complemento", "bairro", "municipio"):
        valor = data.get(campo)
        if valor:
            parts.append(valor)

    uf = data.get("uf")
    cep = data.get("cep")
    if uf:
        parts.append(uf)
    if cep:
        parts.append(f"CEP {cep}")

    return ", ".join(parts) if parts else None


def _normalizar_estado(uf: Optional[str]) -> Optional[str]:
    if not uf:
        return None
    uf = uf.strip().upper()
    return uf if uf else None


def _capitalizar_se_tudo_caps(texto: Optional[str]) -> Optional[str]:
    if not texto:
        return None
    texto = texto.strip()
    if texto.isupper():
        return texto.title()
    return texto


def _build_socios(qsa: List[Dict[str, Any]]) -> List[Socio]:
    socios: List[Socio] = []
    for item in qsa or []:
        nome = item.get("nome_socio") or item.get("nome")
        if not nome:
            continue
        socios.append(
            Socio(
                nome=_capitalizar_se_tudo_caps(nome) or nome,
                qualificacao=item.get("qualificacao_socio")
                or item.get("descricao_qualificacao_socio"),
            )
        )
    return socios


def _avisar_situacao_irregular(
    descricao_situacao: Optional[str], empresa_nome: str
) -> Optional[str]:
    if not descricao_situacao:
        return None
    situacao = descricao_situacao.strip().upper()
    if situacao == "ATIVA":
        return None
    aviso = f"⚠️ Situação cadastral na Receita: **{situacao}**. Verificar antes de prospectar."
    logger.warning(f"Empresa '{empresa_nome}' está com situação {situacao}")
    return aviso


def map_to_empresa(data: Dict[str, Any]) -> Empresa:
    razao_social = _capitalizar_se_tudo_caps(data.get("razao_social"))
    nome_fantasia = _capitalizar_se_tudo_caps(data.get("nome_fantasia"))
    nome = nome_fantasia or razao_social or "Empresa sem nome"

    cnpj_digits = "".join(c for c in str(data.get("cnpj", "")) if c.isdigit())

    cnae_codigo = data.get("cnae_fiscal")
    setor = classificar_setor(cnae_codigo)
    if cnae_codigo and not setor:
        logger.info(
            f"CNAE {cnae_codigo} ({data.get('cnae_fiscal_descricao', '?')}) "
            f"sem mapeamento de Setor pra {nome}"
        )

    capital_social = data.get("capital_social")
    porte = data.get("porte") or data.get("descricao_porte")
    opcao_mei = bool(data.get("opcao_pelo_mei", False))
    tamanho = classificar_tamanho(porte, capital_social, opcao_mei)

    estado = _normalizar_estado(data.get("uf"))
    if estado and estado not in ESTADO_OPCOES:
        logger.info(f"Estado {estado} não está nas opções do Notion")

    cidade = _capitalizar_se_tudo_caps(data.get("municipio"))

    aviso_situacao = _avisar_situacao_irregular(
        data.get("descricao_situacao_cadastral"), nome
    )

    notas_partes = []
    if aviso_situacao:
        notas_partes.append(aviso_situacao)
    if cnae_codigo:
        cnae_desc = data.get("cnae_fiscal_descricao", "")
        notas_partes.append(f"CNAE principal: {cnae_codigo} — {cnae_desc}")
    if data.get("data_inicio_atividade"):
        notas_partes.append(f"Início de atividade: {data['data_inicio_atividade']}")
    notas = "\n".join(notas_partes) if notas_partes else None

    return Empresa(
        nome=nome,
        razao_social=razao_social,
        cnpj=cnpj_digits or None,
        capital_social=float(capital_social) if capital_social is not None else None,
        cidade=cidade,
        estado=estado,
        local=_montar_endereco(data),
        setor=setor,
        tamanho=tamanho,
        socios=_build_socios(data.get("qsa", [])),
        notas=notas,
    )


def map_to_contatos(empresa: Empresa) -> List[Contato]:

    contatos: List[Contato] = []
    for socio in empresa.socios:
        contatos.append(
            Contato(
                nome=socio.nome,
                cargo=socio.qualificacao or "Sócio",
                decisor=True,
            )
        )
    return contatos


def map_to_lead(data: Dict[str, Any]) -> Lead:
    empresa = map_to_empresa(data)
    contatos = map_to_contatos(empresa)
    return Lead(empresa=empresa, contatos=contatos)
