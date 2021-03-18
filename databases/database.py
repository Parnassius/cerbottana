# pylint: disable=too-few-public-methods

from __future__ import annotations

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Badges(Base):
    __tablename__ = "badges"

    id: int = Column(Integer, primary_key=True)
    userid: str | None = Column(String, index=True)
    image: str = Column(String, nullable=False)
    label: str = Column(String, nullable=False)


class EightBall(Base):
    __tablename__ = "eightball"
    __table_opts__ = (
        UniqueConstraint("answer", "roomid", sqlite_on_conflict="IGNORE"),
    )

    id: int = Column(Integer, primary_key=True)
    answer: str = Column(String, nullable=False)
    roomid: str = Column(String, nullable=False)


class Quotes(Base):
    __tablename__ = "quotes"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="IGNORE"),
    )

    id: int = Column(Integer, primary_key=True)
    message: str = Column(String, nullable=False)
    roomid: str = Column(String, nullable=False)
    author: str | None = Column(String)
    date: str | None = Column(String)


class Repeats(Base):
    __tablename__ = "repeats"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="REPLACE"),
    )

    id: int = Column(Integer, primary_key=True)
    message: str = Column(String, nullable=False)
    roomid: str = Column(String, nullable=False)
    delta_minutes: int = Column(Integer, nullable=False)
    initial_dt: str = Column(String, nullable=False)
    expire_dt: str | None = Column(String)


class Tokens(Base):
    __tablename__ = "tokens"

    id: int = Column(Integer, primary_key=True)
    token: str = Column(String, index=True, nullable=False)
    room: str | None = Column(String)
    rank: str = Column(String, nullable=False)
    expiry: str = Column(String, nullable=False)


class Users(Base):
    __tablename__ = "users"
    __table_opts__ = (UniqueConstraint("userid", sqlite_on_conflict="IGNORE"),)

    id: int = Column(Integer, primary_key=True)
    userid: str = Column(String, nullable=False)
    username: str | None = Column(String)
    avatar: str | None = Column(String)
    description: str | None = Column(String)
    description_pending: str | None = Column(String, index=True)
