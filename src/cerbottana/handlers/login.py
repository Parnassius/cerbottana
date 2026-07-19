import asyncio
import json

from cerbottana import utils
from cerbottana.handlers import handler_wrapper
from cerbottana.models.protocol_message import ProtocolMessage


@handler_wrapper(["challstr"], required_parameters=1)
async def challstr(msg: ProtocolMessage) -> None:
    url = "https://play.pokemonshowdown.com/api/login"
    payload = {
        "name": msg.conn.username,
        "pass": msg.conn.password,
        "challstr": "|".join(msg.params),
    }

    assertion: str | None = None
    assertion_retries = 0
    while assertion is None:
        async with msg.conn.client_session.post(url, data=payload) as resp:
            try:
                assertion = json.loads((await resp.text("utf-8"))[1:])["assertion"]
            except json.JSONDecodeError, KeyError:
                if assertion_retries == 5:
                    print("Unable to login, closing connection")
                    if msg.conn.websocket is not None:
                        await msg.conn.websocket.close()
                    return
                await asyncio.sleep(2**assertion_retries)
                assertion_retries += 1

    await msg.conn.send(f"|/trn {msg.conn.username},0,{assertion}")

    # Startup commands
    await msg.conn.send("|/cmd rooms")

    if msg.conn.statustext:
        await msg.conn.send(f"|/status {msg.conn.statustext}")

    for roomid in msg.conn.autojoin_rooms:
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
