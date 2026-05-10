import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.logger import get_logger


logger = get_logger()


# ============================================================
# Modelos Pydantic da resposta esperada
# ============================================================

class Dor(BaseModel):
    dor: str
    evidencia: str = ""


class Gancho(BaseModel):
    produto_servico: str
    porque_faz_sentido: str = ""


class AnaliseGemini(BaseModel):
    """Resposta estruturada da análise da IA."""

    score: int = Field(ge=0, le=100)
    score_justificativa: str = ""
    porte_estimado: str = ""
    perfil_negocio: str = ""
    dores_provaveis: List[Dor] = Field(default_factory=list)
    ganchos_venda: List[Gancho] = Field(default_factory=list)
    perguntas_call: List[str] = Field(default_factory=list)
    alertas: List[str] = Field(default_factory=list)
    resumo_executivo: str = ""

    @field_validator("score", mode="before")
    @classmethod
    def _coerce_score(cls, v: Any) -> int:
        """Aceita score como string ou float, converte pra int 0-100."""
        if isinstance(v, str):
            v = "".join(c for c in v if c.isdigit() or c == ".")
        try:
            num = int(float(v))
        except (TypeError, ValueError):
            num = 50
        return max(0, min(100, num))


# ============================================================
# Parsing do JSON cru
# ============================================================

def _limpar_json_cru(texto: str) -> str:
    """
    Limpa o texto pra extrair JSON puro.
    Lida com casos onde o Gemini eventualmente devolve markdown ```json ... ```
    mesmo com responseMimeType configurado.
    """
    texto = texto.strip()

    # Remove cercas de markdown se vierem
    if texto.startswith("```"):
        # Remove primeira linha (```json ou ```)
        texto = texto.split("\n", 1)[-1] if "\n" in texto else texto
        # Remove última linha (```)
        if texto.endswith("```"):
            texto = texto[: -3].rstrip()

    return texto.strip()


def _reparar_json_truncado(texto: str) -> Optional[str]:
    """
    Tenta reparar JSON truncado fechando estruturas abertas.

    Estratégia:
    1. Trunca no último ',' ou '}' válido pra eliminar pedaço incompleto
    2. Conta { [ " e fecha o que ficou aberto
    3. Tenta json.loads no resultado

    Retorna o JSON reparado se conseguir, None se não der.
    """
    # Acha o último ponto "seguro" pra cortar — antes da string truncada
    # Procura de trás pra frente o último '}', ']' ou ',' que feche algo válido
    safe_cuts = []
    for i, c in enumerate(texto):
        if c in '},]':
            safe_cuts.append(i + 1)

    # Tenta cada ponto de corte do mais recente pro mais antigo
    for cut in reversed(safe_cuts[-50:]):  # últimos 50 candidatos é mais que suficiente
        candidato = texto[:cut]
        # Remove vírgula final se houver (JSON não permite)
        if candidato.rstrip().endswith(","):
            candidato = candidato.rstrip()[:-1]

        # Conta delimitadores abertos pra fechar na ordem certa
        reparado = _fechar_delimitadores(candidato)
        if reparado is None:
            continue

        try:
            json.loads(reparado)
            return reparado
        except json.JSONDecodeError:
            continue
    return None


def _fechar_delimitadores(texto: str) -> Optional[str]:
    """
    Conta { [ " ainda abertos no texto e fecha na ordem inversa.
    Ignora chars dentro de strings (respeita escapes).
    """
    pilha: List[str] = []  # pilha de delimitadores abertos
    em_string = False
    escape_next = False

    for c in texto:
        if escape_next:
            escape_next = False
            continue
        if c == "\\" and em_string:
            escape_next = True
            continue
        if c == '"':
            if em_string:
                em_string = False
                if pilha and pilha[-1] == '"':
                    pilha.pop()
            else:
                em_string = True
                pilha.append('"')
            continue
        if em_string:
            continue
        if c == "{":
            pilha.append("}")
        elif c == "[":
            pilha.append("]")
        elif c == "}":
            if pilha and pilha[-1] == "}":
                pilha.pop()
            else:
                return None  # JSON inconsistente
        elif c == "]":
            if pilha and pilha[-1] == "]":
                pilha.pop()
            else:
                return None

    # Fecha na ordem inversa
    fecho = "".join(reversed(pilha))
    return texto + fecho


def _salvar_debug(texto_cru: str, motivo: str) -> None:
    """Salva resposta crua do Gemini pra debug quando algo dá errado."""
    try:
        from datetime import datetime
        from app.config import DATA_DIR

        debug_dir = DATA_DIR / "debug" / "gemini"
        debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = debug_dir / f"{timestamp}_{motivo}.txt"
        path.write_text(texto_cru, encoding="utf-8")
        logger.info(f"   📝 Resposta crua salva em: {path}")
    except Exception as e:
        logger.debug(f"Não consegui salvar debug: {e}")


def parse_resposta(texto_cru: str) -> Optional[AnaliseGemini]:
    """
    Parseia a resposta JSON do Gemini em uma AnaliseGemini.

    Estratégia em 3 níveis:
    1. Tenta parsear o JSON direto
    2. Se falhar (truncado), tenta reparar fechando delimitadores
    3. Se falhar de novo, salva resposta crua em data/debug/gemini/

    Retorna None se nenhuma estratégia funcionou.
    """
    texto_limpo = _limpar_json_cru(texto_cru)

    # Nível 1: parse direto
    data = None
    try:
        data = json.loads(texto_limpo)
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  JSON cru não parseou ({e}). Tentando reparo...")

        # Nível 2: tenta reparar
        reparado = _reparar_json_truncado(texto_limpo)
        if reparado:
            try:
                data = json.loads(reparado)
                logger.info(
                    f"   🔧 JSON reparado com sucesso "
                    f"({len(reparado)}/{len(texto_limpo)} chars usados)"
                )
            except json.JSONDecodeError:
                pass

    if data is None:
        logger.error("❌ JSON do Gemini não pôde ser parseado nem reparado")
        _salvar_debug(texto_cru, "json_invalido")
        return None

    try:
        return AnaliseGemini.model_validate(data)
    except Exception as e:
        logger.error(f"❌ JSON do Gemini não bate com schema: {e}")
        logger.debug(f"   Dados: {data}")
        _salvar_debug(texto_cru, "schema_invalido")
        return None


# ============================================================
# Formatação pra ir nas Notas da Empresa
# ============================================================

def _emoji_score(score: int) -> str:
    if score >= 81:
        return "🔥"
    if score >= 61:
        return "✅"
    if score >= 31:
        return "⚠️"
    return "❄️"


def formatar_para_notas(analise: AnaliseGemini) -> str:
    """
    Converte a análise estruturada em texto bonito pra ir nas Notas
    da Empresa no Notion.
    """
    linhas: List[str] = []

    # Cabeçalho com score
    emoji = _emoji_score(analise.score)
    linhas.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    linhas.append(f"ANÁLISE IA  |  {emoji} Score: {analise.score}/100")
    linhas.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if analise.score_justificativa:
        linhas.append(analise.score_justificativa)
    linhas.append("")

    # Resumo
    if analise.resumo_executivo:
        linhas.append("RESUMO")
        linhas.append(analise.resumo_executivo)
        linhas.append("")

    # Perfil
    if analise.perfil_negocio or analise.porte_estimado:
        linhas.append("PERFIL")
        if analise.porte_estimado:
            linhas.append(f"Porte: {analise.porte_estimado}")
        if analise.perfil_negocio:
            linhas.append(analise.perfil_negocio)
        linhas.append("")

    # Dores
    if analise.dores_provaveis:
        linhas.append("DORES PROVÁVEIS")
        for i, dor in enumerate(analise.dores_provaveis, 1):
            linhas.append(f"{i}. {dor.dor}")
            if dor.evidencia:
                linhas.append(f"   ↳ {dor.evidencia}")
        linhas.append("")

    # Ganchos
    if analise.ganchos_venda:
        linhas.append("GANCHOS DE VENDA")
        for i, g in enumerate(analise.ganchos_venda, 1):
            linhas.append(f"{i}. {g.produto_servico}")
            if g.porque_faz_sentido:
                linhas.append(f"   ↳ {g.porque_faz_sentido}")
        linhas.append("")

    # Perguntas
    if analise.perguntas_call:
        linhas.append("PERGUNTAS PRA CALL")
        for i, p in enumerate(analise.perguntas_call, 1):
            linhas.append(f"{i}. {p}")
        linhas.append("")

    if analise.alertas:
        linhas.append("ALERTAS")
        for a in analise.alertas:
            linhas.append(f"• {a}")
        linhas.append("")

    return "\n".join(linhas).rstrip()