
from pydantic import BaseModel, field_validator


class InputInvestigacao(BaseModel):

    nome: str | None = None
    cnpj: str | None = None
    cidade: str | None = None
    estado: str | None = None  # sigla UF
    site: str | None = None
    instagram: str | None = None  # @handle ou URL
    telefone: str | None = None  # qualquer formato

    @field_validator("nome", "cidade", "estado", "site", mode="before")
    @classmethod
    def _strip_optional(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None

    @field_validator("cnpj", mode="before")
    @classmethod
    def _normaliza_cnpj(cls, v):
        if v is None:
            return None
        digits = "".join(c for c in str(v) if c.isdigit())
        return digits if digits else None

    @field_validator("instagram", mode="before")
    @classmethod
    def _normaliza_instagram(cls, v):
        if v is None:
            return None
        v = str(v).strip().lstrip("@")
        if "instagram.com/" in v:
            v = v.rstrip("/").split("instagram.com/")[-1].split("/")[0]
        return v.split("?")[0] or None

    @field_validator("telefone", mode="before")
    @classmethod
    def _normaliza_telefone(cls, v):
        if v is None:
            return None
        digits = "".join(c for c in str(v) if c.isdigit())
        if len(digits) >= 12 and digits.startswith("55"):
            digits = digits[2:]
        return digits if len(digits) in (10, 11) else None

    def tem_algo(self) -> bool:
        return any([
            self.nome, self.cnpj, self.cidade, self.site,
            self.instagram, self.telefone,
        ])

    def descricao_curta(self) -> str:
        partes = []
        if self.nome:
            partes.append(self.nome)
        if self.cidade:
            partes.append(f"em {self.cidade}")
        if self.cnpj:
            partes.append(f"(CNPJ {self.cnpj})")
        if self.instagram:
            partes.append(f"@{self.instagram}")
        if self.site:
            partes.append(self.site)
        return " ".join(partes) or "(sem entradas)"
