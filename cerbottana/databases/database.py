from __future__ import annotations

from typing import Annotated

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

intpk = Annotated[int, mapped_column(primary_key=True)]  # pylint: disable=invalid-name


class Base(DeclarativeBase):
    pass


class Badges(Base):
    __tablename__ = "badges"

    id: Mapped[intpk]
    userid: Mapped[str | None] = mapped_column(index=True)
    image: Mapped[str]
    label: Mapped[str]


class CustomPermissions(Base):
    __tablename__ = "custom_permissions"
    __table_opts__ = (
        UniqueConstraint("roomid", "command", sqlite_on_conflict="REPLACE"),
    )

    id: Mapped[intpk]
    roomid: Mapped[str]
    command: Mapped[str]
    required_rank: Mapped[str]


class EightBall(Base):
    __tablename__ = "eightball"
    __table_opts__ = (
        UniqueConstraint("answer", "roomid", sqlite_on_conflict="IGNORE"),
    )

    id: Mapped[intpk]
    answer: Mapped[str]
    roomid: Mapped[str]


class Quotes(Base):
    __tablename__ = "quotes"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="IGNORE"),
    )

    id: Mapped[intpk]
    message: Mapped[str]
    roomid: Mapped[str]
    author: Mapped[str | None]
    date: Mapped[str | None]


class Repeats(Base):
    __tablename__ = "repeats"
    __table_opts__ = (
        UniqueConstraint("message", "roomid", sqlite_on_conflict="REPLACE"),
    )

    id: Mapped[intpk]
    message: Mapped[str]
    roomid: Mapped[str]
    delta_minutes: Mapped[int]
    initial_dt: Mapped[str]
    expire_dt: Mapped[str | None]


class TemporaryVoices(Base):
    __tablename__ = "temporary_voices"
    __table_opts__ = (
        UniqueConstraint("roomid", "userid", sqlite_on_conflict="IGNORE"),
    )

    id: Mapped[intpk]
    roomid: Mapped[str]
    userid: Mapped[str]
    date: Mapped[str]


class Users(Base):
    __tablename__ = "users"
    __table_opts__ = (UniqueConstraint("userid", sqlite_on_conflict="IGNORE"),)

    id: Mapped[intpk]
    userid: Mapped[str]
    username: Mapped[str | None]
    avatar: Mapped[str | None]
    description: Mapped[str | None]
    description_pending: Mapped[str | None] = mapped_column(index=True)
    icon: Mapped[str | None]
