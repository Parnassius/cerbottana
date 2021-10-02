from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete

import cerbottana.databases.database as d
from cerbottana.database import Database

from . import init_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection


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
