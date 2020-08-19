"""logs_daily_totals

Revision ID: c5b59a5d8dd6
Revises: 87f3857ce29a
Create Date: 2020-08-15 12:57:44.784311

"""
from sqlalchemy import Column, Index, Integer, String

from alembic import op

# revision identifiers, used by Alembic.
revision = "c5b59a5d8dd6"
down_revision = "87f3857ce29a"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_database():
    pass


def downgrade_database():
    pass


def upgrade_logs():
    op.create_table(
        "daily_totals_per_rank",
        Column("id", Integer, primary_key=True),
        Column("roomid", String),
        Column("date", String, index=True),
        Column("userrank", String),
        Column("messages", Integer),
        Index(
            "ix_daily_totals_per_rank_roomid_userrank_date",
            "roomid",
            "userrank",
            "date",
            unique=True,
        ),
    )

    op.create_table(
        "daily_totals_per_user",
        Column("id", Integer, primary_key=True),
        Column("roomid", String),
        Column("date", String, index=True),
        Column("userid", String),
        Column("messages", Integer),
        Index(
            "ix_daily_totals_per_rank_roomid_userid_date",
            "roomid",
            "userid",
            "date",
            unique=True,
        ),
    )


def downgrade_logs():
    op.drop_table("daily_totals_per_rank")
    op.drop_table("daily_totals_per_user")
