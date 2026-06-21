"""Analyzer de certificado — lê 1 PDF/imagem de certificado e extrai os campos.

Mesmo padrão multimodal do boleto: manda o arquivo pro Gemini Flash-Lite e
recebe JSON. Sem OCR/parse local (certificados costumam ser imagem).
"""
from app.analyzers.certificado.extrator import (
    CertificadoSemChave,
    extrair_certificado_llm,
)
from app.analyzers.certificado.parser import parse_certificado

__all__ = [
    "CertificadoSemChave",
    "extrair_certificado_llm",
    "parse_certificado",
]
