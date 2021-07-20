from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import aiohttp

import utils
from handlers import handler_wrapper
from models.room import Room

if TYPE_CHECKING:
    from connection import Connection


@handler_wrapper(["challstr"])
async def challstr(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    url = "https://play.pokemonshowdown.com/action.php"
    payload = {
        "act": "login",
        "name": conn.username,
        "pass": conn.password,
        "challstr": "|".join(args),
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as resp:
            assertion = json.loads((await resp.text("utf-8"))[1:])["assertion"]

    if assertion:
        await conn.send(f"|/trn {conn.username},0,{assertion}")

    # Startup commands
    await conn.send("|/cmd rooms")

    if conn.statustext:
        await conn.send(f"|/status {conn.statustext}")

    for roomid in list(conn.rooms.keys()):
        if Room.get(conn, roomid).autojoin:
            await asyncio.sleep(0.15)
            await conn.send(f"|/join {roomid}")


@handler_wrapper(["updateuser"])
async def updateuser(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 4:
        return

    user = args[0]
    # named = args[1]
    avatar = args[2]
    settings: dict[str, bool | None] = json.loads(args[3])

    username = user.split("@")[0]
    if utils.to_user_id(username) != utils.to_user_id(conn.username):
        return

    if conn.avatar and avatar != conn.avatar:
        await conn.send(f"|/avatar {conn.avatar}")

    if not settings.get("blockChallenges"):
        await conn.send("|/blockchallenges")
