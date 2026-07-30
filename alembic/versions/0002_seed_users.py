"""seed initial users (migrados do fake_users_db anterior)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

user_table = sa.table(
    "user",
    sa.column("username", sa.String),
    sa.column("full_name", sa.String),
    sa.column("email", sa.String),
    sa.column("scopes", postgresql.ARRAY(sa.String())),
    sa.column("hashed_password", sa.String),
    sa.column("disabled", sa.Boolean),
)

USERS = [
    {
        "username": "uallasleles",
        "full_name": "Uallas Leles",
        "email": "uallasleles@hotmail.com",
        "scopes": ["me", "admin", "carregamento:read", "carregamentos:read"],
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$rHkjAbvDYYo8cwuYw047og$+ifGhU0bcDixhZSH+op8crfsW4FlrLYwlzVxOLiNUXs",
        "disabled": False,
    },
    {
        "username": "controll",
        "full_name": "controll",
        "email": "walissonsk8@hotmail.com",
        "scopes": ["me", "carregamentos:read"],
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$pt5tQNbRrBvU6QDag1s0TQ$n/9QQjxC32o7Wqi8MnPjBsrXAcbHq/GC6im0x0o59QE",
        "disabled": False,
    },
]


def upgrade() -> None:
    op.bulk_insert(user_table, USERS)


def downgrade() -> None:
    conn = op.get_bind()
    for user in USERS:
        conn.execute(
            sa.text("DELETE FROM \"user\" WHERE username = :username"),
            {"username": user["username"]},
        )
