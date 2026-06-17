from app.collectors._common.buscadores import ResultadoBusca
from app.collectors.duckduckgo.search import (
    buscar,
    buscar_cnpj_por_nome,
    buscar_redes_sociais,
)

__all__ = ["buscar", "buscar_redes_sociais", "buscar_cnpj_por_nome", "ResultadoBusca"]
