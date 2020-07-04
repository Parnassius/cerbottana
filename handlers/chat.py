from typing import Optional

from handler_loader import handler_wrapper
import utils


async def parse_chat_message(
    self, roomid: Optional[str], user: str, message: str
) -> None:
    if message[: len(self.command_character)] == self.command_character:
        command = message.split(" ")[0][len(self.command_character) :].lower()

        if command in self.commands:
            message = message[
                (len(self.command_character) + len(command) + 1) :
            ].strip()
            await self.commands[command](self, roomid, user, message)
        elif roomid is None:
            await self.send_pm(user, "Invalid command")

    elif roomid is None:
        c = f"``{self.command_character}help``"
        message = f"I'm a bot: type {c} to get a list of available commands. "
        message += (
            f"Sono un bot: scrivi {c} per ottenere un elenco dei comandi disponibili."
        )
        await self.send_pm(user, message)


@handler_wrapper(["chat", "c"])
async def chat(self, roomid: str, user: str, *message: str) -> None:
    if utils.to_user_id(user) == utils.to_user_id(self.username):
        return
    await parse_chat_message(self, roomid, user, "|".join(message).strip())


@handler_wrapper(["c:"])
async def timestampchat(
    self, roomid: str, timestamp: str, user: str, *message: str
) -> None:
    if utils.to_user_id(user) == utils.to_user_id(self.username):
        return
    if int(timestamp) <= self.timestamp:
        return
    await parse_chat_message(self, roomid, user, "|".join(message).strip())


@handler_wrapper(["pm"])
async def pm(self, roomid: str, sender: str, receiver: str, *message: str) -> None:
    if utils.to_user_id(sender) == utils.to_user_id(self.username):
        return
    if utils.to_user_id(receiver) != utils.to_user_id(self.username):
        return
    await parse_chat_message(self, None, sender, "|".join(message).strip())


@handler_wrapper([":"])
async def server_timestamp(self, roomid: str, timestamp: str) -> None:
    self.timestamp = int(timestamp)
