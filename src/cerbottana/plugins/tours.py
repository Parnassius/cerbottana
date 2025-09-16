from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar, Literal

from cerbottana.handlers import handler_wrapper
from cerbottana.models.attributes import AttributeKey
from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message
    from cerbottana.models.protocol_message import ProtocolMessage


creating_custom_tour = AttributeKey(datetime)


class Tour:
    formatid = "customgame"
    generator: Literal["elimination", "roundrobin"] = "elimination"
    playercap: int = 0
    generatormod: int = 0
    name = ""

    autostart: float = 2
    autodq: float = 1.5
    allow_scouting = False
    forcetimer = False
    rules: ClassVar[list[str]] = []

    @classmethod
    async def create_tour(
        cls,
        msg: Message,
        *,
        formatid: str | None = None,
        generator: Literal["elimination", "roundrobin"] | None = None,
        playercap: int | None = None,
        generatormod: int | None = None,
        name: str | None = None,
        autostart: float | None = None,
        autodq: float | None = None,
        allow_scouting: bool | None = None,
        forcetimer: bool | None = None,
        rules: list[str] | None = None,
        hide_tier_info: bool = True,
    ) -> None:
        if formatid is None:
            formatid = cls.formatid
        if generator is None:
            generator = cls.generator
        if playercap is None:
            playercap = cls.playercap
        if generatormod is None:
            generatormod = cls.generatormod
        if name is None:
            name = cls.name

        if autostart is None:
            autostart = cls.autostart
        if autodq is None:
            autodq = cls.autodq
        if allow_scouting is None:
            allow_scouting = cls.allow_scouting
        if forcetimer is None:
            forcetimer = cls.forcetimer
        if rules is None:
            rules = cls.rules

        if msg.room and hide_tier_info:
            msg.room.attributes[creating_custom_tour] = datetime.now(UTC)

        tournew = (
            "/tour new {formatid}, {generator}, {playercap}, {generatormod}, {name}"
        )
        await msg.reply(
            tournew.format(
                formatid=formatid,
                generator=generator,
                playercap=str(playercap) if playercap else "",
                generatormod=str(generatormod) if generatormod else "",
                name=name,
            ),
            False,
        )
        if autostart:
            await msg.reply(f"/tour autostart {autostart}", False)
        if autodq:
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
class Randtour(Tour):
    autostart = 3.5
    allow_scouting = True
    rules: ClassVar[list[str]] = [
        "Blitz",
        "Inverse Mod",
        "Scalemons Mod",
        "Camomons Mod",
        "Shared Power",
    ]

    @classmethod
    async def cmd_func(cls, msg: Message) -> None:
        tier = random.choice(
            [x for x in msg.conn.tiers.values() if x.random and x.tournament]
        )

        if "1v1" in tier.id or "2v2" in tier.id:
            generator: Literal["elimination", "roundrobin"] = "roundrobin"
        else:
            generator = "elimination"

        rules = []
        for rule in cls.rules:
            if rule == "Shared Power" and any(
                x in tier.id for x in ["1v1", "2v2", "doubles", "triples"]
            ):
                continue
            if random.randint(1, 100) <= 10:
                rules.append(rule)

        await super().create_tour(
            msg,
            formatid=tier.id,
            generator=generator,
            forcetimer="Blitz" in rules,
            rules=rules,
        )


# --- Commands for tours with custom rules ---


@command_wrapper(
    aliases=("monopoke",), is_unlisted=True, required_rank="driver", allow_pm=False
)
class Monopoketour(Tour):
    formatid = "nationaldex"
    name = "MONOPOKE TOUR"

    autostart = 6.5
    rules: ClassVar[list[str]] = [
        "Z-Move Clause",
        "-All Pokemon",
        "-Focus Sash",
    ]

    @classmethod
    async def cmd_func(cls, msg: Message) -> None:
        if len(msg.args) != 1:
            await msg.reply("Specifica un (solo) Pokémon")
            return

        await super().create_tour(msg, rules=[*cls.rules, f"+{msg.arg}-base"])


@command_wrapper(
    helpstr="<i> poke1, poke2, ... </i> Avvia un randpoketour.",
    is_unlisted=True,
    required_rank="driver",
    allow_pm=False,
)
class Randpoketour(Tour):
    formatid = "nationaldex"
    name = "!RANDPOKE TOUR"

    autostart = 12
    rules: ClassVar[list[str]] = [
        "Z-Move Clause",
        "Dynamax Clause",
        "-All Pokemon",
    ]

    @classmethod
    async def cmd_func(cls, msg: Message) -> None:
        if not msg.arg:
            await msg.reply("Inserisci almeno un Pokémon")
            return

        sep = "," if "," in msg.arg else " "
        unbans = [f"+{x}-base" for x in msg.arg.split(sep)]

        await super().create_tour(msg, rules=[*cls.rules, *unbans])


@command_wrapper(
    aliases=("waffletour",),
    helpstr="Avvia un torneo Super Italian Bros. Brawl",
    is_unlisted=True,
    required_rank="driver",
    allow_pm=False,
)
class Sibb(Tour):
    name = "Super Italian Bros. Brawl"

    autostart = 5
    autodq = 3
    forcetimer = True
    rules: ClassVar[list[str]] = [
        "Dynamax Clause",
        "Endless Battle Clause",
        "Evasion Moves Clause",
        "HP Percentage Mod",
        "Force Open Team Sheets",
        "Sleep Clause Mod",
        "Species Clause",
        "Terastal Clause",
    ]

    @classmethod
    async def cmd_func(cls, msg: Message) -> None:
        await super().create_tour(msg)

        await msg.reply("!viewfaq sibb", False)


# --- Tour generation enhancements ---


@handler_wrapper(["tournament"], required_parameters=2)  # hooked on |tournament|create|
async def tournament_create(msg: ProtocolMessage) -> None:
    if msg.params[0] != "create":
        return

    creating_dt = msg.room.attributes.get(creating_custom_tour)
    if creating_dt and (datetime.now(UTC) - creating_dt).total_seconds() < 5:
        return

    tierid = msg.params[1].removesuffix("blitz")
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
        async with msg.conn.client_session.post(
            msg.room.webhook, data={"content": alert}
        ) as resp:
            if err := await resp.text("utf-8"):
                print(f"Error with webhook of {msg.room}:\n{err}")
            else:
                print(f"Sent tour alert to webhook of {msg.room}")
