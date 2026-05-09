"""
Uso:
    python run.py test-conexao      → testa apenas a conexão com o Notion
    python run.py test-notion       → cria empresa + contato de teste
    python run.py list-leads        → lista leads salvos localmente
"""

import sys
import traceback
from datetime import datetime


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