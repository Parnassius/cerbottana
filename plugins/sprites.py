from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING
from urllib.parse import quote

from imageprobe.errors import UnsupportedFormat
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func

import databases.veekun as v
import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


def generate_sprite_url(pokemon: str, shiny: bool = False) -> str:
    """Returns an URL to the PS animated sprite of a pokemon.

    Args:
        pokemon (str): Pokemon name.
        shiny (bool): Whether the required sprite should be shiny.

    Returns:
        str: URL.
    """
    pokemon = re.sub(r"[':\.\s]", "", pokemon.lower())
    pokemon = utils.remove_accents(pokemon)
    pokemon = quote(pokemon)
    category = "ani-shiny" if shiny else "ani"
    return f"https://play.pokemonshowdown.com/sprites/{category}/{pokemon}.gif"


@command_wrapper(helpstr="Mostra lo sprite di un pokemon")
async def sprite(msg: Message) -> None:
    if len(msg.args) == 1:
        url = generate_sprite_url(msg.arg)
    elif len(msg.args) == 2 and msg.args[1].lower() == "shiny":
        url = generate_sprite_url(msg.args[0], True)
    else:
        await msg.reply("Sintassi non valida: ``.sprite nomepokemon[, shiny]``")
        return

    try:
        html = await utils.image_url_to_html(url)
        await msg.reply_htmlbox(html)
    except UnsupportedFormat:
        # We received a generic Apache error webpage.
        await msg.reply("Nome pokemon non valido")


@command_wrapper(
    aliases=("randomsprite",),
    helpstr="Mostra lo sprite di un pokemon scelto randomicamente",
)
async def randsprite(msg: Message) -> None:
    # Get a random pokemon
    db = Database.open("veekun")
    with db.get_session() as session:
        species = (
            session.query(v.PokemonSpeciesNames)
            .filter_by(local_language_id=9)  # English
            .order_by(func.random())
            .first()
        )
        if not species:
            raise SQLAlchemyError("Missing PokemonSpeciesNames data")

        # Pokemon has a 1/8192 chance of being shiny if it isn't explicitly requested.
        shiny = msg.arg.lower() == "shiny" or not random.randint(0, 8192)
        url = generate_sprite_url(species.name, shiny)

        try:
            html = await utils.image_url_to_html(url)
            await msg.reply_htmlbox(html)
        except UnsupportedFormat:
            # Missing sprite, should be rather rare.
            await msg.reply("Non ho trovato lo sprite di {species.name} :(")
