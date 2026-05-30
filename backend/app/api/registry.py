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
    category: str = "Agentes"
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
