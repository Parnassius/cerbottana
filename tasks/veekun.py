from __future__ import annotations

import csv
import inspect
from typing import TYPE_CHECKING

from sqlalchemy.sql import func

import databases.veekun as v
from database import Database
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


@init_task_wrapper()
async def csv_to_sqlite(conn: Connection) -> None:
    open("./veekun.sqlite", "w").close()  # truncate database

    db = Database.open("veekun")

    v.Base.metadata.create_all(db.engine)

    tables_classes = {
        obj.__tablename__: obj
        for name, obj in inspect.getmembers(v)
        if inspect.isclass(obj)
        and obj.__module__ == v.__name__
        and hasattr(obj, "__tablename__")
    }

    with db.get_session() as session:
        for table in v.Base.metadata.sorted_tables:
            tname = table.key
            with open("./data/veekun/" + tname + ".csv", "r") as f:
                csv_data = csv.DictReader(f)
                csv_keys = csv_data.fieldnames

                if csv_keys is not None:
                    session.execute(
                        tables_classes[tname].__table__.insert(),
                        [dict(i) for i in csv_data],
                    )

                    if "identifier" in csv_keys:
                        session.execute(
                            tables_classes[tname]
                            .__table__.update()
                            .values(
                                identifier=func.replace(
                                    tables_classes[tname].__table__.c.identifier,
                                    "-",
                                    "",
                                )
                            )
                        )
