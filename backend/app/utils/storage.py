import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from slugify import slugify

from app.config import PROCESSED_DIR, RAW_DIR, SENT_DIR, UNMAPPED_FIELDS_FILE
from app.models.lead import Lead
from app.utils.logger import get_logger


logger = get_logger(__name__)


def _ensure_dirs():

    for d in (RAW_DIR, PROCESSED_DIR, SENT_DIR):
        d.mkdir(parents=True, exist_ok=True)


def __slug__filename(nome: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{slugify(nome)}.json"


def save_lead(lead: Lead, stage: str = "precessed") -> Path:

    _ensure_dirs()

    stage_map = {"raw": RAW_DIR, "processed": PROCESSED_DIR, "sent": SENT_DIR}
    target_dir = stage_map.get(stage)
    if not target_dir:
        raise ValueError(f"stage inválido: {stage}")

    filepath = target_dir / __slug__filename(lead.empresa.nome)
    filepath.write_text(
        lead.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8"
    )
    logger.info(f"Lead salvo em {stage}: {filepath.name}")
    return filepath


def load_lead(filepath: Path) -> Lead:
    data = json.loads(filepath.read_text(encoding="utf-8"))
    return Lead.model_validate(data)


def list_leads(stage: str = "processed") -> List[Path]:
    _ensure_dirs()
    stage_map = {"raw": RAW_DIR, "processed": PROCESSED_DIR, "sent": SENT_DIR}
    target_dir = stage_map.get(stage)
    if not target_dir:
        raise ValueError(f"stage inválido: {stage}")
    return sorted(target_dir.glob("*.json"))


def move_to_list(filepath: Path) -> Path:
    _ensure_dirs()
    new_path = SENT_DIR / filepath.name
    filepath.rename(new_path)
    logger.info(f"Lead movido para sent: {new_path.name}")
    return new_path


def log_unmapped_field(field_name: str, value: str, empresa_nome: str) -> None:

    _ensure_dirs()

    if UNMAPPED_FIELDS_FILE.exists():
        data: Dict[str, List[Dict[str, Any]]] = json.loads(
            UNMAPPED_FIELDS_FILE.read_text(encoding='utf-8')
        )
    else:
        data = {}

    data.setdefault(field_name, []).append(
        {
            "valor": value,
            "empresa": empresa_nome,
            "registrado_em": datetime.now().isoformat(timespec="seconds"),
        }
    )
    UNMAPPED_FIELDS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.warning(
        f"Campo não mapeado [{field_name}]: '{value}' (empresa: {empresa_nome})"
    )
