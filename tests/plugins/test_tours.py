from __future__ import annotations

import pytest

obtainable = {
    "species": "pikachu",
    "ability": "static",
    "move": "thunderbolt",
    "move_past": "hiddenpower",
}
past = {
    "species_past": "unown",
    "ability": "levitate",
    "move": "hiddenpower",
}
default_form = {
    "species": "wooper",
    "ability": "waterabsorb",
    "move": "watergun",
}
regional_form = {
    "species": "wooperpaldea",
    "ability": "waterabsorb",
    "move": "mudshot",
}

item_past = "beedrillite"


@pytest.mark.parametrize(
    "pokemon_data", [obtainable, past, default_form, regional_form]
)
async def test_obtainability(
    showdown_connection, *, pokemon_data: dict[str, str]
) -> None:
    async with showdown_connection() as (bot, _):
        valid = "species" in pokemon_data

        species = pokemon_data["species" if valid else "species_past"]
        ability = pokemon_data["ability"]
        move = pokemon_data["move"]

        await bot.send(f"|/utm {species}|||{ability}|{move}||4,,,,,|||||")
        await bot.send("|/vtm ou")
        msg = await bot.await_message("|popup|", startswith=True)

        if valid:
            assert msg.startswith("|popup|Your team is valid")
        else:
            assert msg.startswith("|popup|Your team was rejected")

        if "move_past" in pokemon_data:
            move_past = pokemon_data["move_past"]

            await bot.send(f"|/utm {species}|||{ability}|{move_past}||4,,,,,|||||")
            await bot.send("|/vtm ou")
            msg = await bot.await_message("|popup|", startswith=True)

            assert msg.startswith("|popup|Your team was rejected")


@pytest.mark.parametrize(
    "monopoke, species, item, ability, moves, valid",
    [
        (
            # Pokemon with `Past` moves should be accepted
            obtainable["species"],
            obtainable["species"],
            "",
            obtainable["ability"],
            obtainable["move_past"],
            True,
        ),
        (
            # Pokemon with `Past` items should be accepted
            obtainable["species"],
            obtainable["species"],
            item_past,
            obtainable["ability"],
            obtainable["move"],
            True,
        ),
        pytest.param(
            # `Past` pokemon should be rejected
            obtainable["species"],
            past["species_past"],
            "",
            past["ability"],
            past["move"],
            False,
            marks=pytest.mark.xfail,
        ),
        (
            default_form["species"],
            default_form["species"],
            "",
            default_form["ability"],
            default_form["move"],
            True,
        ),
        (
            # Non-default forms should be rejected
            default_form["species"],
            regional_form["species"],
            "",
            regional_form["ability"],
            regional_form["move"],
            False,
        ),
        (
            regional_form["species"],
            regional_form["species"],
            "",
            regional_form["ability"],
            regional_form["move"],
            True,
        ),
        (
            # Default forms should be rejected
            regional_form["species"],
            default_form["species"],
            "",
            default_form["ability"],
            default_form["move"],
            False,
        ),
    ],
)
async def test_monopoke(
    showdown_connection,
    *,
    monopoke: str,
    species: str,
    item: str,
    ability: str,
    moves: str,
    valid: bool,
) -> None:
    async with showdown_connection() as (bot, mod):
        # Create the tournament
        await mod.send(f"lobby|.monopoke {monopoke}")
        await mod.await_message(
            '|raw|<div class="infobox infobox-limited">This tournament includes:',
            startswith=True,
        )

        # Validate the pokemon
        await mod.send(f"|/utm {species}||{item}|{ability}|{moves}||4,,,,,|||||")
        await mod.send("lobby|/tournament vtm")
        msg = await mod.await_message("|popup|", startswith=True)

        # Close the tournament
        await bot.send("lobby|/tournament end")
        await bot.await_message("|tournament|forceend")

        # Assertions
        if valid:
            assert msg.startswith("|popup|Your team is valid")
        else:
            assert msg.startswith("|popup|Your team was rejected")
