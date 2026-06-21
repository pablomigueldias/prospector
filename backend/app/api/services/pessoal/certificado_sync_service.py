"""Sync autônomo de certificados: pasta pública do Drive → Perfil Mestre.

Fluxo: lista a pasta → para cada PDF ainda NÃO ingerido (chave = nome do
arquivo) → baixa → extrai via Gemini multimodal → vira uma `Certificacao` →
faz merge no perfil ativo. Idempotente: rodar de novo só pega arquivos novos.

Os PDFs ficam **arquivados no servidor** (`data/certificados/`) na 1ª vez que
são baixados; nos syncs seguintes lê do disco em vez de rebaixar do Drive
(cache-first). Assim os certificados não dependem do Drive e o sync fica rápido.

É o coração da autonomia pedida: o Pablo joga um certificado na pasta e o
sistema se atualiza sozinho (via botão na tela ou cron).
"""
from __future__ import annotations

import re
from pathlib import Path

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
from app.config import CERTIFICADOS_DIR, settings
from app.utils.logger import get_logger

logger = get_logger()


def _caminho_local(nome: str) -> Path:
    """Caminho do PDF arquivado no servidor (nome saneado, sem subpastas)."""
    seguro = re.sub(r"[^\w.\- ]", "_", nome).strip() or "certificado.pdf"
    return CERTIFICADOS_DIR / seguro


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
    arquivados: int = 0          # PDFs baixados pro servidor NESTE sync
    total_arquivados: int = 0    # PDFs já guardados no servidor (data/certificados/)


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

    CERTIFICADOS_DIR.mkdir(parents=True, exist_ok=True)

    itens: list[SyncItem] = []
    novas: list[Certificacao] = []
    arquivados = 0
    for arq in arquivos:
        chave = arq.nome.strip().lower()
        destino = _caminho_local(arq.nome)
        ja_no_perfil = chave in ja_tem

        # Regime estável: já extraído E já arquivado → nada a fazer (sem Drive).
        if ja_no_perfil and destino.exists():
            itens.append(SyncItem(arquivo=arq.nome, status="ja_existia"))
            continue

        # Precisa dos bytes (pra arquivar e/ou extrair). Cache-first: se o PDF já
        # está no servidor, lê do disco; senão baixa do Drive UMA vez e guarda.
        try:
            if destino.exists():
                conteudo = destino.read_bytes()
            else:
                conteudo = baixar_arquivo(arq.file_id)
                destino.write_bytes(conteudo)
                arquivados += 1
        except Exception as e:  # noqa: BLE001 — registra e segue pros próximos
            logger.warning("Falha ao obter %s: %s", arq.nome, e)
            itens.append(SyncItem(arquivo=arq.nome, status="falha", detalhe=str(e)))
            continue

        # Já estava no perfil, só faltava arquivar → guardado agora, sem LLM.
        if ja_no_perfil:
            itens.append(SyncItem(arquivo=arq.nome, status="ja_existia"))
            continue

        try:
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

    total_arquivados = sum(1 for p in CERTIFICADOS_DIR.glob("*") if p.is_file())
    return SyncResultado(
        total_na_pasta=len(arquivos),
        novos=sum(1 for i in itens if i.status == "novo"),
        ja_existiam=sum(1 for i in itens if i.status == "ja_existia"),
        falhas=sum(1 for i in itens if i.status == "falha"),
        itens=itens,
        total_no_perfil=total_perfil,
        arquivados=arquivados,
        total_arquivados=total_arquivados,
    )
