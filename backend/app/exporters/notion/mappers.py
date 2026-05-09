from typing import Any, Dict, List, Optional

from app.config import (
    COMO_CONHECEU_OPCOES,
    DEFAULT_COMO_CONHECEU,
    DEFAULT_ORIGEM_CONTATO,
    DEFAULT_STATUS,
    ESTADO_OPCOES,
    ORIGEM_CONTATO_OPCOES,
    SETOR_OPCOES,
    STATUS_OPCOES,
    TAMANHO_OPCOES,
)
from app.exporters.notion.property_builder import NOT_WRITABLE_TYPES, build_value
from app.models.lead import Contato, Empresa
from app.utils.logger import get_logger
from app.utils.storage import log_unmapped_field


logger = get_logger()


def validate_select(
    field_name: str,
    value: Optional[str],
    valid_options: list,
    empresa_nome: str,
) -> Optional[str]:
    if value is None or value == "":
        return None
    if value in valid_options:
        return value
    log_unmapped_field(field_name, value, empresa_nome)
    return None


def empresa_to_values(empresa: Empresa) -> Dict[str, Any]:
    nome = empresa.nome

    setor = validate_select("setor", empresa.setor, SETOR_OPCOES, nome)
    tamanho = validate_select("tamanho", empresa.tamanho, TAMANHO_OPCOES, nome)
    estado = validate_select("estado", empresa.estado, ESTADO_OPCOES, nome)
    status = validate_select(
        "status", empresa.status or DEFAULT_STATUS, STATUS_OPCOES, nome
    )
    como_conheceu = validate_select(
        "como_conheceu",
        empresa.como_conheceu or DEFAULT_COMO_CONHECEU,
        COMO_CONHECEU_OPCOES,
        nome,
    )

    socios_str = (
        ", ".join(s.nome for s in empresa.socios) if empresa.socios else None
    )
    cnpj_formatado = format_cnpj(empresa.cnpj) if empresa.cnpj else None

    return {
        "Nome": empresa.nome,
        "Razão Social": empresa.razao_social,
        "CNPJ": cnpj_formatado,
        "Capital Social": empresa.capital_social,
        "Cidade": empresa.cidade,
        "Estado": estado,
        "Local": empresa.local,
        "Site": empresa.site,
        "Instagram": empresa.instagram,
        "Facebook": empresa.facebook,
        "Setor": setor,
        "Tamanho": tamanho,
        "Socio": socios_str,
        "Status": status,
        "Como conheceu": como_conheceu,
        "Notas": empresa.notas,
    }


def contato_to_values(contato: Contato, empresa_nome: str) -> Dict[str, Any]:
    origem = validate_select(
        "origem_contato",
        contato.origem_contato or DEFAULT_ORIGEM_CONTATO,
        ORIGEM_CONTATO_OPCOES,
        empresa_nome,
    )

    values: Dict[str, Any] = {
        "Nome": contato.nome,
        "Cargo": contato.cargo,
        "Decisor?": "Sim" if contato.decisor else "Não",
        "E-mail": contato.email,
        "Telefone": contato.telefone,
        "WhatsApp": contato.whatsapp,
        "LinkedIn": contato.linkedin,
        "Origem do contato": origem,
    }

    if contato.empresa_notion_id:
        values["Empresas"] = [contato.empresa_notion_id]

    return values


def apply_schema(
    values: Dict[str, Any],
    schema: Dict[str, str],
    context: str,
) -> Dict[str, dict]:
    
    properties: Dict[str, dict] = {}
    skipped_unsupported: List[str] = []
    skipped_missing: List[str] = []

    for field_name, value in values.items():
        notion_type = schema.get(field_name)

        if notion_type is None:
            skipped_missing.append(field_name)
            continue

        if notion_type in NOT_WRITABLE_TYPES:
            skipped_unsupported.append(f"{field_name}={notion_type}")
            continue

        built = build_value(notion_type, value)
        if built is None:
            skipped_unsupported.append(f"{field_name}={notion_type}")
            continue

        properties[field_name] = built

    if skipped_missing:
        logger.warning(
            f"⚠️  [{context}] Campos do código que NÃO existem no Notion: "
            f"{', '.join(skipped_missing)}"
        )
    if skipped_unsupported:
        logger.warning(
            f"⚠️  [{context}] Campos pulados (tipo não suportado): "
            f"{', '.join(skipped_unsupported)}"
        )

    return properties


def format_cnpj(cnpj: str) -> str:

    digits = "".join(c for c in cnpj if c.isdigit())
    if len(digits) != 14:
        return cnpj
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
