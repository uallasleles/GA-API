from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from auth.models.user import UserDB


class UserRoleLink(SQLModel, table=True):
    __tablename__ = "user_role"

    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)


class RoleDB(SQLModel, table=True):
    __tablename__ = "role"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    scopes: List[str] = Field(sa_column=Column(ARRAY(String)))

    users: List["UserDB"] = Relationship(back_populates="roles", link_model=UserRoleLink)
