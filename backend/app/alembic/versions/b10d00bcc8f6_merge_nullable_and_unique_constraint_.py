"""merge nullable and unique constraint migrations

Revision ID: b10d00bcc8f6
Revises: f1d2c3b4unique, f2a1b6c7nullable
Create Date: 2025-10-31 12:44:37.050926

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'b10d00bcc8f6'
down_revision = ('f1d2c3b4unique', 'f2a1b6c7nullable')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
