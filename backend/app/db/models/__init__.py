from app.db.models.empresa import Empresa
from app.db.models.contato import Contato
from app.db.models.socio import Socio
from app.db.models.ai_call import AiCall
from app.db.models.pipeline_event import PipelineEvent
from app.db.models.email_outreach import EmailOutreach

# ── Área pessoal (tabelas pessoal_*) — isolada da Reative ──────────
from app.db.models.pessoal.perfil_mestre import PerfilMestre
from app.db.models.pessoal.vaga import Vaga
from app.db.models.pessoal.candidatura_email import CandidaturaEmail


__all__ = [
    "Empresa",
    "Contato",
    "Socio",
    "AiCall",
    "PipelineEvent",
    "EmailOutreach",
    # pessoal
    "PerfilMestre",
    "Vaga",
    "CandidaturaEmail",
]