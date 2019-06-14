import json
import requests

import utils


async def add_user(self, user):
  body = utils.database_request(self, 'adduser', {'userid': utils.to_user_id(user),
                                           'nome': user[1:]})
  if body:
    if 'needs_avatar' in body:
      await self.send_message('', '/cmd userdetails {}'.format(user))

  if utils.to_user_id(user) in self.administrators:
    body = utils.databaseRequest(self, 'getunapprovedprofiles', {'user': utils.to_user_id(user)})
    if body:
      if body['num'] > 0:
        text = 'Ci sono {} profili in attesa di approvazione.'
        text += 'Usa .token per approvarli o rifiutarli.'
        await self.send_pm(user, text.format(body['num']))

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
    avatar = data['avatar']
    if avatar in utils.AVATAR_IDS:
      avatar = utils.AVATAR_IDS[avatar]
    utils.database_request(self,
                           'setavatar',
                           {'userid': userid, 'avatar': avatar})



async def init(self, room, roomtype):
  pass

async def title(self, room, message):
  pass

async def users(self, room, userlist):
  for user in userlist.split(',')[1:]:
    await add_user(self, user)


async def join(self, room, user):
  await add_user(self, user)

async def leave(self, room, user):
  pass

async def name(self, room, user, oldid):
  await add_user(self, user)


async def chat(self, room, user, *message):
  if utils.to_user_id(user) == utils.to_user_id(self.username):
    return
  await parse_chat_message(self, room, user, '|'.join(message).strip())

async def server_timestamp(self, room, timestamp):
  self.timestamp = timestamp

async def timestampchat(self, room, timestamp, user, *message):
  if utils.to_user_id(user) == utils.to_user_id(self.username):
    return
  if timestamp <= self.timestamp:
    return
  await parse_chat_message(self, room, user, '|'.join(message).strip())

async def pm(self, room, sender, receiver, *message):
  if utils.to_user_id(sender) == utils.to_user_id(self.username):
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

async def updateuser(self, room, username, named, avatar, settings):
  # pylint: disable=too-many-arguments
  if utils.to_user_id(username) != utils.to_user_id(self.username):
    return

  if avatar != self.avatar:
    await self.send_message('', '/avatar {}'.format(self.avatar))

  for public_room in self.rooms:
    await self.send_message('', '/join {}'.format(public_room))

  for private_room in self.private_rooms:
    await self.send_message('', '/join {}'.format(private_room))

async def formats(self, room, *formatslist):
  pass

async def updatesearch(self, room, data):
  data = json.loads(data)
  if 'games' in data and data['games'] is not None:
    for i in data['games']:
      if i[:7] == 'battle-':
        pass
        #if not i in battles:
          #await self.send_message('', '/join {}'.format(i))

async def updatechallenges(self, room, data):
  data = json.loads(data)
  if 'challengesFrom' in data:
    for i in data['challengesFrom']:
      if data['challengesFrom'][i][4:] in self.battle_tiers:
        await self.send_message('', '/accept {}'.format(i))
      else:
        await self.send_message('', '/reject {}'.format(i))

async def queryresponse(self, room, querytype, data):
  await parse_queryresponse(self, querytype, data)
