from __future__ import annotations

from typing import TYPE_CHECKING

import cerbottana.databases.database as d
from cerbottana.database import Database
from cerbottana.tasks import init_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection


@init_task_wrapper()
async def create_or_upgrade_database(conn: Connection) -> None:  # noqa: ARG001
    db = Database.open()
    d.Base.metadata.create_all(db.engine)
