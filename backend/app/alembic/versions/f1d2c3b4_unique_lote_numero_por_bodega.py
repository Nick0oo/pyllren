"""add unique constraint (numero_lote, id_bodega) on lote

Revision ID: f1d2c3b4unique
Revises: d98dd8ec85a3
Create Date: 2025-10-31
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f1d2c3b4_unique_lote_numero_por_bodega"
down_revision = "d98dd8ec85a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_lote_numero_bodega", "lote", ["numero_lote", "id_bodega"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_lote_numero_bodega", "lote", type_="unique")


