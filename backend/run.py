import sys
import traceback
from datetime import datetime
from typing import Optional


def test_conexao():
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
    from app.exporters.notion import NotionExporter
    from app.models.lead import Contato, Empresa, Lead, Socio
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

    filepath = save_lead(lead, stage="processed")

    exporter = NotionExporter()
    lead = exporter.send_lead(lead)

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
    from app.utils.logger import get_logger
    from app.utils.storage import list_leads

    logger = get_logger()
    for stage in ("raw", "processed", "sent"):
        leads = list_leads(stage)
        logger.info(f"📁 {stage}/ → {len(leads)} arquivo(s)")
        for path in leads:
            logger.info(f"   - {path.name}")


def cmd_buscar_cnpj(cnpj: str):
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
    from app.collectors.brasilapi import buscar_lead_por_cnpj
    from app.exporters.notion import NotionExporter
    from app.utils.logger import get_logger
    from app.utils.storage import save_lead

    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🎯 PROSPECÇÃO POR CNPJ: {cnpj}")
    logger.info("=" * 60)

    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Não foi possível obter o Lead. Abortando.")
        return

    save_lead(lead, stage="processed")

    exporter = NotionExporter()
    lead = exporter.send_lead(lead)

    save_lead(lead, stage="sent")

    logger.info("=" * 60)
    logger.success(f"✅ PROSPECÇÃO CONCLUÍDA: {lead.empresa.nome}")
    logger.info(f"   Empresa:  {lead.empresa.notion_page_id}")
    logger.info(f"   Contatos: {len(lead.contatos)} criado(s)/atualizado(s)")
    logger.info("=" * 60)


def cmd_extrair_site(url: str, force_playwright: bool = False):
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

    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Não foi possível obter o Lead. Abortando.")
        return

    if url_site:
        lead = enriquecer_lead_com_site(lead, url_site)

    save_lead(lead, stage="processed")

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


def cmd_prospectar_full(cnpj: str, url_site: Optional[str] = None):
    from app.analyzers.gemini import enriquecer_lead_com_analise
    from app.collectors.brasilapi import buscar_lead_por_cnpj
    from app.collectors.website import enriquecer_lead_com_site
    from app.exporters.notion import NotionExporter
    from app.utils.logger import get_logger
    from app.utils.storage import save_lead

    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🚀 PROSPECÇÃO FULL: {cnpj}")
    if url_site:
        logger.info(f"   + site: {url_site}")
    logger.info("   + análise IA")
    logger.info("=" * 60)

    lead = buscar_lead_por_cnpj(cnpj)
    if lead is None:
        logger.error("❌ Não foi possível obter o Lead. Abortando.")
        return

    if url_site:
        lead = enriquecer_lead_com_site(lead, url_site)

    lead = enriquecer_lead_com_analise(lead)

    save_lead(lead, stage="processed")

    exporter = NotionExporter()
    lead = exporter.send_lead(lead)
    save_lead(lead, stage="sent")

    logger.info("=" * 60)
    logger.success(f"✅ FULL CONCLUÍDO: {lead.empresa.nome}")
    logger.info(f"   Empresa: {lead.empresa.notion_page_id}")
    logger.info(f"   Contatos: {len(lead.contatos)}")
    logger.info(f"   👉 Vai no Notion ver a análise da IA nas Notas!")
    logger.info("=" * 60)


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
            print("❌ Uso: python run.py prospectar-full <CNPJ> [URL]")
            sys.exit(1)
        cnpj = sys.argv[2]
        url = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_prospectar_full(cnpj, url)
    else:
        print(f"❌ Comando desconhecido: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\n" + "=" * 60, file=sys.stderr, flush=True)
        print(f"❌ ERRO: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        print("=" * 60, file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)
