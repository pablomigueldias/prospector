"""Importa o CRM do Notion PRA o Postgres (caminho reverso do exporter).

Keystone do "CRM fora do Notion": lê as bases de Empresas e Contatos do Notion
e faz upsert idempotente no Postgres (empresas por CNPJ, contatos por
empresa+email/nome). Guarda o `notion_page_id` pra casar nos re-runs e pro
dual-write continuar batendo.

One-shot, mas idempotente: rodar de novo só atualiza/insere o que mudou.
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from notion_client import Client
from pydantic import BaseModel
from sqlalchemy import select

from app.config import settings
from app.db.models.atividade import Atividade
from app.db.models.contato import Contato
from app.db.models.empresa import Empresa
from app.db.models.negocio import Negocio
from app.db.models.projeto import ProjetoCRM
from app.db.models.socio import Socio
from app.db.session import get_session
from app.repositories.contato_repository import ContatoRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.utils.logger import get_logger

logger = get_logger()


class ResultadoImport(BaseModel):
    empresas_lidas: int
    paginas_ignoradas: int   # páginas vazias do Notion (sem nome e sem CNPJ)
    contatos_lidos: int
    empresas_sem_link: int   # contatos cuja empresa não foi encontrada
    negocios_lidos: int = 0
    projetos_lidos: int = 0
    atividades_lidas: int = 0
    erros: list[str]


# ── leitura tipada de propriedades do Notion ─────────────────────────

def _title(p: dict | None) -> str | None:
    if not p or p.get("type") != "title":
        return None
    arr = p.get("title") or []
    return arr[0]["plain_text"].strip() if arr else None


def _texto(p: dict | None) -> str | None:
    if not p or p.get("type") != "rich_text":
        return None
    arr = p.get("rich_text") or []
    txt = "".join(t.get("plain_text", "") for t in arr).strip()
    return txt or None


def _select(p: dict | None) -> str | None:
    if not p or p.get("type") != "select":
        return None
    v = p.get("select")
    return v.get("name") if v else None


def _numero(p: dict | None) -> float | None:
    if not p or p.get("type") != "number":
        return None
    return p.get("number")


def _url(p: dict | None) -> str | None:
    if not p or p.get("type") != "url":
        return None
    return (p.get("url") or "").strip() or None


def _email(p: dict | None) -> str | None:
    if not p or p.get("type") != "email":
        return None
    return (p.get("email") or "").strip() or None


def _phone(p: dict | None) -> str | None:
    if not p or p.get("type") != "phone_number":
        return None
    return (p.get("phone_number") or "").strip() or None


def _relation_ids(p: dict | None) -> list[str]:
    if not p or p.get("type") != "relation":
        return []
    return [r["id"] for r in (p.get("relation") or [])]


def _so_digitos(cnpj: str | None) -> str | None:
    if not cnpj:
        return None
    d = "".join(c for c in cnpj if c.isdigit())
    return d or None


def _multi_select(p: dict | None) -> list[str] | None:
    if not p or p.get("type") != "multi_select":
        return None
    vals = [x["name"] for x in (p.get("multi_select") or [])]
    return vals or None


def _status_sel(p: dict | None) -> str | None:
    """Lê tanto 'select' quanto 'status' (tipos diferentes no Notion)."""
    if not p:
        return None
    t = p.get("type")
    if t in ("select", "status"):
        v = p.get(t)
        return v.get("name") if v else None
    return None


def _data_str(p: dict | None) -> str | None:
    if not p or p.get("type") != "date":
        return None
    v = p.get("date")
    return v.get("start") if v else None


def _data_only(p: dict | None) -> date | None:
    s = _data_str(p)
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _data_hora(p: dict | None) -> datetime | None:
    s = _data_str(p)
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=None)  # coluna é naive
    except ValueError:
        try:
            return datetime.fromisoformat(s[:10])
        except ValueError:
            return None


# ── paginação ────────────────────────────────────────────────────────

def _listar_paginas(client: Client, db_id: str) -> list[dict[str, Any]]:
    paginas: list[dict] = []
    cursor: str | None = None
    while True:
        kwargs: dict[str, Any] = {"database_id": db_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = client.databases.query(**kwargs)
        paginas.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return paginas


# ── montagem dos modelos ─────────────────────────────────────────────

def _pagina_para_empresa(pg: dict) -> Empresa:
    pr = pg["properties"]
    emp = Empresa(
        nome=_title(pr.get("Nome")) or "(sem nome)",
        razao_social=_texto(pr.get("Razão Social")),
        cnpj=_so_digitos(_texto(pr.get("CNPJ"))),
        cidade=_texto(pr.get("Cidade")),
        estado=_select(pr.get("Estado")),
        local=_texto(pr.get("Local")),
        site=_url(pr.get("Site")),
        instagram=_texto(pr.get("Instagram")),
        facebook=_url(pr.get("Facebook")),
        capital_social=_numero(pr.get("Capital Social")),
        setor=_select(pr.get("Setor")),
        tamanho=_select(pr.get("Tamanho")),
        status=_select(pr.get("Status")),
        como_conheceu=_select(pr.get("Como conheceu")),
        notas=_texto(pr.get("Notas")),
        notion_page_id=pg["id"],
        notion_synced_at=datetime.now(UTC).replace(tzinfo=None),
    )
    # Sócios: rich_text "A, B" → linhas Socio.
    socios_txt = _texto(pr.get("Socio"))
    if socios_txt:
        for nome in (s.strip() for s in socios_txt.split(",")):
            if nome:
                emp.socios.append(Socio(nome=nome))
    return emp


_CAMPOS_EMPRESA = (
    "nome", "razao_social", "cnpj", "cidade", "estado", "local", "site",
    "instagram", "facebook", "capital_social", "setor", "tamanho", "status",
    "como_conheceu", "notas", "notion_page_id", "notion_synced_at",
)


def _copiar_campos_empresa(dest: Empresa, src: Empresa) -> None:
    """Atualiza os campos escalares de uma empresa já existente (re-run)."""
    for campo in _CAMPOS_EMPRESA:
        setattr(dest, campo, getattr(src, campo))


def _eh_lixo(emp: Empresa) -> bool:
    """Página vazia do Notion (sem nome e sem CNPJ) — ignora."""
    return emp.nome == "(sem nome)" and not emp.cnpj


def _pagina_para_contato(pg: dict) -> tuple[Contato, list[str]]:
    pr = pg["properties"]
    ct = Contato(
        nome=_title(pr.get("Nome")) or "(sem nome)",
        cargo=_texto(pr.get("Cargo")),
        decisor=(_select(pr.get("Decisor?")) == "Sim"),
        email=_email(pr.get("E-mail")),
        telefone=_phone(pr.get("Telefone")),
        whatsapp=_phone(pr.get("WhatsApp")),
        linkedin=_url(pr.get("LinkedIn")),
        origem_contato=_select(pr.get("Origem do contato")) or "Network",
        notion_page_id=pg["id"],
        notion_synced_at=datetime.now(UTC).replace(tzinfo=None),
    )
    return ct, _relation_ids(pr.get("Empresas"))


def _pagina_para_negocio(pg: dict) -> tuple[Negocio, dict[str, list[str]]]:
    pr = pg["properties"]
    n = Negocio(
        nome=_title(pr.get("Nome")) or "(sem nome)",
        estagio=_status_sel(pr.get("Estágio")),
        valor_estimado=_numero(pr.get("Valor estimado")),
        probabilidade=_status_sel(pr.get("Probabilidade")),
        origem=_status_sel(pr.get("Origem")),
        tipo_servico=_multi_select(pr.get("Tipo de serviço")),
        notas=_texto(pr.get("Notas")),
        motivo_perda=_status_sel(pr.get("Motivo perda")),
        previsao_fechamento=_data_only(pr.get("Previsão fechamento")),
        data_fechamento_real=_data_only(pr.get("Data fechamento real")),
        proxima_acao=_data_only(pr.get("Próxima ação")),
        notion_page_id=pg["id"],
        notion_synced_at=datetime.now(UTC).replace(tzinfo=None),
    )
    rel = {
        "empresa": _relation_ids(pr.get("Empresas")),
        "contato": _relation_ids(pr.get("Contato Principal")),
    }
    return n, rel


def _pagina_para_projeto(pg: dict) -> tuple[ProjetoCRM, dict[str, list[str]]]:
    pr = pg["properties"]
    p = ProjetoCRM(
        nome=_title(pr.get("Nome do Projeto")) or "(sem nome)",
        status=_status_sel(pr.get("Status")),
        tipo_servico=_status_sel(pr.get("Tipo de Serviço")),
        valor_total=_numero(pr.get("Valor total")),
        valor_recebido=_numero(pr.get("Valor recebido")),
        briefing=_texto(pr.get("Briefing")),
        link_producao=_url(pr.get("Link produção")),
        repo_github=_url(pr.get("Repo GitHub")),
        forma_pagamento=_status_sel(pr.get("Forma de pagamento")),
        prazo_entrega=_data_only(pr.get("Prazo de entrega")),
        data_inicio=_data_only(pr.get("Data início")),
        data_entrega_real=_data_only(pr.get("Data entrega real")),
        notion_page_id=pg["id"],
        notion_synced_at=datetime.now(UTC).replace(tzinfo=None),
    )
    rel = {
        "empresa": _relation_ids(pr.get("Empresas")),
        "negocio": _relation_ids(pr.get("Negócio Origem")),
    }
    return p, rel


def _pagina_para_atividade(pg: dict) -> tuple[Atividade, dict[str, list[str]]]:
    pr = pg["properties"]
    a = Atividade(
        titulo=_title(pr.get("Titulo")) or "(sem título)",
        tipo=_status_sel(pr.get("Tipo")),
        status=_status_sel(pr.get("Status")),
        data=_data_hora(pr.get("Data")),
        resumo=_texto(pr.get("Resumo")),
        proximos_passos=_texto(pr.get("Próximos passos")),
        notion_page_id=pg["id"],
        notion_synced_at=datetime.now(UTC).replace(tzinfo=None),
    )
    rel = {
        "negocio": _relation_ids(pr.get("Negócios")),
        "contato": _relation_ids(pr.get("Contatos")),
    }
    return a, rel


def _primeiro_id(maps: dict, ids: list[str]):
    """Resolve o 1º page_id que existe no mapa → o id local (uuid)."""
    for i in ids:
        obj = maps.get(i)
        if obj is not None:
            return obj.id
    return None


async def _upsert_por_page_id(session, modelo, novo, campos: list[str]):
    """Upsert idempotente por notion_page_id. Devolve o objeto persistido."""
    existing = None
    if novo.notion_page_id:
        existing = await session.scalar(
            select(modelo).where(modelo.notion_page_id == novo.notion_page_id)
        )
    if existing is not None:
        for c in campos:
            setattr(existing, c, getattr(novo, c))
        return existing
    session.add(novo)
    return novo


_CAMPOS_NEGOCIO = [
    "nome", "estagio", "valor_estimado", "probabilidade", "origem",
    "tipo_servico", "notas", "motivo_perda", "previsao_fechamento",
    "data_fechamento_real", "proxima_acao", "empresa_id", "contato_id",
    "notion_page_id", "notion_synced_at",
]
_CAMPOS_PROJETO = [
    "nome", "status", "tipo_servico", "valor_total", "valor_recebido",
    "briefing", "link_producao", "repo_github", "forma_pagamento",
    "prazo_entrega", "data_inicio", "data_entrega_real", "empresa_id",
    "negocio_id", "notion_page_id", "notion_synced_at",
]
_CAMPOS_ATIVIDADE = [
    "titulo", "tipo", "status", "data", "resumo", "proximos_passos",
    "negocio_id", "contato_id", "notion_page_id", "notion_synced_at",
]


# ── orquestração ─────────────────────────────────────────────────────

async def importar() -> ResultadoImport:
    if not settings.notion_token:
        raise RuntimeError("NOTION_TOKEN não configurado.")

    client = Client(auth=settings.notion_token)
    erros: list[str] = []

    logger.info("Notion→PG: lendo as 5 bases…")
    pgs_emp = _listar_paginas(client, settings.notion_db_empresas)
    pgs_ct = _listar_paginas(client, settings.notion_db_contatos)
    pgs_neg = _listar_paginas(client, settings.notion_db_negocios)
    pgs_proj = _listar_paginas(client, settings.notion_db_projetos)
    pgs_atv = _listar_paginas(client, settings.notion_db_atividades)

    sem_link = 0
    async with get_session() as session:
        emp_repo = EmpresaRepository(session)
        ct_repo = ContatoRepository(session)

        # notion_page_id da empresa → objeto Empresa (pra ligar contatos).
        # Dedupe por page_id (chave estável) e, em fallback, por CNPJ —
        # garante idempotência mesmo pra empresa sem CNPJ.
        por_page_id: dict[str, Empresa] = {}
        ignoradas = 0
        for pg in pgs_emp:
            try:
                emp = _pagina_para_empresa(pg)
                if _eh_lixo(emp):
                    ignoradas += 1
                    continue
                existing = await emp_repo.find_by_notion_page_id(emp.notion_page_id)
                if existing is None and emp.cnpj:
                    existing = await emp_repo.find_by_cnpj(emp.cnpj)
                if existing is not None:
                    _copiar_campos_empresa(existing, emp)
                    por_page_id[pg["id"]] = existing
                else:
                    emp_repo.add(emp)
                    por_page_id[pg["id"]] = emp
            except Exception as e:  # noqa: BLE001 — registra e segue
                erros.append(f"empresa {pg.get('id')}: {e}")
        await session.flush()  # garante PKs das empresas novas

        ct_por_page_id: dict[str, Contato] = {}
        for pg in pgs_ct:
            try:
                ct, empresa_ids = _pagina_para_contato(pg)
                empresa = next(
                    (por_page_id[i] for i in empresa_ids if i in por_page_id),
                    None,
                )
                if empresa is None:
                    sem_link += 1
                    continue
                ct.empresa_id = empresa.id
                salvo = await ct_repo.upsert(ct)
                ct_por_page_id[pg["id"]] = salvo
            except Exception as e:  # noqa: BLE001
                erros.append(f"contato {pg.get('id')}: {e}")
        await session.flush()  # PKs dos contatos pra ligar negócios/atividades

        # ── Negócios (ligam empresa + contato) ──────────────────────
        neg_por_page_id: dict[str, Negocio] = {}
        for pg in pgs_neg:
            try:
                neg, rel = _pagina_para_negocio(pg)
                neg.empresa_id = _primeiro_id(por_page_id, rel["empresa"])
                neg.contato_id = _primeiro_id(ct_por_page_id, rel["contato"])
                salvo = await _upsert_por_page_id(
                    session, Negocio, neg, _CAMPOS_NEGOCIO
                )
                neg_por_page_id[pg["id"]] = salvo
            except Exception as e:  # noqa: BLE001
                erros.append(f"negocio {pg.get('id')}: {e}")
        await session.flush()  # PKs dos negócios pra ligar projetos/atividades

        # ── Projetos (ligam empresa + negócio origem) ───────────────
        for pg in pgs_proj:
            try:
                proj, rel = _pagina_para_projeto(pg)
                proj.empresa_id = _primeiro_id(por_page_id, rel["empresa"])
                proj.negocio_id = _primeiro_id(neg_por_page_id, rel["negocio"])
                await _upsert_por_page_id(session, ProjetoCRM, proj, _CAMPOS_PROJETO)
            except Exception as e:  # noqa: BLE001
                erros.append(f"projeto {pg.get('id')}: {e}")

        # ── Atividades (ligam negócio + contato) ────────────────────
        for pg in pgs_atv:
            try:
                atv, rel = _pagina_para_atividade(pg)
                atv.negocio_id = _primeiro_id(neg_por_page_id, rel["negocio"])
                atv.contato_id = _primeiro_id(ct_por_page_id, rel["contato"])
                await _upsert_por_page_id(
                    session, Atividade, atv, _CAMPOS_ATIVIDADE
                )
            except Exception as e:  # noqa: BLE001
                erros.append(f"atividade {pg.get('id')}: {e}")

        await session.commit()

    return ResultadoImport(
        empresas_lidas=len(pgs_emp),
        paginas_ignoradas=ignoradas,
        contatos_lidos=len(pgs_ct),
        empresas_sem_link=sem_link,
        negocios_lidos=len(pgs_neg),
        projetos_lidos=len(pgs_proj),
        atividades_lidas=len(pgs_atv),
        erros=erros,
    )
