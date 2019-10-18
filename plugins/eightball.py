import random

import utils

async def eightball(self, room, user, arg):
  if room is not None and not utils.is_voice(user):
    return
  answers = utils.database_request(self, 'get8ballanswers', {})
  answer = random.choice(answers)
  if answer[0] == '/':
    answer = '/' + answer
  await self.send_reply(room, user, answer)


commands = {'8ball': eightball,
            'eightball': eightball}
