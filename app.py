import asyncio
import os
import sys
import time
import traceback

import veekun

from connection import Connection
from server import Server

import utils

def handle_exception(exc_type, exc_value, exc_traceback):
  utils.database_request(CONNECTION,
                         'logerror',
                         {'err': ''.join(traceback.format_exception(exc_type,
                                                                    exc_value,
                                                                    exc_traceback))})

  while True:
    utils.restart_bot(CONNECTION)
    time.sleep(15)

sys.excepthook = handle_exception


if __name__ == '__main__':
  veekun.csv_to_sqlite()

  SERVER = Server()
  SERVER.listen()

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
                          os.environ['DATABASE_API_URL'],
                          os.environ['DATABASE_API_KEY'],
                          os.environ['ADMINISTRATORS'].split(','),
                          os.environ['HEROKU_TOKEN'])

  asyncio.get_event_loop().run_until_complete(CONNECTION.open_connection())
