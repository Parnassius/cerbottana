from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection

import json

import urllib.request
import urllib.parse

from handler_loader import handler_wrapper
import utils


@handler_wrapper(["challstr"])
async def challstr(conn: Connection, roomid: str, *challstring: str) -> None:
    payload = "act=login&name={username}&pass={password}&challstr={challstr}".format(
        username=conn.username, password=conn.password, challstr="|".join(challstring)
    ).encode()

    req = urllib.request.Request(
        "https://play.pokemonshowdown.com/action.php",
        payload,
        {"User-Agent": "Mozilla"},
    )
    resp = urllib.request.urlopen(req)

    assertion = json.loads(resp.read().decode("utf-8")[1:])["assertion"]

    if assertion:
        await conn.send_message(
            "", "/trn {},0,{}".format(conn.username, assertion), False
        )


@handler_wrapper(["updateuser"])
async def updateuser(
    conn: Connection, roomid: str, user: str, named: str, avatar: str, settings: str
) -> None:
    username = user.split("@")[0]
    if utils.to_user_id(username) != utils.to_user_id(conn.username):
        return

    if avatar != conn.avatar:
        await conn.send_message("", "/avatar {}".format(conn.avatar), False)

    await conn.send_message("", "/status {}".format(conn.statustext), False)

    for public_room in conn.rooms:
        await conn.send_message("", "/join {}".format(public_room), False)

    for private_room in conn.private_rooms:
        await conn.send_message("", "/join {}".format(private_room), False)
