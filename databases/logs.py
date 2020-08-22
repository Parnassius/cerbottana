# pylint: disable=too-few-public-methods

from sqlalchemy import Column, Index, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from database import Database

db = Database.open("logs")

Base = declarative_base(metadata=db.metadata)


class Logs(Base):
    __tablename__ = "logs"
    __table_opts__ = (
        Index("ix_logs_roomid_userid_date", "roomid", "userid", "date"),
        Index("ix_logs_roomid_userrank_date", "roomid", "userrank", "date"),
    )

    id = Column(Integer, primary_key=True)
    roomid = Column(String, nullable=False)
    date = Column(String, index=True, nullable=False)
    time = Column(String)
    userrank = Column(String)
    userid = Column(String)
    message = Column(String)


class DailyTotalsPerRank(Base):
    __tablename__ = "daily_totals_per_rank"
    __table_opts__ = (
        Index(
            "ix_daily_totals_per_rank_roomid_userrank_date",
            "roomid",
            "userrank",
            "date",
        ),
    )

    id = Column(Integer, primary_key=True)
    roomid = Column(String, nullable=False)
    date = Column(String, index=True, nullable=False)
    userrank = Column(String, nullable=False)
    messages = Column(Integer, nullable=False)


class DailyTotalsPerUser(Base):
    __tablename__ = "daily_totals_per_user"
    __table_opts__ = (
        Index(
            "ix_daily_totals_per_rank_roomid_userid_date", "roomid", "userid", "date"
        ),
    )

    id = Column(Integer, primary_key=True)
    roomid = Column(String, nullable=False)
    date = Column(String, index=True, nullable=False)
    userid = Column(String, nullable=False)
    messages = Column(Integer, nullable=False)
