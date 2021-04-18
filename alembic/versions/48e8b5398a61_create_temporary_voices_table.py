"""Create temporary_voices table

Revision ID: 48e8b5398a61
Revises: 9d7bd391e564
Create Date: 2021-04-18 16:25:37.827903

"""
# pylint: skip-file
from sqlalchemy import Column, Integer, String, UniqueConstraint

from alembic import op

# revision identifiers, used by Alembic.
revision = "48e8b5398a61"
down_revision = "9d7bd391e564"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "temporary_voices",
        Column("id", Integer, primary_key=True),
        Column("roomid", String, nullable=False),
        Column("userid", String, nullable=False),
        Column("date", String, nullable=False),
        UniqueConstraint("roomid", "userid", sqlite_on_conflict="IGNORE"),
    )


def downgrade():
    op.drop_table("temporary_voices")
