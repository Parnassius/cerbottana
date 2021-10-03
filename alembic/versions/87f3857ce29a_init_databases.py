"""Init databases

Revision ID: 87f3857ce29a
Revises:
Create Date: 2020-08-01 15:20:22.352871

"""
from sqlalchemy import Column, Index, Integer, String, UniqueConstraint

from alembic import op

# revision identifiers, used by Alembic.
revision = "87f3857ce29a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "badges",
        Column("id", Integer, primary_key=True),
        Column("userid", String, index=True),
        Column("image", String),
        Column("label", String),
    )

    op.create_table(
        "eightball", Column("id", Integer, primary_key=True), Column("answer", String)
    )

    op.create_table(
        "quotes",
        Column("id", Integer, primary_key=True),
        Column("message", String),
        Column("roomid", String),
        Column("author", String),
        Column("date", String),
        UniqueConstraint("message", "roomid", sqlite_on_conflict="IGNORE"),
    )

    op.create_table(
        "repeats",
        Column("id", Integer, primary_key=True),
        Column("message", String),
        Column("roomid", String),
        Column("delta_minutes", Integer),
        Column("initial_dt", String),
        Column("expire_dt", String),
        UniqueConstraint("message", "roomid", sqlite_on_conflict="REPLACE"),
    )

    op.create_table(
        "tokens",
        Column("id", Integer, primary_key=True),
        Column("token", String, index=True),
        Column("room", String),
        Column("rank", String),
        Column("expiry", String),
    )

    op.create_table(
        "users",
        Column("id", Integer, primary_key=True),
        Column("userid", String),
        Column("username", String),
        Column("avatar", String),
        Column("description", String),
        Column("description_pending", String, index=True),
        UniqueConstraint("userid", sqlite_on_conflict="IGNORE"),
    )


def downgrade():
    op.drop_table("badges")
    op.drop_table("eightball")
    op.drop_table("quotes")
    op.drop_table("repeats")
    op.drop_table("tokens")
    op.drop_table("users")
