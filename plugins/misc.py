import random

from plugin_loader import plugin_wrapper
import utils

from room import Room


@plugin_wrapper(helpstr="Seleziona un utente a caso presente nella room.")
async def randomuser(self, room: str, user: str, arg: str) -> None:
    users = Room.get(room).users
    await self.send_reply(
        room, user, users[random.choice(list(users.keys()))]["username"]
    )
