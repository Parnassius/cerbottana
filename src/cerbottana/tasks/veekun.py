import csv
import inspect
import re
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING
from zlib import crc32

from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import OperationalError

import cerbottana.databases.veekun as v
from cerbottana import utils
from cerbottana.database import Database
from cerbottana.tasks import init_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection


@init_task_wrapper()
async def csv_to_sqlite(conn: Connection) -> None:  # noqa: ARG001
    csv_dir = Path(__file__).parent.parent / "data/veekun"
    files = chain(
        csv_dir.iterdir(),
        (
            Path(__file__).parent.parent / x
            for x in ["databases/veekun.py", "tasks/veekun.py"]
        ),
    )
    new_crc = crc32(b"")
    for file in sorted(files):
        new_crc = crc32(file.read_bytes(), new_crc)

    try:
        db = Database.open("veekun")
        with db.get_session() as session:
            stmt = select(v.LatestVersion.crc)
            if session.scalar(stmt) == new_crc:
                return  # database is already up-to-date, skip rebuild

    except OperationalError:  # table does not exist
        pass  # always rebuild on error

    print("Rebuilding veekun database...")

    with utils.get_config_file("veekun.sqlite").open("wb"):  # truncate database
        pass

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
        session.add(v.LatestVersion(crc=new_crc))

        for table in v.Base.metadata.sorted_tables:
            tname = table.key
            csv_file = utils.get_data_file(f"veekun/{tname}.csv")
            if csv_file.is_file():
                with csv_file.open(encoding="utf-8") as f:
                    csv_data = csv.DictReader(f)
                    csv_keys = csv_data.fieldnames

                    if csv_keys is not None:
                        data = [dict(i) for i in csv_data]

                        if hasattr(table.columns, "name_normalized"):
                            for row in data:
                                row["name_normalized"] = utils.to_user_id(
                                    utils.remove_diacritics(row["name"])
                                )

                        if tname == "locations":
                            for row in data:
                                if num := re.search(r"route-(\d+)", row["identifier"]):
                                    row["route_number"] = num[1]

                        bulk_insert_stmt = insert(tables_classes[tname])
                        session.execute(bulk_insert_stmt, data)

                        if "identifier" in csv_keys:
                            bulk_update_stmt = (
                                update(tables_classes[tname])
                                .values(
                                    identifier=func.replace(
                                        tables_classes[tname].identifier, "-", ""
                                    )
                                )
                                .execution_options(synchronize_session=False)
                            )
                            session.execute(bulk_update_stmt)

    print("Done.")
