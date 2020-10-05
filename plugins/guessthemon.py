from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func

import databases.veekun as v
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(
    aliases=("gtm", "hangmanpokemon", "pokemonhangman"),
    helpstr="Indovina un pokemon da una sua entry del pokedex!",
)
async def guessthemon(msg: Message) -> None:
    if msg.room is None:
        return

    db = Database.open("veekun")
    with db.get_session() as session:
        # Retrieve a random pokemon
        species = session.query(v.PokemonSpecies).order_by(func.random()).first()
        if not species:
            raise SQLAlchemyError("Missing PokemonSpecies data")

        # Get localized pokemon name
        species_name = next(
            (i.name for i in species.pokemon_species_name if i.local_language_id == 8),
            None,
        )
        if species_name is None:
            raise SQLAlchemyError(
                f"Missing italian localization for PokemonSpecies row {species.id}"
            )

        # Get pokedex flavor text
        dex_entries = [
            i.flavor_text
            for i in species.pokemon_species_flavor_text
            if i.language_id == 8 and len(i.flavor_text) <= 150  # PS limit
        ]
        if not dex_entries:  # This might fail but practically it never should
            return
        dex_entry = random.choice(dex_entries)

        # Hide pokemon name from flavor text
        regexp = re.compile(re.escape(species_name), re.IGNORECASE)
        dex_entry = regexp.sub("???", dex_entry)

        # Flavor text strings usually have unneeded newlines
        dex_entry = dex_entry.replace("\n", " ")

        await msg.room.send(
            f"/hangman create {species_name}, {dex_entry}", escape=False
        )
