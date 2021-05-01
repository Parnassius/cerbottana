from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete

import databases.database as d
from database import Database
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


@init_task_wrapper(priority=5)
async def cleanup_table(conn: Connection) -> None:
    db = Database.open()
    with db.get_session() as session:
        stmt = (
            delete(d.Tokens)
            .where(d.Tokens.expiry < str(datetime.utcnow()))
            .execution_options(synchronize_session=False)
        )
        session.execute(stmt)
