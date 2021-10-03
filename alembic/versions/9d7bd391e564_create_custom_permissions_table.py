"""Create custom_permissions table

Revision ID: 9d7bd391e564
Revises: 21bfb4710834
Create Date: 2021-04-10 18:43:43.425718

"""
from sqlalchemy import Column, Integer, String, UniqueConstraint

from alembic import op

# revision identifiers, used by Alembic.
revision = "9d7bd391e564"
down_revision = "21bfb4710834"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "custom_permissions",
        Column("id", Integer, primary_key=True),
        Column("roomid", String, nullable=False),
        Column("command", String, nullable=False),
        Column("required_rank", String, nullable=False),
        UniqueConstraint("roomid", "command", sqlite_on_conflict="REPLACE"),
    )


def downgrade():
    op.drop_table("custom_permissions")
