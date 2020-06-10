import utils


async def kill(self, room: str, user: str, arg: str) -> None:
    if utils.to_user_id(user) in self.administrators:
        await self.websocket.close()


commands = {"kill": kill}
