import sys
import traceback
from datetime import datetime
from typing import Optional


def test_conexao():
    """Testa só a conexão com o Notion (sem criar nada)."""
    from app.exporters.notion import NotionExporter
    from app.utils.logger import get_logger

    logger = get_logger()
    logger.info("🔌 Testando conexão com o Notion...")

    exporter = NotionExporter()
    me = exporter.client.users.me()
    logger.success(f"✅ Conexão OK! Bot: {me.get('name', 'sem nome')}")
    logger.info(f"   ID do bot: {me.get('id', 'sem id')}")

    logger.info("📋 Testando acesso aos databases...")
    db_emp = exporter.client.databases.retrieve(database_id=exporter.db_empresas)
    title_emp = db_emp.get("title", [{}])
    logger.success(
        f"✅ Database Empresas OK: "
        f"{title_emp[0].get('plain_text', '?') if title_emp else '?'}"
    )

    db_con = exporter.client.databases.retrieve(database_id=exporter.db_contatos)
    title_con = db_con.get("title", [{}])
    logger.success(
        f"✅ Database Contatos OK: "
        f"{title_con[0].get('plain_text', '?') if title_con else '?'}"
    )


def test_notion():
    """
    Cria um Lead de teste e envia pro Notion.
    Salva em data/processed/ e move pra data/sent/ depois.
    """
    from app.exporters.notion import NotionExporter
    from backend.app.db.models.lead import Contato, Empresa, Lead, Socio
    from app.utils.logger import get_logger
    from app.utils.storage import save_lead

    logger = get_logger()
    logger.info("=" * 60)
    logger.info("🧪 TESTE DE INTEGRAÇÃO — FASE 1")
    logger.info("=" * 60)

    empresa = Empresa(
        nome="Padaria do Zé (TESTE)",
        razao_social="Padaria do Zé Ltda",
        cnpj="12345678000199",
        capital_social=50000.00,
        cidade="Santo André",
        estado="SP",
        local="Rua das Flores, 123, Centro, Santo André - SP",
        site="https://exemplo.com.br",
        instagram="https://instagram.com/padariadoze",
        facebook="https://facebook.com/padariadoze",
        setor="Varejo",
        tamanho="Pequena (1-10)",
        socios=[
            Socio(nome="José da Silva", qualificacao="Sócio-Administrador"),
        ],
        notas=(
            "🤖 LEAD DE TESTE — pode deletar depois.\n\n"
            f"Coletado em {datetime.now().strftime('%d/%m/%Y %H:%M')}.\n"
            "Esta é uma análise crítica fictícia gerada pra validar "
            "a Fase 1 do agente de prospecção."
        ),
    )

    contato = Contato(
        nome="José da Silva (TESTE)",
        cargo="Sócio-Administrador",
        decisor=True,
        email="jose@exemplo.com.br",
        telefone="(11) 1234-5678",
        whatsapp="(11) 99999-8888",
    )

    lead = Lead(empresa=empresa, contatos=[contato])

    # 1. Salva localmente em processed/
    filepath = save_lead(lead, stage="processed")

    # 2. Envia pro Notion
    exporter = NotionExporter()
    lead = exporter.send_lead(lead)

    # 3. Move pra sent/
    save_lead(lead, stage="sent")
    filepath.unlink()

    logger.info("=" * 60)
    logger.success("✅ TESTE CONCLUÍDO COM SUCESSO!")
    logger.info(f"   Empresa: {lead.empresa.notion_page_id}")
    if lead.contatos:
        logger.info(f"   Contato: {lead.contatos[0].notion_page_id}")
    logger.info("   👉 Vai no Notion conferir se apareceu!")
    logger.info("=" * 60)


def cmd_list_leads():
    """Lista os leads salvos localmente."""
    from app.utils.logger import get_logger
    from app.utils.storage import list_leads

    logger = get_logger()
    for stage in ("raw", "processed", "sent"):
        leads = list_leads(stage)
        logger.info(f"📁 {stage}/ → {len(leads)} arquivo(s)")
        for path in leads:
            logger.info(f"   - {path.name}")


def cmd_buscar_cnpj(cnpj: str):
    """
    Só busca o CNPJ na BrasilAPI e mostra os dados (sem mandar pro Notion).
    Útil pra debugar o mapeamento antes de cadastrar.
    """
    from app.collectors.brasilapi import buscar_lead_por_cnpj
    from app.utils.logger import get_logger

    logger = get_logger()
    logger.info(f"🔎 Buscando CNPJ: {cnpj}")

    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Lead não pôde ser montado (CNPJ inválido ou não encontrado)")
        return

    e = lead.empresa
    logger.info("=" * 60)
    logger.info(f"🏢 {e.nome}")
    logger.info(f"   Razão Social:    {e.razao_social}")
    logger.info(f"   CNPJ:            {e.cnpj}")
    logger.info(f"   Capital Social:  R$ {e.capital_social or 0:,.2f}")
    logger.info(f"   Setor:           {e.setor or '(não mapeado)'}")
    logger.info(f"   Tamanho:         {e.tamanho or '(não estimado)'}")
    logger.info(f"   Cidade/Estado:   {e.cidade}/{e.estado}")
    logger.info(f"   Endereço:        {e.local}")
    logger.info(f"   Sócios ({len(e.socios)}):")
    for s in e.socios:
        logger.info(f"     - {s.nome} ({s.qualificacao or 'sem qualificação'})")
    if e.notas:
        logger.info(f"   📝 Notas:")
        for linha in e.notas.split("\n"):
            logger.info(f"      {linha}")
    logger.info("=" * 60)


def cmd_prospectar_cnpj(cnpj: str):
    """
    Pipeline completo: busca CNPJ na BrasilAPI + envia pro Notion.
    """
    from app.collectors.brasilapi import buscar_lead_por_cnpj
    from app.exporters.notion import NotionExporter
    from app.utils.logger import get_logger
    from app.utils.storage import save_lead

    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🎯 PROSPECÇÃO POR CNPJ: {cnpj}")
    logger.info("=" * 60)

    # 1. Busca na BrasilAPI
    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Não foi possível obter o Lead. Abortando.")
        return

    # 2. Salva em processed/ antes de mandar pro Notion (segurança)
    save_lead(lead, stage="processed")

    # 3. Envia pro Notion
    exporter = NotionExporter()
    lead = exporter.send_lead(lead)

    # 4. Atualiza o JSON com os notion_page_ids preenchidos
    save_lead(lead, stage="sent")

    logger.info("=" * 60)
    logger.success(f"✅ PROSPECÇÃO CONCLUÍDA: {lead.empresa.nome}")
    logger.info(f"   Empresa:  {lead.empresa.notion_page_id}")
    logger.info(f"   Contatos: {len(lead.contatos)} criado(s)/atualizado(s)")
    logger.info("=" * 60)


def cmd_extrair_site(url: str, force_playwright: bool = False):
    """Extrai contatos de um site (sem mandar pro Notion)."""
    from app.collectors.website import coletar_do_site
    from app.utils.logger import get_logger

    logger = get_logger()
    logger.info(f"🌐 Extraindo de: {url}")
    if force_playwright:
        logger.info("   (Modo Playwright forçado)")

    contatos = coletar_do_site(url, force_playwright=force_playwright)
    logger.info("=" * 60)
    logger.info(f"   📧 Emails:     {contatos.get('emails') or '(nenhum)'}")
    logger.info(f"   📱 WhatsApp:   {contatos.get('whatsapps') or '(nenhum)'}")
    logger.info(f"   ☎️  Telefones:  {contatos.get('telefones') or '(nenhum)'}")
    logger.info(f"   📷 Instagram:  {contatos.get('instagram') or '(nenhum)'}")
    logger.info(f"   📘 Facebook:   {contatos.get('facebook') or '(nenhum)'}")
    logger.info(f"   💼 LinkedIn:   {contatos.get('linkedin') or '(nenhum)'}")
    logger.info("=" * 60)


def cmd_prospectar_completo(cnpj: str, url_site: Optional[str] = None):
    """
    Pipeline completo: BrasilAPI + (opcional) site → Notion.
    """
    from app.collectors.brasilapi import buscar_lead_por_cnpj
    from app.collectors.website import enriquecer_lead_com_site
    from app.exporters.notion import NotionExporter
    from app.utils.logger import get_logger
    from app.utils.storage import save_lead

    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🎯 PROSPECÇÃO COMPLETA: {cnpj}")
    if url_site:
        logger.info(f"   + site: {url_site}")
    logger.info("=" * 60)

    # 1. BrasilAPI
    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Não foi possível obter o Lead. Abortando.")
        return

    # 2. (opcional) enriquecimento via site
    if url_site:
        lead = enriquecer_lead_com_site(lead, url_site)

    # 3. Salva backup local antes de mandar pro Notion
    save_lead(lead, stage="processed")

    # 4. Notion
    exporter = NotionExporter()
    lead = exporter.send_lead(lead)
    save_lead(lead, stage="sent")

    logger.info("=" * 60)
    logger.success(f"✅ PROSPECÇÃO COMPLETA: {lead.empresa.nome}")
    logger.info(f"   Empresa Notion: {lead.empresa.notion_page_id}")
    logger.info(f"   Contatos: {len(lead.contatos)}")
    for c in lead.contatos:
        marca = "📞" if c.telefone or c.whatsapp else "📭"
        logger.info(f"     {marca} {c.nome} — email={c.email or '-'} whats={c.whatsapp or '-'}")
    logger.info("=" * 60)


def cmd_analisar_cnpj(cnpj: str, url_site: Optional[str] = None):
    """
    Roda só a análise da IA (BrasilAPI + site opcional + Gemini).
    NÃO manda pro Notion. Útil pra debugar o prompt.
    """
    from app.analyzers.gemini import analisar_lead
    from app.analyzers.gemini.parser import formatar_para_notas
    from app.collectors.brasilapi import buscar_lead_por_cnpj
    from app.collectors.website import enriquecer_lead_com_site
    from app.utils.logger import get_logger

    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🤖 ANÁLISE IA: {cnpj}")
    logger.info("=" * 60)

    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Não foi possível obter o Lead. Abortando.")
        return

    if url_site:
        lead = enriquecer_lead_com_site(lead, url_site)

    analise = analisar_lead(lead)
    if analise is None:
        logger.error("❌ Análise falhou. Abortando.")
        return

    print()
    print(formatar_para_notas(analise))
    print()


def cmd_prospectar_full(
    cnpj: str,
    url_site: Optional[str] = None,
    extras: Optional[dict] = None,
):
    """
    Pipeline TOTAL: BrasilAPI + site + análise IA + Notion.
    O comando 'turbo' que junta todas as fases.

    `extras` (opcional) aceita overrides manuais com as chaves:
        instagram, facebook   → vão pra Empresa
        linkedin, email, telefone, whatsapp → vão pro Contato principal
    Input manual SEMPRE prevalece sobre dados automáticos.
    """
    from app.analyzers.gemini import enriquecer_lead_com_analise
    from app.collectors.brasilapi import buscar_lead_por_cnpj
    from app.collectors.website import enriquecer_lead_com_site
    from app.exporters.notion import NotionExporter
    from app.services.manual_overrides import aplicar_overrides_manuais
    from app.utils.logger import get_logger
    from app.utils.storage import save_lead

    extras = extras or {}

    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🚀 PROSPECÇÃO FULL: {cnpj}")
    if url_site:
        logger.info(f"   + site: {url_site}")
    if extras:
        logger.info(f"   + overrides manuais: {', '.join(extras.keys())}")
    logger.info("   + análise IA")
    logger.info("=" * 60)

    # 1. BrasilAPI
    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Não foi possível obter o Lead. Abortando.")
        return

    # 2. Site (se informado)
    if url_site:
        lead = enriquecer_lead_com_site(lead, url_site)

    # 3. Overrides manuais (DEPOIS do site, pra ganhar prioridade)
    if extras:
        lead = aplicar_overrides_manuais(lead, **extras)

    # 4. Análise IA (anexa nas Notas)
    lead = enriquecer_lead_com_analise(lead)

    # 5. Salva backup
    save_lead(lead, stage="processed")

    # 6. Notion
    exporter = NotionExporter()
    lead = exporter.send_lead(lead)
    save_lead(lead, stage="sent")

    logger.info("=" * 60)
    logger.success(f"✅ FULL CONCLUÍDO: {lead.empresa.nome}")
    logger.info(f"   Empresa: {lead.empresa.notion_page_id}")
    logger.info(f"   Contatos: {len(lead.contatos)}")
    logger.info(f"   👉 Vai no Notion ver a análise da IA nas Notas!")
    logger.info("=" * 60)


def _parse_prospectar_full_args(argv: list) -> tuple:
    """
    Parser flexível pro prospectar-full. Aceita posicional, flags, ou ambos.

    Exemplos válidos:
        prospectar-full <CNPJ> [URL]                          (modo antigo)
        prospectar-full --cnpj X --site Y                     (só flags)
        prospectar-full <CNPJ> [URL] --email x@y.com          (misto)

    Flags suportadas:
        --cnpj, --site (=--url)
        --ig (=--instagram), --fb (=--facebook), --linkedin
        --email, --tel (=--telefone), --whats (=--whatsapp)

    Devolve: (cnpj: str, url_site: Optional[str], extras: dict)
    Lança ValueError se input for inválido.
    """
    FLAGS_VALIDAS = {
        "cnpj", "site", "url",
        "ig", "instagram",
        "fb", "facebook",
        "linkedin",
        "email",
        "tel", "telefone",
        "whats", "whatsapp",
    }

    posicionais = []
    flags = {}

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            chave = arg[2:]
            if chave not in FLAGS_VALIDAS:
                raise ValueError(f"Flag desconhecida: --{chave}")
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                raise ValueError(f"Flag --{chave} precisa de valor")
            flags[chave] = argv[i + 1]
            i += 2
        else:
            posicionais.append(arg)
            i += 1

    # CNPJ: flag tem prioridade, senão pega o 1º posicional
    cnpj = flags.get("cnpj") or (posicionais[0] if posicionais else None)
    if not cnpj:
        raise ValueError("CNPJ é obrigatório (via --cnpj ou posicional)")

    # URL do site: --site, --url, ou 2º posicional
    url_site = (
        flags.get("site")
        or flags.get("url")
        or (posicionais[1] if len(posicionais) > 1 else None)
    )

    # Overrides manuais
    extras: dict = {}
    if "ig" in flags or "instagram" in flags:
        extras["instagram"] = flags.get("ig") or flags.get("instagram")
    if "fb" in flags or "facebook" in flags:
        extras["facebook"] = flags.get("fb") or flags.get("facebook")
    if "linkedin" in flags:
        extras["linkedin"] = flags["linkedin"]
    if "email" in flags:
        extras["email"] = flags["email"]
    if "tel" in flags or "telefone" in flags:
        extras["telefone"] = flags.get("tel") or flags.get("telefone")
    if "whats" in flags or "whatsapp" in flags:
        extras["whatsapp"] = flags.get("whats") or flags.get("whatsapp")

    return cnpj, url_site, extras


def cmd_test_buscadores(query: str = "padaria são paulo"):
    """
    Testa cada motor de busca individualmente.
    Útil pra ver quem está bloqueado AGORA antes de uma investigação.
    """
    from app.collectors._common.buscadores import (
        DuckDuckGoBuscador, BraveBuscador, BingBuscador,
        BuscadorBloqueado, BuscadorIndisponivel,
    )
    from app.utils.logger import get_logger

    logger = get_logger()
    print()
    print("═" * 60)
    print(f"🔎 TESTE DOS BUSCADORES — query: {query!r}")
    print("═" * 60)

    motores = [DuckDuckGoBuscador(), BraveBuscador(), BingBuscador()]
    for m in motores:
        print(f"\n→ Testando {m.nome.upper()}...")
        try:
            resultados = m.buscar(query, max_resultados=3)
            if resultados:
                print(f"   ✅ {m.nome}: {len(resultados)} resultados")
                for r in resultados[:2]:
                    print(f"      • {r.titulo[:60]}")
                    print(f"        {r.url[:80]}")
            else:
                print(f"   📭 {m.nome}: sem resultados (mas funcionou)")
        except BuscadorBloqueado as e:
            print(f"   🚫 {m.nome} BLOQUEADO: {e}")
        except BuscadorIndisponivel as e:
            print(f"   ⚠️  {m.nome} indisponível: {e}")
        except Exception as e:
            print(f"   ❌ {m.nome} erro: {type(e).__name__}: {e}")
    print()
    print("═" * 60)


def cmd_tor_status():
    """
    Verifica se o Tor está acessível e mostra seu IP atual via Tor vs direto.

    Pra instalar Tor:
      Ubuntu: sudo apt install tor && sudo systemctl start tor
      Mac:    brew install tor && brew services start tor
    """
    from app.collectors._common import tor_client
    from app.utils.logger import get_logger

    logger = get_logger()
    logger.info("🧅 Verificando status do Tor...")

    status = tor_client.status()
    print()
    print("═" * 60)
    print("🧅 STATUS DO TOR")
    print("═" * 60)
    print(f"  Disponível: {'✅ SIM' if status['disponivel'] else '❌ NÃO'}")
    print(f"  IP direto (seu IP real):  {status['ip_direto']}")
    if status["disponivel"]:
        print(f"  IP via Tor:               {status['ip_via_tor']}")
        print()
        print("✅ Tor funcionando! Pra usar, defina no .env:")
        print("     USAR_TOR=true")
    else:
        print()
        print("❌ Tor NÃO está disponível. Instale e inicie:")
        print("   Ubuntu: sudo apt install tor && sudo systemctl start tor")
        print("   Mac:    brew install tor && brew services start tor")
    print("═" * 60)


def cmd_investigar(args: list):
    """
    Investigação multi-fonte. Aceita flags flexíveis.

    Uso:
        python run.py investigar --nome "Padaria do Zé" --cidade "Atibaia"
        python run.py investigar --cnpj 40165696000120
        python run.py investigar --instagram padariadoze
        python run.py investigar --site exemplo.com.br
        python run.py investigar --nome X --cidade Y --site Z   # combina o que quiser

    Flags disponíveis: --nome, --cnpj, --cidade, --estado, --site,
                        --instagram, --telefone
    """
    from app.analyzers.gemini import enriquecer_lead_com_analise
    from app.exporters.notion import NotionExporter
    from app.services.investigador import (
        InputInvestigacao,
        investigar_e_montar_lead,
    )
    from app.utils.logger import get_logger
    from app.utils.storage import save_lead

    logger = get_logger()

    # Parsing simples de --flag valor
    kwargs = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            chave = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                kwargs[chave] = args[i + 1]
                i += 2
                continue
        i += 1

    if not kwargs:
        print("❌ Você precisa passar pelo menos uma flag.")
        print(cmd_investigar.__doc__)
        return

    try:
        input_ = InputInvestigacao(**kwargs)
    except Exception as e:
        print(f"❌ Input inválido: {e}")
        return

    if not input_.tem_algo():
        print("❌ Nenhum campo válido foi reconhecido.")
        return

    logger.info("=" * 60)
    logger.info(f"🔬 INVESTIGAÇÃO MULTI-FONTE")
    logger.info(f"   Entrada: {input_.descricao_curta()}")
    logger.info("=" * 60)

    # Aquecimento: pausa longa no início pra parecer humano que acabou
    # de abrir o navegador. Pular essa pausa é red flag forte.
    from app.config import settings
    if settings.aquecer_sessao:
        from app.collectors._common.humano import aquecer_sessao
        import random
        delay = random.uniform(15, 45)  # 15-45s no início
        logger.info(f"   ☕ Aquecendo sessão ({delay:.0f}s)...")
        import time
        time.sleep(delay)

    # 1. Investigação interativa (pergunta site + aprovação)
    lead, inv, aprovado = investigar_e_montar_lead(input_, interativo=True)

    # 2. Análise IA (sempre roda — qualidade > velocidade)
    logger.info("")
    logger.info("🤖 Rodando análise IA...")
    lead = enriquecer_lead_com_analise(lead)

    # 3. Salva backup local
    save_lead(lead, stage="processed")

    # 4. Notion
    exporter = NotionExporter()
    lead = exporter.send_lead(lead)
    save_lead(lead, stage="sent")

    # 5. Resumo final
    logger.info("=" * 60)
    if aprovado:
        logger.success(f"✅ APROVADO — Status: 🔵 Prospect")
    else:
        logger.info(f"📌 NÃO APROVADO — Status: 🔬 Em investigação")
        logger.info(f"   Revise no Notion e mude o status manualmente.")
    logger.info(f"   Empresa Notion: {lead.empresa.notion_page_id}")
    logger.info(f"   Contatos criados: {len(lead.contatos)}")
    logger.info("=" * 60)


def cmd_debug_site(url: str, force_playwright: bool = False):
    """
    Investiga o que o site scraper consegue extrair de uma URL.

    Útil quando você prospectou uma empresa e os contatos vieram vazios
    — esse comando mostra exatamente o que o crawler achou (ou não).

    Uso:
        python run.py debug-site https://endolive.com.br/
        python run.py debug-site https://exemplo.com --playwright
    """
    from app.collectors.website.crawler import coletar_do_site
    from app.collectors.website.extractors import (
        formatar_telefone,
        normalizar_url,
    )

    url_norm = normalizar_url(url)
    print("=" * 60)
    print(f"🔍 DEBUG SITE: {url_norm}")
    print(f"   Playwright: {'ON' if force_playwright else 'OFF (HTTP simples)'}")
    print("=" * 60)

    try:
        resultado = coletar_do_site(url_norm, force_playwright=force_playwright)
    except Exception as e:
        print(f"❌ FALHA: {type(e).__name__}: {e}")
        return

    emails = resultado.get("emails", []) or []
    whatsapps = resultado.get("whatsapps", []) or []
    telefones = resultado.get("telefones", []) or []
    instagram = resultado.get("instagram")
    facebook = resultado.get("facebook")
    linkedin = resultado.get("linkedin")

    def linha(rotulo: str, valor):
        marca = "✅" if valor else "  "
        print(f"  {marca} {rotulo}")

    print()
    print("━━━ Resultado ━━━")
    linha(f"Emails ({len(emails)}):", emails)
    for e in emails[:5]:
        print(f"       • {e}")
    if len(emails) > 5:
        print(f"       ... e mais {len(emails) - 5}")

    linha(f"WhatsApps ({len(whatsapps)}):", whatsapps)
    for w in whatsapps[:5]:
        try:
            print(f"       • {formatar_telefone(w)}")
        except Exception:
            print(f"       • {w}")

    linha(f"Telefones fixos ({len(telefones)}):", telefones)
    for t in telefones[:5]:
        try:
            print(f"       • {formatar_telefone(t)}")
        except Exception:
            print(f"       • {t}")

    linha("Instagram:", instagram)
    if instagram:
        print(f"       • {instagram}")
    linha("Facebook:", facebook)
    if facebook:
        print(f"       • {facebook}")
    linha("LinkedIn:", linkedin)
    if linkedin:
        print(f"       • {linkedin}")

    print()
    nada = not any([emails, whatsapps, telefones, instagram, facebook, linkedin])
    if nada:
        print("⚠️  Nada foi extraído.")
        if not force_playwright:
            print("   💡 Tenta com --playwright (site pode ser SPA / JS).")
        else:
            print("   💡 Site pode bloquear bots ou esconder contato.")
            print("      Considere passar os dados manualmente (--email, --whats, etc).")
    print("=" * 60)


def cmd_serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """
    Inicia a API HTTP (FastAPI) pro frontend consumir.

    Docs interativos:
        http://localhost:8000/docs

    Healthcheck:
        http://localhost:8000/api/health
    """
    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn não está instalado. Rode: pip install fastapi uvicorn[standard]")
        sys.exit(1)

    from app.utils.logger import get_logger
    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🌐 Subindo API em http://{host}:{port}")
    logger.info(f"   📚 Swagger:  http://{host}:{port}/docs")
    logger.info(f"   ❤️  Health:   http://{host}:{port}/api/health")
    logger.info(f"   🔄 Reload:   {'ON' if reload else 'OFF'}")
    logger.info("=" * 60)

    uvicorn.run(
        "app.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )

def cmd_db_init():
    """
    Sobe o schema do banco do zero — aplica TODAS as migrations.

    Use depois de rodar `docker compose up -d`. Idempotente:
    se o banco já está atualizado, não faz nada.
    """
    import subprocess
    print("=" * 60)
    print("🗄️  Aplicando migrations no Postgres...")
    print("=" * 60)
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(BASE_DIR := __import__("pathlib").Path(__file__).parent),
        capture_output=False,
    )
    if result.returncode == 0:
        print("\n✅ Schema atualizado.")
    else:
        print("\n❌ Falhou. Verifique se o Docker subiu o Postgres.")
        sys.exit(result.returncode)


def cmd_db_migrate(message: str):
    """
    Gera uma migration nova baseada nas mudanças dos modelos ORM.

    Uso: python run.py db-migrate "adiciona tabela ai_calls"

    O Alembic compara `app.db.models.*` com o banco e detecta
    diferenças. SEMPRE revise o arquivo gerado em `alembic/versions/`
    antes de commitar — autogenerate erra em casos sutis (renomes,
    índices condicionais, etc).
    """
    import subprocess
    print("=" * 60)
    print(f"📝 Gerando migration: {message!r}")
    print("=" * 60)
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", message],
        cwd=str(__import__("pathlib").Path(__file__).parent),
    )
    if result.returncode == 0:
        print("\n✅ Migration criada. Revise o arquivo em alembic/versions/")
        print("   Depois aplique com: python run.py db-init")
    else:
        sys.exit(result.returncode)


def cmd_db_smoke():
    """Roda o teste de smoke do Passo 1."""
    from tests.test_db_smoke import main as smoke_main
    smoke_main()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "test-notion":
        test_notion()
    elif cmd == "test-conexao":
        test_conexao()
    elif cmd == "list-leads":
        cmd_list_leads()
    elif cmd == "buscar-cnpj":
        if len(sys.argv) < 3:
            print("❌ Uso: python run.py buscar-cnpj <CNPJ>")
            sys.exit(1)
        cmd_buscar_cnpj(sys.argv[2])
    elif cmd == "prospectar-cnpj":
        if len(sys.argv) < 3:
            print("❌ Uso: python run.py prospectar-cnpj <CNPJ>")
            sys.exit(1)
        cmd_prospectar_cnpj(sys.argv[2])
    elif cmd == "extrair-site":
        if len(sys.argv) < 3:
            print("❌ Uso: python run.py extrair-site <URL> [--playwright]")
            sys.exit(1)
        force_pw = "--playwright" in sys.argv[2:]
        # Pega a URL ignorando flags
        url = next((a for a in sys.argv[2:] if not a.startswith("--")), None)
        if not url:
            print("❌ URL não informada")
            sys.exit(1)
        cmd_extrair_site(url, force_playwright=force_pw)
    elif cmd == "prospectar-completo":
        if len(sys.argv) < 3:
            print("❌ Uso: python run.py prospectar-completo <CNPJ> [URL]")
            sys.exit(1)
        cnpj = sys.argv[2]
        url = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_prospectar_completo(cnpj, url)
    elif cmd == "analisar-cnpj":
        if len(sys.argv) < 3:
            print("❌ Uso: python run.py analisar-cnpj <CNPJ> [URL]")
            sys.exit(1)
        cnpj = sys.argv[2]
        url = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_analisar_cnpj(cnpj, url)
    elif cmd == "prospectar-full":
        if len(sys.argv) < 3:
            print("❌ Uso:")
            print("   python run.py prospectar-full <CNPJ> [URL]")
            print("   python run.py prospectar-full --cnpj X --site Y \\")
            print("       --ig @foo --fb foo --linkedin pessoa \\")
            print("       --email a@b.com --tel '11 1234-5678' --whats '11 91234-5678'")
            sys.exit(1)
        try:
            cnpj, url, extras = _parse_prospectar_full_args(sys.argv[2:])
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)
        cmd_prospectar_full(cnpj, url, extras)
    elif cmd == "investigar":
        cmd_investigar(sys.argv[2:])
    elif cmd == "tor-status":
        cmd_tor_status()
    elif cmd == "test-buscadores":
        query = sys.argv[2] if len(sys.argv) > 2 else "padaria são paulo"
        cmd_test_buscadores(query)
    elif cmd == "debug-site":
        if len(sys.argv) < 3:
            print("❌ Uso: python run.py debug-site <URL> [--playwright]")
            sys.exit(1)
        url = sys.argv[2]
        usar_pw = "--playwright" in sys.argv[3:]
        cmd_debug_site(url, force_playwright=usar_pw)
    elif cmd == "serve":
        port = 8000
        host = "127.0.0.1"
        reload_flag = True
        # Flags simples: --port 8001 --host 0.0.0.0 --no-reload
        argv = sys.argv[2:]
        i = 0
        while i < len(argv):
            if argv[i] == "--port" and i + 1 < len(argv):
                port = int(argv[i + 1]); i += 2
            elif argv[i] == "--host" and i + 1 < len(argv):
                host = argv[i + 1]; i += 2
            elif argv[i] == "--no-reload":
                reload_flag = False; i += 1
            else:
                i += 1   
        cmd_serve(host=host, port=port, reload=reload_flag)
    elif cmd == "db-init":
        cmd_db_init()
    elif cmd == "db-migrate":
        if len(sys.argv) < 3:
            print("Uso: python run.py db-migrate \"mensagem da migration\"")
            sys.exit(1)
        cmd_db_migrate(sys.argv[2])
    elif cmd == "db-smoke":
        cmd_db_smoke()
        
    else:
        print(f"❌ Comando desconhecido: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    # Wrapper com try/except global pra NUNCA sair silencioso.
    # Se algo der errado, mostra o erro completo.
    try:
        main()
    except Exception as exc:
        print("\n" + "=" * 60, file=sys.stderr, flush=True)
        print(f"❌ ERRO: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        print("=" * 60, file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)