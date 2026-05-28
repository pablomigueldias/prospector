from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional


from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.converters import contato_to_orm, empresa_to_orm, socio_to_orm
from app.db.models.contato import Contato as ContatoORM
from app.db.models.empresa import Empresa as EmpresaORM
from app.db.models.socio import Socio as SocioORM
from app.models.lead import Lead
from app.repositories.contato_repository import ContatoRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.utils.logger import get_logger

logger = get_logger()

_bridge_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.db_echo,
)

_BridgeSession = async_sessionmaker(
    bind=_bridge_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def _bridge_session():
    session = _BridgeSession()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# O serviço

class LeadPersistenceService:
    def __init__(self,session: AsyncSession):
        self.session = session
        self.empresas = EmpresaRepository(session)
        self.contatos = ContatoRepository(session)

    async def persit(self, lead: Lead) -> uuid.UUID:

        empresa = await self.empresas.upsert_by_cnpj(empresa_to_orm(lead.empresa))

        await self.session.flush()

        nomes_existentes = {s.nome for s in empresa.socios}
        for s_pyd in lead.empresa.socios:
            if s_pyd.nome not in nomes_existentes:
                empresa.socios.append(socio_to_orm(s_pyd))
        
        for c_pyd in lead.contatos:
            contato = contato_to_orm(c_pyd)
            contato.empresa_id =  empresa.id
            await self.contatos.upsert(contato)

        await self.session.commit()

        logger.success(
            f"Postgres: {empresa.nome}"
            f"{len(lead.empresa.socios)} sócios(s), {len(lead.contatos)} contato(s)"
        )
        return empresa.id
    
# ponte sync -> async

async def _persist_async(lead: Lead) -> uuid.UUID:
    async with _bridge_session() as session:
        return await LeadPersistenceService(session).persit(lead)
    
def persist_lead_sync(lead: Lead) -> Optional[uuid.UUID]:
    return asyncio.run(_persist_async(lead))

# stats endpoint de teste

async def _db_stats_async() -> dict:

    async with _bridge_session() as session:
        return {
            "empresas": await session.scalar(select(func.count(EmpresaORM.id))) or 0,
            "socios": await session.scalar(select(func.count(SocioORM.id))) or 0,
            "contatos": await session.scalar(select(func.count(ContatoORM.id))) or 0,
        }
    
def db_stats_sync() -> dict:
    return asyncio.run(_db_stats_async())



