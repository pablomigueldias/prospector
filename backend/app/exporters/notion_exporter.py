from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import (
    COMO_CONHECEU_OPCOES,
    DEFAULT_COMO_CONHECEU,
    DEFAULT_ORIGEM_CONTATO,
    DEFAULT_STATUS,
    ESTADO_OPCOES,
    ORIGEM_CONTATO_OPCOES,
    SETOR_OPCOES,
    STATUS_OPCOES,
    TAMANHO_OPCOES,
    settings,
)
from app.domain.lead import Contato, Empresa, Lead
from app.utils.logger import get_logger
from app.utils.storage import log_unmapped_field

logger = get_logger()

NOT_WRITABLE_TYPES = {
    "place",
    "formula",
    "rollup",
    "created_time",
    "last_edited_time",
    "created_by",
    "last_edited_by",
    "unique_id",
    "verification",
    "button",
}


class NotionExporter:

    def __init__(self):
        self.client = Client(auth=settings.notion_token)
        self.db_empresas = settings.notion_db_empresas
        self.db_contatos = settings.notion_db_contatos

        self._schema_empresas: dict[str, str] = {}
        self._schema_contatos: dict[str, str] = {}
        self._schemas_loaded = False

    def _load_schemas(self) -> None:
        if self._schemas_loaded:
            return

        logger.info("📋 Carregando schemas do Notion...")

        db_emp = self.client.databases.retrieve(database_id=self.db_empresas)
        self._schema_empresas = {
            name: prop["type"] for name, prop in db_emp["properties"].items() #type: ignore
        }
        logger.info(
            f"   Empresas: {len(self._schema_empresas)} campos detectados"
        )

        db_con = self.client.databases.retrieve(database_id=self.db_contatos)
        self._schema_contatos = {
            name: prop["type"] for name, prop in db_con["properties"].items() #type: ignore
        }
        logger.info(
            f"   Contatos: {len(self._schema_contatos)} campos detectados"
        )

        self._schemas_loaded = True

    def _validate_select(
        self,
        field_name: str,
        value: str | None,
        valid_options: list,
        empresa_nome: str,
    ) -> str | None:
        if value is None or value == "":
            return None
        if value in valid_options:
            return value
        log_unmapped_field(field_name, value, empresa_nome)
        return None


    @staticmethod
    def _build_value_for_type(notion_type: str, value: Any) -> dict | None:
        if value is None or value == "":
            return _empty_value_for_type(notion_type)

        if notion_type == "title":
            return {"title": [{"text": {"content": str(value)}}]}

        if notion_type == "rich_text":
            return {"rich_text": [{"text": {"content": str(value)}}]}

        if notion_type == "number":
            try:
                return {"number": float(value)}
            except (TypeError, ValueError):
                return {"number": None}

        if notion_type == "select":
            return {"select": {"name": str(value)}}

        if notion_type == "multi_select":
            if isinstance(value, str):
                value = [value]
            return {"multi_select": [{"name": str(v)} for v in value]}

        if notion_type == "url":
            return {"url": str(value)}

        if notion_type == "email":
            return {"email": str(value)}

        if notion_type == "phone_number":
            return {"phone_number": str(value)}

        if notion_type == "checkbox":
            return {"checkbox": bool(value)}

        if notion_type == "date":
            if isinstance(value, dict):
                return {"date": value}
            return {"date": {"start": str(value)}}

        if notion_type == "relation":
            ids = value if isinstance(value, list) else [value]
            return {"relation": [{"id": pid} for pid in ids]}

        if notion_type == "people":
            ids = value if isinstance(value, list) else [value]
            return {"people": [{"id": pid} for pid in ids]}

        if notion_type == "files":
            return {"files": value if isinstance(value, list) else []}

        # Tipo não suportado
        return None


    def _empresa_to_values(self, empresa: Empresa) -> dict[str, Any]:
        nome = empresa.nome

        setor = self._validate_select(
            "setor", empresa.setor, SETOR_OPCOES, nome)
        tamanho = self._validate_select(
            "tamanho", empresa.tamanho, TAMANHO_OPCOES, nome
        )
        estado = self._validate_select(
            "estado", empresa.estado, ESTADO_OPCOES, nome)
        status = self._validate_select(
            "status", empresa.status or DEFAULT_STATUS, STATUS_OPCOES, nome
        )
        como_conheceu = self._validate_select(
            "como_conheceu",
            empresa.como_conheceu or DEFAULT_COMO_CONHECEU,
            COMO_CONHECEU_OPCOES,
            nome,
        )

        socios_str = (
            ", ".join(s.nome for s in empresa.socios) if empresa.socios else None
        )
        cnpj_formatado = self._format_cnpj(
            empresa.cnpj) if empresa.cnpj else None

        return {
            "Nome": empresa.nome,
            "Razão Social": empresa.razao_social,
            "CNPJ": cnpj_formatado,
            "Capital Social": empresa.capital_social,
            "Cidade": empresa.cidade,
            "Estado": estado,  # valor validado (igual a setor/tamanho/status)
            "Local": empresa.local,
            "Site": empresa.site,
            "Instagram": empresa.instagram,
            "Facebook": empresa.facebook,
            "Setor": setor,
            "Tamanho": tamanho,
            "Socio": socios_str,
            "Status": status,
            "Como conheceu": como_conheceu,
            "Notas": empresa.notas,
        }

    def _contato_to_values(
        self, contato: Contato, empresa_nome: str
    ) -> dict[str, Any]:
        origem = self._validate_select(
            "origem_contato",
            contato.origem_contato or DEFAULT_ORIGEM_CONTATO,
            ORIGEM_CONTATO_OPCOES,
            empresa_nome,
        )

        values = {
            "Nome": contato.nome,
            "Cargo": contato.cargo,
            "Decisor?": "Sim" if contato.decisor else "Não",
            "E-mail": contato.email,
            "Telefone": contato.telefone,
            "WhatsApp": contato.whatsapp,
            "LinkedIn": contato.linkedin,
            "Origem do contato": origem,
        }

        if contato.empresa_notion_id:
            values["Empresas"] = [contato.empresa_notion_id]

        return values


    def _apply_schema(
        self, values: dict[str, Any], schema: dict[str, str], context: str
    ) -> dict[str, dict]:
        properties = {}
        skipped_unsupported: list[str] = []
        skipped_missing: list[str] = []

        for field_name, value in values.items():
            notion_type = schema.get(field_name)

            if notion_type is None:
                skipped_missing.append(field_name)
                continue

            if notion_type in NOT_WRITABLE_TYPES:
                skipped_unsupported.append(f"{field_name}={notion_type}")
                continue

            built = self._build_value_for_type(notion_type, value)
            if built is None:
                skipped_unsupported.append(f"{field_name}={notion_type}")
                continue

            properties[field_name] = built

        if skipped_missing:
            logger.warning(
                f"⚠️  [{context}] Campos do código que NÃO existem no Notion: "
                f"{', '.join(skipped_missing)}"
            )
        if skipped_unsupported:
            logger.warning(
                f"⚠️  [{context}] Campos pulados (tipo não suportado): "
                f"{', '.join(skipped_unsupported)}"
            )

        return properties


    def find_empresa_by_cnpj(self, cnpj: str) -> str | None:

        if not cnpj:
            return None

        cnpj_formatado = self._format_cnpj(cnpj)
        try:
            response = self.client.databases.query(
                database_id=self.db_empresas,
                filter={
                    "property": "CNPJ",
                    "rich_text": {"equals": cnpj_formatado},
                },
            )
            results = response.get("results", []) #type: ignore
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
            try:
                response = self.client.databases.query(
                    database_id=self.db_contatos,
                    filter={
                        "and": [
                            empresa_filter,
                            {"property": "E-mail", "email": {"equals": email}},
                        ]
                    },
                )
                results = response.get("results", []) #type: ignore
                if results:
                    page_id = results[0]["id"]
                    logger.info(
                        f"Contato já existe (email {email} na empresa): {page_id}"
                    )
                    return page_id
            except APIResponseError as e:
                logger.error(f"Erro ao buscar contato por email: {e}")

        if nome:
            try:
                response = self.client.databases.query(
                    database_id=self.db_contatos,
                    filter={
                        "and": [
                            empresa_filter,
                            {"property": "Nome", "title": {"equals": nome}},
                        ]
                    },
                )
                results = response.get("results", []) #type: ignore
                if results:
                    page_id = results[0]["id"]
                    logger.info(
                        f"Contato já existe (nome '{nome}' na empresa): {page_id}"
                    )
                    return page_id
            except APIResponseError as e:
                logger.error(f"Erro ao buscar contato por nome: {e}")

        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    def _update_page(self, page_id: str, properties: dict) -> None:
        self.client.pages.update(page_id=page_id, properties=properties)


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    def upsert_empresa(self, empresa: Empresa) -> str:

        self._load_schemas()

        existing_id = None
        if empresa.cnpj:
            existing_id = self.find_empresa_by_cnpj(empresa.cnpj)

        values = self._empresa_to_values(empresa)
        properties = self._apply_schema(
            values, self._schema_empresas, "Empresa")

        if existing_id:
            self._update_page(existing_id, properties)
            empresa.notion_page_id = existing_id
            logger.info(
                f"🔄 Empresa atualizada: {empresa.nome} (id={existing_id})")
            return existing_id

        response = self.client.pages.create(
            parent={"database_id": self.db_empresas},
            properties=properties,
        )
        page_id = response["id"] #type: ignore
        empresa.notion_page_id = page_id
        logger.success(f"✅ Empresa criada: {empresa.nome} (id={page_id})")
        return page_id

    create_empresa = upsert_empresa


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    def upsert_contato(self, contato: Contato, empresa_nome: str) -> str:
        self._load_schemas()

        existing_id = None
        if contato.empresa_notion_id:
            existing_id = self.find_contato(
                empresa_notion_id=contato.empresa_notion_id,
                email=contato.email,
                nome=contato.nome,
            )

        values = self._contato_to_values(contato, empresa_nome)
        properties = self._apply_schema(
            values, self._schema_contatos, "Contato")

        if existing_id:
            self._update_page(existing_id, properties)
            contato.notion_page_id = existing_id
            logger.info(
                f"🔄 Contato atualizado: {contato.nome} (id={existing_id})")
            return existing_id

        response = self.client.pages.create(
            parent={"database_id": self.db_contatos},
            properties=properties,
        )
        page_id = response["id"] #type: ignore
        contato.notion_page_id = page_id
        logger.success(f"✅ Contato criado: {contato.nome} (id={page_id})")
        return page_id

    create_contato = upsert_contato


    def send_lead(self, lead: Lead) -> Lead:
        logger.info(f"📤 Enviando lead pro Notion: {lead.empresa.nome}")
        empresa_id = self.upsert_empresa(lead.empresa)

        for contato in lead.contatos:
            contato.empresa_notion_id = empresa_id
            try:
                self.upsert_contato(contato, lead.empresa.nome)
            except Exception as e:
                logger.error(
                    f"Falhou ao processar contato {contato.nome}: {e}")

        return lead


    @staticmethod
    def _format_cnpj(cnpj: str) -> str:
        digits = "".join(c for c in cnpj if c.isdigit())
        if len(digits) != 14:
            return cnpj
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def _empty_value_for_type(notion_type: str) -> dict | None:
    if notion_type in NOT_WRITABLE_TYPES:
        return None
    empties = {
        "title": {"title": []},
        "rich_text": {"rich_text": []},
        "number": {"number": None},
        "select": {"select": None},
        "multi_select": {"multi_select": []},
        "url": {"url": None},
        "email": {"email": None},
        "phone_number": {"phone_number": None},
        "checkbox": {"checkbox": False},
        "date": {"date": None},
        "relation": {"relation": []},
        "people": {"people": []},
        "files": {"files": []},
    }
    return empties.get(notion_type)
