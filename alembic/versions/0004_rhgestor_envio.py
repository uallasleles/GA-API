"""historico de envios de CSV ao RHGestor (Solides)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rhgestor_envio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("usuario", sa.String(), nullable=False),
        sa.Column("layout", sa.String(), nullable=False),
        sa.Column("codigo_layout", sa.String(), nullable=False),
        sa.Column("ambiente", sa.String(), nullable=False),
        sa.Column("arquivo", sa.String(), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column("linhas", sa.Integer(), nullable=True),
        sa.Column("convertido", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("sucesso", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mensagem", sa.Text(), nullable=True),
    )
    op.create_index(op.f("ix_rhgestor_envio_criado_em"), "rhgestor_envio", ["criado_em"])
    op.create_index(op.f("ix_rhgestor_envio_usuario"), "rhgestor_envio", ["usuario"])


def downgrade() -> None:
    op.drop_index(op.f("ix_rhgestor_envio_usuario"), table_name="rhgestor_envio")
    op.drop_index(op.f("ix_rhgestor_envio_criado_em"), table_name="rhgestor_envio")
    op.drop_table("rhgestor_envio")
