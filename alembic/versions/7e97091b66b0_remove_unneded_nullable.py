"""remove_unneded_nullable

Revision ID: 7e97091b66b0
Revises: c5b59a5d8dd6
Create Date: 2020-08-21 22:38:38.866052

"""
from sqlalchemy import Index, UniqueConstraint

from alembic import op

# revision identifiers, used by Alembic.
revision = "7e97091b66b0"
down_revision = "c5b59a5d8dd6"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_database():
    with op.batch_alter_table("badges") as batch_op:
        batch_op.alter_column("image", nullable=False)
        batch_op.alter_column("label", nullable=False)

    with op.batch_alter_table("eightball") as batch_op:
        batch_op.alter_column("answer", nullable=False)

    with op.batch_alter_table(
        "quotes",
        table_args=(
            UniqueConstraint("message", "roomid", sqlite_on_conflict="IGNORE"),
        ),
    ) as batch_op:
        batch_op.alter_column("message", nullable=False)
        batch_op.alter_column("roomid", nullable=False)

    with op.batch_alter_table(
        "repeats",
        table_args=(
            UniqueConstraint("message", "roomid", sqlite_on_conflict="REPLACE"),
        ),
    ) as batch_op:
        batch_op.alter_column("message", nullable=False)
        batch_op.alter_column("roomid", nullable=False)
        batch_op.alter_column("delta_minutes", nullable=False)
        batch_op.alter_column("initial_dt", nullable=False)
        batch_op.alter_column("expire_dt")

    with op.batch_alter_table("tokens") as batch_op:
        batch_op.alter_column("token", nullable=False)
        batch_op.alter_column("rank", nullable=False)
        batch_op.alter_column("expiry", nullable=False)

    with op.batch_alter_table(
        "users", table_args=(UniqueConstraint("userid", sqlite_on_conflict="IGNORE"),)
    ) as batch_op:
        batch_op.alter_column("userid", nullable=False)


def downgrade_database():
    with op.batch_alter_table("badges") as batch_op:
        batch_op.alter_column("image", nullable=True)
        batch_op.alter_column("label", nullable=True)

    with op.batch_alter_table("eightball") as batch_op:
        batch_op.alter_column("answer", nullable=True)

    with op.batch_alter_table(
        "quotes",
        table_args=(
            UniqueConstraint("message", "roomid", sqlite_on_conflict="IGNORE"),
        ),
    ) as batch_op:
        batch_op.alter_column("message", nullable=True)
        batch_op.alter_column("roomid", nullable=True)

    with op.batch_alter_table(
        "repeats",
        table_args=(
            UniqueConstraint("message", "roomid", sqlite_on_conflict="REPLACE"),
        ),
    ) as batch_op:
        batch_op.alter_column("message", nullable=True)
        batch_op.alter_column("roomid", nullable=True)
        batch_op.alter_column("delta_minutes", nullable=True)
        batch_op.alter_column("initial_dt", nullable=True)
        batch_op.alter_column("expire_dt")

    with op.batch_alter_table("tokens") as batch_op:
        batch_op.alter_column("token", nullable=True)
        batch_op.alter_column("rank", nullable=True)
        batch_op.alter_column("expiry", nullable=True)

    with op.batch_alter_table(
        "users", table_args=(UniqueConstraint("userid", sqlite_on_conflict="IGNORE"),)
    ) as batch_op:
        batch_op.alter_column("userid", nullable=True)


def upgrade_logs():
    op.drop_index("ix_logs_roomid_userid_date")
    op.drop_index("ix_logs_roomid_userrank_date")
    with op.batch_alter_table(
        "logs",
        table_args=(
            Index("ix_logs_roomid_userid_date", "roomid", "userid", "date"),
            Index("ix_logs_roomid_userrank_date", "roomid", "userrank", "date"),
        ),
    ) as batch_op:
        batch_op.alter_column("roomid", nullable=False)
        batch_op.alter_column("date", nullable=False)

    op.drop_index("ix_daily_totals_per_rank_roomid_userrank_date")
    with op.batch_alter_table(
        "daily_totals_per_rank",
        table_args=(
            Index(
                "ix_daily_totals_per_rank_roomid_userrank_date",
                "roomid",
                "userrank",
                "date",
            ),
        ),
    ) as batch_op:
        batch_op.alter_column("roomid", nullable=False)
        batch_op.alter_column("date", nullable=False)
        batch_op.alter_column("userrank", nullable=False)
        batch_op.alter_column("messages", nullable=False)

    op.drop_index("ix_daily_totals_per_rank_roomid_userid_date")
    with op.batch_alter_table(
        "daily_totals_per_user",
        table_args=(
            Index(
                "ix_daily_totals_per_rank_roomid_userid_date",
                "roomid",
                "userid",
                "date",
            ),
        ),
    ) as batch_op:
        batch_op.alter_column("roomid", nullable=False)
        batch_op.alter_column("date", nullable=False)
        batch_op.alter_column("userid", nullable=False)
        batch_op.alter_column("messages", nullable=False)


def downgrade_logs():
    op.drop_index("ix_logs_roomid_userid_date")
    op.drop_index("ix_logs_roomid_userrank_date")
    with op.batch_alter_table(
        "logs",
        table_args=(
            Index("ix_logs_roomid_userid_date", "roomid", "userid", "date"),
            Index("ix_logs_roomid_userrank_date", "roomid", "userrank", "date"),
        ),
    ) as batch_op:
        batch_op.alter_column("roomid", nullable=True)
        batch_op.alter_column("date", nullable=True)

    op.drop_index("ix_daily_totals_per_rank_roomid_userrank_date")
    with op.batch_alter_table(
        "daily_totals_per_rank",
        table_args=(
            Index(
                "ix_daily_totals_per_rank_roomid_userrank_date",
                "roomid",
                "userrank",
                "date",
            ),
        ),
    ) as batch_op:
        batch_op.alter_column("roomid", nullable=True)
        batch_op.alter_column("date", nullable=True)
        batch_op.alter_column("userrank", nullable=True)
        batch_op.alter_column("messages", nullable=True)

    op.drop_index("ix_daily_totals_per_rank_roomid_userid_date")
    with op.batch_alter_table(
        "daily_totals_per_user",
        table_args=(
            Index(
                "ix_daily_totals_per_rank_roomid_userid_date",
                "roomid",
                "userid",
                "date",
            ),
        ),
    ) as batch_op:
        batch_op.alter_column("roomid", nullable=True)
        batch_op.alter_column("date", nullable=True)
        batch_op.alter_column("userid", nullable=True)
        batch_op.alter_column("messages", nullable=True)
