from __future__ import annotations

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
    rules: List[str] = []
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
        await conn.send_message(room, "/tour autostart {}".format(autostart), False)
    if autodq is not None:
        await conn.send_message(room, "/tour autodq {}".format(autodq), False)
    if not allow_scouting:
        await conn.send_message(room, "/tour scouting off", False)
    if forcetimer:
        await conn.send_message(room, "/tour forcetimer on", False)
    if rules:
        await conn.send_message(room, "/tour rules {}".format(",".join(rules)), False)


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
    aliases=["sibb"],
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
