from __future__ import annotations

import random
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import pytz

from plugins import plugin_wrapper

if TYPE_CHECKING:
    from connection import Connection


@plugin_wrapper()
async def acher(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "lo acher che bontà ♫")


@plugin_wrapper(aliases=["aeth", "eterno"])
async def aethernum(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "__eterno__ indeciso :^)")


@plugin_wrapper(aliases=["alphawittem", "wittem"])
async def alpha(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Italian luck jajaja")


@plugin_wrapper(aliases=["acii"])
async def altcauseiminsecure(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    await conn.send_reply(
        room,
        user,
        "A, wi, we. La fortuna viene a me. Wi, we, wa. La fortuna viene qua. A, we, wi. La fortuna non va lì",
    )


@plugin_wrapper()
async def ciarizardmille(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    text = "beh comunque ormai lo avete capito che sono un alt di {}".format(
        random.choice(
            [
                "duck",
                "test2017",
                "parnassius",
                "parna",
                "inflikted",
                "infli",
                "trev",
                "silver97",
                "silver",
                "usy",
                "useless trainer",
            ]
        )
    )
    await conn.send_reply(room, user, text)


@plugin_wrapper(aliases=["cinse", "cobse", "conse"])
async def consecutio(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    text = "opss{} ho lasciato il pc acceso tutta notte".format(
        "s" * random.randint(0, 3)
    )
    await conn.send_reply(room, user, text)


@plugin_wrapper()
async def duck(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "quack")


@plugin_wrapper(aliases=["ed"])
async def edgummet(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "soccontro")


@plugin_wrapper(aliases=["francy"])
async def francyy(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "aiuto ho riso irl")


@plugin_wrapper()
async def haund(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "( ͡° ͜ʖ ͡°)")


@plugin_wrapper()
async def howkings(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Che si vinca o si perda, v0lca merda :3")


@plugin_wrapper(aliases=["infli"])
async def inflikted(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    letters = {1: "I", 2: "N", 3: "F", 4: "L", 5: "I", 6: "K", 7: "T", 8: "E", 9: "D"}
    shuffled = sorted(letters, key=lambda x: random.random() * x / len(letters))
    text = ""
    for i in shuffled:
        text += letters[i]
    await conn.send_reply(room, user, "ciao {}".format(text))


@plugin_wrapper()
async def lange(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Haund mi traduci questo post?")


@plugin_wrapper()
async def mammalu(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "clicca la stab")


@plugin_wrapper()
async def maurizio(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "MAURIZIO used ICE PUNCH!")


@plugin_wrapper(aliases=["gr"])
async def megagr(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "GRRRRRR")


@plugin_wrapper()
async def milak(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "I just salmonella gurl")


@plugin_wrapper()
async def mister(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Master")


@plugin_wrapper()
async def mistercantiere(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    await conn.send_reply(room, user, "MasterCantiere")


@plugin_wrapper(aliases=["azyz"])
async def oizys(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "no")


@plugin_wrapper(aliases=["palt0", "palto", "plato"])
async def plat0(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    text = "oh {} non mi spoilerare".format(
        random.choice(["basta", "senti", "smettila"])
    )
    tz = pytz.timezone("Europe/Rome")
    timestamp = datetime.now(tz)
    if 3 <= timestamp.hour <= 5:
        text += ", che mi sono appena svegliato"
    await conn.send_reply(room, user, text)


@plugin_wrapper(aliases=["rospe"])
async def r0spe(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "buondì")


@plugin_wrapper(aliases=["boiler"])
async def roiler(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "ehm volevo dire")


@plugin_wrapper(aliases=["silver"])
async def silver97(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    tier = random.choice(conn.tiers)["name"]
    await conn.send_reply(room, user, "qualcuno mi passa un team {}".format(tier))


@plugin_wrapper()
async def smilzo(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "mai na gioia")


@plugin_wrapper(aliases=["spec"])
async def specn(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Vi muto tutti")


@plugin_wrapper(aliases=["cul1", "culone", "kul1", "swcul1", "swkul1"])
async def swculone(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "hue")


@plugin_wrapper(aliases=["quas"])
async def thequasar(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Basta con le pupazzate")


@plugin_wrapper(aliases=["3v", "vvv"])
async def trev(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "gioco di merda")


@plugin_wrapper()
async def ultrasuca(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "@Ultrasuca left")


@plugin_wrapper(aliases=["useless", "usy"])
async def uselesstrainer(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    await conn.send_reply(room, user, "kek")


@plugin_wrapper(aliases=["volca"])
async def v0lca(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Porco mele...")
