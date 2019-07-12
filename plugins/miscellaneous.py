import random
import utils

async def 8ball(self, room, user, arg):
  if room is not None and not utils.is_voice(user):
    return
  replies = []
  # here the code to bring the replies from database
  randomIndex = random.randint(0,len(replies)-1)
  self.send_reply(room, user, replies[randomIndex])

async def list8ball(self, room, user, arg):
  if room is not None and not utils.is_voice(user):
    return
  replies = []
  # here the code to bring the replies from database
  reply = ''
  counter = 0
  for x in replies:
    counter += 1
    reply += counter+'. '+x+'  '
  self.send_reply(room, user, reply)

async def add8ball(self, room, user, arg):
  if not utils.is_voice(user):
    return
  replies = []
  # here the code to bring the replies from database
  replies.append(arg)
  # here the code to save replies on database
  self.send_reply(room, user, 'Frase aggiunta.')

async def remove8ball(self, room, user, arg):
  if not utils.is_voice(user):
    return
  indexToRemove = None
  try:
    indexToRemove = int(args)
  except ValueError:
    self.send_reply(room, user, 'Numero non valido.')
    return
  replies = []
  # here the code to bring the replies from database
  if indexToRemove>len(replies):
    self.send_reply(room, user, 'Numero non valido.')
    return
  replies.pop(indexToRemove)
  # here the code to save replies on database
  self.send_reply(room, user, 'Frase rimossa.')