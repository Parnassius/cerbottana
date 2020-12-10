# pylint: disable=too-few-public-methods

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

from database import Database

db = Database.open()

Base = declarative_base(metadata=db.metadata)


class Badges(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True)
    userid = Column(String, index=True)
    image = Column(String, nullable=False)
    label = Column(String, nullable=False)


class EightBall(Base):
    __tablename__ = "eightball"
    __table_opts__ = (
        UniqueConstraint("answer", "roomid", sqlite_on_conflict="IGNORE"),
    )

    id = Column(Integer, primary_key=True)
    answer = Column(String, nullable=False)
    roomid = Column(String, nullable=False)


class Quotes(Base):
    __tablename__ = "quotes"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="IGNORE"),
    )

    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=False)
    roomid = Column(String, nullable=False)
    author = Column(String)
    date = Column(String)


class Repeats(Base):
    __tablename__ = "repeats"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="REPLACE"),
    )

    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=False)
    roomid = Column(String, nullable=False)
    delta_minutes = Column(Integer, nullable=False)
    initial_dt = Column(String, nullable=False)
    expire_dt = Column(String)


class Tokens(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String, index=True, nullable=False)
    room = Column(String)
    rank = Column(String, nullable=False)
    expiry = Column(String, nullable=False)


class Users(Base):
    __tablename__ = "users"
    __table_opts__ = (UniqueConstraint("userid", sqlite_on_conflict="IGNORE"),)

    id = Column(Integer, primary_key=True)
    userid = Column(String, nullable=False)
    username = Column(String)
    avatar = Column(String)
    description = Column(String)
    description_pending = Column(String, index=True)
