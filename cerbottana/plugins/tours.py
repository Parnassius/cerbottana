from __future__ import annotations

import random
from typing import TYPE_CHECKING

import aiohttp

from cerbottana.handlers import handler_wrapper
from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message
    from cerbottana.models.protocol_message import ProtocolMessage


async def create_tour(
    msg: Message,
    *,
    formatid: str = "customgame",
    generator: str = "elimination",
    playercap: int | None = None,
    generatormod: str = "",
    name: str = "",
    autostart: float = 2,
    autodq: float = 1.5,
    allow_scouting: bool = False,
    forcetimer: bool = False,
    rules: list[str] | None = None,
) -> None:
    tournew = "/tour new {formatid}, {generator}, {playercap}, {generatormod}, {name}"
    await msg.reply(
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
        await msg.reply(f"/tour autostart {autostart}", False)
    if autodq is not None:
        await msg.reply(f"/tour autodq {autodq}", False)
    if not allow_scouting:
        await msg.reply("/tour scouting off", False)
    if forcetimer:
        await msg.reply("/tour forcetimer on", False)
    if rules:
        rules_str = ",".join(rules)
        await msg.reply(f"/tour rules {rules_str}", False)


# --- Commands for generic tours ---


@command_wrapper(
    aliases=("randomtour",),
    helpstr="Avvia un torneo di una tier scelta a caso tra quelle con team random",
    is_unlisted=True,
    required_rank="driver",
    allow_pm=False,
)
async def randtour(msg: Message) -> None:
    tiers = [x.name for x in msg.conn.tiers.values() if x.random and x.tournament]

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

    if random.randint(1, 100) <= 10 and "1v1" not in formatid and "2v2" not in formatid:
        rules.append("Gen 8 Shared Power")

    if "1v1" in formatid or "2v2" in formatid:
        generator = "roundrobin"
    else:
        generator = "elimination"

    await create_tour(
        msg,
        formatid=formatid,
        generator=generator,
        autostart=3.5,
        allow_scouting=True,
        rules=rules,
        forcetimer=forcetimer,
    )


# --- Commands for tours with custom rules ---


@command_wrapper(
    aliases=("monopoke",), is_unlisted=True, required_rank="driver", allow_pm=False
)
async def monopoketour(msg: Message) -> None:
    if len(msg.args) != 1:
        await msg.reply("Specifica un (solo) Pokémon")
        return

    await create_tour(
        msg,
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
async def randpoketour(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Inserisci almeno un Pokémon")
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

    await create_tour(msg, formatid=formatid, name=name, autostart=12, rules=rules)


@command_wrapper(
    aliases=("sibb",),
    helpstr="Avvia un torneo Super Italian Bros. Brawl",
    is_unlisted=True,
    required_rank="driver",
    allow_pm=False,
)
async def waffletour(msg: Message) -> None:
    name = "Super Italian Bros. Brawl"
    rules = [
        "Cancel Mod",
        "Dynamax Clause",
        "Endless Battle Clause",
        "Evasion Moves Clause",
        "HP Percentage Mod",
        "Force Open Team Sheets",
        "Sleep Clause Mod",
        "Species Clause",
        "Terastal Clause",
    ]

    await create_tour(
        msg, name=name, autostart=5, autodq=3, forcetimer=True, rules=rules
    )

    await msg.reply("!viewfaq sibb", False)


# --- Tour generation enhancements ---


@handler_wrapper(["tournament"], required_parameters=2)  # hooked on |tournament|create|
async def tournament_create(msg: ProtocolMessage) -> None:
    if msg.params[0] != "create":
        return

    tierid = msg.params[1]
    if tierid.endswith("blitz"):
        tierid = tierid[:-5]

    tier = msg.conn.tiers.get(tierid)
    if tier is None:
        print(f"Unrecognized tier: '{tierid}'")
        return

    # Show !tier info for non-random non-custom formats
    if not tier.random and not tierid.endswith("customgame"):
        await msg.room.send(f"!tier {tier.name}", False)

    # Push a notification to discord webhook
    if msg.room.webhook is not None:
        name = tier.name.replace("[", r"\[").replace("]", r"\]")
        alert = f"[**{name}** tour in {msg.room.title}](https://psim.us/{msg.room})"
        async with aiohttp.ClientSession() as session:
            async with session.post(msg.room.webhook, data={"content": alert}) as resp:
                if err := await resp.text("utf-8"):
                    print(f"Error with webhook of {msg.room}:\n{err}")
                else:
                    print(f"Sent tour alert to webhook of {msg.room}")
