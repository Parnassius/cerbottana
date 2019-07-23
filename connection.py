import asyncio

import websockets

import utils

import handlers
import plugins

class Connection:
  # pylint: disable=too-many-instance-attributes
  def __init__(self, url, username, password, avatar, statustext,
               rooms, private_rooms, command_character, database_api_url, database_api_key,
               administrators, battle_tiers, heroku_token):
    self.url = url
    self.username = username
    self.password = password
    self.avatar = avatar
    self.statustext = statustext
    self.rooms = rooms
    self.private_rooms = private_rooms
    self.command_character = command_character
    self.database_api_url = database_api_url
    self.database_api_key = database_api_key
    self.administrators = administrators
    self.battle_tiers = battle_tiers
    self.heroku_token = heroku_token
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
        'updatesearch': handlers.updatesearch,
        'updatechallenges': handlers.updatechallenges,
        'queryresponse': handlers.queryresponse}
    self.commands = {
        '8ball': plugins.eightball.eightball,
        'eightball': plugins.eightball.eightball,

        'campione': plugins.profile.champion,
        'champion': plugins.profile.champion,
        'e4': plugins.profile.elitefour,
        'elite4': plugins.profile.elitefour,
        'elitefour': plugins.profile.elitefour,
        'super4': plugins.profile.elitefour,
        'superquattro': plugins.profile.elitefour,
        'profile': plugins.profile.profile,
        'setprofile': plugins.profile.setprofile,

        'meme': plugins.shitpost.memes,
        'memes': plugins.shitpost.memes,
        'mims': plugins.shitpost.memes,
        'say': plugins.shitpost.shitpost,
        'shitpost': plugins.shitpost.shitpost,

        'token': plugins.token.token,

        'leaderboard': plugins.tours.leaderboard,

        'trad': plugins.translations.trad,

        'acher': plugins.usernames.acher,
        'aeth': plugins.usernames.aethernum,
        'aethernum': plugins.usernames.aethernum,
        'eterno': plugins.usernames.aethernum,
        'alpha': plugins.usernames.alpha,
        'alphawittem': plugins.usernames.alpha,
        'wittem': plugins.usernames.alpha,
        'cinse': plugins.usernames.consecutio,
        'cobse': plugins.usernames.consecutio,
        'conse': plugins.usernames.consecutio,
        'consecutio': plugins.usernames.consecutio,
        'duck': plugins.usernames.duck,
        'ed': plugins.usernames.edgummet,
        'edgummet': plugins.usernames.edgummet,
        'francy': plugins.usernames.francyy,
        'francyy': plugins.usernames.francyy,
        'haund': plugins.usernames.haund,
        'howkings': plugins.usernames.howkings,
        'infli': plugins.usernames.inflikted,
        'inflikted': plugins.usernames.inflikted,
        'lange': plugins.usernames.lange,
        'milak': plugins.usernames.milak,
        'mister': plugins.usernames.mister,
        'mistercantiere': plugins.usernames.mistercantiere,
        'azyz': plugins.usernames.oizys,
        'oizys': plugins.usernames.oizys,
        'r0spe': plugins.usernames.r0spe,
        'rospe': plugins.usernames.r0spe,
        'silver': plugins.usernames.silver97,
        'silver97': plugins.usernames.silver97,
        'smilzo': plugins.usernames.smilzo,
        'spec': plugins.usernames.specn,
        'specn': plugins.usernames.specn,
        'cul1': plugins.usernames.swculone,
        'culone': plugins.usernames.swculone,
        'kul1': plugins.usernames.swculone,
        'swcul1': plugins.usernames.swculone,
        'swculone': plugins.usernames.swculone,
        'swkul1': plugins.usernames.swculone,
        'quas': plugins.usernames.thequasar,
        'quasar': plugins.usernames.thequasar,
        'thequasar': plugins.usernames.thequasar,
        '3v': plugins.usernames.trev,
        'trev': plugins.usernames.trev,
        'vvv': plugins.usernames.trev,
        'uselesstrainer': plugins.usernames.uselesstrainer,
        'usy': plugins.usernames.uselesstrainer,
        'v0lca': plugins.usernames.v0lca,
        'volca': plugins.usernames.v0lca}
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

    room = ''
    if message[0] == '>':
      room = message.split('\n')[0]
    roomid = utils.to_room_id(room)

    for msg in message.split('\n'):

      if not msg or msg[0] != '|':
        continue

      parts = msg.split('|')

      if parts[1] in self.handlers:
        await self.handlers[parts[1]](self, roomid, *parts[2:])


  async def send_htmlbox(self, room, message):
    await self.send_message(room, '/addhtmlbox {}'.format(message))

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
