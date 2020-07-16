import asyncio
import signal
import threading
from types import FrameType

from connection import CONNECTION
from server import SERVER

if __name__ == "__main__":
    threading.Thread(target=SERVER.serve_forever, daemon=True).start()
    threading.Thread(target=CONNECTION.open_connection).start()

    def shutdown(signal: signal.Signals, frame_type: FrameType) -> None:
        try:
            if CONNECTION.websocket is not None and CONNECTION.loop is not None:
                coro = CONNECTION.websocket.close()
                asyncio.run_coroutine_threadsafe(coro, CONNECTION.loop)
        except:  # lgtm [py/catch-base-exception]
            pass

    signal.signal(signal.SIGINT, shutdown)
