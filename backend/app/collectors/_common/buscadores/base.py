from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse


class BuscadorError(Exception):
    """Erro genérico."""


class BuscadorBloqueado(BuscadorError):
    """Buscador bloqueou (429, 403, captcha)."""


class BuscadorIndisponivel(BuscadorError):
    """Buscador fora do ar (5xx, timeout)."""


@dataclass
class ResultadoBusca:
    titulo: str
    url: str
    snippet: str
    motor: str = ""

    @property
    def dominio(self) -> str:
        try:
            netloc = urlparse(self.url).netloc.lower()
            return netloc[4:] if netloc.startswith("www.") else netloc
        except Exception:
            return ""


class BuscadorBase(ABC):

    nome: str = "base"

    @abstractmethod
    def buscar(self, query: str, max_resultados: int = 10) -> List[ResultadoBusca]:
        ...
