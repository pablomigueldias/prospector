from typing import Dict

from notion_client import Client

from app.config import settings
from app.exporters.notion.mappers import (
    apply_schema,
    contato_to_values,
    empresa_to_values,
)
from app.exporters.notion.repository import NotionRepository
from app.domain.lead import Contato, Empresa, Lead
from app.utils.logger import get_logger


logger = get_logger()


class NotionExporter:

    def __init__(self):
        self.client = Client(auth=settings.notion_token)
        self.db_empresas = settings.notion_db_empresas
        self.db_contatos = settings.notion_db_contatos
        self.repo = NotionRepository(
            client=self.client,
            db_empresas=self.db_empresas,
            db_contatos=self.db_contatos,
        )

        self._schema_empresas: Dict[str, str] = {}
        self._schema_contatos: Dict[str, str] = {}
        self._schemas_loaded = False


    def _load_schemas(self) -> None:
        if self._schemas_loaded:
            return

        logger.info("📋 Carregando schemas do Notion...")

        db_emp = self.client.databases.retrieve(database_id=self.db_empresas)
        self._schema_empresas = {
            name: prop["type"] for name, prop in db_emp["properties"].items()  # type: ignore
        }
        logger.info(f"   Empresas: {len(self._schema_empresas)} campos detectados")

        db_con = self.client.databases.retrieve(database_id=self.db_contatos)
        self._schema_contatos = {
            name: prop["type"] for name, prop in db_con["properties"].items()  # type: ignore
        }
        logger.info(f"   Contatos: {len(self._schema_contatos)} campos detectados")

        self._schemas_loaded = True


    def upsert_empresa(self, empresa: Empresa) -> str:
        self._load_schemas()

        existing_id = (
            self.repo.find_empresa_by_cnpj(empresa.cnpj) if empresa.cnpj else None
        )

        values = empresa_to_values(empresa)
        properties = apply_schema(values, self._schema_empresas, "Empresa")

        if existing_id:
            self.repo.update_page(existing_id, properties)
            empresa.notion_page_id = existing_id
            logger.info(f"🔄 Empresa atualizada: {empresa.nome} (id={existing_id})")
            return existing_id

        page_id = self.repo.create_page(self.db_empresas, properties)
        empresa.notion_page_id = page_id
        logger.success(f"✅ Empresa criada: {empresa.nome} (id={page_id})")
        return page_id

    def upsert_contato(self, contato: Contato, empresa_nome: str) -> str:
        self._load_schemas()

        existing_id = None
        if contato.empresa_notion_id:
            existing_id = self.repo.find_contato(
                empresa_notion_id=contato.empresa_notion_id,
                email=contato.email,
                nome=contato.nome,
            )

        values = contato_to_values(contato, empresa_nome)
        properties = apply_schema(values, self._schema_contatos, "Contato")

        if existing_id:
            self.repo.update_page(existing_id, properties)
            contato.notion_page_id = existing_id
            logger.info(f"🔄 Contato atualizado: {contato.nome} (id={existing_id})")
            return existing_id

        page_id = self.repo.create_page(self.db_contatos, properties)
        contato.notion_page_id = page_id
        logger.success(f"✅ Contato criado: {contato.nome} (id={page_id})")
        return page_id

    def send_lead(self, lead: Lead) -> Lead:
        logger.info(f"📤 Enviando lead pro Notion: {lead.empresa.nome}")
        empresa_id = self.upsert_empresa(lead.empresa)

        for contato in lead.contatos:
            contato.empresa_notion_id = empresa_id
            try:
                self.upsert_contato(contato, lead.empresa.nome)
            except Exception as e:
                logger.error(f"Falhou ao processar contato {contato.nome}: {e}")

        return lead

    create_empresa = upsert_empresa
    create_contato = upsert_contato
