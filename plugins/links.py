from plugin_loader import plugin_wrapper
import utils


@plugin_wrapper(
    helpstr="Elenca gli avatar disponibili. Per usarne uno, <code>/avatar [nome]</code>"
)
async def avatars(self, room: str, user: str, arg: str) -> None:
    await self.send_reply(
        room, user, "https://play.pokemonshowdown.com/sprites/trainers/"
    )
