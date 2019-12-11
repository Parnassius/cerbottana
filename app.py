import asyncio
import os
import sys
import time
import threading

import veekun

from server import SERVER

from connection import Connection

import utils


if __name__ == '__main__':
  veekun.csv_to_sqlite()

  threading.Thread(target=SERVER.serve_forever).start()

  CONNECTION = Connection(('wss' if os.environ['SHOWDOWN_PORT'] == '443' else 'ws') +
                          '://' + os.environ['SHOWDOWN_HOST'] +
                          ':' + os.environ['SHOWDOWN_PORT'] +
                          '/showdown/websocket',
                          os.environ['USERNAME'],
                          os.environ['PASSWORD'],
                          os.environ['AVATAR'],
                          os.environ['STATUSTEXT'],
                          os.environ['ROOMS'].split(','),
                          os.environ['PRIVATE_ROOMS'].split(','),
                          os.environ['COMMAND_CHARACTER'],
                          os.environ['ADMINISTRATORS'].split(','))

  asyncio.get_event_loop().run_until_complete(CONNECTION.open_connection())
