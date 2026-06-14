from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Agent:
    slug: str
    name: str
    description: str
    icon: str
    status: str  # "active" | "soon" | "experimental"
    order: int
    category: str = "Reative Systems"
    capabilities: Dict[str, bool] = field(default_factory=dict)
    roadmap_label: Optional[str] = None  # ex: "Roadmap Q3"

    def to_dict(self) -> dict:
        return asdict(self)


_AGENTS: List[Agent] = [
    Agent(
        slug="prospector",
        name="Prospector",
        description=(
            "Cadastra empresas, descobre contatos decisores e envia "
            "tudo direto pro Notion."
        ),
        icon="ti-radar",
        status="active",
        order=10,
        capabilities={
            "manual": True,
            "investigate": False,  # ainda em revisão
            "csv_import": False,
        },
    ),
    Agent(
        slug="copywriter",
        name="Copywriter",
        description=(
            "Gera e-mails de prospecção persuasivos e personalizados "
            "a partir dos dados do lead."
        ),
        icon="ti-mail",
        status="active",
        order=15,  # entre prospector (10) e cobrança (20)
        capabilities={"gera_email": True, "usa_lead_existente": True},
    ),
    Agent(
        slug="outreach",
        name="Outreach",
        description=(
            "Gera rascunhos de e-mail pros contatos, acompanha envios "
            "e detecta respostas pra follow-up."
        ),
        icon="ti-mail",
        status="active",
        order=18,
        capabilities={"gera_rascunho": True, "sincroniza": True},
    ),
    Agent(
        slug="cobranca",
        name="Cobrança",
        description=(
            "Acompanha boletos, dispara lembretes via WhatsApp e "
            "atualiza o Notion."
        ),
        icon="ti-cash",
        status="soon",
        order=20,
        roadmap_label="Roadmap Q3",
    ),
    Agent(
        slug="suporte",
        name="Suporte",
        description=(
            "Triagem de tickets, respostas iniciais e escalonamento "
            "automático."
        ),
        icon="ti-headset",
        status="soon",
        order=30,
        roadmap_label="Roadmap Q3",
    ),
    Agent(
        slug="onboarding",
        name="Onboarding",
        description=(
            "Recebe novo cliente, monta acesso, agenda kickoff e envia "
            "welcome."
        ),
        icon="ti-rocket",
        status="soon",
        order=40,
        roadmap_label="Roadmap Q4",
    ),

    # ══════════════════════════════════════════════════════════════
    # Área PESSOAL — meus agentes do dia a dia (tabelas pessoal_*).
    # Separada da Reative pra não misturar o que é trabalho e o que
    # é meu. Mesma tela, grupo próprio na sidebar.
    # ══════════════════════════════════════════════════════════════
    Agent(
        slug="perfil-mestre",
        name="Perfil Mestre",
        description=(
            "Quem EU sou: habilidades, projetos, experiência e tom de "
            "escrita. Insumo central dos agentes pessoais."
        ),
        icon="ti-user-circle",
        status="active",
        order=100,
        category="Pessoal",
        capabilities={"edita_perfil": True},
    ),
    Agent(
        slug="vagas",
        name="Vagas",
        description=(
            "Registra a vaga, destrincha o que ela exige, mede seu match "
            "e rascunha o e-mail de candidatura — você revisa e envia."
        ),
        icon="ti-briefcase",
        status="active",
        order=110,
        category="Pessoal",
        capabilities={
            "cadastra_vaga": True,
            "analisa_vaga": True,
            "gera_rascunho": True,
        },
    ),
    Agent(
        slug="financas",
        name="Finanças",
        description=(
            "Organizador financeiro pessoal: contas, despesas, cartões e "
            "boletos. Importa o boleto por foto e lança gasto pelo Telegram."
        ),
        icon="ti-wallet",
        status="active",
        order=120,
        category="Pessoal",
        capabilities={
            "resumo_mes": True,
            "importa_boleto": True,
            "bot_telegram": True,
        },
    ),
    Agent(
        slug="freela",
        name="Freela",
        description=(
            "Copiloto de propostas freelancer (Workana): você cola o projeto, "
            "a IA analisa o fit, precifica embutindo a comissão e rascunha a "
            "proposta ancorada nos seus projetos. Você revisa e envia na mão."
        ),
        icon="ti-briefcase",
        status="active",
        order=130,
        category="Pessoal",
        capabilities={
            "crm_propostas": True,
            "analisa_projeto": True,    # Fase 3 (IA)
            "precifica": True,          # Fase 4
            "rascunha_proposta": False,  # Fase 5 (IA)
        },
    ),
]


def list_agents() -> List[Agent]:
    return sorted(_AGENTS, key=lambda a: a.order)


def get_agent(slug: str) -> Optional[Agent]:
    for agent in _AGENTS:
        if agent.slug == slug:
            return agent
    return None


def is_active(slug: str) -> bool:
    agent = get_agent(slug)
    return agent is not None and agent.status == "active"
