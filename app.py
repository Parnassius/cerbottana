import asyncio
import threading
import signal

import veekun

from server import SERVER

from connection import CONNECTION


if __name__ == "__main__":
    veekun.csv_to_sqlite()

    threading.Thread(target=SERVER.serve_forever).start()
    threading.Thread(target=CONNECTION.open_connection).start()

    def shutdown(*args, **kwargs):
        try:
            SERVER.stop()
        except:
            pass
        try:
            coro = CONNECTION.websocket.close()
            asyncio.run_coroutine_threadsafe(coro, CONNECTION.loop)
        except:
            pass

    signal.signal(signal.SIGINT, shutdown)
