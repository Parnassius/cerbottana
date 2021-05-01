from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker


class Database:
    _instances: dict[str, Database] = {}

    def __init__(self, dbname: str) -> None:
        self.engine = create_engine(f"sqlite:///{dbname}.sqlite", future=True)
        self.session_factory = sessionmaker(  # type: ignore[call-overload]
            self.engine, future=True
        )
        self.Session = scoped_session(self.session_factory)
        self._instances[dbname] = self

    @classmethod
    def open(cls, dbname: str = "database") -> Database:
        if dbname not in cls._instances:
            cls(dbname)
        return cls._instances[dbname]

    @contextmanager
    def get_session(self, language_id: int | None = None) -> Iterator[Session]:
        session = self.Session()
        if language_id:
            session.info["language_id"] = language_id
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
