# pylint: disable=too-few-public-methods

from sqlalchemy import Integer, String, Column, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

from database import Database

db = Database.open()

Base = declarative_base(metadata=db.metadata)


class Badges(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True)
    userid = Column(String, index=True)
    image = Column(String)
    label = Column(String)


class EightBall(Base):
    __tablename__ = "eightball"
    id = Column(Integer, primary_key=True)
    answer = Column(String)


class Quotes(Base):
    __tablename__ = "quotes"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="IGNORE"),
    )

    id = Column(Integer, primary_key=True)
    message = Column(String)
    roomid = Column(String)
    author = Column(String)
    date = Column(String)


class Repeats(Base):
    __tablename__ = "repeats"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="REPLACE"),
    )

    id = Column(Integer, primary_key=True)
    message = Column(String)
    roomid = Column(String)
    delta_minutes = Column(Integer)
    initial_dt = Column(String)
    expire_dt = Column(String)
    message = Column(String)


class Tokens(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String, index=True)
    room = Column(String)
    rank = Column(String)
    expiry = Column(String)


class Users(Base):
    __tablename__ = "users"
    __table_opts__ = (UniqueConstraint("userid", sqlite_on_conflict="IGNORE"),)

    id = Column(Integer, primary_key=True)
    userid = Column(String)
    username = Column(String)
    avatar = Column(String)
    description = Column(String)
    description_pending = Column(String, index=True)
