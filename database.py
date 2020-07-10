from typing import Iterable, Any

import sqlite3


class Database:
    def __init__(self, dbname: str = "database") -> None:
        self.db = sqlite3.connect(f"./{dbname}.sqlite")
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

    @property
    def connection(self) -> sqlite3.Connection:
        return self.db

    def executemany(
        self, sql: str, params: Iterable[Iterable[Any]] = []
    ) -> sqlite3.Cursor:
        return self.cursor.executemany(sql, params)

    def executenow(self, sql: str, params: Iterable[Any] = []) -> sqlite3.Cursor:
        cur = self.execute(sql, params)
        self.commit()
        return cur

    def execute(self, sql: str, params: Iterable[Any] = []) -> sqlite3.Cursor:
        return self.cursor.execute(sql, params)

    def commit(self) -> None:
        self.db.commit()

    def __del__(self) -> None:
        self.db.close()
