from handler_loader import Handler, handler_wrapper
import utils


async def parse_chat_message(self, roomid, user, message):
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
        await self.send_pm(user, "I'm a bot")


@handler_wrapper(["chat", "c"])
async def chat(self, roomid, user, *message):
    if utils.to_user_id(user) == utils.to_user_id(self.username):
        return
    await parse_chat_message(self, roomid, user, "|".join(message).strip())


@handler_wrapper(["c:"])
async def timestampchat(self, roomid, timestamp, user, *message):
    if utils.to_user_id(user) == utils.to_user_id(self.username):
        return
    if int(timestamp) <= self.timestamp:
        return
    await parse_chat_message(self, roomid, user, "|".join(message).strip())


@handler_wrapper(["pm"])
async def pm(self, roomid, sender, receiver, *message):
    if utils.to_user_id(sender) == utils.to_user_id(self.username):
        return
    if utils.to_user_id(receiver) != utils.to_user_id(self.username):
        return
    await parse_chat_message(self, None, sender, "|".join(message).strip())


@handler_wrapper([":"])
async def server_timestamp(self, roomid, timestamp):
    self.timestamp = int(timestamp)
