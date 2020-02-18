import utils


async def avatars(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "https://www.smogon.com/forums/threads/3646930/")


async def lega(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(
        room, user, "https://showdownitalia.forumcommunity.net/?t=61248258"
    )


commands = {"avatars": avatars, "lega": lega}
