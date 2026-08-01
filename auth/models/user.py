from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from auth.models.role import RoleDB, UserRoleLink


class UserDB(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    email: Optional[str] = None
    hashed_password: str
    disabled: bool = False

    roles: List[RoleDB] = Relationship(back_populates="users", link_model=UserRoleLink)
