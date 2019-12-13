import asyncio
import websockets
from datetime import datetime
from time import time
import pytz
import re

import utils

import handlers
from plugins import plugins

from room import Room

class Connection:
  def __init__(self, url, username, password, avatar, statustext,
               rooms, private_rooms, command_character, administrators):
    self.url = url
    self.username = username
    self.password = password
    self.avatar = avatar
    self.statustext = statustext
    self.rooms = rooms
    self.private_rooms = private_rooms
    self.command_character = command_character
    self.administrators = administrators
    self.handlers = {
        'init': handlers.init,
        'title': handlers.title,
        'users': handlers.users,
        'join': handlers.join, 'j': handlers.join, 'J': handlers.join,
        'leave': handlers.leave, 'l': handlers.leave, 'L': handlers.leave,
        'name': handlers.name, 'n': handlers.name, 'N': handlers.name,
        'chat': handlers.chat, 'c': handlers.chat,
        ':': handlers.server_timestamp,
        'c:': handlers.timestampchat,
        'pm': handlers.pm,
        'challstr': handlers.challstr,
        'updateuser': handlers.updateuser,
        'formats': handlers.formats,
        'queryresponse': handlers.queryresponse,
        'tournament': handlers.tournament}
    self.commands = plugins
    self.timestamp = 0
    self.websocket = None
    self.tiers = None

  async def open_connection(self):
    async with websockets.connect(self.url, ping_interval=None) as websocket:
      self.websocket = websocket
      while True:
        message = await websocket.recv()
        print('<< {}'.format(message))
        asyncio.ensure_future(self.parse_message(message))

  async def parse_message(self, message):
    if not message:
      return

    init = False

    room = ''
    if message[0] == '>':
      room = message.split('\n')[0]
    roomid = utils.to_room_id(room)

    if roomid in self.rooms:
      await self.try_modchat(roomid)

    for msg in message.split('\n'):

      if roomid in self.rooms:
        match = re.match('^\(.+ set modchat to (.*)\)$', msg)
        if not match:
          match = re.match('^\|error\|Modchat is already set to (.*)\.$', msg)

        if match and len(match.group(1)) == 1:
          modchat_room = Room.get(roomid)
          if modchat_room is not None:
            modchat_room.modchat = utils.is_voice(match.group(1))

      if not msg or msg[0] != '|':
        continue

      parts = msg.split('|')

      command = parts[1]

      if command == 'init':
        init = True

      if init and command in ['tournament']:
        return

      if command in self.handlers:
        await self.handlers[command](self, roomid, *parts[2:])


  async def try_modchat(self, roomid):
    room = Room.get(roomid)
    if room and not room.modchat and room.no_mods_online:
      tz = pytz.timezone('Europe/Rome')
      timestamp = datetime.now(tz)
      minutes = timestamp.hour * 60 + timestamp.minute
      # 00:30 - 08:00
      if minutes >= 30 and minutes < 8 * 60 and room.no_mods_online + (15 * 60) < time():
        await self.send_message(roomid, '/modchat +')



  async def send_rankhtmlbox(self, rank, room, message):
    await self.send_message(room, '/addrankhtmlbox {}, {}'.format(rank, message.replace('\n', '<br>')))

  async def send_htmlbox(self, room, user, message, simple_message=''):
    message = message.replace('\n', '<br>')
    if room is not None:
      await self.send_message(room, '/addhtmlbox {}'.format(message))
    elif user is not None:
      room = utils.can_pminfobox_to(self, utils.to_user_id(user))
      if room is not None:
        await self.send_message(room, '/pminfobox {}, {}'.format(user, message))
      else:
        if simple_message == '':
          simple_message = 'Questo comando è disponibile in PM '
          simple_message += 'solo se sei online in una room dove sono Roombot'
        await self.send_pm(user, simple_message)

  async def send_reply(self, room, user, message):
    if room is None:
      await self.send_pm(user, message)
    else:
      await self.send_message(room, message)

  async def send_message(self, room, message):
    await self.send('{}|{}'.format(room, message))

  async def send_pm(self, user, message):
    await self.send('|/w {}, {}'.format(utils.to_user_id(user), message))

  async def send(self, message):
    print('>> {}'.format(message))
    await self.websocket.send(message)
