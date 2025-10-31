"""add nombre_generico nullable

Revision ID: 4b9d44257f01
Revises: b10d00bcc8f6
Create Date: 2025-10-31 12:57:15.554412

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '4b9d44257f01'
down_revision = 'b10d00bcc8f6'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("producto", "nombre_generico", existing_type=sa.String(), nullable=True)


def downgrade():
    op.alter_column("producto", "nombre_generico", existing_type=sa.String(), nullable=False)
