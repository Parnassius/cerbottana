# Author: Plato (palt0)


import random
import re

from pokedex import pokedex
from pokedex import tables as t
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from cerbottana.models.message import Message
from cerbottana.plugins import command_wrapper


@command_wrapper(
    aliases=("gtm", "hangmanpokemon", "pokemonhangman"),
    helpstr="Indovina un pokemon da una sua entry del pokedex!",
    allow_pm=False,
    required_rank_editable=True,
)
async def guessthemon(msg: Message) -> None:
    async with pokedex.async_session() as session:
        # Retrieve a random pokemon
        # Hangman words can only have ascii letters, so a few pokemon names wouldn't be
        # parsed correctly. Punctuation signs are preserved.
        # Some exceptions pass silently for simplicity, i.e. Nidoran♂ / Nidoran♀.
        invalid_identifiers = ("porygon2",)
        stmt = (
            select(t.PokemonSpecies)
            .where(t.PokemonSpecies.identifier.notin_(invalid_identifiers))
            .order_by(func.random())
            .limit(1)
            .options(
                selectinload(t.PokemonSpecies.name_associations),
                selectinload(t.PokemonSpecies.pokemon).selectinload(
                    t.Pokemon.flavor_text_associations
                ),
            )
        )
        species = await session.scalar(stmt)

        if not species:
            err = "Missing PokemonSpecies data"
            raise SQLAlchemyError(err)

        # Get localized pokemon name
        species_name = species.names[msg.language]

        # Get pokedex flavor text
        dex_entries = [
            entry
            for poke in species.pokemon
            for (lang, _), entry in poke.flavor_text.items()
            if lang == msg.language and len(entry) <= 150
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
