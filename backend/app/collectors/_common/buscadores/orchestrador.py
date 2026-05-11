import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.collectors._common.buscadores.base import (
    BuscadorBase,
    BuscadorBloqueado,
    BuscadorError,
    BuscadorIndisponivel,
    ResultadoBusca,
)
from app.collectors._common.buscadores.bing import BingBuscador
from app.collectors._common.buscadores.brave import BraveBuscador
from app.collectors._common.buscadores.duckduckgo import DuckDuckGoBuscador
from app.utils.logger import get_logger


logger = get_logger()


TTL_BLOQUEIO = 3600 


@dataclass
class EstadoBuscador:

    bloqueado_ate: float = 0.0  # epoch
    falhas_consecutivas: int = 0
    sucessos_totais: int = 0


class OrchestradorBuscadores:

    def __init__(self, ordem: Optional[List[BuscadorBase]] = None):

        self.buscadores: List[BuscadorBase] = ordem or [
            DuckDuckGoBuscador(),
            BraveBuscador(),
            BingBuscador(),
        ]
        self.estado: Dict[str, EstadoBuscador] = {
            b.nome: EstadoBuscador() for b in self.buscadores
        }

    def buscar(self, query: str, max_resultados: int = 10) -> List[ResultadoBusca]:
   
        if not query.strip():
            return []

        for buscador in self._ordem_dinamica():
            est = self.estado[buscador.nome]

            if est.bloqueado_ate > time.time():
                restante = int(est.bloqueado_ate - time.time())
                logger.debug(f"   ⏭️  Pulando {buscador.nome} (bloqueado por mais {restante}s)")
                continue

            try:
                resultados = buscador.buscar(query, max_resultados)
                est.falhas_consecutivas = 0
                est.sucessos_totais += 1
                if resultados:
                    return resultados
     
                logger.info(f"   📭 {buscador.nome} sem resultados pra essa query")
                return []

            except BuscadorBloqueado as e:
                est.falhas_consecutivas += 1
                est.bloqueado_ate = time.time() + TTL_BLOQUEIO
                logger.warning(f"   🚫 {buscador.nome} BLOQUEOU ({e}). Tentando próximo motor...")
                continue

            except BuscadorIndisponivel as e:
                est.falhas_consecutivas += 1
                est.bloqueado_ate = time.time() + 600
                logger.warning(f"   ⚠️  {buscador.nome} indisponível ({e}). Tentando próximo...")
                continue

            except Exception as e:

                est.falhas_consecutivas += 1
                logger.warning(f"   ❌ {buscador.nome} erro inesperado ({e}). Tentando próximo...")
                continue


        logger.error("   ❌ TODOS os buscadores falharam pra essa query")
        return []

    def _ordem_dinamica(self) -> List[BuscadorBase]:
 
        agora = time.time()

        def chave(b: BuscadorBase) -> tuple:
            est = self.estado[b.nome]
            bloqueado = est.bloqueado_ate > agora
            return (
                bloqueado,                             
                -est.sucessos_totais,                   
                est.falhas_consecutivas,            
            )

        return sorted(self.buscadores, key=chave)

    def relatorio(self) -> str:

        agora = time.time()
        linhas = []
        for nome, est in self.estado.items():
            if est.bloqueado_ate > agora:
                restante = int(est.bloqueado_ate - agora)
                linhas.append(f"  {nome}: 🚫 bloqueado por mais {restante}s ({est.sucessos_totais} sucessos totais)")
            else:
                linhas.append(f"  {nome}: ✅ ok ({est.sucessos_totais} sucessos totais)")
        return "\n".join(linhas)


_orchestrador_global: Optional[OrchestradorBuscadores] = None


def get_orchestrador() -> OrchestradorBuscadores:

    global _orchestrador_global
    if _orchestrador_global is None:
        _orchestrador_global = OrchestradorBuscadores()
    return _orchestrador_global


def buscar(query: str, max_resultados: int = 10) -> List[ResultadoBusca]:
    return get_orchestrador().buscar(query, max_resultados)
