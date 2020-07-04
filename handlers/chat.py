from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection

from handler_loader import handler_wrapper
import utils


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
async def chat(conn: Connection, roomid: str, user: str, *message: str) -> None:
    if utils.to_user_id(user) == utils.to_user_id(conn.username):
        return
    await parse_chat_message(conn, roomid, user, "|".join(message).strip())


@handler_wrapper(["c:"])
async def timestampchat(
    conn: Connection, roomid: str, timestamp: str, user: str, *message: str
) -> None:
    if utils.to_user_id(user) == utils.to_user_id(conn.username):
        return
    if int(timestamp) <= conn.timestamp:
        return
    await parse_chat_message(conn, roomid, user, "|".join(message).strip())


@handler_wrapper(["pm"])
async def pm(
    conn: Connection, roomid: str, sender: str, receiver: str, *message: str
) -> None:
    if utils.to_user_id(sender) == utils.to_user_id(conn.username):
        return
    if utils.to_user_id(receiver) != utils.to_user_id(conn.username):
        return
    await parse_chat_message(conn, None, sender, "|".join(message).strip())


@handler_wrapper([":"])
async def server_timestamp(conn: Connection, roomid: str, timestamp: str) -> None:
    conn.timestamp = int(timestamp)
