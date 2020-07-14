from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from typing_extensions import TypedDict

from database import Database
from inittasks import inittask_wrapper

if TYPE_CHECKING:
    from connection import Connection


TablesDict = TypedDict(
    "TablesDict", {"name": str, "columns": Dict[str, str], "keys": List[str]}
)


@inittask_wrapper(priority=1)
async def initialize_database(conn: Connection) -> None:
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'metadata'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE metadata (
            id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE UNIQUE INDEX idx_unique_metadata_key
        ON metadata (
            key
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_metadata', '1')"
        db.execute(sql)

        db.commit()
