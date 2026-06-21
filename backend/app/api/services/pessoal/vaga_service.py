"""Service de Vagas — registro (Fase 1), análise+match (Fase 2/3) e
geração de candidatura (Fase 4). PARA no rascunho: nada aqui envia e-mail.
"""
from __future__ import annotations

import asyncio
import re
import unicodedata
import uuid
from collections import Counter

from app.analyzers.candidatura.parser import parse_resposta as parse_candidatura
from app.analyzers.candidatura.prompt_builder import (
    construir_prompt as construir_prompt_candidatura,
)
from app.analyzers.curriculo.parser import parse_resposta as parse_curriculo
from app.analyzers.curriculo.prompt_builder import (
    construir_prompt as construir_prompt_curriculo,
)
from app.analyzers.llm_provider import gerar_texto
from app.analyzers.vaga.parser import parse_resposta as parse_vaga
from app.analyzers.vaga.prompt_builder import (
    construir_prompt as construir_prompt_vaga,
)
from app.analyzers.vaga.extrator.parser import parse_resposta as parse_extracao
from app.analyzers.vaga.extrator.prompt_builder import (
    construir_prompt as construir_prompt_extracao,
)
from app.api.schemas.pessoal import (
    AnalisarVagaResponse,
    AnaliseVaga,
    CandidaturaEmailItem,
    CurriculoVaga,
    EmailCandidatura,
    EstudoVagasResponse,
    ExtrairVagaResponse,
    GerarCandidaturaRequest,
    GerarCandidaturaResponse,
    GerarCurriculoResponse,
    MatchVaga,
    SkillEstudo,
    VagaCreate,
    VagaListItem,
    VagaListResponse,
    VagaResponse,
    VagasMetricas,
    VagaUpdate,
)
from app.api.services._helpers import iso as _iso
from app.api.services._helpers import parse_uuid
from app.api.services.pessoal.perfil_service import get_perfil
from app.collectors.website.pagina import texto_de_url
from app.db.models.pessoal.vaga import Vaga
from app.db.session import get_session
from app.repositories.pessoal.vaga_repository import VagaRepository
from app.utils.logger import get_logger

logger = get_logger()


class VagaError(Exception):
    """Erro de negócio de Vagas — vira HTTP 400 no router."""


def _uuid(valor: str) -> uuid.UUID:
    return parse_uuid(valor, erro=VagaError, label="id de vaga")


def _to_response(v: Vaga) -> VagaResponse:
    return VagaResponse(
        id=str(v.id),
        titulo=v.titulo,
        empresa=v.empresa,
        link=v.link,
        fonte=v.fonte,
        contato_nome=v.contato_nome,
        contato_email=v.contato_email,
        localizacao=v.localizacao,
        modelo=v.modelo,
        senioridade=v.senioridade,
        descricao=v.descricao,
        notas=v.notas,
        status=v.status,
        analise_json=v.analise_json,        # pydantic coage dict→AnaliseVaga
        match_json=v.match_json,
        match_score=v.match_score,
        curriculo=v.curriculo_json,         # pydantic coage dict→CurriculoVaga
        curriculo_gerado_em=_iso(v.curriculo_gerado_em),
        created_at=_iso(v.created_at),
        updated_at=_iso(v.updated_at),
    )


# ── CRUD ─────────────────────────────────────────────────────────

async def criar_vaga(payload: VagaCreate) -> VagaResponse:
    if not payload.titulo.strip():
        raise VagaError("A vaga precisa de um título.")
    if not payload.descricao.strip():
        raise VagaError("Cole a descrição da vaga.")

    async with get_session() as session:
        vaga = await VagaRepository(session).create(payload.model_dump())
        return _to_response(vaga)


async def extrair_vaga(
    texto: str | None = None, url: str | None = None
) -> ExtrairVagaResponse:
    """Campos pré-preenchidos a partir do texto colado OU da URL (não salva).

    Com URL, busca a página (httpx/Playwright, em thread por ser bloqueante) e
    usa o texto visível como fonte. Devolve `descricao` (texto-fonte) e `link`
    pra o form já guardar a origem.
    """
    url = (url or "").strip() or None
    texto = (texto or "").strip() or None
    if not texto and not url:
        raise VagaError("Cole o texto da vaga ou informe a URL.")

    if not texto and url:
        texto = await asyncio.to_thread(texto_de_url, url)
        if not texto:
            raise VagaError(
                "Não consegui ler a página dessa URL. Cole o texto da vaga na mão."
            )

    prompt = construir_prompt_extracao(texto)
    resposta = _chamar_llm(prompt, agente="vaga", operacao="extrair")
    dados = parse_extracao(resposta)
    if dados is None:
        raise VagaError("A IA não conseguiu extrair os campos. Preencha na mão.")
    dados.descricao = texto
    dados.link = url
    return dados


async def listar_vagas(
    status: str | None = None,
    *,
    busca: str | None = None,
    match_min: int | None = None,
    modelo: str | None = None,
    fonte: str | None = None,
    tem_rascunho: bool | None = None,
    ordenar_por: str = "match",
) -> VagaListResponse:
    async with get_session() as session:
        linhas = await VagaRepository(session).listar(
            status=status,
            busca=busca,
            match_min=match_min,
            modelo=modelo,
            fonte=fonte,
            tem_rascunho=tem_rascunho,
            ordenar_por=ordenar_por,
        )
        items = [
            VagaListItem(
                id=str(v.id),
                titulo=v.titulo,
                empresa=v.empresa,
                status=v.status,
                modelo=v.modelo,
                senioridade=v.senioridade,
                match_score=v.match_score,
                tem_analise=v.analise_json is not None,
                tem_curriculo=v.curriculo_json is not None,
                qtd_rascunhos=qtd,
                created_at=_iso(v.created_at),
            )
            for v, qtd in linhas
        ]
    return VagaListResponse(items=items, total=len(items))


async def metricas() -> VagasMetricas:
    """Funil + taxas de resposta/entrevista pra medir se você está sendo efetivo."""
    async with get_session() as session:
        dados = await VagaRepository(session).metricas()

    ps = dados["por_status"]
    candidaturas = ps["candidatei"] + ps["respondeu"] + ps["entrevista"] + ps["fim"]
    em_andamento = ps["candidatei"] + ps["respondeu"] + ps["entrevista"]
    responderam = ps["respondeu"] + ps["entrevista"]
    entrevistas = ps["entrevista"]

    def _pct(parte: int, todo: int) -> int | None:
        return round(parte * 100 / todo) if todo else None

    def _round(v) -> int | None:
        return round(v) if v is not None else None

    return VagasMetricas(
        total=sum(ps.values()),
        por_status=ps,
        candidaturas=candidaturas,
        em_andamento=em_andamento,
        responderam=responderam,
        entrevistas=entrevistas,
        taxa_resposta=_pct(responderam, em_andamento),
        taxa_entrevista=_pct(entrevistas, em_andamento),
        match_medio=_round(dados["match_medio"]),
        match_medio_candidaturas=_round(dados["match_medio_candidaturas"]),
    )


# Apelidos comuns → forma canônica (já normalizada: minúscula, sem ponto/acento).
_SKILL_ALIAS = {
    "reactjs": "react",
    "nextjs": "next",
    "nodejs": "node",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "tailwindcss": "tailwind",
    # dedup de variações que apareciam como linhas separadas no ranking
    "github action": "github actions",
    "apis": "api rest",
    "apis rest": "api rest",
    "api": "api rest",
    "rest api": "api rest",
    "bancos de dados relacionais": "bancos relacionais",
    "banco de dados relacional": "bancos relacionais",
    "bancos de dados nao relacionais": "bancos nao relacionais",
    "banco de dados nao relacional": "bancos nao relacionais",
    "apache airflow": "airflow",
}

# "Cobre": skill do perfil (forma canônica) que JÁ satisfaz outras pedidas pelas
# vagas — evita falso-gap por sinônimo/idioma/derivação (quem usa PostgreSQL sabe
# SQL; quem integra LLMs sabe usar Claude/Gemini; "engenharia de prompt"≈"prompt
# engineering"). Chave = forma do perfil; valores = formas (de vaga) que ela cobre.
_COBRE = {
    "postgresql": {"sql", "bancos relacionais", "modelagem de dados", "bancos de dados"},
    "sqlalchemy": {"sql", "orm"},
    "typescript": {"javascript"},
    "fastapi": {"api rest", "rest", "openapi", "swagger"},
    "engenharia de prompt": {"prompt engineering", "prompt"},
    "integracao com llms": {
        "llm", "llms", "ia", "ia generativa", "inteligencia artificial",
        "claude", "chatgpt", "gpt 4", "gemini", "anthropic", "openai", "copilot",
        "ai agents", "agentes", "llm apis",
    },
    "machine learning": {"ml", "modelos preditivos", "classificacao", "regressao"},
    "docker": {"docker compose", "containers", "conteineres"},
    "git": {"github", "controle de versao", "versionamento", "gitlab"},
    "web scraping": {"scraping", "automacao"},
    "deploy em vps": {"linux", "ssh"},
    "testes": {"pytest", "testes automatizados"},
}

# Termos que denunciam frase de requisito / soft-skill (não é tecnologia p/ estudar).
_NAO_SKILL = (
    "conhecimento", "experiencia", "experiência", "capacidade", "habilidade",
    "ensino superior", "anos de", "anos com", "boa ", "boas ", "vivencia",
    "comunicacao", "trabalho em equipe", "proativ", "ferramentas", "raciocinio",
)


def _norm_skill(s: str) -> str:
    """Normaliza nome de skill pra agregar variações ('React.js'≈'react').
    Tira o parêntese descritivo ('IA (Inteligência Artificial)'→'ia')."""
    s = re.sub(r"\(.*?\)", " ", s)
    t = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    t = t.lower().replace(".", "").strip()
    t = re.sub(r"[^a-z0-9+# ]", " ", t)   # mantém + e # (c++, c#); resto vira espaço
    t = re.sub(r"\s+", " ", t).strip()
    return _SKILL_ALIAS.get(t, t)


_SEPS = re.compile(r"[/+,&]")


def _formas_perfil(s: str) -> set[str]:
    """Formas que uma skill do perfil cobre. Separa a cabeça do parêntese
    ('Git (commits…)'→'git') mas TAMBÉM aproveita o que há dentro dele, que às
    vezes são tools de verdade ('… (Playwright, BeautifulSoup)', '(JWT, RBAC)'),
    e quebra compostos ('Docker / docker-compose', 'Gemini/Groq/Ollama')."""
    sem_paren = re.sub(r"\(.*?\)", " ", s)
    dentro = " , ".join(re.findall(r"\((.*?)\)", s))   # conteúdo dos parênteses
    formas = {_norm_skill(s)}
    for bloco in (sem_paren, dentro):
        for parte in _SEPS.split(bloco):
            formas.add(_norm_skill(parte))
    formas.discard("")
    return formas


def _norm_text(s: str) -> str:
    """Normaliza uma FRASE de requisito p/ busca (mantém o que está em parêntese,
    ex.: '(ex.: Airflow ou similares)' continua tendo 'airflow')."""
    t = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    t = t.lower().replace(".", " ")
    t = re.sub(r"[^a-z0-9+# ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _word_in(texto_norm: str, termo: str) -> bool:
    """`termo` aparece como palavra inteira em `texto_norm` (ambos normalizados)."""
    if not termo:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(termo)}(?![a-z0-9])", texto_norm) is not None


def _eh_skill(s: str) -> bool:
    """Tag de stack que é tecnologia de fato (descarta frase/soft-skill vaga)."""
    nk = _norm_skill(s)
    if not nk or len(nk.split()) > 5:
        return False
    return not any(p in nk for p in _NAO_SKILL)


async def estudo_gaps() -> EstudoVagasResponse:
    """Agrega as skills pedidas por TODAS as vagas analisadas e cruza com o perfil.

    Skills saem do `stack` (tags limpas); as frases de `requisitos_obrigatorios`
    servem só pra marcar a obrigatoriedade de cada tag (busca por palavra inteira).
    Resultado: o que a maioria pede e você ainda NÃO tem + seus pontos fortes.
    """
    perfil = await get_perfil()
    async with get_session() as session:
        vagas = await VagaRepository(session).listar_com_analise()

    total = len(vagas)
    if total == 0:
        return EstudoVagasResponse(total_vagas=0)

    # Skills que você JÁ tem (perfil): habilidades + stacks de projetos + alvo —
    # com parênteses/compostos quebrados e expandido pelos sinônimos de _COBRE.
    tenho: set[str] = set()
    if perfil is not None:
        for h in perfil.habilidades:
            tenho |= _formas_perfil(h.nome)
        for pr in perfil.projetos:
            for s in pr.stack or []:
                tenho |= _formas_perfil(s)
        if perfil.o_que_procuro:
            for s in perfil.o_que_procuro.stack or []:
                tenho |= _formas_perfil(s)
    for base, cobre in _COBRE.items():
        if base in tenho:
            tenho |= cobre
    tenho.discard("")

    n_vagas: Counter = Counter()        # norm -> nº de vagas em que aparece (no stack)
    obrig: Counter = Counter()          # norm -> nº de vagas em que é OBRIGATÓRIA
    formas: dict[str, Counter] = {}     # norm -> contagem das formas originais (display)

    for v in vagas:
        a = v.analise_json or {}
        obrig_txt = " / ".join(
            _norm_text(x) for x in (a.get("requisitos_obrigatorios") or [])
        )
        # uma skill conta UMA vez por vaga
        na_vaga: dict[str, str] = {}
        for x in a.get("stack") or []:
            if isinstance(x, str) and _eh_skill(x):
                nk = _norm_skill(x)
                if nk:
                    na_vaga.setdefault(nk, x)
        for nk, orig in na_vaga.items():
            n_vagas[nk] += 1
            formas.setdefault(nk, Counter())[orig] += 1
            if _word_in(obrig_txt, nk):
                obrig[nk] += 1

    def _mk(nk: str) -> SkillEstudo:
        disp = formas[nk].most_common(1)[0][0]
        return SkillEstudo(
            skill=disp,
            n_vagas=n_vagas[nk],
            pct_vagas=round(n_vagas[nk] * 100 / total),
            obrigatoria_em=obrig[nk],
            tenho=nk in tenho,
        )

    itens = [_mk(nk) for nk in n_vagas]
    para_estudar = sorted(
        (i for i in itens if not i.tenho),
        key=lambda i: (-i.n_vagas, -i.obrigatoria_em, i.skill.lower()),
    )
    pontos_fortes = sorted(
        (i for i in itens if i.tenho),
        key=lambda i: (-i.n_vagas, i.skill.lower()),
    )[:12]
    return EstudoVagasResponse(
        total_vagas=total,
        para_estudar=para_estudar,
        pontos_fortes=pontos_fortes,
    )


async def get_vaga(vaga_id: str) -> VagaResponse:
    async with get_session() as session:
        vaga = await VagaRepository(session).get(_uuid(vaga_id))
        if vaga is None:
            raise VagaError("Vaga não encontrada.")
        return _to_response(vaga)


async def atualizar_vaga(vaga_id: str, payload: VagaUpdate) -> VagaResponse:
    dados = payload.model_dump(exclude_unset=True)
    async with get_session() as session:
        vaga = await VagaRepository(session).update(_uuid(vaga_id), dados)
        if vaga is None:
            raise VagaError("Vaga não encontrada.")
        return _to_response(vaga)


async def deletar_vaga(vaga_id: str) -> bool:
    async with get_session() as session:
        ok = await VagaRepository(session).delete(_uuid(vaga_id))
        if not ok:
            raise VagaError("Vaga não encontrada.")
        return True


# ── IA: análise + match (Fase 2/3) ───────────────────────────────

async def analisar_vaga(vaga_id: str) -> AnalisarVagaResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise VagaError(
            "Cadastre seu Perfil Mestre antes de analisar vagas — "
            "a análise cruza a vaga com quem você é."
        )

    async with get_session() as session:
        repo = VagaRepository(session)
        vaga = await repo.get(_uuid(vaga_id))
        if vaga is None:
            raise VagaError("Vaga não encontrada.")

        prompt = construir_prompt_vaga(
            vaga.descricao, perfil, titulo=vaga.titulo, empresa=vaga.empresa
        )
        texto = _chamar_llm(prompt, agente="vaga", operacao="analisar")

        resultado = parse_vaga(texto)
        if resultado is None:
            raise VagaError("A IA não retornou uma análise válida. Tente de novo.")
        analise, match = resultado

        await repo.salvar_analise(
            _uuid(vaga_id),
            analise.model_dump(mode="json"),
            match.model_dump(mode="json"),
            match.aderencia,
        )

    return AnalisarVagaResponse(
        analise=analise, match=match, match_score=match.aderencia
    )


# ── IA: geração de candidatura (Fase 4) ──────────────────────────

async def gerar_candidatura(
    vaga_id: str, payload: GerarCandidaturaRequest
) -> GerarCandidaturaResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise VagaError(
            "Cadastre seu Perfil Mestre antes — sem ele a carta sai genérica."
        )

    async with get_session() as session:
        repo = VagaRepository(session)
        vaga = await repo.get(_uuid(vaga_id))
        if vaga is None:
            raise VagaError("Vaga não encontrada.")

        analise = AnaliseVaga(**vaga.analise_json) if vaga.analise_json else None
        match = MatchVaga(**vaga.match_json) if vaga.match_json else None

        prompt = construir_prompt_candidatura(
            perfil,
            titulo=vaga.titulo,
            empresa=vaga.empresa,
            analise=analise,
            match=match,
            gerar_carta=payload.gerar_carta,
            instrucoes_extra=payload.instrucoes_extra,
        )
        texto = _chamar_llm(prompt, agente="candidatura", operacao="gerar")

        resultado = parse_candidatura(texto)
        if resultado is None:
            raise VagaError("A IA não retornou um rascunho válido. Tente de novo.")

        # Persiste o rascunho — status nasce 'rascunho'. Envio é manual.
        contexto = {
            "match_score": vaga.match_score,
            "instrucoes_extra": payload.instrucoes_extra,
        }
        email_row = await repo.add_email({
            "vaga_id": vaga.id,
            "tipo": "email",
            "destinatario": vaga.contato_email,
            "assunto": resultado.email.assunto,
            "corpo": resultado.email.corpo,
            "tom": resultado.email.tom,
            "status": "rascunho",
            "variantes": [v.model_dump(mode="json") for v in resultado.variantes_email],
            "contexto": contexto,
        })

        if resultado.carta:
            await repo.add_email({
                "vaga_id": vaga.id,
                "tipo": "carta",
                "destinatario": vaga.contato_email,
                "corpo": resultado.carta.corpo,
                "tom": resultado.carta.tom,
                "status": "rascunho",
                "contexto": contexto,
            })

        resultado.rascunho_id = str(email_row.id)

    logger.info("Candidatura: rascunho gerado pra vaga %s", vaga_id)
    return resultado


# ── IA: currículo sob medida pra vaga (gera PDF no front) ─────────

async def gerar_curriculo(vaga_id: str) -> GerarCurriculoResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise VagaError(
            "Cadastre seu Perfil Mestre antes — o currículo é montado a partir dele."
        )

    async with get_session() as session:
        repo = VagaRepository(session)
        vaga = await repo.get(_uuid(vaga_id))
        if vaga is None:
            raise VagaError("Vaga não encontrada.")

        prompt = construir_prompt_curriculo(
            perfil,
            vaga.descricao,
            titulo_vaga=vaga.titulo,
            empresa=vaga.empresa,
            analise_json=vaga.analise_json,
            match_json=vaga.match_json,
        )
        texto = _chamar_llm(prompt, agente="curriculo", operacao="gerar")

    llm = parse_curriculo(texto)
    if llm is None:
        raise VagaError("A IA não retornou um currículo válido. Tente de novo.")

    # Links de projeto são factuais: vêm do perfil, não do que o LLM escreveu.
    links_perfil = {
        (p.nome or "").strip().lower(): p.link
        for p in perfil.projetos
        if p.link
    }
    for proj in llm.projetos:
        proj.link = links_perfil.get((proj.nome or "").strip().lower())

    # Dados factuais saem do perfil, NUNCA do LLM (anti-mentira).
    curriculo = CurriculoVaga(
        nome=perfil.nome,
        titulo=llm.titulo or perfil.titulo,
        contato=perfil.contato,
        resumo=llm.resumo or perfil.resumo,
        competencias=llm.competencias,
        experiencias=llm.experiencias,
        projetos=llm.projetos,
        formacao=perfil.formacao,
    )

    # Persiste pra não regerar (gasta LLM) toda vez que reabrir a vaga.
    async with get_session() as session:
        vaga = await VagaRepository(session).salvar_curriculo(
            _uuid(vaga_id), curriculo.model_dump(mode="json")
        )
        gerado_em = _iso(vaga.curriculo_gerado_em) if vaga else None

    logger.info("Currículo: gerado e salvo pra vaga %s", vaga_id)
    return GerarCurriculoResponse(
        vaga_id=vaga_id, curriculo=curriculo, gerado_em=gerado_em
    )


async def listar_rascunhos(vaga_id: str) -> list[CandidaturaEmailItem]:
    async with get_session() as session:
        rows = await VagaRepository(session).listar_emails(_uuid(vaga_id))
        return [
            CandidaturaEmailItem(
                id=str(r.id),
                vaga_id=str(r.vaga_id),
                tipo=r.tipo,
                destinatario=r.destinatario,
                assunto=r.assunto,
                corpo=r.corpo,
                tom=r.tom,
                status=r.status,
                variantes=[EmailCandidatura(**v) for v in (r.variantes or [])],
                created_at=_iso(r.created_at),
            )
            for r in rows
        ]


# ── helper LLM ───────────────────────────────────────────────────

def _chamar_llm(prompt: str, *, agente: str, operacao: str) -> str:
    try:
        return gerar_texto(
            prompt, json_mode=True, agente=agente, operacao=operacao
        )
    except Exception as e:
        logger.error("%s: falha na LLM: %s", agente, e)
        raise VagaError(
            "Não consegui falar com o modelo de IA. "
            "Verifique a conexão/configuração e tente de novo."
        )
