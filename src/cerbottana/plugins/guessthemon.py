# Author: Plato (palt0)


import random
import re
from collections.abc import Iterable
from itertools import chain

from pokedex import Pokemon, PokemonForm, PokemonGmaxForm

from cerbottana.models.message import Message
from cerbottana.plugins import command_wrapper


@command_wrapper(
    aliases=("gtm", "hangmanpokemon", "pokemonhangman"),
    helpstr="Indovina un pokemon da una sua entry del pokedex!",
    allow_pm=False,
    required_rank_editable=True,
)
async def guessthemon(msg: Message) -> None:
    # Retrieve a random pokemon
    # Hangman words can only have ascii letters, so a few pokemon names wouldn't be
    # parsed correctly. Punctuation signs are preserved.
    # Some exceptions pass silently for simplicity, i.e. Nidoran♂ / Nidoran♀.
    invalid_identifiers = ("porygon2",)
    identifier = random.choice(
        [x for x in Pokemon.list_identifiers() if x not in invalid_identifiers]
    )
    species = Pokemon.get(identifier)

    # Get localized pokemon name
    species_name = species.names.get()
    if not species_name:
        err = f"Missing Pokemon name for {species.identifier}"
        raise ValueError(err)

    # Get pokedex flavor text
    dex_entries: list[str] = []
    all_forms: Iterable[PokemonForm | PokemonGmaxForm] = chain(
        species.forms.values(), species.gmax_forms.values()
    )
    for form in all_forms:
        form_entries = form.descriptions.with_language()
        dex_entries.extend(
            entry
            for games_entries in form_entries.values()
            for entry in games_entries.values()
            if len(entry) <= 150
        )
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
