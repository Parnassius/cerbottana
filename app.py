import asyncio
import os
import sys
import time
import traceback

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
  SERVER = Server()
  SERVER.listen()

  CONNECTION = Connection()
  CONNECTION.set_url(('wss' if os.environ['SHOWDOWN_PORT'] == '443' else 'ws') +
                     '://' + os.environ['SHOWDOWN_HOST'] +
                     ':' + os.environ['SHOWDOWN_PORT'] +
                     '/showdown/websocket')
  CONNECTION.set_username(os.environ['USERNAME'])
  CONNECTION.set_password(os.environ['PASSWORD'])
  CONNECTION.set_avatar(os.environ['AVATAR'])
  CONNECTION.set_rooms(os.environ['ROOMS'].split(','))
  CONNECTION.set_private_rooms(os.environ['PRIVATE_ROOMS'].split(','))
  CONNECTION.set_command_character(os.environ['COMMAND_CHARACTER'])
  CONNECTION.set_database_api_url(os.environ['DATABASE_API_URL'])
  CONNECTION.set_database_api_key(os.environ['DATABASE_API_KEY'])
  CONNECTION.set_administrators(os.environ['ADMINISTRATORS'].split(','))
  CONNECTION.set_battle_tiers(['randombattle',
                               'battlefactory',
                               'bssfactory',
                               'monotyperandombattle',
                               'superstaffbrosbrawl',
                               'challengecup1v1',
                               'hackmonscup'])
  asyncio.get_event_loop().run_until_complete(CONNECTION.open_connection())
