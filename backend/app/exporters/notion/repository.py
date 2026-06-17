
from notion_client.errors import APIResponseError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.exporters.notion.mappers import format_cnpj
from app.utils.logger import get_logger

logger = get_logger()


class NotionRepository:

    def __init__(self, client, db_empresas: str, db_contatos: str):
        self.client = client
        self.db_empresas = db_empresas
        self.db_contatos = db_contatos


    def find_empresa_by_cnpj(self, cnpj: str) -> str | None:
        if not cnpj:
            return None

        cnpj_formatado = format_cnpj(cnpj)
        try:
            response = self.client.databases.query(
                database_id=self.db_empresas,
                filter={
                    "property": "CNPJ",
                    "rich_text": {"equals": cnpj_formatado},
                },
            )
            results = response.get("results", [])  # type: ignore
            if results:
                page_id = results[0]["id"]
                logger.info(
                    f"Empresa já existe no Notion (CNPJ {cnpj_formatado}): {page_id}"
                )
                return page_id
        except APIResponseError as e:
            logger.error(f"Erro ao buscar empresa por CNPJ: {e}")
        return None

    def find_contato(
        self,
        empresa_notion_id: str,
        email: str | None = None,
        nome: str | None = None,
    ) -> str | None:
        if not empresa_notion_id:
            return None

        empresa_filter = {
            "property": "Empresas",
            "relation": {"contains": empresa_notion_id},
        }

        if email:
            page_id = self._query_first(
                self.db_contatos,
                {
                    "and": [
                        empresa_filter,
                        {"property": "E-mail", "email": {"equals": email}},
                    ]
                },
            )
            if page_id:
                logger.info(f"Contato já existe (email {email} na empresa): {page_id}")
                return page_id

        if nome:
            page_id = self._query_first(
                self.db_contatos,
                {
                    "and": [
                        empresa_filter,
                        {"property": "Nome", "title": {"equals": nome}},
                    ]
                },
            )
            if page_id:
                logger.info(f"Contato já existe (nome '{nome}' na empresa): {page_id}")
                return page_id

        return None

    def _query_first(self, database_id: str, filter_: dict) -> str | None:
        try:
            response = self.client.databases.query(
                database_id=database_id, filter=filter_
            )
            results = response.get("results", [])  # type: ignore
            return results[0]["id"] if results else None
        except APIResponseError as e:
            logger.error(f"Erro em query: {e}")
            return None


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    def create_page(self, database_id: str, properties: dict[str, dict]) -> str:
        response = self.client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
        )
        return response["id"]  # type: ignore

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    def update_page(self, page_id: str, properties: dict[str, dict]) -> None:
        self.client.pages.update(page_id=page_id, properties=properties)
