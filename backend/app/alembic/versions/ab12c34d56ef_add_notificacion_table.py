"""add notificacion table

Revision ID: ab12c34d56ef
Revises: f2a1b6c7_nullable_bodega_and_optional_codes
Create Date: 2025-12-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ab12c34d56ef"
down_revision = "f2a1b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notificacion",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("prioridad", sa.String(), nullable=False, server_default="normal"),
        sa.Column("leida", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("receptor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sucursal_id", sa.Integer(), nullable=True),
        sa.Column("bodega_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["receptor_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sucursal_id"], ["sucursal.id_sucursal"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["bodega_id"], ["bodega.id_bodega"], ondelete="SET NULL"),
    )
    op.create_index("ix_notificacion_receptor_leida", "notificacion", ["receptor_id", "leida"], unique=False)
    op.create_index("ix_notificacion_tipo", "notificacion", ["tipo"], unique=False)
    op.create_index("ix_notificacion_creado_en", "notificacion", ["creado_en"], unique=False)
    op.create_index("ix_notificacion_sucursal", "notificacion", ["sucursal_id"], unique=False)
    op.create_index("ix_notificacion_bodega", "notificacion", ["bodega_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notificacion_bodega", table_name="notificacion")
    op.drop_index("ix_notificacion_sucursal", table_name="notificacion")
    op.drop_index("ix_notificacion_creado_en", table_name="notificacion")
    op.drop_index("ix_notificacion_tipo", table_name="notificacion")
    op.drop_index("ix_notificacion_receptor_leida", table_name="notificacion")
    op.drop_table("notificacion")
