"""add transferencia table

Revision ID: bc23d45e67ab
Revises: ab12c34d56ef
Create Date: 2025-12-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bc23d45e67ab"
down_revision = "ab12c34d56ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transferencia",
        sa.Column("id_transferencia", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("id_bodega_origen", sa.Integer(), nullable=False),
        sa.Column("id_bodega_destino", sa.Integer(), nullable=False),
        sa.Column("id_usuario_origen", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.String(), nullable=False, server_default="pendiente"),
        sa.Column("productos", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("observaciones", sa.String(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_bodega_origen"], ["bodega.id_bodega"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["id_bodega_destino"], ["bodega.id_bodega"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["id_usuario_origen"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_transferencia_estado",
        "transferencia",
        ["estado"],
        unique=False,
    )
    op.create_index(
        "ix_transferencia_bodegas",
        "transferencia",
        ["id_bodega_origen", "id_bodega_destino"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transferencia_bodegas", table_name="transferencia")
    op.drop_index("ix_transferencia_estado", table_name="transferencia")
    op.drop_table("transferencia")
