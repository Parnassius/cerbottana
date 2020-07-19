from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from typing_extensions import TypedDict

from database import Database
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


TablesDict = TypedDict(
    "TablesDict", {"name": str, "columns": Dict[str, str], "keys": List[str]}
)


@init_task_wrapper()
async def create_table(conn: Connection) -> None:
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'tokens'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE tokens (
            id INTEGER,
            token TEXT,
            room TEXT,
            rank TEXT,
            expiry TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE INDEX idx_tokens_token
        ON tokens (
            token
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_tokens', '1')"
        db.execute(sql)

        db.commit()


@init_task_wrapper(priority=5)
async def cleanup_table(conn: Connection) -> None:
    db = Database()

    sql = "DELETE FROM tokens WHERE JULIANDAY() - JULIANDAY(expiry) > 0"
    db.executenow(sql)
