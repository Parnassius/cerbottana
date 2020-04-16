import utils


async def avatars(self, room: str, user: str, arg: str) -> None:
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(
        room, user, "https://play.pokemonshowdown.com/sprites/trainers/"
    )


async def lega(self, room: str, user: str, arg: str) -> None:
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(
        room, user, "https://showdownitalia.forumcommunity.net/?t=61248258"
    )


commands = {"avatars": avatars, "lega": lega}
