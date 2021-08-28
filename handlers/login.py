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
    from models.protocol_message import ProtocolMessage


@handler_wrapper(["challstr"], required_parameters=1)
async def challstr(msg: ProtocolMessage) -> None:
    url = "https://play.pokemonshowdown.com/action.php"
    payload = {
        "act": "login",
        "name": msg.conn.username,
        "pass": msg.conn.password,
        "challstr": "|".join(msg.params),
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as resp:
            assertion = json.loads((await resp.text("utf-8"))[1:])["assertion"]

    if assertion:
        await msg.conn.send(f"|/trn {msg.conn.username},0,{assertion}")

    # Startup commands
    await msg.conn.send("|/cmd rooms")

    if msg.conn.statustext:
        await msg.conn.send(f"|/status {msg.conn.statustext}")

    for roomid in list(msg.conn.rooms.keys()):
        if Room.get(msg.conn, roomid).autojoin:
            await asyncio.sleep(0.15)
            await msg.conn.send(f"|/join {roomid}")


@handler_wrapper(["updateuser"], required_parameters=4)
async def updateuser(msg: ProtocolMessage) -> None:
    user = msg.params[0]
    # named = msg.params[1]
    avatar = msg.params[2]
    settings: dict[str, bool | None] = json.loads(msg.params[3])

    username = user.split("@")[0]
    if utils.to_user_id(username) != utils.to_user_id(msg.conn.username):
        return

    if msg.conn.avatar and avatar != msg.conn.avatar:
        await msg.conn.send(f"|/avatar {msg.conn.avatar}")

    if not settings.get("blockChallenges"):
        await msg.conn.send("|/blockchallenges")
