"""Parser da direção de arte (L5)."""
from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.linkedin import MidiaSugestao
from app.utils.logger import get_logger

logger = get_logger()

_RECOMENDACOES = {
    "imagem_ia", "foto", "carrossel", "video_reel", "screenshot", "grafico", "sem_midia",
}


def parse_midia(texto_cru: str) -> MidiaSugestao | None:
    dados = extrair_json(texto_cru)
    if not isinstance(dados, dict):
        return None

    # Normaliza recomendação desconhecida pra um default seguro.
    rec = str(dados.get("recomendacao") or "").strip().lower().replace(" ", "_")
    if rec not in _RECOMENDACOES:
        rec = "imagem_ia"
    dados["recomendacao"] = rec

    # Listas que podem vir como string única.
    for campo in ("passos", "dicas"):
        v = dados.get(campo)
        if isinstance(v, str):
            dados[campo] = [v]

    try:
        return MidiaSugestao(**dados)
    except ValidationError as e:
        logger.warning("Direção de mídia não validou: {}", e)
        return None
