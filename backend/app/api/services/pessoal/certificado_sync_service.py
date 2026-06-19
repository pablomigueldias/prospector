"""Sync autônomo de certificados: pasta pública do Drive → Perfil Mestre.

Fluxo: lista a pasta → para cada PDF ainda NÃO ingerido (chave = nome do
arquivo) → baixa → extrai via Gemini multimodal → vira uma `Certificacao` →
faz merge no perfil ativo. Idempotente: rodar de novo só pega arquivos novos.

É o coração da autonomia pedida: o Pablo joga um certificado na pasta e o
sistema se atualiza sozinho (via botão na tela ou cron).
"""
from __future__ import annotations

from pydantic import BaseModel

from app.analyzers.certificado import (
    CertificadoSemChave,
    extrair_certificado_llm,
    parse_certificado,
)
from app.api.schemas.pessoal import (
    Certificacao,
    CertificadoExtraido,
    PerfilMestreUpsert,
)
from app.api.services.pessoal.perfil_service import get_perfil, salvar_perfil
from app.collectors.drive import baixar_arquivo, listar_pasta_publica
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()


class CertificadoSyncError(Exception):
    """Erro de negócio do sync — vira HTTP 400 no router."""


class SyncItem(BaseModel):
    arquivo: str
    status: str          # "novo" | "ja_existia" | "falha"
    nome: str | None = None
    detalhe: str | None = None


class SyncResultado(BaseModel):
    total_na_pasta: int
    novos: int
    ja_existiam: int
    falhas: int
    itens: list[SyncItem]
    total_no_perfil: int


def _para_certificacao(ex: CertificadoExtraido, arquivo: str) -> Certificacao:
    return Certificacao(
        nome=(ex.nome_curso or arquivo.rsplit(".", 1)[0]).strip(),
        tema=ex.tema,
        instituicao=ex.instituicao,
        ano=ex.data_conclusao,
        carga_horaria=ex.carga_horaria,
        prova=ex.prova,
        arquivo=arquivo,
    )


async def sincronizar(folder_id: str | None = None) -> SyncResultado:
    """Puxa certificados novos da pasta pública e atualiza o Perfil Mestre."""
    if not settings.gemini_api_key:
        raise CertificadoSyncError("GEMINI_API_KEY não configurada — sem ela o "
                                   "extrator não roda.")

    folder = folder_id or settings.certificados_drive_folder_id
    if not folder:
        raise CertificadoSyncError("Sem pasta do Drive configurada "
                                   "(CERTIFICADOS_DRIVE_FOLDER_ID).")

    perfil = await get_perfil()
    if perfil is None:
        raise CertificadoSyncError("Não há Perfil Mestre ativo.")

    atuais: list[Certificacao] = list(perfil.certificacoes or [])
    # chave de dedupe: nome do arquivo de origem (case-insensitive).
    ja_tem = {c.arquivo.strip().lower() for c in atuais if c.arquivo}

    try:
        arquivos = listar_pasta_publica(folder)
    except Exception as e:  # noqa: BLE001 — vira erro de negócio amigável
        raise CertificadoSyncError(f"Falha ao listar a pasta do Drive: {e}")

    itens: list[SyncItem] = []
    novas: list[Certificacao] = []
    for arq in arquivos:
        chave = arq.nome.strip().lower()
        if chave in ja_tem:
            itens.append(SyncItem(arquivo=arq.nome, status="ja_existia"))
            continue
        try:
            conteudo = baixar_arquivo(arq.file_id)
            cru = extrair_certificado_llm(conteudo, "application/pdf")
            extraido = parse_certificado(cru)
            if extraido is None:
                itens.append(SyncItem(arquivo=arq.nome, status="falha",
                                      detalhe="LLM não devolveu JSON válido"))
                continue
            cert = _para_certificacao(extraido, arq.nome)
            novas.append(cert)
            ja_tem.add(chave)
            itens.append(SyncItem(arquivo=arq.nome, status="novo", nome=cert.nome))
        except CertificadoSemChave as e:
            raise CertificadoSyncError(str(e))
        except Exception as e:  # noqa: BLE001 — registra e segue pros próximos
            logger.warning("Falha no certificado %s: %s", arq.nome, e)
            itens.append(SyncItem(arquivo=arq.nome, status="falha", detalhe=str(e)))

    if novas:
        completo = atuais + novas
        payload = PerfilMestreUpsert(
            **perfil.model_dump(exclude={"id", "ativo", "created_at",
                                         "updated_at", "certificacoes"}),
            certificacoes=completo,
        )
        salvo = await salvar_perfil(payload)
        total_perfil = len(salvo.certificacoes)
    else:
        total_perfil = len(atuais)

    return SyncResultado(
        total_na_pasta=len(arquivos),
        novos=sum(1 for i in itens if i.status == "novo"),
        ja_existiam=sum(1 for i in itens if i.status == "ja_existia"),
        falhas=sum(1 for i in itens if i.status == "falha"),
        itens=itens,
        total_no_perfil=total_perfil,
    )
