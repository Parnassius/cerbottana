from __future__ import annotations

import random
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import pytz

from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper()
async def acher(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "lo acher che bontà ♫")


@command_wrapper(aliases=["aeth", "eterno"])
async def aethernum(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "__eterno__ indeciso :^)")


@command_wrapper(aliases=["alphawittem", "wittem"])
async def alpha(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Italian luck jajaja")


@command_wrapper(aliases=["acii"])
async def altcauseiminsecure(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    await conn.send_reply(
        room,
        user,
        "A, wi, we. La fortuna viene a me. Wi, we, wa. La fortuna viene qua. A, we, wi. La fortuna non va lì",
    )


@command_wrapper()
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


@command_wrapper(aliases=["cinse", "cobse", "conse"])
async def consecutio(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    text = "opss{} ho lasciato il pc acceso tutta notte".format(
        "s" * random.randint(0, 3)
    )
    await conn.send_reply(room, user, text)


@command_wrapper()
async def duck(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "quack")


@command_wrapper(aliases=["ed"])
async def edgummet(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "soccontro")


@command_wrapper(aliases=["francy"])
async def francyy(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "aiuto ho riso irl")


@command_wrapper()
async def haund(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "( ͡° ͜ʖ ͡°)")


@command_wrapper()
async def howkings(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Che si vinca o si perda, v0lca merda :3")


@command_wrapper(aliases=["infli"])
async def inflikted(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    letters = {1: "I", 2: "N", 3: "F", 4: "L", 5: "I", 6: "K", 7: "T", 8: "E", 9: "D"}
    shuffled = sorted(letters, key=lambda x: random.random() * x / len(letters))
    text = ""
    for i in shuffled:
        text += letters[i]
    await conn.send_reply(room, user, "ciao {}".format(text))


@command_wrapper()
async def lange(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Haund mi traduci questo post?")


@command_wrapper()
async def mammalu(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "clicca la stab")


@command_wrapper()
async def maurizio(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "MAURIZIO used ICE PUNCH!")


@command_wrapper(aliases=["gr"])
async def megagr(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "GRRRRRR")


@command_wrapper()
async def milak(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "I just salmonella gurl")


@command_wrapper()
async def mister(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Master")


@command_wrapper()
async def mistercantiere(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    await conn.send_reply(room, user, "MasterCantiere")


@command_wrapper(aliases=["azyz"])
async def oizys(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "no")


@command_wrapper(aliases=["palt0", "palto", "plato"])
async def plat0(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    text = "oh {} non mi spoilerare".format(
        random.choice(["basta", "senti", "smettila"])
    )
    tz = pytz.timezone("Europe/Rome")
    timestamp = datetime.now(tz)
    if 3 <= timestamp.hour <= 5:
        text += ", che mi sono appena svegliato"
    await conn.send_reply(room, user, text)


@command_wrapper(aliases=["rospe"])
async def r0spe(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "buondì")


@command_wrapper(aliases=["boiler"])
async def roiler(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "ehm volevo dire")


@command_wrapper(aliases=["silver"])
async def silver97(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    tier = random.choice(conn.tiers)["name"]
    await conn.send_reply(room, user, "qualcuno mi passa un team {}".format(tier))


@command_wrapper()
async def smilzo(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "mai na gioia")


@command_wrapper(aliases=["spec"])
async def specn(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Vi muto tutti")


@command_wrapper(aliases=["cul1", "culone", "kul1", "swcul1", "swkul1"])
async def swculone(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "hue")


@command_wrapper(aliases=["quas"])
async def thequasar(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Basta con le pupazzate")


@command_wrapper(aliases=["3v", "vvv"])
async def trev(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "gioco di merda")


@command_wrapper()
async def ultrasuca(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "@Ultrasuca left")


@command_wrapper(aliases=["useless", "usy"])
async def uselesstrainer(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    await conn.send_reply(room, user, "kek")


@command_wrapper(aliases=["volca"])
async def v0lca(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, "Porco mele...")
