import asyncio
import threading
import signal
from types import FrameType

from server import SERVER

from connection import CONNECTION


if __name__ == "__main__":
    threading.Thread(target=SERVER.serve_forever, daemon=True).start()
    threading.Thread(target=CONNECTION.open_connection).start()

    def shutdown(signal: signal.Signals, frame_type: FrameType) -> None:
        try:
            if CONNECTION.websocket is not None and CONNECTION.loop is not None:
                coro = CONNECTION.websocket.close()
                asyncio.run_coroutine_threadsafe(coro, CONNECTION.loop)
        except:
            pass

    signal.signal(signal.SIGINT, shutdown)
