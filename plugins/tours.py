from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional

from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import MessageDisallowPM
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
    required_rank="driver",
    allow_pm=False,
)
async def randtour(msg: MessageDisallowPM) -> None:
    tiers = [x["name"] for x in msg.conn.tiers if x["random"]]

    formatid = random.choice(tiers)

    rules = []
    forcetimer = False

    if random.randint(1, 100) <= 10:
        rules.append("Blitz")
        forcetimer = True

    if random.randint(1, 100) <= 10:
        rules.append("Inverse Mod")

    if random.randint(1, 100) <= 10:
        rules.append("Scalemons Mod")

    if random.randint(1, 100) <= 10:
        rules.append("Gen 8 Camomons")

    if "1v1" in formatid or "2v2" in formatid:
        generator = "roundrobin"
    else:
        generator = "elimination"

    await create_tour(
        msg.room,
        formatid=formatid,
        generator=generator,
        autostart=3.5,
        allow_scouting=True,
        rules=rules,
        forcetimer=forcetimer,
    )


# --- Commands for tours with custom rules ---


@command_wrapper(aliases=("monopoke",), is_unlisted=True)
async def monopoketour(msg: Message) -> None:
    if msg.room is None or not msg.user.has_role("driver", msg.room):
        return

    if len(msg.args) != 1:
        await msg.reply("Specifica un (solo) Pokémon")
        return

    await create_tour(
        msg.room,
        formatid="nationaldex",
        name="MONOPOKE TOUR",
        autostart=6.5,
        rules=["-All Pokemon", f"+{msg.arg}-base", "-Focus Sash", "Z-Move Clause"],
    )


@command_wrapper(
    helpstr="<i> poke1, poke2, ... </i> Avvia un randpoketour.",
    is_unlisted=True,
    required_rank="driver",
    allow_pm=False,
)
async def randpoketour(msg: MessageDisallowPM) -> None:
    if not msg.arg:
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
    required_rank="driver",
    allow_pm=False,
)
async def waffletour(msg: MessageDisallowPM) -> None:
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
