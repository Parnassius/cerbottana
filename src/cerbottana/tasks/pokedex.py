from typing import TYPE_CHECKING

import pokedex

from cerbottana import utils
from cerbottana.tasks import init_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection


@init_task_wrapper()
async def setup_database(conn: Connection) -> None:  # noqa: ARG001
    path = utils.get_config_file("pokedex_cache")
    path.mkdir(exist_ok=True)
    pokedex.load_all(path)
