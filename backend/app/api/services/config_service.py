"""S3 — Configurações na UI (self-service).

O coração do "sem pedir pro Claude": um catálogo curado de `Settings` editáveis
+ uma tabela `config_app` que guarda os overrides + aplicação em runtime sobre o
singleton `settings`. Quem lê `settings.x` em tempo de chamada (followups, LLM,
briefing, alertas) enxerga o novo valor sem reiniciar. As mudanças que afetam o
*agendamento* dos jobs (horas/ligar-desligar o scheduler) só valem no próximo
restart da API — sinalizado no catálogo via `requer_restart`.

Segredos e infra (db, s3, tokens) NÃO entram no catálogo de propósito.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.db.models.config_app import ConfigApp
from app.db.session import get_session


class ConfigError(ValueError):
    """Entrada inválida ao atualizar uma configuração."""


@dataclass(frozen=True)
class ConfigItem:
    chave: str
    categoria: str
    label: str
    tipo: str  # "bool" | "int" | "select"
    ajuda: str = ""
    opcoes: tuple[str, ...] = ()
    minimo: int | None = None
    maximo: int | None = None
    requer_restart: bool = False


# Catálogo curado — só o que é seguro e útil mexer pela tela.
CATALOGO: tuple[ConfigItem, ...] = (
    # ── Agendador ──
    ConfigItem("scheduler_enabled", "Agendador", "Agendador ligado", "bool",
               "Liga os jobs automáticos no startup da API.", requer_restart=True),
    ConfigItem("lembretes_enabled", "Agendador", "Lembretes diários", "bool",
               "Manda o digest de vencimentos no Telegram."),
    ConfigItem("lembretes_hora", "Agendador", "Hora dos lembretes", "int",
               "Hora local 0–23.", minimo=0, maximo=23, requer_restart=True),
    ConfigItem("lembretes_dias_antes", "Agendador",
               "Avisar boletos com (dias) de antecedência", "int", "",
               minimo=0, maximo=30),
    # ── Briefing (MAS-4) ──
    ConfigItem("briefing_enabled", "Briefing", "Resumo da Noite ligado", "bool",
               "Manda o briefing noturno no Telegram.", requer_restart=True),
    ConfigItem("briefing_hora", "Briefing", "Hora do briefing", "int",
               "Hora local 0–23.", minimo=0, maximo=23, requer_restart=True),
    # ── Freela ──
    ConfigItem("freela_followup_enabled", "Freela", "Follow-up de propostas",
               "bool", ""),
    ConfigItem("freela_followup_dias", "Freela",
               "Avisar propostas paradas há (dias)", "int", "",
               minimo=1, maximo=60),
    ConfigItem("freela_capacidade_horas_semana", "Freela",
               "Capacidade faturável (horas/semana)", "int",
               "Horas livres/semana pra novos projetos (anti-furada).",
               minimo=1, maximo=80),
    # ── LLM ──
    ConfigItem("llm_provider", "LLM", "Provedor de IA primário", "select",
               "Modelo primário (com fallback automático Gemini → Groq).",
               opcoes=("gemini", "groq")),
    # ── Orçamento ──
    ConfigItem("orcamento_alerta_pct", "Orçamento",
               "Alerta de categoria acima de (%)", "int", "",
               minimo=10, maximo=100),
)

_POR_CHAVE: dict[str, ConfigItem] = {i.chave: i for i in CATALOGO}


def _default(chave: str) -> Any:
    """Default declarado no `Settings` (não o valor efetivo já sobrescrito)."""
    return Settings.model_fields[chave].default


def _parse(item: ConfigItem, valor: Any) -> Any:
    """Texto/JSON → valor tipado e validado conforme o catálogo."""
    if item.tipo == "bool":
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in {"true", "1", "sim", "on"}
    if item.tipo == "int":
        try:
            n = int(valor)
        except (TypeError, ValueError):
            raise ConfigError(
                f"{item.label}: precisa ser um número inteiro."
            ) from None
        if item.minimo is not None and n < item.minimo:
            raise ConfigError(f"{item.label}: mínimo {item.minimo}.")
        if item.maximo is not None and n > item.maximo:
            raise ConfigError(f"{item.label}: máximo {item.maximo}.")
        return n
    # select / str
    v = str(valor).strip()
    if item.opcoes and v not in item.opcoes:
        raise ConfigError(f"{item.label}: opção inválida ({v!r}).")
    return v


def _serializar(valor: Any) -> str:
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor)


async def aplicar(session: AsyncSession) -> int:
    """Aplica os overrides salvos sobre o singleton `settings`. Retorna quantos."""
    rows = (await session.execute(select(ConfigApp))).scalars().all()
    overrides = {r.chave: r.valor for r in rows}
    n = 0
    for item in CATALOGO:
        if item.chave in overrides:
            try:
                setattr(settings, item.chave, _parse(item, overrides[item.chave]))
                n += 1
            except ConfigError:
                # override corrompido no banco — ignora, mantém o default.
                continue
    return n


async def listar() -> list[dict]:
    """Catálogo com o valor efetivo atual, o default e se está sobrescrito."""
    async with get_session() as session:
        rows = (await session.execute(select(ConfigApp))).scalars().all()
    sobrescritos = {r.chave for r in rows}
    return [
        {
            "chave": item.chave,
            "categoria": item.categoria,
            "label": item.label,
            "tipo": item.tipo,
            "ajuda": item.ajuda,
            "opcoes": list(item.opcoes),
            "minimo": item.minimo,
            "maximo": item.maximo,
            "requer_restart": item.requer_restart,
            "valor": getattr(settings, item.chave),
            "default": _default(item.chave),
            "sobrescrito": item.chave in sobrescritos,
        }
        for item in CATALOGO
    ]


async def atualizar(mudancas: dict[str, Any]) -> None:
    """Valida, faz upsert dos overrides e reaplica no `settings`."""
    if not mudancas:
        return
    async with get_session() as session:
        for chave, valor in mudancas.items():
            item = _POR_CHAVE.get(chave)
            if item is None:
                raise ConfigError(f"chave desconhecida: {chave}")
            tipado = _parse(item, valor)  # valida
            texto = _serializar(tipado)
            existente = (
                await session.execute(
                    select(ConfigApp).where(ConfigApp.chave == chave)
                )
            ).scalar_one_or_none()
            if existente is not None:
                existente.valor = texto
            else:
                session.add(ConfigApp(chave=chave, valor=texto))
        await session.commit()
        await aplicar(session)
