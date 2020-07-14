from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import utils
from handlers import handler_wrapper

if TYPE_CHECKING:
    from connection import Connection


async def parse_chat_message(
    conn: Connection, roomid: Optional[str], user: str, message: str
) -> None:
    if message[: len(conn.command_character)] == conn.command_character:
        command = message.split(" ")[0][len(conn.command_character) :].lower()

        if command in conn.commands:
            message = message[
                (len(conn.command_character) + len(command) + 1) :
            ].strip()
            await conn.commands[command].callback(conn, roomid, user, message)
        elif roomid is None:
            await conn.send_pm(user, "Invalid command")

    elif roomid is None:
        c = f"``{conn.command_character}help``"
        message = f"I'm a bot: type {c} to get a list of available commands. "
        message += (
            f"Sono un bot: scrivi {c} per ottenere un elenco dei comandi disponibili."
        )
        await conn.send_pm(user, message)


@handler_wrapper(["chat", "c"])
async def chat(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 2:
        return

    user = args[0]
    message = "|".join(args[1:]).strip()

    if utils.to_user_id(user) == utils.to_user_id(conn.username):
        return
    await parse_chat_message(conn, roomid, user, message)


@handler_wrapper(["c:"])
async def timestampchat(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 3:
        return

    timestamp = args[0]
    user = args[1]
    message = "|".join(args[2:]).strip()

    if utils.to_user_id(user) == utils.to_user_id(conn.username):
        return
    if int(timestamp) <= conn.timestamp:
        return
    await parse_chat_message(conn, roomid, user, message)


@handler_wrapper(["pm"])
async def pm(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 3:
        return

    sender = args[0]
    receiver = args[1]
    message = "|".join(args[2:]).strip()

    if utils.to_user_id(sender) == utils.to_user_id(conn.username):
        return
    if utils.to_user_id(receiver) != utils.to_user_id(conn.username):
        return
    await parse_chat_message(conn, None, sender, message)


@handler_wrapper([":"])
async def server_timestamp(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 1:
        return

    timestamp = int(args[0])

    conn.timestamp = timestamp
