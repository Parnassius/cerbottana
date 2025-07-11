from __future__ import annotations

import asyncio

from cerbottana.connection import Connection
from cerbottana.utils import env


def main() -> None:
    host = env.str("SHOWDOWN_HOST")
    port = env.int("SHOWDOWN_PORT")
    protocol = "wss" if port == 443 else "ws"
    url = f"{protocol}://{host}:{port}/showdown/websocket"

    conn = Connection(
        url=url,
        username=env.str("USERNAME"),
        password=env.str("PASSWORD"),
        avatar=env.str("AVATAR", default=""),
        statustext=env.str("STATUSTEXT", default=""),
        rooms=env.list("ROOMS", default=[]),
        main_room=env.str("MAIN_ROOM"),
        command_character=env.str("COMMAND_CHARACTER"),
        base_url=env.str("BASE_URL"),
        webhooks=env.json("WEBHOOKS", default={}),
    )

    asyncio.run(conn.open_connection())


if __name__ == "__main__":
    main()
