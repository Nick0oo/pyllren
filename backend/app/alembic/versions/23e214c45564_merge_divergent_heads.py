"""merge divergent heads

Revision ID: 23e214c45564
Revises: 4b9d44257f01, a1b2c3d4e5f6, bc23d45e67ab
Create Date: 2025-12-15 16:28:14.685512

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '23e214c45564'
down_revision = ('4b9d44257f01', 'a1b2c3d4e5f6', 'bc23d45e67ab')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
