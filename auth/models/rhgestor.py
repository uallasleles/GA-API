from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


class RHGestorEnvioDB(SQLModel, table=True):
    """Histórico de cada envio (ou tentativa) de CSV à API da Sólides/RHGestor."""
    __tablename__ = "rhgestor_envio"

    id: Optional[int] = Field(default=None, primary_key=True)
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    usuario: str = Field(index=True)
    layout: str
    codigo_layout: str
    ambiente: str
    arquivo: str
    tamanho_bytes: int
    linhas: Optional[int] = None
    convertido: bool = False
    http_status: Optional[int] = None
    sucesso: bool = False
    mensagem: Optional[str] = Field(default=None, sa_column=Column(Text))
