# pylint: disable=too-few-public-methods

from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base

from database import Database

db = Database.open("logs")

Base = declarative_base(metadata=db.metadata)


class Logs(Base):
    __table__ = Table("logs", Base.metadata, autoload=True)
