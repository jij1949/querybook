"""add_catalog_display

Revision ID: 58a7907a75df
Revises: 56f99f47af3f
Create Date: 2025-12-19 17:09:36.431622

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '58a7907a75df'
down_revision = '56f99f47af3f'
branch_labels = None
depends_on = None


def upgrade():
    # Add catalog display configuration as a JSON column
    # MySQL doesn't support default values for JSON columns, so we:
    # 1. Add as nullable
    # 2. Populate with default value
    # 3. Make NOT NULL

    # Step 1: Add the column as nullable
    op.add_column(
        'query_metastore',
        sa.Column(
            'catalog_display_config',
            mysql.JSON,
            nullable=True
        )
    )

    # Step 2: Set default value for existing rows
    op.execute(
        sa.text(
            "UPDATE query_metastore "
            "SET catalog_display_config = :config "
            "WHERE catalog_display_config IS NULL"
        ),
        {"config": '{"show_catalog_in_ui": false}'}
    )

    # Step 3: Make the column NOT NULL
    op.alter_column(
        'query_metastore',
        'catalog_display_config',
        nullable=False,
        existing_type=mysql.JSON
    )


def downgrade():
    op.drop_column('query_metastore', 'catalog_display_config')
