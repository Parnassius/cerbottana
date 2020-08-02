from __future__ import annotations

import asyncio
import signal
import threading
from queue import SimpleQueue
from types import FrameType

from connection import CONNECTION
from server import SERVER

if __name__ == "__main__":
    queue: SimpleQueue[str] = SimpleQueue()

    threading.Thread(target=SERVER.serve_forever, args=(queue,), daemon=True).start()
    threading.Thread(target=CONNECTION.open_connection, args=(queue,)).start()

    def shutdown(
        sig: signal.Signals, frame_type: FrameType
    ) -> None:  # pylint: disable=unused-argument
        try:
            if CONNECTION.websocket is not None and CONNECTION.loop is not None:
                for task in asyncio.all_tasks(loop=CONNECTION.loop):
                    task.cancel()
                coro = CONNECTION.websocket.close()
                asyncio.run_coroutine_threadsafe(coro, CONNECTION.loop)
        except:  # lgtm [py/catch-base-exception]
            pass

    signal.signal(signal.SIGINT, shutdown)
