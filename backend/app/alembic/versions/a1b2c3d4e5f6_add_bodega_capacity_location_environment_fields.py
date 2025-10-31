"""add bodega capacity location environment fields

Revision ID: a1b2c3d4e5f6
Revises: b10d00bcc8f6
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'b10d00bcc8f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar capacidad con default 0
    op.add_column('bodega', sa.Column('capacidad', sa.Integer(), nullable=False, server_default='0'))
    
    # Agregar ubicación (nullable)
    op.add_column('bodega', sa.Column('ubicacion', sa.String(length=255), nullable=True))
    
    # Agregar temperatura_min y temperatura_max (nullable)
    op.add_column('bodega', sa.Column('temperatura_min', sa.Float(), nullable=True))
    op.add_column('bodega', sa.Column('temperatura_max', sa.Float(), nullable=True))
    
    # Agregar humedad_min y humedad_max (nullable)
    op.add_column('bodega', sa.Column('humedad_min', sa.Float(), nullable=True))
    op.add_column('bodega', sa.Column('humedad_max', sa.Float(), nullable=True))


def downgrade() -> None:
    # Eliminar columnas en orden inverso
    op.drop_column('bodega', 'humedad_max')
    op.drop_column('bodega', 'humedad_min')
    op.drop_column('bodega', 'temperatura_max')
    op.drop_column('bodega', 'temperatura_min')
    op.drop_column('bodega', 'ubicacion')
    op.drop_column('bodega', 'capacidad')

