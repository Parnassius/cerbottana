from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional

from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message
    from models.room import Room


async def create_tour(
    room: Room,
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
    await room.send(
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
        await room.send(f"/tour autostart {autostart}", False)
    if autodq is not None:
        await room.send(f"/tour autodq {autodq}", False)
    if not allow_scouting:
        await room.send("/tour scouting off", False)
    if forcetimer:
        await room.send("/tour forcetimer on", False)
    if rules:
        rules_str = ",".join(rules)
        await room.send(f"/tour rules {rules_str}", False)


# --- Commands for generic tours ---


@command_wrapper(
    aliases=("randomtour",),
    helpstr="Avvia un torneo di una tier scelta a caso tra quelle con team random",
    is_unlisted=True,
)
async def randtour(msg: Message) -> None:
    if msg.room is None or not msg.user.has_role("driver", msg.room):
        return

    tiers = [x["name"] for x in msg.conn.tiers if x["random"]]

    rules = []

    if random.randint(1, 100) <= 10:
        rules.append("Blitz")

    if random.randint(1, 100) <= 10:
        rules.append("Inverse Mod")

    if random.randint(1, 100) <= 10:
        rules.append("Scalemons Mod")

    if random.randint(1, 100) <= 10:
        rules.append("Gen 8 Camomons")

    await create_tour(
        msg.room,
        formatid=random.choice(tiers),
        autostart=3.5,
        allow_scouting=True,
        rules=rules,
    )


# --- Commands for tours with custom rules ---


@command_wrapper(
    helpstr="<i> poke1, poke2, ... </i> Avvia un randpoketour.", is_unlisted=True
)
async def randpoketour(msg: Message) -> None:
    if msg.room is None or not msg.user.has_role("driver", msg.room):
        return

    if msg.arg.strip() == "":
        await msg.room.send("Inserisci almeno un Pokémon")
        return

    formatid = "nationaldex"
    name = "!RANDPOKE TOUR"
    rules = ["Z-Move Clause", "Dynamax Clause"]
    bans = ["All Pokemon"]
    unbans = []
    if "," in msg.arg:
        sep = ","
    else:
        sep = " "
    for item in msg.arg.split(sep):
        unbans.append(item.strip() + "-base")

    rules.extend(["-" + i for i in bans])
    rules.extend(["+" + i for i in unbans])

    await create_tour(msg.room, formatid=formatid, name=name, autostart=12, rules=rules)


@command_wrapper(
    aliases=("sibb",),
    helpstr="Avvia un torneo Super Italian Bros. Brawl",
    is_unlisted=True,
)
async def waffletour(msg: Message) -> None:
    if msg.room is None or not msg.user.has_role("driver", msg.room):
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
        msg.room, name=name, autostart=5, autodq=3, forcetimer=True, rules=rules
    )

    await msg.room.send("!viewfaq sibb", False)
