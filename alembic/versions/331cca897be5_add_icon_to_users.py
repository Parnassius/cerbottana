"""Add icon to users

Revision ID: 331cca897be5
Revises: 48e8b5398a61
Create Date: 2021-09-12 17:22:45.759614

"""
from sqlalchemy import Column, String

from alembic import op

# revision identifiers, used by Alembic.
revision = "331cca897be5"
down_revision = "48e8b5398a61"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(Column("icon", String))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("icon")
