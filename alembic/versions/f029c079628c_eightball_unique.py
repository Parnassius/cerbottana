"""eightball_unique

Revision ID: f029c079628c
Revises: 7e97091b66b0
Create Date: 2020-10-17 21:10:58.091866

"""
# pylint: skip-file
from sqlalchemy import Column, Integer, MetaData, String, Table, UniqueConstraint

from alembic import op

# revision identifiers, used by Alembic.
revision = "f029c079628c"
down_revision = "7e97091b66b0"
branch_labels = None
depends_on = None


def upgrade():
    meta = MetaData()

    with op.batch_alter_table(
        "eightball",
        reflect_args=(
            UniqueConstraint(
                "answer", name="unique_answer", sqlite_on_conflict="IGNORE"
            ),
        ),
    ) as batch_op:
        # dummy operation
        batch_op.alter_column("id")

    with op.batch_alter_table(
        "quotes",
        copy_from=Table(
            "quotes",
            meta,
            Column("id", Integer, primary_key=True),
            Column("message", String, nullable=False),
            Column("roomid", String, nullable=False),
            Column("author", String),
            Column("date", String),
            UniqueConstraint(
                "message",
                "roomid",
                name="unique_message_roomid",
                sqlite_on_conflict="IGNORE",
            ),
        ),
    ) as batch_op:
        # dummy operation
        batch_op.alter_column("id")

    with op.batch_alter_table(
        "repeats",
        copy_from=Table(
            "repeats",
            meta,
            Column("id", Integer, primary_key=True),
            Column("message", String, nullable=False),
            Column("roomid", String, nullable=False),
            Column("delta_minutes", Integer, nullable=False),
            Column("initial_dt", String, nullable=False),
            Column("expire_dt", String),
            UniqueConstraint(
                "message",
                "roomid",
                name="unique_message_roomid",
                sqlite_on_conflict="REPLACE",
            ),
        ),
    ) as batch_op:
        # dummy operation
        batch_op.alter_column("id")

    with op.batch_alter_table(
        "users",
        copy_from=Table(
            "users",
            meta,
            Column("id", Integer, primary_key=True),
            Column("userid", String, nullable=False),
            Column("username", String),
            Column("avatar", String),
            Column("description", String),
            Column("description_pending", String, index=True),
            UniqueConstraint(
                "userid", name="unique_userid", sqlite_on_conflict="IGNORE"
            ),
        ),
    ) as batch_op:
        # dummy operation
        batch_op.alter_column("id")


def downgrade():
    with op.batch_alter_table("eightball") as batch_op:
        batch_op.drop_constraint("unique_answer")
