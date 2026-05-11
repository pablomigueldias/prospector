import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.logger import get_logger


logger = get_logger()

class Dor(BaseModel):
    dor: str
    evidencia: str = ""


class Gancho(BaseModel):
    produto_servico: str
    porque_faz_sentido: str = ""


class AnaliseGemini(BaseModel):

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
        if isinstance(v, str):
            v = "".join(c for c in v if c.isdigit() or c == ".")
        try:
            num = int(float(v))
        except (TypeError, ValueError):
            num = 50
        return max(0, min(100, num))



def _limpar_json_cru(texto: str) -> str:

    texto = texto.strip()

    if texto.startswith("```"):
        texto = texto.split("\n", 1)[-1] if "\n" in texto else texto

        if texto.endswith("```"):
            texto = texto[: -3].rstrip()

    return texto.strip()


def _reparar_json_truncado(texto: str) -> Optional[str]:
 
    safe_cuts = []
    for i, c in enumerate(texto):
        if c in '},]':
            safe_cuts.append(i + 1)
    for cut in reversed(safe_cuts[-50:]):
        candidato = texto[:cut]
       
        if candidato.rstrip().endswith(","):
            candidato = candidato.rstrip()[:-1]

       
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

    pilha: List[str] = [] 
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
                return None 
        elif c == "]":
            if pilha and pilha[-1] == "]":
                pilha.pop()
            else:
                return None


    fecho = "".join(reversed(pilha))
    return texto + fecho


def _salvar_debug(texto_cru: str, motivo: str) -> None:
  
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
 
    texto_limpo = _limpar_json_cru(texto_cru)


    data = None
    try:
        data = json.loads(texto_limpo)
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  JSON cru não parseou ({e}). Tentando reparo...")


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


def _emoji_score(score: int) -> str:
    if score >= 81:
        return "🔥"
    if score >= 61:
        return "✅"
    if score >= 31:
        return "⚠️"
    return "❄️"


def formatar_para_notas(analise: AnaliseGemini) -> str:
 
    linhas: List[str] = []

    emoji = _emoji_score(analise.score)
    linhas.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    linhas.append(f"ANÁLISE IA  |  {emoji} Score: {analise.score}/100")
    linhas.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if analise.score_justificativa:
        linhas.append(analise.score_justificativa)
    linhas.append("")

  
    if analise.resumo_executivo:
        linhas.append("RESUMO")
        linhas.append(analise.resumo_executivo)
        linhas.append("")

    if analise.perfil_negocio or analise.porte_estimado:
        linhas.append("PERFIL")
        if analise.porte_estimado:
            linhas.append(f"Porte: {analise.porte_estimado}")
        if analise.perfil_negocio:
            linhas.append(analise.perfil_negocio)
        linhas.append("")

    if analise.dores_provaveis:
        linhas.append("DORES PROVÁVEIS")
        for i, dor in enumerate(analise.dores_provaveis, 1):
            linhas.append(f"{i}. {dor.dor}")
            if dor.evidencia:
                linhas.append(f"   ↳ {dor.evidencia}")
        linhas.append("")

    if analise.ganchos_venda:
        linhas.append("GANCHOS DE VENDA")
        for i, g in enumerate(analise.ganchos_venda, 1):
            linhas.append(f"{i}. {g.produto_servico}")
            if g.porque_faz_sentido:
                linhas.append(f"   ↳ {g.porque_faz_sentido}")
        linhas.append("")

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