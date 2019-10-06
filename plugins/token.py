import os

import utils

from room import Room

def create_token(self, rank):
  token_id = os.urandom(16).hex()
  utils.database_request(self, 'newtoken',
                         {'token': token_id,
                          'rank': rank})
  return token_id

async def token(self, room, user, arg):
  userid = utils.to_user_id(user)
  for room in self.rooms:
    users = Room.get(room).users
    if userid in users and utils.is_driver(users[userid]['rank']):
      rank = users[userid]['rank']
      break
  else:
    return

  token_id = create_token(self, rank)

  await self.send_pm(user, '{url}dashboard.php?token={token}'.format(url=self.database_api_url,
                                                                     token=token_id))
