"""rename metadata to meta_data in notificacion

Revision ID: 7f3b2a1c9d10
Revises: 23e214c45564
Create Date: 2025-12-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7f3b2a1c9d10"
down_revision = "23e214c45564"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename column metadata -> meta_data for consistency with models
    op.execute("ALTER TABLE notificacion RENAME COLUMN metadata TO meta_data;")


def downgrade() -> None:
    # Revert column name
    op.execute("ALTER TABLE notificacion RENAME COLUMN meta_data TO metadata;")
