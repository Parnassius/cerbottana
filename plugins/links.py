import utils

async def lega(self, room, user, arg):
  if room is not None and not utils.is_voice(user):
    return
  await self.send_reply(room, user, 'https://showdownitalia.forumcommunity.net/?t=61248258')


commands = {'lega': lega}
