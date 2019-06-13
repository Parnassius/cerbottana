import os

import utils

def create_token(self):
  token_id = os.urandom(16).hex()
  utils.database_request(self, 'newtoken',
                         {'token': token_id})
  return token_id

async def token(self, room, user, arg):
  if utils.to_user_id(user) not in self.administrators:
    return

  token_id = create_token(self)
  await self.send_pm(user, '{url}dashboard.php?token={token}'.format(url=self.database_api_url,
                                                                     token=token_id))
