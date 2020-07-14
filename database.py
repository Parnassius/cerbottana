import sqlite3
from typing import Any, Iterable


class Database:
    def __init__(self, dbname: str = "database") -> None:
        self.db = sqlite3.connect(f"./{dbname}.sqlite", check_same_thread=False)
        self.db.row_factory = sqlite3.Row

    @property
    def connection(self) -> sqlite3.Connection:
        return self.db

    def executemany(
        self, sql: str, params: Iterable[Iterable[Any]] = []
    ) -> sqlite3.Cursor:
        return self.db.executemany(sql, params)

    def executenow(self, sql: str, params: Iterable[Any] = []) -> sqlite3.Cursor:
        cur = self.execute(sql, params)
        self.commit()
        return cur

    def execute(self, sql: str, params: Iterable[Any] = []) -> sqlite3.Cursor:
        return self.db.execute(sql, params)

    def commit(self) -> None:
        self.db.commit()

    def __del__(self) -> None:
        self.db.close()
