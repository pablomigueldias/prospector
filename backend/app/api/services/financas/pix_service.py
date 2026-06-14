"""Parser do PIX 'copia e cola' (BR Code / EMV-MPM).

O código é um TLV (tag de 2 dígitos + tamanho de 2 dígitos + valor). A gente lê
o valor (tag 54), o beneficiário (tag 59), a cidade (tag 60) e a chave (dentro
do merchant account info, tags 26-51, sub-tag 01). Sem IA — é só formato.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Dict, Optional

from app.api.schemas.financas import PixParseResponse


class PixError(Exception):
    """Código PIX inválido — vira HTTP 400 no router."""


def _parse_tlv(s: str) -> Dict[str, str]:
    """Quebra um EMV-TLV em {tag: valor}. Para no 1º campo malformado."""
    out: Dict[str, str] = {}
    i = 0
    n = len(s)
    while i + 4 <= n:
        tag = s[i : i + 2]
        try:
            tam = int(s[i + 2 : i + 4])
        except ValueError:
            break
        ini = i + 4
        fim = ini + tam
        if fim > n:
            break
        out[tag] = s[ini:fim]
        i = fim
    return out


def parse_copia_cola(codigo: str) -> PixParseResponse:
    """Extrai valor/beneficiário/cidade/chave de um PIX copia-e-cola."""
    if not codigo or not codigo.strip():
        raise PixError("Cole o código PIX.")
    # Tira só bordas e quebras de linha do copy-paste — espaços INTERNOS contam
    # (o nome/cidade nas tags 59/60 podem ter espaço).
    bruto = codigo.strip().replace("\r", "").replace("\n", "").replace("\t", "")

    campos = _parse_tlv(bruto)
    # Sanidade: PIX começa com 000201 e tem o GUI do BACEN em algum merchant tag.
    tem_gui = "br.gov.bcb.pix" in bruto.lower()
    if not (campos.get("00") and tem_gui):
        raise PixError("Isso não parece um código PIX válido.")

    valor: Optional[Decimal] = None
    if campos.get("54"):
        try:
            v = Decimal(campos["54"])
            valor = v if v > 0 else None
        except InvalidOperation:
            valor = None

    # Chave: merchant account info nas tags 26..51 (sub-TLV, chave na sub-tag 01).
    chave: Optional[str] = None
    for t in (f"{n:02d}" for n in range(26, 52)):
        if t in campos:
            sub = _parse_tlv(campos[t])
            if sub.get("01"):
                chave = sub["01"].strip()
                break

    beneficiario = (campos.get("59") or "").strip() or None
    cidade = (campos.get("60") or "").strip() or None

    return PixParseResponse(
        valor=valor,
        beneficiario=beneficiario,
        cidade=cidade,
        chave=chave,
    )
