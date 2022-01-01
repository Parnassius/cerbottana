from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from . import init_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection


@init_task_wrapper(skip_unittesting=True)
async def create_or_upgrade_database(conn: Connection) -> None:
    subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        cwd=Path(__file__).parent.parent.parent,
        check=True,
    )
