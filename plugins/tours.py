from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


async def create_tour(
    conn: Connection,
    room: str,
    *,
    formatid: str = "customgame",
    generator: str = "elimination",
    playercap: Optional[int] = None,
    generatormod: str = "",
    name: str = "",
    autostart: float = 2,
    autodq: float = 1.5,
    allow_scouting: bool = False,
    forcetimer: bool = False,
    rules: Optional[List[str]] = None,
) -> None:
    tournew = "/tour new {formatid}, {generator}, {playercap}, {generatormod}, {name}"
    await conn.send_message(
        room,
        tournew.format(
            formatid=formatid,
            generator=generator,
            playercap=str(playercap) if playercap else "",
            generatormod=generatormod,
            name=name,
        ),
        False,
    )
    if autostart is not None:
        await conn.send_message(room, f"/tour autostart {autostart}", False)
    if autodq is not None:
        await conn.send_message(room, f"/tour autodq {autodq}", False)
    if not allow_scouting:
        await conn.send_message(room, "/tour scouting off", False)
    if forcetimer:
        await conn.send_message(room, "/tour forcetimer on", False)
    if rules:
        rules_str = ",".join(rules)
        await conn.send_message(room, f"/tour rules {rules_str}", False)


@command_wrapper(
    helpstr="<i> poke1, poke2, ... </i> Avvia un randpoketour.", is_unlisted=True
)
async def randpoketour(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None or not utils.is_driver(user):
        return

    if arg.strip() == "":
        await conn.send_message(room, "Inserisci almeno un Pokémon")
        return

    formatid = "nationaldex"
    name = "!RANDPOKE TOUR"
    rules = ["Z-Move Clause", "Dynamax Clause"]
    bans = ["All Pokemon"]
    unbans = []
    if "," in arg:
        sep = ","
    else:
        sep = " "
    for item in arg.split(sep):
        unbans.append(item.strip() + "-base")

    rules.extend(["-" + i for i in bans])
    rules.extend(["+" + i for i in unbans])

    await create_tour(
        conn, room, formatid=formatid, name=name, autostart=12, rules=rules
    )


@command_wrapper(
    aliases=("sibb",),
    helpstr="Avvia un torneo Super Italian Bros. Brawl",
    is_unlisted=True,
)
async def waffletour(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None or not utils.is_driver(user):
        return

    name = "Super Italian Bros. Brawl"
    rules = [
        "Cancel Mod",
        "Dynamax Clause",
        "Endless Battle Clause",
        "Evasion Moves Clause",
        "HP Percentage Mod",
        "Obtainable Formes",  # to avoid multiple Mega-Evolutions
        "Sleep Clause Mod",
        "Species Clause",
    ]

    await create_tour(
        conn, room, name=name, autostart=5, autodq=3, forcetimer=True, rules=rules
    )

    await conn.send_message(room, "!viewfaq sibb", False)


@command_wrapper(
    helpstr="Avvia un torneo di una tier scelta a caso tra quelle con team random",
    is_unlisted=True,
)
async def randtour(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if room is None or not utils.is_driver(user):
        return

    tiers = [x["name"] for x in conn.tiers if x["random"]]

    rules = []

    if random.randint(1, 100) <= 10:
        rules.append("Blitz")

    if random.randint(1, 100) <= 10:
        rules.append("Inverse Mod")

    await create_tour(
        conn,
        room,
        formatid=random.choice(tiers),
        autostart=3.5,
        allow_scouting=True,
        rules=rules,
    )
