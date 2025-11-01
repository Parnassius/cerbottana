from typing import TYPE_CHECKING

from pokedex import pokedex

from cerbottana import utils
from cerbottana.tasks import init_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection


@init_task_wrapper()
async def setup_database(conn: Connection) -> None:  # noqa: ARG001
    pokedex.setup_database(utils.get_config_file("pokedex.sqlite"))
