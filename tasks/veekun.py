from __future__ import annotations

import csv
import inspect
import re
import subprocess
from os.path import isfile
from typing import TYPE_CHECKING

from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import func

import databases.veekun as v
from database import Database
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


@init_task_wrapper(skip_unittesting=True)
async def csv_to_sqlite(conn: Connection) -> None:
    latest_veekun_commit = ""
    try:
        latest_veekun_commit = (
            subprocess.run(
                [
                    "git",
                    "rev-list",
                    "-1",
                    "HEAD",
                    "--",
                    "data/veekun",
                    "databases/veekun.py",
                    "tasks/veekun.py",
                ],
                capture_output=True,
                check=True,
            )
            .stdout.decode()
            .strip()
        )
        db = Database.open("veekun")
        with db.get_session() as session:
            db_commit = session.query(  # type: ignore  # sqlalchemy
                v.LatestCommit.commit_id
            ).scalar()
            if db_commit == latest_veekun_commit:
                return  # database is already up-to-date, skip rebuild

    except (
        subprocess.SubprocessError,  # generic subprocess error
        FileNotFoundError,  # git is not available
        OperationalError,  # table does not exist
    ):
        pass  # always rebuild on error

    print("Rebuilding veekun database...")

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
        if latest_veekun_commit:
            session.add(v.LatestCommit(commit_id=latest_veekun_commit))

        for table in v.Base.metadata.sorted_tables:
            tname = table.key
            if isfile("./data/veekun/" + tname + ".csv"):
                with open("./data/veekun/" + tname + ".csv") as f:
                    csv_data = csv.DictReader(f)
                    csv_keys = csv_data.fieldnames

                    if csv_keys is not None:
                        data = [dict(i) for i in csv_data]

                        if tname == "locations":
                            for row in data:
                                if num := re.search(r"route-(\d+)", row["identifier"]):
                                    row["route_number"] = num[1]

                        session.bulk_insert_mappings(tables_classes[tname], data)

                        if "identifier" in csv_keys:
                            session.query(tables_classes[tname]).update(
                                {
                                    tables_classes[tname].identifier: func.replace(
                                        tables_classes[tname].identifier, "-", ""
                                    )
                                },
                                synchronize_session=False,
                            )

    print("Done.")
