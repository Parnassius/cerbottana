# pylint: disable=too-few-public-methods

from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base

from database import Database

db = Database.open()

Base = declarative_base(metadata=db.metadata)


class Badges(Base):
    __table__ = Table("badges", Base.metadata, autoload=True)


class EightBall(Base):
    __table__ = Table("eightball", Base.metadata, autoload=True)


class Quotes(Base):
    __table__ = Table("quotes", Base.metadata, autoload=True)


class Repeats(Base):
    __table__ = Table("repeats", Base.metadata, autoload=True)


class Tokens(Base):
    __table__ = Table("tokens", Base.metadata, autoload=True)


class Users(Base):
    __table__ = Table("users", Base.metadata, autoload=True)
