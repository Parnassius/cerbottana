from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import utils
from handlers import handler_wrapper
from models.message import Message
from models.room import Room
from models.user import User

if TYPE_CHECKING:
    from connection import Connection
    from models.protocol_message import ProtocolMessage


async def parse_chat_message(
    conn: Connection, room: Room | None, user: User, message: str
) -> None:
    """Parses potential bot commands to their respective callback.

    Args:
        conn (Connection): Used to access the websocket.
        room (Room | None): Command room if it isn't a PM. Defaults to None.
        user (User): User that requested the command.
        message (str): Command argument.
    """
    if message[: len(conn.command_character)] == conn.command_character:
        command = message.split(" ")[0][len(conn.command_character) :].lower()

        if command in conn.commands:
            message = message[
                (len(conn.command_character) + len(command) + 1) :
            ].strip()
            msg = Message(room, user, message)
            asyncio.create_task(conn.commands[command].callback(msg))
        elif room is None:
            await user.send("Invalid command")

    elif room is None and (not message.startswith("/") or message.startswith("//")):
        c = f"``{conn.command_character}help``"
        message = f"I'm a bot: type {c} to get a list of available commands. "
        message += (
            f"Sono un bot: scrivi {c} per ottenere un elenco dei comandi disponibili."
        )
        await user.send(message)


@handler_wrapper(["chat", "c"], required_parameters=2)
async def chat(msg: ProtocolMessage) -> None:
    user = User.get(msg.conn, msg.params[0])
    message = "|".join(msg.params[1:]).strip()

    msg.room.dynamic_buffer.append(message)

    if user.userid == utils.to_user_id(msg.conn.username):
        return

    await parse_chat_message(msg.conn, msg.room, user, message)


@handler_wrapper(["c:"], required_parameters=3)
async def timestampchat(msg: ProtocolMessage) -> None:
    timestamp = msg.params[0]
    user = User.get(msg.conn, msg.params[1])
    message = "|".join(msg.params[2:]).strip()

    msg.room.dynamic_buffer.append(message)

    if user.userid == utils.to_user_id(msg.conn.username):
        return
    if int(timestamp) <= msg.conn.timestamp:
        return

    await parse_chat_message(msg.conn, msg.room, user, message)


@handler_wrapper(["pm"], required_parameters=3)
async def pm(msg: ProtocolMessage) -> None:
    if len(msg.params) >= 4 and msg.params[3] == "requestpage":
        return

    sender = User.get(msg.conn, msg.params[0])
    receiver = User.get(msg.conn, msg.params[1])
    message = "|".join(msg.params[2:]).strip()

    if sender.userid == utils.to_user_id(msg.conn.username):
        return
    if receiver.userid != utils.to_user_id(msg.conn.username):
        return

    await parse_chat_message(msg.conn, None, sender, message)


@handler_wrapper([":"], required_parameters=1)
async def server_timestamp(msg: ProtocolMessage) -> None:
    timestamp = int(msg.params[0])

    msg.conn.timestamp = timestamp
