"""make lote.id_bodega nullable and producto codes optional

Revision ID: f2a1b6c7_nullable_bodega_and_optional_codes
Revises: a64b033fab0d
Create Date: 2025-10-31
"""

from alembic import op


revision = "f2a1b6c7"
down_revision = "a64b033fab0d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import Integer, String
    
    # lote.id_bodega nullable
    op.alter_column("lote", "id_bodega", existing_type=Integer(), nullable=True)
    # producto.nombre_generico nullable
    op.alter_column("producto", "nombre_generico", existing_type=String(), nullable=True)
    # producto.codigo_interno nullable
    op.alter_column("producto", "codigo_interno", existing_type=String(), nullable=True)
    # producto.codigo_barras nullable
    op.alter_column("producto", "codigo_barras", existing_type=String(), nullable=True)


def downgrade() -> None:
    from sqlalchemy import Integer, String
    
    op.alter_column("producto", "codigo_barras", existing_type=String(), nullable=False)
    op.alter_column("producto", "codigo_interno", existing_type=String(), nullable=False)
    op.alter_column("producto", "nombre_generico", existing_type=String(), nullable=False)
    op.alter_column("lote", "id_bodega", existing_type=Integer(), nullable=False)


