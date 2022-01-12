from __future__ import annotations

import asyncio
import signal
from types import FrameType

from typenv import Env

from .connection import Connection


def main() -> None:
    def shutdown(sig: int, frame_type: FrameType | None) -> None:
        if conn.websocket is not None and conn.loop is not None:
            for task in asyncio.all_tasks(conn.loop):
                task.cancel()
            coro = conn.websocket.close()
            asyncio.run_coroutine_threadsafe(coro, conn.loop)

    env = Env()
    env.read_env()

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
        administrators=env.list("ADMINISTRATORS", default=[]),
        webhooks=env.json("WEBHOOKS", default={}),
    )

    signal.signal(signal.SIGINT, shutdown)

    conn.open_connection()


if __name__ == "__main__":

    main()
