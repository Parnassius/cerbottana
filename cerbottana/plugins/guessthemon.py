# Author: Plato (palt0)

from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

import cerbottana.databases.veekun as v
from cerbottana.database import Database

from . import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


@command_wrapper(
    aliases=("gtm", "hangmanpokemon", "pokemonhangman"),
    helpstr="Indovina un pokemon da una sua entry del pokedex!",
    allow_pm=False,
    required_rank_editable=True,
)
async def guessthemon(msg: Message) -> None:
    db = Database.open("veekun")
    with db.get_session() as session:
        # Retrieve a random pokemon
        # Hangman words can only have ascii letters, so a few pokemon names wouldn't be
        # parsed correctly. Punctuation signs are preserved.
        # Some exceptions pass silently for simplicity, i.e. Nidoran♂ / Nidoran♀.
        invalid_identifiers = ("porygon2",)
        stmt = (
            select(v.PokemonSpecies)
            .where(v.PokemonSpecies.identifier.notin_(invalid_identifiers))
            .order_by(func.random())  # pylint: disable=not-callable
        )
        # TODO: remove annotation
        species: v.PokemonSpecies | None = session.scalar(stmt)

        if not species:
            raise SQLAlchemyError("Missing PokemonSpecies data")

        # Get localized pokemon name
        species_name = next(
            (
                i.name
                for i in species.pokemon_species_names
                if i.local_language_id == msg.language_id
            ),
            None,
        )
        if species_name is None:
            raise SQLAlchemyError(
                f"PokemonSpecies row {species.id}: no {msg.language} localization"
            )

        # Get pokedex flavor text
        dex_entries = [
            i.flavor_text
            for i in species.pokemon_species_flavor_text
            if i.language_id == msg.language_id
            and i.flavor_text
            and len(i.flavor_text) <= 150
        ]
        if not dex_entries:  # This might fail but practically it never should
            return
        dex_entry = random.choice(dex_entries)

        # Hide pokemon name from flavor text
        filtered_word = re.escape(species_name)
        regexp = re.compile(rf"\b{filtered_word}\b", re.IGNORECASE)
        dex_entry = regexp.sub("???", dex_entry)

        # Flavor text strings usually have unneeded newlines
        dex_entry = dex_entry.replace("\n", " ")

        await msg.reply(f"/hangman create {species_name}, {dex_entry}", escape=False)
