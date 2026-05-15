from __future__ import annotations

from typing import Any, Dict, List, Optional


def normalizar_opencnpj_para_brasilapi(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cnpj": raw.get("cnpj"),
        "razao_social": raw.get("razao_social"),
        "nome_fantasia": raw.get("nome_fantasia"),

        "descricao_situacao_cadastral": raw.get("situacao_cadastral"),
        "data_inicio_atividade": raw.get("data_inicio_atividade") or None,

        "cnae_fiscal": _parse_cnae(raw.get("cnae_principal")),
        "cnae_fiscal_descricao": "",

        "capital_social": _parse_capital_social(raw.get("capital_social")),

    
        "porte": _extrair_sigla_porte(raw.get("porte_empresa")),
        "opcao_pelo_mei": _parse_opcao_mei(raw.get("opcao_mei")),

        "logradouro": _montar_logradouro_com_tipo(
            raw.get("tipo_logradouro"), raw.get("logradouro")
        ),
        "numero": raw.get("numero") or None,
        "complemento": raw.get("complemento") or None,
        "bairro": raw.get("bairro") or None,
        "cep": _normalizar_cep(raw.get("cep")),
        "uf": raw.get("uf"),
        "municipio": raw.get("municipio"),

        "qsa": raw.get("QSA") or raw.get("qsa") or [],
        "_extras_opencnpj": _coletar_extras(raw),
    }



def _parse_cnae(valor: Any) -> Optional[int]:
    if valor is None or valor == "":
        return None
    try:
        return int(str(valor).strip())
    except (ValueError, TypeError):
        return None


def _parse_capital_social(valor: Any) -> Optional[float]:
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        s = str(valor).strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return None


def _extrair_sigla_porte(porte_extenso: Optional[str]) -> Optional[str]:
    if not porte_extenso:
        return None
    porte = porte_extenso.strip()
    if not porte:
        return None
    if "(" in porte and ")" in porte:
        inicio = porte.rfind("(") + 1
        fim = porte.rfind(")")
        if inicio < fim:
            sigla = porte[inicio:fim].strip()
            if sigla:
                return sigla
    return porte


def _parse_opcao_mei(valor: Any) -> bool:
    if valor is None:
        return False
    s = str(valor).strip().upper()
    if not s:
        return False
    if s in ("N", "NAO", "NÃO", "FALSE", "0"):
        return False
    return True


def _montar_logradouro_com_tipo(
    tipo: Optional[str], logradouro: Optional[str]
) -> Optional[str]:

    if not logradouro:
        return None
    if tipo and tipo.strip():
        log_upper = logradouro.strip().upper()
        tipo_upper = tipo.strip().upper()
        if not log_upper.startswith(tipo_upper):
            return f"{tipo.strip()} {logradouro.strip()}"
    return logradouro.strip()


def _normalizar_cep(cep: Optional[str]) -> Optional[str]:
    if not cep:
        return None
    digits = "".join(c for c in str(cep) if c.isdigit())
    return digits or None


def _coletar_extras(raw: Dict[str, Any]) -> Dict[str, Any]:
    extras: Dict[str, Any] = {}

    email = (raw.get("email") or "").strip()
    if email:
        extras["email_receita"] = email.lower()

    telefones_normalizados: List[Dict[str, Any]] = []
    for tel in raw.get("telefones") or []:
        if not isinstance(tel, dict):
            continue
        ddd = (tel.get("ddd") or "").strip()
        numero = (tel.get("numero") or "").strip()
        if not (ddd and numero):
            continue
        telefones_normalizados.append({
            "ddd": ddd,
            "numero": numero,
            "is_fax": bool(tel.get("is_fax", False)),
            "formatado": _formatar_telefone_br(ddd, numero),
        })
    if telefones_normalizados:
        extras["telefones"] = telefones_normalizados

    return extras


def _formatar_telefone_br(ddd: str, numero: str) -> str:
    digitos = "".join(c for c in numero if c.isdigit())
    if len(digitos) == 8:
        return f"({ddd}) {digitos[:4]}-{digitos[4:]}"
    if len(digitos) == 9:
        return f"({ddd}) {digitos[:5]}-{digitos[5:]}"
    return f"({ddd}) {digitos}"
