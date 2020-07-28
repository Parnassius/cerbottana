from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session


class Database:
    _instances: Dict[str, Database] = dict()

    def __init__(self, dbname: str) -> None:
        self.engine = create_engine(f"sqlite:///{dbname}.sqlite", echo=True)
        self.metadata = MetaData(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._instances[dbname] = self

    @classmethod
    def open(cls, dbname: str = "database") -> Database:
        if dbname not in cls._instances:
            cls(dbname)
        return cls._instances[dbname]

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
