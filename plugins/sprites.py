from __future__ import annotations

import random
from typing import TYPE_CHECKING

from imageprobe.errors import UnsupportedFormat
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func

import databases.veekun as v
from database import Database
from plugins import command_wrapper
from typedefs import JsonDict
from utils import get_ps_dex_entry, image_url_to_html, to_id

if TYPE_CHECKING:
    from models.message import Message


def generate_sprite_url(dex_entry: JsonDict, shiny: bool = False) -> str:
    """Returns an URL to the PS animated sprite of a pokemon.

    Args:
        dex_entry (JsonDict): Pokedex entry from the PS database.
        shiny (bool): Whether the required sprite should be shiny. Defaults to False.

    Returns:
        str: URL.
    """
    if "baseSpecies" in dex_entry:  # Alternate form, e.g. mega, gmax
        dex_name = to_id(dex_entry["baseSpecies"]) + "-" + to_id(dex_entry["forme"])
    else:  # Base form
        dex_name = to_id(dex_entry["name"])

    category = "ani-shiny" if shiny else "ani"
    return f"https://play.pokemonshowdown.com/sprites/{category}/{dex_name}.gif"


@command_wrapper(helpstr="Mostra lo sprite di un pokemon")
async def sprite(msg: Message) -> None:
    if len(msg.args) == 1:
        shiny = False
    elif len(msg.args) == 2 and msg.args[1].lower() == "shiny":
        shiny = True
    else:
        await msg.reply("Sintassi non valida: ``.sprite nomepokemon[, shiny]``")
        return

    dex_entry = get_ps_dex_entry(msg.args[0])
    if dex_entry is None:
        await msg.reply("Nome pokemon non valido")
        return

    url = generate_sprite_url(dex_entry, shiny)

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
        species = session.query(v.PokemonSpecies).order_by(func.random()).first()
        if not species:
            raise SQLAlchemyError("Missing PokemonSpecies data")

        dex_entry = get_ps_dex_entry(species.identifier)
        if dex_entry is None:
            print(f"Missing PS data for {species.identifier}")
            return

    # Pokemon has a 1/8192 chance of being shiny if it isn't explicitly requested.
    shiny = msg.arg.lower() == "shiny" or not random.randint(0, 8192)

    url = generate_sprite_url(dex_entry, shiny)

    try:
        html = await image_url_to_html(url)
        await msg.reply_htmlbox(html)
    except UnsupportedFormat:
        # Missing sprite. We received a generic Apache error webpage.
        await msg.reply("Sprite di {} non trovato".format(dex_entry["name"]))
