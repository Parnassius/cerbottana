"""Per-room eightball answers

Revision ID: 21bfb4710834
Revises: f029c079628c
Create Date: 2020-12-06 17:11:25.270563

"""
from environs import Env
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    column,
    select,
    table,
)

from alembic import op

# revision identifiers, used by Alembic.
revision = "21bfb4710834"
down_revision = "f029c079628c"
branch_labels = None
depends_on = None


env = Env()
env.read_env()

main_room = env("MAIN_ROOM")
rooms = env.list("ROOMS", [])


def upgrade():
    meta = MetaData()

    with op.batch_alter_table("eightball") as batch_op:
        batch_op.add_column(
            Column("roomid", String, nullable=False, server_default=main_room)
        )

    with op.batch_alter_table(
        "eightball",
        copy_from=Table(
            "eightball",
            meta,
            Column("id", Integer, primary_key=True),
            Column("answer", String, nullable=False),
            Column("roomid", String, nullable=False),
            UniqueConstraint(
                "answer",
                "roomid",
                name="unique_answer_roomid",
                sqlite_on_conflict="IGNORE",
            ),
        ),
    ) as batch_op:
        # dummy operation
        batch_op.alter_column("id")

    eightball = table(
        "eightball",
        Column("answer", String),
        Column("roomid", String),
    )

    for room in set(rooms) - {main_room}:
        op.execute(
            eightball.insert().from_select(
                ["answer", "roomid"],
                select([eightball.c.answer, op.inline_literal(room)]).where(
                    eightball.c.roomid == main_room
                ),
            )
        )


def downgrade():
    meta = MetaData()

    with op.batch_alter_table(
        "eightball",
        copy_from=Table(
            "eightball",
            meta,
            Column("id", Integer, primary_key=True),
            Column("answer", String, nullable=False),
            UniqueConstraint(
                "answer",
                name="unique_answer",
                sqlite_on_conflict="IGNORE",
            ),
        ),
    ) as batch_op:
        # dummy operation
        batch_op.alter_column("id")
