from __future__ import annotations

import asyncio
import signal
import threading
from queue import SimpleQueue
from types import FrameType

from connection import CONNECTION
from server import SERVER


def shutdown(
    sig: signal.Signals, frame_type: FrameType,  # pylint: disable=no-member
) -> None:
    if CONNECTION.websocket is not None and CONNECTION.loop is not None:
        for task in asyncio.all_tasks(loop=CONNECTION.loop):
            task.cancel()
        coro = CONNECTION.websocket.close()
        asyncio.run_coroutine_threadsafe(coro, CONNECTION.loop)


def main() -> None:
    queue: SimpleQueue[str] = SimpleQueue()
    threading.Thread(target=SERVER.serve_forever, args=(queue,), daemon=True).start()
    threading.Thread(target=CONNECTION.open_connection, args=(queue,)).start()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    main()
