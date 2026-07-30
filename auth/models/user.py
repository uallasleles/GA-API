from typing import List, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, String as PGString
from sqlmodel import Field, SQLModel


class UserDB(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    email: Optional[str] = None
    scopes: List[str] = Field(sa_column=Column(ARRAY(PGString)))
    hashed_password: str
    disabled: bool = False
