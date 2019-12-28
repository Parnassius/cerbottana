import json
import requests

import utils

from room import Room

import database

async def add_user(self, room, user, skip_avatar_check=False):
  rank = user[0]
  username = user[1:].split('@')[0]
  userid = utils.to_user_id(username)
  idle = user[-2:] == '@!'

  Room.get(room).add_user(userid, rank, username, idle)

  if userid == utils.to_user_id(self.username):
    Room.get(room).roombot = (rank == '*')

  db = database.open_db()
  sql = "INSERT INTO utenti (userid, nome) VALUES (?, ?) "
  sql += " ON CONFLICT (userid) DO UPDATE SET nome = excluded.nome"
  db.execute(sql, [userid, username])
  db.connection.commit()
  db.connection.close()

  if not skip_avatar_check:
    await self.send_message('', '/cmd userdetails {}'.format(username))

async def remove_user(self, room, user):
  Room.get(room).remove_user(utils.to_user_id(user))

async def parse_chat_message(self, room, user, message):
  if message[:len(self.command_character)] == self.command_character:
    command = message.split(' ')[0][len(self.command_character):].lower()

    if command in self.commands:
      message = message[(len(self.command_character) + len(command) + 1):].strip()
      await self.commands[command](self, room, user, message)
    elif room is None:
      await self.send_pm(user, 'Invalid command')

  elif room is None:
    await self.send_pm(user, 'I\'m a bot')

async def parse_queryresponse(self, cmd, data):
  data = json.loads(data)
  if cmd == 'userdetails':
    userid = data['userid']
    avatar = str(data['avatar'])
    if avatar in utils.AVATAR_IDS:
      avatar = utils.AVATAR_IDS[avatar]

    db = database.open_db()
    sql = "INSERT INTO utenti (userid, avatar) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET avatar = excluded.avatar"
    db.execute(sql, [userid, avatar])
    db.connection.commit()
    db.connection.close()


async def init(self, room, roomtype):
  if roomtype == 'chat':
    if not Room.get(room):
      Room(room)

async def title(self, room, roomtitle):
  Room.get(room).title = roomtitle

async def users(self, room, userlist):
  for user in userlist.split(',')[1:]:
    await add_user(self, room, user, True)


async def join(self, room, user):
  await add_user(self, room, user)

async def leave(self, room, user):
  await remove_user(self, room, user)

async def name(self, room, user, oldid):
  await remove_user(self, room, oldid)
  await add_user(self, room, user)


async def chat(self, room, user, *message):
  if utils.to_user_id(user) == utils.to_user_id(self.username):
    return
  await parse_chat_message(self, room, user, '|'.join(message).strip())

async def server_timestamp(self, room, timestamp):
  self.timestamp = int(timestamp)

async def timestampchat(self, room, timestamp, user, *message):
  if utils.to_user_id(user) == utils.to_user_id(self.username):
    return
  if int(timestamp) <= self.timestamp:
    return
  await parse_chat_message(self, room, user, '|'.join(message).strip())

async def pm(self, room, sender, receiver, *message):
  if utils.to_user_id(sender) == utils.to_user_id(self.username):
    return
  if utils.to_user_id(receiver) != utils.to_user_id(self.username):
    return
  await parse_chat_message(self, None, sender, '|'.join(message).strip())


async def challstr(self, room, *challstring):
  challstring = '|'.join(challstring)

  payload = {'act': 'login',
             'name': self.username,
             'pass': self.password,
             'challstr': challstring}
  req = requests.post('https://play.pokemonshowdown.com/action.php', data=payload)
  assertion = json.loads(req.text[1:])['assertion']

  if assertion:
    await self.send_message('', '/trn {},0,{}'.format(self.username, assertion))

async def updateuser(self, room, user, named, avatar, settings):
  # pylint: disable=too-many-arguments,unused-argument
  username = user.split('@')[0]
  if utils.to_user_id(username) != utils.to_user_id(self.username):
    return

  if avatar != self.avatar:
    await self.send_message('', '/avatar {}'.format(self.avatar))

  await self.send_message('', '/status {}'.format(self.statustext))

  for public_room in self.rooms:
    await self.send_message('', '/join {}'.format(public_room))

  for private_room in self.private_rooms:
    await self.send_message('', '/join {}'.format(private_room))

async def formats(self, room, *formatslist):
  tiers = []
  section = None
  section_next = False
  for tier in formatslist:
    if tier[0] == ',':
      section_next = True
      continue
    if section_next:
      section = tier
      section_next = False
      continue
    parts = tier.split(',')
    tiers.append({'name': parts[0], 'section': section})
  self.tiers = tiers

async def queryresponse(self, room, querytype, data):
  await parse_queryresponse(self, querytype, data)

async def tournament(self, room, command, *params):
  if command == 'create':
    tour_format = params[0]
    await self.commands['sampleteams'](self, room, None, tour_format)
