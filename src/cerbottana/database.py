from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from cerbottana import utils

if TYPE_CHECKING:
    from collections.abc import Iterator


class Database:
    _instances: ClassVar[dict[str, Database]] = {}

    def __init__(self, dbname: str) -> None:
        dbpath = str(utils.get_config_file(f"{dbname}.sqlite"))
        engine = f"sqlite:///{dbpath}"
        self.engine = create_engine(engine)
        self.Session = sessionmaker(self.engine)
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
