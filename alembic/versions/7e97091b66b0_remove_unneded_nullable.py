"""remove_unneded_nullable

Revision ID: 7e97091b66b0
Revises: c5b59a5d8dd6
Create Date: 2020-08-21 22:38:38.866052

"""
# pylint: skip-file
from sqlalchemy import Index, UniqueConstraint

from alembic import op

# revision identifiers, used by Alembic.
revision = "7e97091b66b0"
down_revision = "87f3857ce29a"
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
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
