from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SENT_DIR = DATA_DIR / "sent"
CERTIFICADOS_DIR = DATA_DIR / "certificados"   # arquivo local dos PDFs do Drive
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
    # Bases do CRM espelhadas do Notion (descobertas via search). Defaults =
    # IDs reais do workspace do Pablo; trocáveis por env.
    notion_db_negocios: str = "35a6c23e-8c3c-80d0-a9bf-fd7740ca5b67"
    notion_db_atividades: str = "35a6c23e-8c3c-8008-a842-d750e897cdf4"
    notion_db_projetos: str = "35a6c23e-8c3c-8012-9054-eecead911b30"

    gemini_api_key: str = ""
    # Modelo de geração de IMAGEM (capa/seções do blog, B-IMG). Imagen via a
    # mesma generativelanguage API (:predict). Blog é ≤1 post/dia → custo irrisório,
    # então usa o Ultra (mais qualidade). Alternativas: imagen-4.0-generate-001
    # (standard), imagen-4.0-fast-generate-001 (rápido/barato). O topo absoluto
    # (gemini-3-pro-image, "nano banana pro") usa outra API (generateContent).
    gemini_image_model: str = "imagen-4.0-ultra-generate-001"
    # Modelo de TEXTO do agente Blog. Blog é público/SEO e de baixo volume → vale
    # um Pro (qualidade > custo, irrisório a poucos posts/semana); os demais agentes
    # seguem no flash (constante MODEL em gemini/client.py). Estável: gemini-2.5-pro;
    # topo (preview): gemini-3-pro-preview. Vazio → cai no flash padrão.
    gemini_model_blog: str = "gemini-2.5-pro"
    groq_api_key: str = ""

    # Pasta pública do Drive com os certificados do Pablo (sync autônomo do
    # Perfil Mestre). Só o ID da pasta. Trocar = trocar a fonte.
    certificados_drive_folder_id: str = "1utrqB5rxd8OLAm5X9y0MuUjptlZuBN4U"

    # Storage S3-compatível (MinIO). Defaults batem com o compose de dev.
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    # Base PÚBLICA pra URLs permanentes de imagem (blog). Em dev aponta pro MinIO
    # local; em produção, o MinIO atrás do Caddy (ex.: https://cdn.reativesystems.com.br).
    # Vazio → cai no s3_endpoint (presumindo bucket de leitura pública). A URL final
    # é "{s3_public_url}/{bucket}/{key}" — ver utils/s3_storage.public_url.
    s3_public_url: str = ""
    # Bucket dos assets do blog (imagens de capa/seção geradas pelo agente).
    s3_bucket_blog: str = "blog"

    # URL pública do SITE institucional (não do studio). Usada pra montar links
    # absolutos no sitemap.xml / feed.xml do blog headless.
    site_url: str = "https://reativesystems.com.br"

    # Agente Blog — cron semanal que mantém o backlog de pautas cheio (B4).
    # Desligado por padrão (consome cota de LLM); ligue no .env quando quiser.
    blog_pautas_cron_enabled: bool = False
    blog_pautas_min_backlog: int = 3   # gera só se houver < N pautas "ideia"
    blog_pautas_gerar: int = 5         # quantas gerar quando o backlog está baixo
    blog_pautas_dia_semana: str = "mon"  # cron day_of_week
    blog_pautas_hora: int = 7

    # Telegram (Organizador Financeiro). chat_id → usuario_id mapeia quem fala
    # no bot pro perfil do financas (você / Sandra). Sem tabela usuarios ainda.
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_chat_id: str = ""
    telegram_usuario_id: str = ""
    telegram_chat_id_sandra: str = ""
    telegram_usuario_id_sandra: str = ""

    # Agente Freela — follow-up de propostas sem resposta (lembrete no Telegram
    # pro telegram_chat_id, dentro da rotina diária).
    freela_followup_enabled: bool = True
    freela_followup_dias: int = 3        # avisa propostas "enviada" há ≥ N dias
    # Capacidade semanal faturável (anti-furada): horas livres/semana pra novos
    # projetos. Default ~25h = 5h/dia × 5 dias (premissa da meta).
    freela_capacidade_horas_semana: int = 25

    # Agendador in-process (APScheduler no container da API). Roda 1x/dia:
    # processa recorrências (gera previstas + marca atrasadas) e manda o
    # lembrete de vencimento dos boletos/contas a pagar no Telegram.
    scheduler_enabled: bool = True       # liga o agendador no startup da API
    lembretes_enabled: bool = True       # manda o digest de vencimento no Telegram
    lembretes_hora: int = 8              # hora local (America/Sao_Paulo) do envio
    lembretes_dias_antes: int = 3        # avisa boletos vencendo em até N dias
    orcamento_alerta_pct: int = 80       # avisa categorias acima de X% do teto
    briefing_enabled: bool = True        # MAS-4: "Resumo da Noite" no Telegram
    briefing_hora: int = 18              # hora local do briefing noturno
    timezone: str = "America/Sao_Paulo"

    # Auth / sessão (portão de entrada). Cookie opaco httpOnly; o token vai
    # hasheado no Postgres (ver app.api.services.auth). Em produção o Caddy
    # serve tudo em HTTPS → cookie Secure + prefixo __Host-. Em dev http puro,
    # ponha SESSION_COOKIE_SECURE=false (aí o cookie vira só "sessao").
    session_cookie_secure: bool = True
    session_dias_absoluto: int = 7      # expiração absoluta
    session_horas_inatividade: int = 24  # expira se ficar parado tanto tempo
    # Seed do admin (script seed_admin.py). Nunca hardcoded no código.
    admin_email: str = ""
    admin_senha_inicial: str = ""
    # 2FA (TOTP): chave Fernet pra cifrar o secret TOTP no banco. Gere com
    # `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
    # e ponha em TOTP_ENC_KEY no .env. Vazia = 2FA desabilitado (setup recusa).
    totp_enc_key: str = ""

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

    # Ferramentas de DEV (NUNCA ligar em produção). Habilita rotas perigosas
    # como o sync produção→dev (que APAGA o banco de dev). Default desligado;
    # só o .env de dev seta DEV_TOOLS_ENABLED=true.
    dev_tools_enabled: bool = False

    # CORS — origens liberadas pro front. Como o front usa credentials:'include'
    # (cookie de sessão), o navegador exige uma lista explícita; '*' não vale.
    # Em dev o Next cai na 3001 quando a 3000 está ocupada, então as duas portas
    # entram no default. Em produção, sobrescreva no .env:
    #   CORS_ORIGINS=https://studio.reativesystems.com.br
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

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


# ══════════════════════════════════════════════════════════════════
# Opções dos selects do CRM (espelham os selects do Notion).
# Usadas pelos dropdowns do front via GET /api/crm/opcoes.
# ══════════════════════════════════════════════════════════════════

# ── Negócios ──
ESTAGIO_NEGOCIO_OPCOES = [
    "⚪ Lead novo",
    "🔵 Primeiro contato",
    "🟣 Qualificado",
    "🟡 Briefing agendado",
    "🟠 Briefing realizado",
    "🔴 Proposta enviada",
    "🔴 Em negociação",
    "🟢 Ganho",
    "⚪ Perdido",
    "🟣 Standby",
]
PROBABILIDADE_OPCOES = ["10%", "25%", "50%", "75%", "90%"]
ORIGEM_NEGOCIO_OPCOES = [
    "LinkedIn", "Indicação", "Site", "Comunidade",
    "Network", "Inbound", "Outbound", "Evento",
]
TIPO_SERVICO_OPCOES = [
    "Landing page", "Site institucional", "Sistema web",
    "Automação", "Bot", "Manutenção", "Consultoria",
]

# ── Atividades ──
ATIVIDADE_STATUS_OPCOES = [
    "🟡 Agendada", "🟢 Realizada", "🔴 Não compareceu", "⚪ Cancelada",
]
ATIVIDADE_TIPO_OPCOES = [
    "📞 Call", "💬 WhatsApp", "✉️ E-mail",
    "🤝 Reunião presencial", "💼 LinkedIn DM", "🎥 Videocall",
]

# ── Projetos ──
PROJETO_STATUS_OPCOES = [
    "🆕 Onboarding", "🛠️ Em desenvolvimento", "🚀 Em produção",
    "👀 Em revisão", "⏸️ Pausado", "✅ Concluído",
]
FORMA_PAGAMENTO_OPCOES = ["À vista", "50/50", "40/30/30", "Mensal", "Outro"]
