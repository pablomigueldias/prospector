from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SENT_DIR = DATA_DIR / "sent"
LOGS_DIR = BASE_DIR / "logs"
UNMAPPED_FIELDS_FILE = DATA_DIR / "unmapped_fields.json"


class Settings(BaseSettings):

    database_url: str = (
        "postgresql+asyncpg://reative:reative_dev@localhost:5433/reative"
    )
    db_echo: bool = False

    observer_enabled: bool = True
    observ_store_payloads: bool = True

    llm_provider: str = "gemini"      # "gemini" ou "ollama"
    ollama_model: str = "llama3.1:8b"

    #Email
    mail_user: str = ""
    mail_password: str = ""
    mail_imap_host: str = "imap.hostinger.com"
    mail_imap_port: int = 993
    mail_smtp_host: str = "smtp.hostinger.com"
    mail_smtp_port: int = 465
    mail_from_name: str = "Reative Systems"

    # Notion
    notion_token: str
    notion_db_empresas: str
    notion_db_contatos: str

    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Storage S3-compatível (MinIO). Defaults batem com o compose de dev.
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"

    # Rate limiting
    max_leads_per_day: int = 30
    min_delay_seconds: int = 5
    max_delay_seconds: int = 15

    # Comportamento
    log_level: str = "INFO"
    headless_browser: bool = False

    # Stealth
    usar_tor: bool = False
    modo_stealth: bool = True
    aquecer_sessao: bool = True

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()  # type: ignore


SETOR_OPCOES = [
    "Tech",
    "Saúde",
    "Educação",
    "Varejo",
    "Serviços",
    "Marketing",
    "Jurídico",
    "Financeiro",
    "Imobiliário",
    "Indústria",
]

TAMANHO_OPCOES = [
    "MEI",
    "Pequena (1-10)",
    "Média (11-50)",
    "Grande (51-200)",
    "Corporativa (200+)",
]

STATUS_OPCOES = [
    "🔴 Não qualificado",
    "⚪ Cliente inativo",
    "🟡 Lead ativo",
    "🔵 Prospect",
    "🟢 Cliente ativo",
    "🔬 Em investigação",
]

COMO_CONHECEU_OPCOES = [
    "LinkedIn",
    "Indicação",
    "Site",
    "Comunidade dev",
    "Network pessoal",
    "Outbound",
    "Inbound",
]

ORIGEM_CONTATO_OPCOES = [
    "LinkedIn",
    "Indicação",
    "Site",
    "Comunidade",
    "Evento",
    "Network",
]

ESTADO_OPCOES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF"]


DEFAULT_STATUS = "🔵 Prospect"
DEFAULT_COMO_CONHECEU = "Outbound"
DEFAULT_ORIGEM_CONTATO = "Network"
