"""roles e permissoes (substitui user.scopes por roles)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

role_table = sa.table(
    "role",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("scopes", postgresql.ARRAY(sa.String())),
)

user_table = sa.table(
    "user",
    sa.column("id", sa.Integer),
    sa.column("username", sa.String),
)

user_role_table = sa.table(
    "user_role",
    sa.column("user_id", sa.Integer),
    sa.column("role_id", sa.Integer),
)

ROLES = [
    {
        "name": "Admin",
        "description": "Acesso administrativo completo",
        "scopes": ["estoque:read", "prestador:read", "carregamentos:read", "carregamento:read", "admin"],
    },
    {
        "name": "Controll",
        "description": "Consulta de carregamentos (Controll)",
        "scopes": ["carregamentos:read"],
    },
]

ROLE_ASSIGNMENTS = {
    "uallasleles": "Admin",
    "controll": "Controll",
}


def upgrade() -> None:
    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=False),
    )
    op.create_index(op.f("ix_role_name"), "role", ["name"], unique=True)

    op.create_table(
        "user_role",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id"), primary_key=True),
    )

    conn = op.get_bind()

    role_ids = {}
    for role in ROLES:
        result = conn.execute(
            role_table.insert().values(**role).returning(role_table.c.id)
        )
        role_ids[role["name"]] = result.scalar_one()

    for username, role_name in ROLE_ASSIGNMENTS.items():
        user_id = conn.execute(
            sa.select(user_table.c.id).where(user_table.c.username == username)
        ).scalar_one_or_none()
        if user_id is not None:
            conn.execute(
                user_role_table.insert().values(user_id=user_id, role_id=role_ids[role_name])
            )

    op.drop_column("user", "scopes")


def downgrade() -> None:
    op.add_column("user", sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=True))
    op.drop_table("user_role")
    op.drop_index(op.f("ix_role_name"), table_name="role")
    op.drop_table("role")
