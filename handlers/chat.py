from __future__ import annotations

from typing import TYPE_CHECKING

import utils
from handlers import handler_wrapper
from models.message import Message
from models.room import Room
from models.user import User

if TYPE_CHECKING:
    from connection import Connection


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
            await conn.commands[command].callback(msg)
        elif room is None:
            await user.send("Invalid command")

    elif room is None:
        c = f"``{conn.command_character}help``"
        message = f"I'm a bot: type {c} to get a list of available commands. "
        message += (
            f"Sono un bot: scrivi {c} per ottenere un elenco dei comandi disponibili."
        )
        await user.send(message)


@handler_wrapper(["chat", "c"])
async def chat(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 2:
        return

    user = User.get(conn, args[0])
    message = "|".join(args[1:]).strip()

    room.dynamic_buffer.append(message)

    if user.userid == utils.to_user_id(conn.username):
        return

    await parse_chat_message(conn, room, user, message)


@handler_wrapper(["c:"])
async def timestampchat(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 3:
        return

    timestamp = args[0]
    user = User.get(conn, args[1])
    message = "|".join(args[2:]).strip()

    room.dynamic_buffer.append(message)

    if user.userid == utils.to_user_id(conn.username):
        return
    if int(timestamp) <= conn.timestamp:
        return

    await parse_chat_message(conn, room, user, message)


@handler_wrapper(["pm"])
async def pm(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 3:
        return

    if len(args) >= 4 and args[3] == "requestpage":
        return

    sender = User.get(conn, args[0])
    receiver = User.get(conn, args[1])
    message = "|".join(args[2:]).strip()

    if sender.userid == utils.to_user_id(conn.username):
        return
    if receiver.userid != utils.to_user_id(conn.username):
        return

    await parse_chat_message(conn, None, sender, message)


@handler_wrapper([":"])
async def server_timestamp(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    timestamp = int(args[0])

    conn.timestamp = timestamp
