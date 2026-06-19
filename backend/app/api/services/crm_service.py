"""Service do CRM — empresas/contatos no Postgres (leitura + CRUD).

O CRM dentro do sistema. A escrita aqui é a fonte de verdade; o Prospector
segue alimentando (dual-write Notion+Postgres) até desligarmos o Notion.
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.schemas.crm import (
    AtividadeListItem,
    AtividadeListResponse,
    AtividadeUpsert,
    ContatoListItem,
    ContatoListResponse,
    ContatoOut,
    ContatoUpsert,
    CrmDashboard,
    CrmMetricas,
    EmpresaDetalhe,
    EmpresaListItem,
    EmpresaListResponse,
    EmpresaRelacionados,
    EmpresaUpsert,
    EstagioResumo,
    KanbanColuna,
    KanbanResponse,
    NegocioColuna,
    NegocioListItem,
    NegociosPipeline,
    NegocioUpsert,
    OpcaoCreate,
    OpcaoOut,
    OpcaoReorder,
    OpcaoUpdate,
    ProjetoListItem,
    ProjetoListResponse,
    ProjetoUpsert,
    RecordCampo,
    RecordDetalhe,
    RecordGrupo,
    RecordLink,
    SocioOut,
)
from app.api.services import memoria_service
from app.db.models.atividade import Atividade
from app.db.models.contato import Contato
from app.db.models.crm_opcao import CrmOpcao
from app.db.models.empresa import Empresa
from app.db.models.negocio import Negocio
from app.db.models.projeto import ProjetoCRM
from app.db.session import get_session
from app.repositories.contato_repository import ContatoRepository
from app.repositories.empresa_repository import EmpresaRepository


class CrmError(Exception):
    """Erro de negócio do CRM — vira HTTP 400 no router."""


_SEM_STATUS = "(sem status)"


async def _ordem_grupo(session, grupo: str) -> list[str]:
    """Valores ativos de um grupo de opções, na ordem definida (pro kanban/pipeline)."""
    rows = (await session.execute(
        select(CrmOpcao.valor)
        .where(CrmOpcao.grupo == grupo, CrmOpcao.ativo.is_(True))
        .order_by(CrmOpcao.ordem)
    )).scalars().all()
    return list(rows)


async def opcoes() -> dict[str, list[str]]:
    """Opções dos selects do CRM, lidas da tabela gerenciável (ativas, em ordem)."""
    async with get_session() as session:
        rows = (await session.execute(
            select(CrmOpcao)
            .where(CrmOpcao.ativo.is_(True))
            .order_by(CrmOpcao.grupo, CrmOpcao.ordem)
        )).scalars().all()
    mapa: dict[str, list[str]] = {}
    for r in rows:
        mapa.setdefault(r.grupo, []).append(r.valor)
    return mapa


async def opcoes_cores() -> dict[str, dict[str, str]]:
    """Mapa grupo→valor→cor (só opções ativas com cor) — pra pintar as pílulas."""
    async with get_session() as session:
        rows = (await session.execute(
            select(CrmOpcao).where(
                CrmOpcao.ativo.is_(True), CrmOpcao.cor.is_not(None)
            )
        )).scalars().all()
    mapa: dict[str, dict[str, str]] = {}
    for r in rows:
        if r.cor:
            mapa.setdefault(r.grupo, {})[r.valor] = r.cor
    return mapa


# ── CRUD das opções gerenciáveis ─────────────────────────────────────
# Grupo de opção → (modelo, coluna) onde o valor é gravado. Usado p/ propagar
# um rename da opção aos registros existentes (mantém tudo consistente).
# tipo_servico fica de fora (é multi no negócio / texto no projeto).
def _grupo_campo():
    return {
        "setor": (Empresa, Empresa.setor),
        "tamanho": (Empresa, Empresa.tamanho),
        "status": (Empresa, Empresa.status),
        "como_conheceu": (Empresa, Empresa.como_conheceu),
        "estado": (Empresa, Empresa.estado),
        "origem_contato": (Contato, Contato.origem_contato),
        "estagio": (Negocio, Negocio.estagio),
        "probabilidade": (Negocio, Negocio.probabilidade),
        "origem_negocio": (Negocio, Negocio.origem),
        "projeto_status": (ProjetoCRM, ProjetoCRM.status),
        "forma_pagamento": (ProjetoCRM, ProjetoCRM.forma_pagamento),
        "atividade_status": (Atividade, Atividade.status),
        "atividade_tipo": (Atividade, Atividade.tipo),
    }


def _to_opcao(o: CrmOpcao) -> OpcaoOut:
    return OpcaoOut(id=str(o.id), grupo=o.grupo, valor=o.valor, cor=o.cor,
                    ordem=o.ordem, ativo=o.ativo)


async def listar_opcoes() -> list[OpcaoOut]:
    async with get_session() as session:
        rows = (await session.execute(
            select(CrmOpcao).order_by(CrmOpcao.grupo, CrmOpcao.ordem)
        )).scalars().all()
    return [_to_opcao(o) for o in rows]


async def criar_opcao(p: OpcaoCreate) -> OpcaoOut:
    grupo = (p.grupo or "").strip()
    valor = (p.valor or "").strip()
    if not grupo or not valor:
        raise CrmError("Grupo e valor são obrigatórios.")
    async with get_session() as session:
        maxo = (await session.execute(
            select(func.max(CrmOpcao.ordem)).where(CrmOpcao.grupo == grupo)
        )).scalar()
        o = CrmOpcao(grupo=grupo, valor=valor, cor=(p.cor or None),
                     ordem=(maxo if maxo is not None else -1) + 1, ativo=True)
        session.add(o)
        try:
            await session.commit()
        except IntegrityError as e:
            raise CrmError("Essa opção já existe nesse grupo.") from e
        await session.refresh(o)
        return _to_opcao(o)


async def atualizar_opcao(opcao_id: str, p: OpcaoUpdate) -> OpcaoOut:
    uid = _p_uuid(opcao_id)
    async with get_session() as session:
        o = await session.get(CrmOpcao, uid)
        if o is None:
            raise CrmError("Opção não encontrada.")
        if p.valor is not None:
            novo = p.valor.strip()
            if not novo:
                raise CrmError("O valor não pode ficar vazio.")
            if novo != o.valor:
                mp = _grupo_campo().get(o.grupo)
                if mp is not None:
                    model, col = mp
                    await session.execute(
                        update(model).where(col == o.valor).values({col.key: novo})
                    )
                o.valor = novo
        if p.cor is not None:
            o.cor = p.cor or None
        if p.ativo is not None:
            o.ativo = p.ativo
        try:
            await session.commit()
        except IntegrityError as e:
            raise CrmError("Já existe essa opção no grupo.") from e
        await session.refresh(o)
        return _to_opcao(o)


async def excluir_opcao(opcao_id: str) -> None:
    uid = _p_uuid(opcao_id)
    async with get_session() as session:
        o = await session.get(CrmOpcao, uid)
        if o is None:
            raise CrmError("Opção não encontrada.")
        await session.delete(o)
        await session.commit()


async def reordenar_opcoes(p: OpcaoReorder) -> list[OpcaoOut]:
    async with get_session() as session:
        for i, oid in enumerate(p.ids):
            o = await session.get(CrmOpcao, _p_uuid(oid))
            if o is not None and o.grupo == p.grupo:
                o.ordem = i
        await session.commit()
        rows = (await session.execute(
            select(CrmOpcao).where(CrmOpcao.grupo == p.grupo)
            .order_by(CrmOpcao.ordem)
        )).scalars().all()
    return [_to_opcao(o) for o in rows]


def _to_item(e: Empresa) -> EmpresaListItem:
    return EmpresaListItem(
        id=str(e.id),
        nome=e.nome,
        cnpj=e.cnpj,
        site=e.site,
        cidade=e.cidade,
        estado=e.estado,
        setor=e.setor,
        tamanho=e.tamanho,
        status=e.status,
        como_conheceu=e.como_conheceu,
        score=e.score,
        n_contatos=len(e.contatos),
    )


def _to_detalhe(e: Empresa) -> EmpresaDetalhe:
    return EmpresaDetalhe(
        id=str(e.id),
        nome=e.nome,
        razao_social=e.razao_social,
        cnpj=e.cnpj,
        cidade=e.cidade,
        estado=e.estado,
        local=e.local,
        site=e.site,
        instagram=e.instagram,
        facebook=e.facebook,
        capital_social=float(e.capital_social) if e.capital_social is not None else None,
        setor=e.setor,
        tamanho=e.tamanho,
        score=e.score,
        status=e.status,
        como_conheceu=e.como_conheceu,
        notas=e.notas,
        analise_json=e.analise_json,
        notion_page_id=e.notion_page_id,
        contatos=[
            ContatoOut(
                id=str(c.id), nome=c.nome, cargo=c.cargo, decisor=c.decisor,
                email=c.email, telefone=c.telefone, whatsapp=c.whatsapp,
                linkedin=c.linkedin, origem_contato=c.origem_contato,
            )
            for c in e.contatos
        ],
        socios=[
            SocioOut(id=str(s.id), nome=s.nome, qualificacao=s.qualificacao)
            for s in e.socios
        ],
    )


async def listar_empresas(
    *, limit: int = 50, offset: int = 0,
    ordenar_por: str | None = None, desc: bool = False, **filtros,
) -> EmpresaListResponse:
    async with get_session() as session:
        repo = EmpresaRepository(session)
        empresas = await repo.listar(
            limit=limit, offset=offset,
            ordenar_por=ordenar_por, desc=desc, **filtros,
        )
        total = await repo.contar(**filtros)
        return EmpresaListResponse(
            items=[_to_item(e) for e in empresas], total=total
        )


async def facetas() -> dict[str, list[str]]:
    async with get_session() as session:
        return await EmpresaRepository(session).facetas()


def _aplicar_empresa(e: Empresa, p: EmpresaUpsert) -> None:
    e.nome = p.nome
    e.razao_social = p.razao_social
    e.cnpj = "".join(c for c in (p.cnpj or "") if c.isdigit()) or None
    e.site = p.site
    e.cidade = p.cidade
    e.estado = p.estado
    e.local = p.local
    e.instagram = p.instagram
    e.facebook = p.facebook
    e.capital_social = p.capital_social
    e.setor = p.setor
    e.tamanho = p.tamanho
    e.score = p.score
    e.notas = p.notas
    # status e como_conheceu são NOT NULL (têm default no banco). Só
    # sobrescreve quando vier valor — nunca grava NULL.
    if p.status is not None:
        e.status = p.status
    if p.como_conheceu is not None:
        e.como_conheceu = p.como_conheceu


async def criar_empresa(payload: EmpresaUpsert) -> EmpresaDetalhe:
    if not payload.nome or not payload.nome.strip():
        raise CrmError("A empresa precisa de um nome.")
    async with get_session() as session:
        empresa = Empresa()
        _aplicar_empresa(empresa, payload)
        session.add(empresa)
        await session.commit()
        await session.refresh(empresa)
        return _to_detalhe(empresa)


async def atualizar_empresa(empresa_id: str, payload: EmpresaUpsert) -> EmpresaDetalhe:
    try:
        uid = uuid.UUID(empresa_id)
    except ValueError as e:
        raise CrmError("ID inválido.") from e
    async with get_session() as session:
        repo = EmpresaRepository(session)
        empresa = await repo.get_by_id(uid)
        if empresa is None:
            raise CrmError("Empresa não encontrada.")
        _aplicar_empresa(empresa, payload)
        await session.commit()
        await session.refresh(empresa)
        return _to_detalhe(empresa)


async def excluir_empresa(empresa_id: str) -> None:
    try:
        uid = uuid.UUID(empresa_id)
    except ValueError as e:
        raise CrmError("ID inválido.") from e
    async with get_session() as session:
        repo = EmpresaRepository(session)
        empresa = await repo.get_by_id(uid)
        if empresa is None:
            raise CrmError("Empresa não encontrada.")
        await repo.excluir(empresa)
        await session.commit()


async def get_empresa(empresa_id: str) -> EmpresaDetalhe | None:
    try:
        uid = uuid.UUID(empresa_id)
    except ValueError:
        return None
    async with get_session() as session:
        empresa = await EmpresaRepository(session).get_by_id(uid)
        return _to_detalhe(empresa) if empresa else None


async def kanban() -> KanbanResponse:
    async with get_session() as session:
        empresas = await EmpresaRepository(session).listar_todas()
        ordem_status = await _ordem_grupo(session, "status")

    grupos: dict[str, list[EmpresaListItem]] = {}
    for e in empresas:
        chave = e.status or _SEM_STATUS
        grupos.setdefault(chave, []).append(_to_item(e))

    # ordena as colunas: conhecidas primeiro (na ordem definida), resto depois.
    conhecidas = [s for s in ordem_status if s in grupos]
    resto = [s for s in grupos if s not in ordem_status]
    ordem = conhecidas + resto

    colunas = [
        KanbanColuna(status=s, total=len(grupos[s]), empresas=grupos[s])
        for s in ordem
    ]
    return KanbanResponse(colunas=colunas)


async def metricas() -> CrmMetricas:
    async with get_session() as session:
        empresas = await EmpresaRepository(session).listar_todas()

    por_status: dict[str, int] = {}
    total_contatos = 0
    total_decisores = 0
    for e in empresas:
        chave = e.status or _SEM_STATUS
        por_status[chave] = por_status.get(chave, 0) + 1
        total_contatos += len(e.contatos)
        total_decisores += sum(1 for c in e.contatos if c.decisor)

    return CrmMetricas(
        total_empresas=len(empresas),
        total_contatos=total_contatos,
        total_decisores=total_decisores,
        por_status=por_status,
    )


# ══════════════════════════════════════════════════════════════════
# Contatos — lista + CRUD
# ══════════════════════════════════════════════════════════════════

def _to_contato_item(c: Contato) -> ContatoListItem:
    # c.empresa vem via selectinload no listar.
    empresa_nome = c.empresa.nome if c.empresa is not None else None
    return ContatoListItem(
        id=str(c.id),
        nome=c.nome,
        cargo=c.cargo,
        decisor=c.decisor,
        email=c.email,
        telefone=c.telefone,
        whatsapp=c.whatsapp,
        linkedin=c.linkedin,
        origem_contato=c.origem_contato,
        empresa_id=str(c.empresa_id),
        empresa_nome=empresa_nome,
    )


def _aplicar_contato(c: Contato, p: ContatoUpsert) -> None:
    c.nome = p.nome
    c.cargo = p.cargo
    c.decisor = p.decisor
    c.email = p.email
    c.telefone = p.telefone
    c.whatsapp = p.whatsapp
    c.linkedin = p.linkedin
    c.origem_contato = p.origem_contato or "Network"


async def listar_contatos(
    *, busca: str | None = None, empresa_id: str | None = None,
    decisor: bool | None = None, origem: str | None = None,
    limit: int = 100, offset: int = 0,
) -> ContatoListResponse:
    emp_uid = None
    if empresa_id:
        try:
            emp_uid = uuid.UUID(empresa_id)
        except ValueError as e:
            raise CrmError("empresa_id inválido.") from e
    async with get_session() as session:
        repo = ContatoRepository(session)
        contatos = await repo.listar(
            busca=busca, empresa_id=emp_uid, decisor=decisor,
            origem=origem, limit=limit, offset=offset,
        )
        total = await repo.contar(
            busca=busca, empresa_id=emp_uid, decisor=decisor, origem=origem
        )
        return ContatoListResponse(
            items=[_to_contato_item(c) for c in contatos], total=total
        )


async def criar_contato(payload: ContatoUpsert) -> ContatoListItem:
    if not payload.nome or not payload.nome.strip():
        raise CrmError("O contato precisa de um nome.")
    try:
        emp_uid = uuid.UUID(payload.empresa_id)
    except ValueError as e:
        raise CrmError("empresa_id inválido.") from e
    async with get_session() as session:
        empresa = await EmpresaRepository(session).get_by_id(emp_uid)
        if empresa is None:
            raise CrmError("Empresa do contato não encontrada.")
        contato = Contato(empresa_id=emp_uid)
        _aplicar_contato(contato, payload)
        session.add(contato)
        await session.commit()
        await session.refresh(contato)
        contato.empresa = empresa
        return _to_contato_item(contato)


async def atualizar_contato(contato_id: str, payload: ContatoUpsert) -> ContatoListItem:
    try:
        uid = uuid.UUID(contato_id)
    except ValueError as e:
        raise CrmError("ID inválido.") from e
    async with get_session() as session:
        repo = ContatoRepository(session)
        contato = await repo.get_by_id(uid)
        if contato is None:
            raise CrmError("Contato não encontrado.")
        _aplicar_contato(contato, payload)
        await session.commit()
        # recarrega com empresa pra devolver o nome.
        contatos = await repo.listar(empresa_id=contato.empresa_id, limit=200)
        atual = next((c for c in contatos if c.id == uid), None)
        return _to_contato_item(atual or contato)


async def excluir_contato(contato_id: str) -> None:
    try:
        uid = uuid.UUID(contato_id)
    except ValueError as e:
        raise CrmError("ID inválido.") from e
    async with get_session() as session:
        repo = ContatoRepository(session)
        contato = await repo.get_by_id(uid)
        if contato is None:
            raise CrmError("Contato não encontrado.")
        await repo.excluir(contato)
        await session.commit()


# ══════════════════════════════════════════════════════════════════
# Negócios (pipeline) · Atividades · Projetos — leitura
# ══════════════════════════════════════════════════════════════════

def _iso(d) -> str | None:
    return d.isoformat() if d is not None else None


def _frac_prob(prob: str | None) -> float:
    """'75%' → 0.75. Sem valor → 1.0 (não pondera)."""
    if not prob:
        return 1.0
    try:
        return float(prob.replace("%", "").strip()) / 100.0
    except ValueError:
        return 1.0


_SEM_ESTAGIO = "(sem estágio)"


def _to_negocio_item(n: Negocio) -> NegocioListItem:
    valor = float(n.valor_estimado) if n.valor_estimado is not None else None
    pond = round(valor * _frac_prob(n.probabilidade), 2) if valor is not None else None
    return NegocioListItem(
        id=str(n.id),
        nome=n.nome,
        estagio=n.estagio,
        valor_estimado=valor,
        valor_ponderado=pond,
        probabilidade=n.probabilidade,
        origem=n.origem,
        tipo_servico=n.tipo_servico or [],
        previsao_fechamento=_iso(n.previsao_fechamento),
        proxima_acao=_iso(n.proxima_acao),
        empresa_id=str(n.empresa_id) if n.empresa_id else None,
        empresa_nome=n.empresa.nome if n.empresa is not None else None,
        contato_nome=n.contato.nome if n.contato is not None else None,
        notas=n.notas,
    )


async def pipeline_negocios() -> NegociosPipeline:
    async with get_session() as session:
        negocios = (
            await session.execute(select(Negocio).order_by(Negocio.nome))
        ).scalars().all()
        ordem_estagio = await _ordem_grupo(session, "estagio")

    grupos: dict[str, list[NegocioListItem]] = {}
    for n in negocios:
        item = _to_negocio_item(n)
        grupos.setdefault(item.estagio or _SEM_ESTAGIO, []).append(item)

    conhecidas = [s for s in ordem_estagio if s in grupos]
    resto = [s for s in grupos if s not in ordem_estagio]
    colunas: list[NegocioColuna] = []
    tot = pond_tot = 0.0
    for est in conhecidas + resto:
        itens = grupos[est]
        vt = sum(i.valor_estimado or 0 for i in itens)
        vp = sum(i.valor_ponderado or 0 for i in itens)
        tot += vt
        pond_tot += vp
        colunas.append(NegocioColuna(
            estagio=est, total=len(itens),
            valor_total=round(vt, 2), valor_ponderado=round(vp, 2),
            negocios=itens,
        ))
    return NegociosPipeline(
        colunas=colunas,
        valor_total=round(tot, 2),
        valor_ponderado=round(pond_tot, 2),
    )


async def listar_negocios() -> list[NegocioListItem]:
    async with get_session() as session:
        negocios = (
            await session.execute(select(Negocio).order_by(Negocio.nome))
        ).scalars().all()
    return [_to_negocio_item(n) for n in negocios]


async def listar_atividades() -> AtividadeListResponse:
    async with get_session() as session:
        ativs = (
            await session.execute(
                select(Atividade).order_by(Atividade.data.desc().nullslast())
            )
        ).scalars().all()
    items = [
        AtividadeListItem(
            id=str(a.id), titulo=a.titulo, tipo=a.tipo, status=a.status,
            data=a.data.isoformat() if a.data else None,
            resumo=a.resumo, proximos_passos=a.proximos_passos,
            negocio_id=str(a.negocio_id) if a.negocio_id else None,
            negocio_nome=a.negocio.nome if a.negocio is not None else None,
            contato_nome=a.contato.nome if a.contato is not None else None,
        )
        for a in ativs
    ]
    return AtividadeListResponse(items=items, total=len(items))


async def listar_projetos() -> ProjetoListResponse:
    async with get_session() as session:
        projs = (
            await session.execute(select(ProjetoCRM).order_by(ProjetoCRM.nome))
        ).scalars().all()
    items = []
    for p in projs:
        vt = float(p.valor_total) if p.valor_total is not None else None
        vr = float(p.valor_recebido) if p.valor_recebido is not None else None
        ar = round((vt or 0) - (vr or 0), 2) if vt is not None else None
        items.append(ProjetoListItem(
            id=str(p.id), nome=p.nome, status=p.status,
            tipo_servico=p.tipo_servico, valor_total=vt, valor_recebido=vr,
            a_receber=ar, prazo_entrega=_iso(p.prazo_entrega),
            data_entrega_real=_iso(p.data_entrega_real),
            link_producao=p.link_producao, repo_github=p.repo_github,
            empresa_nome=p.empresa.nome if p.empresa is not None else None,
            negocio_nome=p.negocio.nome if p.negocio is not None else None,
            briefing=p.briefing,
        ))
    return ProjetoListResponse(items=items, total=len(items))


# ══════════════════════════════════════════════════════════════════
# CRUD de Negócios · Atividades · Projetos
# ══════════════════════════════════════════════════════════════════

def _p_date(s: str | None):
    from datetime import date as _date
    if not s:
        return None
    try:
        return _date.fromisoformat(s[:10])
    except ValueError as e:
        raise CrmError(f"Data inválida: {s}") from e


def _p_datetime(s: str | None):
    from datetime import datetime as _dt
    if not s:
        return None
    try:
        return _dt.fromisoformat(s).replace(tzinfo=None)
    except ValueError:
        d = _p_date(s)
        return _dt(d.year, d.month, d.day) if d else None


def _p_uuid(s: str | None):
    if not s:
        return None
    try:
        return uuid.UUID(s)
    except ValueError as e:
        raise CrmError(f"ID inválido: {s}") from e


def _aplicar_negocio(n: Negocio, p: NegocioUpsert) -> None:
    n.nome = p.nome
    n.estagio = p.estagio
    n.valor_estimado = p.valor_estimado
    n.probabilidade = p.probabilidade
    n.origem = p.origem
    n.tipo_servico = p.tipo_servico or None
    n.notas = p.notas
    n.motivo_perda = p.motivo_perda
    n.previsao_fechamento = _p_date(p.previsao_fechamento)
    n.data_fechamento_real = _p_date(p.data_fechamento_real)
    n.proxima_acao = _p_date(p.proxima_acao)
    n.empresa_id = _p_uuid(p.empresa_id)
    n.contato_id = _p_uuid(p.contato_id)


async def _recarregar_negocio(session, uid) -> Negocio:
    return await session.scalar(select(Negocio).where(Negocio.id == uid))


async def criar_negocio(p: NegocioUpsert) -> NegocioListItem:
    if not p.nome or not p.nome.strip():
        raise CrmError("O negócio precisa de um nome.")
    async with get_session() as session:
        n = Negocio()
        _aplicar_negocio(n, p)
        session.add(n)
        await session.commit()
        return _to_negocio_item(await _recarregar_negocio(session, n.id))


async def atualizar_negocio(negocio_id: str, p: NegocioUpsert) -> NegocioListItem:
    uid = _p_uuid(negocio_id)
    async with get_session() as session:
        n = await session.get(Negocio, uid)
        if n is None:
            raise CrmError("Negócio não encontrado.")
        _aplicar_negocio(n, p)
        await session.commit()
        return _to_negocio_item(await _recarregar_negocio(session, uid))


async def excluir_negocio(negocio_id: str) -> None:
    uid = _p_uuid(negocio_id)
    async with get_session() as session:
        n = await session.get(Negocio, uid)
        if n is None:
            raise CrmError("Negócio não encontrado.")
        await session.delete(n)
        await session.commit()


async def mover_negocio_estagio(negocio_id: str, estagio: str) -> NegocioListItem:
    """Só muda o estágio (pro drag-and-drop do pipeline). Não toca no resto."""
    uid = _p_uuid(negocio_id)
    async with get_session() as session:
        n = await session.get(Negocio, uid)
        if n is None:
            raise CrmError("Negócio não encontrado.")
        n.estagio = estagio
        await session.commit()
        item = _to_negocio_item(await _recarregar_negocio(session, uid))
    await memoria_service.registrar(
        agente="crm", alvo_tipo="negocio", alvo_id=negocio_id, tipo="estagio",
        resumo=f"Estágio → {estagio}", payload={"estagio": estagio},
        origem="manual",
    )
    return item


def _aplicar_atividade(a: Atividade, p: AtividadeUpsert) -> None:
    a.titulo = p.titulo
    a.tipo = p.tipo
    a.status = p.status
    a.data = _p_datetime(p.data)
    a.resumo = p.resumo
    a.proximos_passos = p.proximos_passos
    a.negocio_id = _p_uuid(p.negocio_id)
    a.contato_id = _p_uuid(p.contato_id)


def _atividade_item(a: Atividade) -> AtividadeListItem:
    return AtividadeListItem(
        id=str(a.id), titulo=a.titulo, tipo=a.tipo, status=a.status,
        data=a.data.isoformat() if a.data else None,
        resumo=a.resumo, proximos_passos=a.proximos_passos,
        negocio_id=str(a.negocio_id) if a.negocio_id else None,
        negocio_nome=a.negocio.nome if a.negocio is not None else None,
        contato_nome=a.contato.nome if a.contato is not None else None,
    )


async def criar_atividade(p: AtividadeUpsert) -> AtividadeListItem:
    if not p.titulo or not p.titulo.strip():
        raise CrmError("A atividade precisa de um título.")
    async with get_session() as session:
        a = Atividade()
        _aplicar_atividade(a, p)
        session.add(a)
        await session.commit()
        return _atividade_item(
            await session.scalar(select(Atividade).where(Atividade.id == a.id))
        )


async def atualizar_atividade(atividade_id: str, p: AtividadeUpsert) -> AtividadeListItem:
    uid = _p_uuid(atividade_id)
    async with get_session() as session:
        a = await session.get(Atividade, uid)
        if a is None:
            raise CrmError("Atividade não encontrada.")
        _aplicar_atividade(a, p)
        await session.commit()
        return _atividade_item(
            await session.scalar(select(Atividade).where(Atividade.id == uid))
        )


async def excluir_atividade(atividade_id: str) -> None:
    uid = _p_uuid(atividade_id)
    async with get_session() as session:
        a = await session.get(Atividade, uid)
        if a is None:
            raise CrmError("Atividade não encontrada.")
        await session.delete(a)
        await session.commit()


def _aplicar_projeto(pr: ProjetoCRM, p: ProjetoUpsert) -> None:
    pr.nome = p.nome
    pr.status = p.status
    pr.tipo_servico = p.tipo_servico
    pr.valor_total = p.valor_total
    pr.valor_recebido = p.valor_recebido
    pr.briefing = p.briefing
    pr.link_producao = p.link_producao
    pr.repo_github = p.repo_github
    pr.forma_pagamento = p.forma_pagamento
    pr.prazo_entrega = _p_date(p.prazo_entrega)
    pr.data_inicio = _p_date(p.data_inicio)
    pr.data_entrega_real = _p_date(p.data_entrega_real)
    pr.empresa_id = _p_uuid(p.empresa_id)
    pr.negocio_id = _p_uuid(p.negocio_id)


def _projeto_item(pr: ProjetoCRM) -> ProjetoListItem:
    vt = float(pr.valor_total) if pr.valor_total is not None else None
    vr = float(pr.valor_recebido) if pr.valor_recebido is not None else None
    ar = round((vt or 0) - (vr or 0), 2) if vt is not None else None
    return ProjetoListItem(
        id=str(pr.id), nome=pr.nome, status=pr.status,
        tipo_servico=pr.tipo_servico, valor_total=vt, valor_recebido=vr,
        a_receber=ar, prazo_entrega=_iso(pr.prazo_entrega),
        data_entrega_real=_iso(pr.data_entrega_real),
        link_producao=pr.link_producao, repo_github=pr.repo_github,
        empresa_nome=pr.empresa.nome if pr.empresa is not None else None,
        negocio_nome=pr.negocio.nome if pr.negocio is not None else None,
        briefing=pr.briefing,
    )


async def criar_projeto(p: ProjetoUpsert) -> ProjetoListItem:
    if not p.nome or not p.nome.strip():
        raise CrmError("O projeto precisa de um nome.")
    async with get_session() as session:
        pr = ProjetoCRM()
        _aplicar_projeto(pr, p)
        session.add(pr)
        await session.commit()
        return _projeto_item(
            await session.scalar(select(ProjetoCRM).where(ProjetoCRM.id == pr.id))
        )


async def atualizar_projeto(projeto_id: str, p: ProjetoUpsert) -> ProjetoListItem:
    uid = _p_uuid(projeto_id)
    async with get_session() as session:
        pr = await session.get(ProjetoCRM, uid)
        if pr is None:
            raise CrmError("Projeto não encontrado.")
        _aplicar_projeto(pr, p)
        await session.commit()
        return _projeto_item(
            await session.scalar(select(ProjetoCRM).where(ProjetoCRM.id == uid))
        )


async def excluir_projeto(projeto_id: str) -> None:
    uid = _p_uuid(projeto_id)
    async with get_session() as session:
        pr = await session.get(ProjetoCRM, uid)
        if pr is None:
            raise CrmError("Projeto não encontrado.")
        await session.delete(pr)
        await session.commit()


# ══════════════════════════════════════════════════════════════════
# Ficha 360 — tudo ligado a uma empresa
# ══════════════════════════════════════════════════════════════════

async def empresa_relacionados(empresa_id: str) -> EmpresaRelacionados:
    uid = _p_uuid(empresa_id)
    async with get_session() as session:
        negocios = (
            await session.execute(
                select(Negocio).where(Negocio.empresa_id == uid).order_by(Negocio.nome)
            )
        ).scalars().all()
        projetos = (
            await session.execute(
                select(ProjetoCRM).where(ProjetoCRM.empresa_id == uid)
                .order_by(ProjetoCRM.nome)
            )
        ).scalars().all()
        # Atividades ligadas aos negócios desta empresa.
        neg_ids = [n.id for n in negocios]
        ativs = []
        if neg_ids:
            ativs = (
                await session.execute(
                    select(Atividade).where(Atividade.negocio_id.in_(neg_ids))
                    .order_by(Atividade.data.desc().nullslast())
                )
            ).scalars().all()

    return EmpresaRelacionados(
        negocios=[_to_negocio_item(n) for n in negocios],
        projetos=[_projeto_item(p) for p in projetos],
        atividades=[_atividade_item(a) for a in ativs],
    )


# ══════════════════════════════════════════════════════════════════
# Record universal — navegação relacional bidirecional
# ══════════════════════════════════════════════════════════════════

def _c(label: str, valor, *, campo: str | None = None, kind: str = "text",
       opcoes_key: str | None = None, raw: str | None = None) -> RecordCampo | None:
    """Monta um campo do record. Campos editáveis (campo != None) aparecem mesmo
    vazios (pra preencher no lugar); os não editáveis vazios somem."""
    disp = "" if valor is None else str(valor)
    if campo is None and not disp:
        return None
    return RecordCampo(
        label=label, valor=disp, campo=campo, kind=kind,
        opcoes_key=opcoes_key, raw=(raw if raw is not None else disp),
    )


def _brl(v) -> str | None:
    return f"R$ {float(v):,.2f}" if v is not None else None


def _link_negocio(n: Negocio) -> RecordLink:
    partes = [p for p in [_brl(n.valor_estimado), n.estagio] if p]
    return RecordLink(tipo="negocio", id=str(n.id), nome=n.nome,
                      sub=" · ".join(partes) or None)


def _link_projeto(p: ProjetoCRM) -> RecordLink:
    return RecordLink(tipo="projeto", id=str(p.id), nome=p.nome, sub=p.status)


def _link_atividade(a: Atividade) -> RecordLink:
    partes = [x for x in [a.tipo, a.status] if x]
    return RecordLink(tipo="atividade", id=str(a.id), nome=a.titulo,
                      sub=" · ".join(partes) or None)


def _link_contato(c: Contato) -> RecordLink:
    return RecordLink(tipo="contato", id=str(c.id), nome=c.nome,
                      sub=(c.cargo or None))


async def record_detalhe(tipo: str, registro_id: str) -> RecordDetalhe:  # noqa: C901
    uid = _p_uuid(registro_id)
    async with get_session() as session:
        if tipo == "empresa":
            e = await EmpresaRepository(session).get_by_id(uid)
            if e is None:
                raise CrmError("Empresa não encontrada.")
            negs = (await session.execute(
                select(Negocio).where(Negocio.empresa_id == uid))).scalars().all()
            projs = (await session.execute(
                select(ProjetoCRM).where(ProjetoCRM.empresa_id == uid))).scalars().all()
            ativ = []
            if negs:
                ativ = (await session.execute(select(Atividade).where(
                    Atividade.negocio_id.in_([n.id for n in negs])))).scalars().all()
            campos = [c for c in [
                _c("CNPJ", e.cnpj, campo="cnpj"),
                _c("Status", e.status, campo="status", kind="select",
                   opcoes_key="status"),
                _c("Setor", e.setor, campo="setor", kind="select",
                   opcoes_key="setor"),
                _c("Tamanho", e.tamanho, campo="tamanho", kind="select",
                   opcoes_key="tamanho"),
                _c("Cidade", e.cidade, campo="cidade"),
                _c("Estado", e.estado, campo="estado"),
                _c("Como conheceu", e.como_conheceu, campo="como_conheceu",
                   kind="select", opcoes_key="como_conheceu"),
                _c("Site", e.site, campo="site"),
                _c("Score", e.score, campo="score", kind="num"),
            ] if c]
            grupos = [
                RecordGrupo(titulo="Contatos",
                            itens=[_link_contato(c) for c in e.contatos]),
                RecordGrupo(titulo="Negócios", itens=[_link_negocio(n) for n in negs]),
                RecordGrupo(titulo="Projetos", itens=[_link_projeto(p) for p in projs]),
                RecordGrupo(titulo="Atividades",
                            itens=[_link_atividade(a) for a in ativ]),
            ]
            return RecordDetalhe(tipo="empresa", id=str(e.id), titulo=e.nome,
                                 campos=campos, grupos=grupos, notas=e.notas)

        if tipo == "contato":
            c = await session.scalar(
                select(Contato)
                .where(Contato.id == uid)
                .options(selectinload(Contato.empresa)))
            if c is None:
                raise CrmError("Contato não encontrado.")
            negs = (await session.execute(
                select(Negocio).where(Negocio.contato_id == uid))).scalars().all()
            ativ = (await session.execute(
                select(Atividade).where(Atividade.contato_id == uid))).scalars().all()
            campos = [x for x in [
                _c("Cargo", c.cargo, campo="cargo"),
                _c("Decisor", "Sim" if c.decisor else "Não", campo="decisor",
                   kind="bool", raw=("true" if c.decisor else "false")),
                _c("E-mail", c.email, campo="email"),
                _c("Telefone", c.telefone, campo="telefone"),
                _c("WhatsApp", c.whatsapp, campo="whatsapp"),
                _c("LinkedIn", c.linkedin, campo="linkedin"),
                _c("Origem", c.origem_contato, campo="origem_contato",
                   kind="select", opcoes_key="origem_contato"),
            ] if x]
            grupos = []
            if c.empresa is not None:
                grupos.append(RecordGrupo(titulo="Empresa", itens=[RecordLink(
                    tipo="empresa", id=str(c.empresa.id), nome=c.empresa.nome,
                    sub=c.empresa.setor)]))
            grupos.append(RecordGrupo(titulo="Negócios",
                                      itens=[_link_negocio(n) for n in negs]))
            grupos.append(RecordGrupo(titulo="Atividades",
                                      itens=[_link_atividade(a) for a in ativ]))
            return RecordDetalhe(tipo="contato", id=str(c.id), titulo=c.nome,
                                 campos=campos, grupos=grupos)

        if tipo == "negocio":
            n = await _recarregar_negocio(session, uid)
            if n is None:
                raise CrmError("Negócio não encontrado.")
            projs = (await session.execute(
                select(ProjetoCRM).where(ProjetoCRM.negocio_id == uid))).scalars().all()
            ativ = (await session.execute(
                select(Atividade).where(Atividade.negocio_id == uid))).scalars().all()
            campos = [x for x in [
                _c("Estágio", n.estagio, campo="estagio", kind="select",
                   opcoes_key="estagio"),
                _c("Valor", _brl(n.valor_estimado), campo="valor_estimado",
                   kind="num",
                   raw=(str(n.valor_estimado) if n.valor_estimado is not None else "")),
                _c("Probabilidade", n.probabilidade, campo="probabilidade",
                   kind="select", opcoes_key="probabilidade"),
                _c("Tipo de serviço", ", ".join(n.tipo_servico or [])),
                _c("Origem", n.origem, campo="origem", kind="select",
                   opcoes_key="origem_negocio"),
                _c("Previsão", _iso(n.previsao_fechamento),
                   campo="previsao_fechamento", kind="date"),
                _c("Próxima ação", _iso(n.proxima_acao), campo="proxima_acao",
                   kind="date"),
            ] if x]
            grupos = []
            if n.empresa is not None:
                grupos.append(RecordGrupo(titulo="Empresa", itens=[RecordLink(
                    tipo="empresa", id=str(n.empresa.id), nome=n.empresa.nome,
                    sub=n.empresa.setor)]))
            if n.contato is not None:
                grupos.append(RecordGrupo(titulo="Contato principal",
                                          itens=[_link_contato(n.contato)]))
            grupos.append(RecordGrupo(titulo="Projetos",
                                      itens=[_link_projeto(p) for p in projs]))
            grupos.append(RecordGrupo(titulo="Atividades",
                                      itens=[_link_atividade(a) for a in ativ]))
            return RecordDetalhe(tipo="negocio", id=str(n.id), titulo=n.nome,
                                 campos=campos, grupos=grupos, notas=n.notas)

        if tipo == "projeto":
            p = await session.scalar(
                select(ProjetoCRM).where(ProjetoCRM.id == uid))
            if p is None:
                raise CrmError("Projeto não encontrado.")
            ar = None
            if p.valor_total is not None:
                ar = _brl(float(p.valor_total) - float(p.valor_recebido or 0))
            campos = [x for x in [
                _c("Status", p.status, campo="status", kind="select",
                   opcoes_key="projeto_status"),
                _c("Tipo", p.tipo_servico, campo="tipo_servico", kind="select",
                   opcoes_key="tipo_servico"),
                _c("Valor total", _brl(p.valor_total), campo="valor_total",
                   kind="num",
                   raw=(str(float(p.valor_total)) if p.valor_total is not None else "")),
                _c("Recebido", _brl(p.valor_recebido), campo="valor_recebido",
                   kind="num",
                   raw=(str(float(p.valor_recebido))
                        if p.valor_recebido is not None else "")),
                _c("A receber", ar),
                _c("Forma pagamento", p.forma_pagamento, campo="forma_pagamento",
                   kind="select", opcoes_key="forma_pagamento"),
                _c("Prazo", _iso(p.prazo_entrega), campo="prazo_entrega",
                   kind="date"),
                _c("Entrega real", _iso(p.data_entrega_real),
                   campo="data_entrega_real", kind="date"),
                _c("Link produção", p.link_producao, campo="link_producao"),
                _c("Repo", p.repo_github, campo="repo_github"),
            ] if x]
            grupos = []
            if p.empresa is not None:
                grupos.append(RecordGrupo(titulo="Empresa", itens=[RecordLink(
                    tipo="empresa", id=str(p.empresa.id), nome=p.empresa.nome,
                    sub=p.empresa.setor)]))
            if p.negocio is not None:
                grupos.append(RecordGrupo(titulo="Negócio origem",
                                          itens=[_link_negocio(p.negocio)]))
            return RecordDetalhe(tipo="projeto", id=str(p.id), titulo=p.nome,
                                 campos=campos, grupos=grupos, notas=p.briefing)

        if tipo == "atividade":
            a = await session.scalar(
                select(Atividade).where(Atividade.id == uid))
            if a is None:
                raise CrmError("Atividade não encontrada.")
            campos = [x for x in [
                _c("Tipo", a.tipo, campo="tipo", kind="select",
                   opcoes_key="atividade_tipo"),
                _c("Status", a.status, campo="status", kind="select",
                   opcoes_key="atividade_status"),
                _c("Quando", a.data.isoformat() if a.data else None, campo="data",
                   kind="date", raw=(a.data.date().isoformat() if a.data else "")),
                _c("Resumo", a.resumo, campo="resumo"),
                _c("Próximos passos", a.proximos_passos, campo="proximos_passos"),
            ] if x]
            grupos = []
            if a.negocio is not None:
                grupos.append(RecordGrupo(titulo="Negócio",
                                          itens=[_link_negocio(a.negocio)]))
            if a.contato is not None:
                grupos.append(RecordGrupo(titulo="Contato",
                                          itens=[_link_contato(a.contato)]))
            return RecordDetalhe(tipo="atividade", id=str(a.id), titulo=a.titulo,
                                 campos=campos, grupos=grupos)

    raise CrmError(f"Tipo desconhecido: {tipo}")


# ── Edição parcial (inline) ──────────────────────────────────────────
# Allowlist de campos editáveis por tipo + como coagir cada um. FKs ("uuid")
# e datas reaproveitam os parsers do CRUD. Campos NOT NULL no banco são
# "str_req" (não podem ficar vazios).

_CAMPOS_EDITAVEIS: dict[str, dict[str, str]] = {
    "empresa": {
        "nome": "str_req", "razao_social": "str", "cnpj": "str",
        "cidade": "str", "estado": "str", "site": "str", "instagram": "str",
        "facebook": "str", "setor": "str", "tamanho": "str", "score": "int",
        "como_conheceu": "str_req", "status": "str_req", "notas": "str",
    },
    "contato": {
        "nome": "str_req", "cargo": "str", "decisor": "bool", "email": "str",
        "telefone": "str", "whatsapp": "str", "linkedin": "str",
        "origem_contato": "str_req", "empresa_id": "uuid",
    },
    "negocio": {
        "nome": "str_req", "estagio": "str", "valor_estimado": "num",
        "probabilidade": "str", "origem": "str", "tipo_servico": "list",
        "notas": "str", "motivo_perda": "str", "previsao_fechamento": "date",
        "data_fechamento_real": "date", "proxima_acao": "date",
        "empresa_id": "uuid", "contato_id": "uuid",
    },
    "projeto": {
        "nome": "str_req", "status": "str", "tipo_servico": "str",
        "valor_total": "num", "valor_recebido": "num", "briefing": "str",
        "link_producao": "str", "repo_github": "str", "forma_pagamento": "str",
        "prazo_entrega": "date", "data_inicio": "date",
        "data_entrega_real": "date", "empresa_id": "uuid", "negocio_id": "uuid",
    },
    "atividade": {
        "titulo": "str_req", "tipo": "str", "status": "str", "data": "datetime",
        "resumo": "str", "proximos_passos": "str", "negocio_id": "uuid",
        "contato_id": "uuid",
    },
}

_MODELO_POR_TIPO = {
    "empresa": Empresa, "contato": Contato, "negocio": Negocio,
    "projeto": ProjetoCRM, "atividade": Atividade,
}


def _coagir(kind: str, valor, campo: str):
    if kind == "bool":
        return bool(valor)
    if kind == "list":
        if valor is None:
            return []
        if not isinstance(valor, list):
            raise CrmError(f"{campo} espera uma lista.")
        return [str(x) for x in valor]
    vazio = valor is None or (isinstance(valor, str) and not valor.strip())
    if vazio:
        if kind == "str_req":
            raise CrmError(f"O campo '{campo}' não pode ficar vazio.")
        return None
    if kind in ("str", "str_req"):
        return str(valor).strip()
    if kind == "int":
        try:
            return int(valor)
        except (ValueError, TypeError) as e:
            raise CrmError(f"'{campo}': número inteiro inválido.") from e
    if kind == "num":
        try:
            return float(valor)
        except (ValueError, TypeError) as e:
            raise CrmError(f"'{campo}': número inválido.") from e
    if kind == "date":
        return _p_date(str(valor))
    if kind == "datetime":
        return _p_datetime(str(valor))
    if kind == "uuid":
        return _p_uuid(str(valor))
    raise CrmError(f"Tipo de campo desconhecido: {kind}")


async def patch_record(tipo: str, registro_id: str, campos: dict) -> RecordDetalhe:
    editaveis = _CAMPOS_EDITAVEIS.get(tipo)
    modelo = _MODELO_POR_TIPO.get(tipo)
    if editaveis is None or modelo is None:
        raise CrmError(f"Tipo desconhecido: {tipo}")
    if not campos:
        raise CrmError("Nada a alterar.")
    uid = _p_uuid(registro_id)
    async with get_session() as session:
        obj = await session.get(modelo, uid)
        if obj is None:
            raise CrmError(f"{tipo.capitalize()} não encontrado.")
        for campo, valor in campos.items():
            if campo not in editaveis:
                raise CrmError(f"Campo não editável: {campo}")
            setattr(obj, campo, _coagir(editaveis[campo], valor, campo))
        await session.commit()

    # Memória compartilhada (MAS-1): registra a edição na linha do tempo do alvo.
    partes = ", ".join(f"{k} = {v}" for k, v in campos.items() if v not in (None, ""))
    await memoria_service.registrar(
        agente="crm", alvo_tipo=tipo, alvo_id=registro_id, tipo="edicao",
        resumo=f"Editou {partes}" if partes else "Limpou campo(s)",
        payload={"campos": campos}, origem="manual",
    )
    return await record_detalhe(tipo, registro_id)


# ══════════════════════════════════════════════════════════════════
# Dashboard comercial
# ══════════════════════════════════════════════════════════════════

def _atividade_concluida(status: str | None) -> bool:
    if not status:
        return False
    s = status.lower()
    return "✅" in status or "feita" in s or "conclu" in s or "realizada" in s


async def dashboard() -> CrmDashboard:
    from datetime import datetime
    agora = datetime.now()

    async with get_session() as session:
        negocios = (await session.execute(select(Negocio))).scalars().all()
        ativs = (await session.execute(select(Atividade))).scalars().all()
        projs = (await session.execute(select(ProjetoCRM))).scalars().all()
        empresas = await EmpresaRepository(session).listar_todas()
        ordem_estagio = await _ordem_grupo(session, "estagio")

    # Pipeline (ignora ganhos/perdidos do "aberto")
    por_est: dict[str, list[float]] = {}
    pipe_val = pipe_pond = 0.0
    abertos = 0
    for n in negocios:
        val = float(n.valor_estimado) if n.valor_estimado is not None else 0.0
        est = n.estagio or _SEM_ESTAGIO
        por_est.setdefault(est, []).append(val)
        fechado = est and ("Ganho" in est or "Perdido" in est)
        if not fechado:
            abertos += 1
            pipe_val += val
            pipe_pond += val * _frac_prob(n.probabilidade)
    conhecidas = [s for s in ordem_estagio if s in por_est]
    resto = [s for s in por_est if s not in ordem_estagio]
    por_estagio = [
        EstagioResumo(estagio=e, total=len(por_est[e]), valor=round(sum(por_est[e]), 2))
        for e in conhecidas + resto
    ]

    pendentes = atrasadas = 0
    for a in ativs:
        if _atividade_concluida(a.status):
            continue
        pendentes += 1
        if a.data is not None and a.data < agora:
            atrasadas += 1

    p_total = p_receb = 0.0
    for p in projs:
        p_total += float(p.valor_total) if p.valor_total is not None else 0.0
        p_receb += float(p.valor_recebido) if p.valor_recebido is not None else 0.0

    clientes = sum(1 for e in empresas if e.status and "Cliente" in e.status)
    contatos = sum(len(e.contatos) for e in empresas)

    return CrmDashboard(
        pipeline_valor=round(pipe_val, 2),
        pipeline_ponderado=round(pipe_pond, 2),
        negocios_abertos=abertos,
        por_estagio=por_estagio,
        atividades_total=len(ativs),
        atividades_pendentes=pendentes,
        atividades_atrasadas=atrasadas,
        projetos_total=len(projs),
        projetos_valor_total=round(p_total, 2),
        projetos_recebido=round(p_receb, 2),
        projetos_a_receber=round(p_total - p_receb, 2),
        empresas_total=len(empresas),
        clientes_ativos=clientes,
        contatos_total=contatos,
    )
