"""Add environment feature params

Revision ID: 111111111111
Revises: 2f40b8318af4
Create Date: 2022-08-22 16:33:00.321111

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "111111111111"
down_revision = "2f40b8318af4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "environment",
        sa.Column("feature_params", sa.JSON(), nullable=False),
    )


def downgrade():
    op.drop_column("environment", "feature_params")
