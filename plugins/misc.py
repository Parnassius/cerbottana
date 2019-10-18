import random

import utils

from room import Room

async def randomuser(self, room, user, arg):
  if room is None or not utils.is_voice(user):
    return
  users = Room.get(room).users
  await self.send_reply(room, user, users[random.choice(list(users.keys()))]['username'])


commands = {'randomuser': randomuser}
