from __future__ import annotations

import random
from typing import TYPE_CHECKING

from imageprobe.errors import UnsupportedFormat
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

import databases.veekun as v
from database import Database
from plugins import command_wrapper
from typedefs import JsonDict
from utils import get_ps_dex_entry, image_url_to_html, to_id

if TYPE_CHECKING:
    from models.message import Message


def generate_sprite_url(
    dex_entry: JsonDict,
    *,
    back: bool = False,
    shiny: bool = False,
    category: str = "ani",
) -> str:
    """Returns an URL to the PS animated sprite of a pokemon.

    Args:
        dex_entry (JsonDict): Pokedex entry from the PS database.
        back (bool): Whether the required sprite should be the back sprite. Defaults to
            False.
        shiny (bool): Whether the required sprite should be shiny. Defaults to False.
        category (str): The category of the required sprite. Defaults to "ani".

    Returns:
        str: URL.
    """
    if back:
        category += "-back"
    if shiny:
        category += "-shiny"

    dex_name = dex_entry["dex_name"]

    ext = "gif" if category.startswith(("gen5ani", "ani")) else "png"

    return f"https://play.pokemonshowdown.com/sprites/{category}/{dex_name}.{ext}"


def get_sprite_parameters(args: list[str]) -> tuple[bool, bool, str]:
    back = False
    shiny = False
    category = "ani"

    for arg in args:
        arg = to_id(arg)
        if arg == "back":
            back = True
        elif arg == "shiny":
            shiny = True
        else:
            category = SPRITE_CATEGORIES.get(arg, category)

    return back, shiny, category


@command_wrapper(helpstr="Mostra lo sprite di un pokemon")
async def sprite(msg: Message) -> None:
    if len(msg.args) < 1:
        return

    search_query = to_id(msg.args[0])
    dex_entry = get_ps_dex_entry(search_query)
    if dex_entry is None:
        await msg.reply("Nome pokemon non valido")
        return

    back, shiny, category = get_sprite_parameters(msg.args[1:])

    url = generate_sprite_url(dex_entry, back=back, shiny=shiny, category=category)

    try:
        html = await image_url_to_html(url)
        await msg.reply_htmlbox(html)
    except UnsupportedFormat:
        # Missing sprite. We received a generic Apache error webpage.
        await msg.reply("Sprite non trovato")


@command_wrapper(
    aliases=("randomsprite",),
    helpstr="Mostra lo sprite di un pokemon scelto randomicamente",
)
async def randsprite(msg: Message) -> None:
    # Get a random pokemon
    db = Database.open("veekun")
    with db.get_session() as session:
        stmt = select(v.PokemonSpecies).order_by(func.random())
        # TODO: remove annotation
        species: v.PokemonSpecies | None = session.scalar(stmt)
        if not species:
            raise SQLAlchemyError("Missing PokemonSpecies data")

        dex_entry = get_ps_dex_entry(species.identifier)
        if dex_entry is None:
            print(f"Missing PS data for {species.identifier}")
            return

    back, shiny, _ = get_sprite_parameters(msg.args)

    if not shiny:
        # Pokemon has a 1/8192 chance of being shiny if it isn't explicitly requested.
        shiny = not random.randint(0, 8192)

    url = generate_sprite_url(dex_entry, back=back, shiny=shiny)

    try:
        html = await image_url_to_html(url)
        await msg.reply_htmlbox(html)
    except UnsupportedFormat:
        # Missing sprite. We received a generic Apache error webpage.
        await msg.reply("Sprite di {} non trovato".format(dex_entry["name"]))


SPRITE_CATEGORIES = {
    "afd": "afd",
    "aprilfools": "afd",
    "aprilfoolsday": "afd",
    "ani": "ani",
    "gen1rg": "gen1rg",
    "redgreen": "gen1rg",
    "green": "gen1rg",
    "rg": "gen1rg",
    "gen1rb": "gen1rb",
    "red": "gen1rb",
    "blue": "gen1rb",
    "redblue": "gen1rb",
    "rb": "gen1rb",
    "gen1": "gen1",
    "yellow": "gen1",
    "gen2g": "gen2g",
    "gold": "gen2g",
    "gen2s": "gen2s",
    "silver": "gen2s",
    "gen2": "gen2",
    "crystal": "gen2",
    "gen3rs": "gen3rs",
    "ruby": "gen3rs",
    "sapphire": "gen3rs",
    "rubysapphire": "gen3rs",
    "rs": "gen3rs",
    "gen3frlg": "gen3frlg",
    "firered": "gen3frlg",
    "leafgreen": "gen3frlg",
    "fireredleafgreen": "gen3frlg",
    "frlg": "gen3frlg",
    "gen3": "gen3",
    "emerald": "gen3",
    "gen4dp": "gen4dp",
    "diamond": "gen4dp",
    "pearl": "gen4dp",
    "diamondpearl": "gen4dp",
    "dp": "gen4dp",
    "gen4": "gen4",
    "platinum": "gen4",
    "heartgold": "gen4",
    "soulsilver": "gen4",
    "heartgoldsoulsilver": "gen4",
    "hgss": "gen4",
    "gen5ani": "gen5ani",
    "gen5": "gen5ani",
    "black": "gen5ani",
    "white": "gen5ani",
    "blackwhite": "gen5ani",
    "bw": "gen5ani",
    "black2": "gen5ani",
    "white2": "gen5ani",
    "black2white2": "gen5ani",
    "b2w2": "gen5ani",
    "blackwhite2": "gen5ani",
    "bw2": "gen5ani",
}
