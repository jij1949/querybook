"""update event_type in event_log table

Revision ID: 63bde0162416
Revises: 27ed76f75107
Create Date: 2022-12-22 20:51:47.678915

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "63bde0162416"
down_revision = "27ed76f75107"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "event_log",
        "event_type",
        existing_type=sa.Enum("API", "VIEW", "CLICK", name="eventtype"),
        type_=sa.Enum("API", "WEBSOCKET", "VIEW", "CLICK", name="eventtype"),
    )


def downgrade():
    op.alter_column(
        "event_log",
        "event_type",
        existing_type=sa.Enum("API", "WEBSOCKET", "VIEW", "CLICK", name="eventtype"),
        type_=sa.Enum("API", "VIEW", "CLICK", name="eventtype"),
    )
