import json
import time
import requests

import utils


async def add_user(self, user):
  pass

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
  if username != self.username:
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






"""
elif parts[1] == 'player':
  #player = parts[2]
  user = parts[3]
  #avatar = parts[4]
  if utils.to_user_id(user) == utils.to_user_id(os.environ['USERNAME']):
    for i in list(battles.keys()):
      if 'ended' in battles[i] and battles[i]['ended'] < time.time() - 60:
        battles.pop(i)
    battles[roomid] = {}

elif parts[1] == 'teamsize':
  pass

elif parts[1] == 'gametype':
  #parts[2] -> singles o doubles o triples
  if not roomid in battles:
    continue
  connection.send_message(roomid, '/timer on')
  connection.send_message(roomid, 'gl hf')

elif parts[1] == 'gen':
  pass

elif parts[1] == 'tier':
  pass

elif parts[1] == 'switch':
  if not roomid in battles:
    continue

elif parts[1] == 'request':
  try:
    data = json.loads(parts[2])
  except:
    continue
  parse_battle_request(roomid, data)

elif parts[1] == 'win' or parts[1] == 'tie':
  if not roomid in battles:
    continue
  connection.send_message(roomid, 'gg')
  connection.send_message(roomid, '/leave')
  battles[roomid]['ended'] = time.time()


elif parts[1] == 'tournament':
  parse_tournament(roomid, '|'.join(parts[2:]))
"""






"""



def parse_tournament(roomid, msg):
  parts = msg.split('|')
  if parts[0] == 'create':
    if parts[1][4:] in battle_tiers:
      connection.send_message(roomid, '/tour join')
  elif parts[0] == 'update':
    data = json.loads(parts[1])
    if 'challenged' in data:
      connection.send_message(roomid, '/tour acceptchallenge')
    elif 'challenges' in data and len(data['challenges']):
      connection.send_message(roomid, '/tour challenge {user}'.format(user = data['challenges'][0]))


def parse_battle_request(roomid, data):
  rqid = data['rqid']
  choices = []
  n = 0
  if 'wait' in data:
    return
  elif 'teamPreview' in data and 'maxTeamSize' in data:
    n = 0
    for i in data['side']['pokemon']:
      n += 1
      choices.append(n)
    random.shuffle(choices)
    team = ''.join(map(str, choices[:data['maxTeamSize']]))
    choice = 'team {team}'.format(team = team)
  elif 'active' in data and len(data['active']) and 'moves' in data['active'][0] and len(data['active'][0]['moves']):
    for i in data['active'][0]['moves']:
      n += 1
      if not 'disabled' in i or not i['disabled']:
        choices.append(n)
    move = random.choice(choices)
    choice = 'move {move}'.format(move = move)
  elif 'side' in data and 'pokemon' in data['side'] and len(data['side']['pokemon']):
    for i in data['side']['pokemon']:
      n += 1
      if not i['active'] and i['condition'] != '0 fnt':
        choices.append(n)
    pokemon = random.choice(choices)
    choice = 'switch {pokemon}'.format(pokemon = pokemon)
  else:
    connection.send_message(roomid, 'non so cosa fare')
    return
  connection.send_message(roomid, '/choose {choice}|{rqid}'.format(choice = choice, rqid = rqid))

"""
