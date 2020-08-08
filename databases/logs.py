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
    roomid = Column(String)
    date = Column(String, index=True)
    time = Column(String)
    userrank = Column(String)
    userid = Column(String)
    message = Column(String)
