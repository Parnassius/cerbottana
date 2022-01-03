from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "monopoke, species, item, ability, moves, valid",
    (
        (
            # Pokemon with `Past` moves should be accepted
            "venonat",
            "venonat",
            "",
            "compoundeyes",
            "flash",
            True,
        ),
        (
            # Pokemon with `Past` items should be accepted
            "venonat",
            "venonat",
            "beedrillite",
            "compoundeyes",
            "agility",
            True,
        ),
        pytest.param(
            # `Past` pokemon should be rejected
            "venonat",
            "unown",
            "",
            "levitate",
            "hiddenpower",
            False,
            marks=pytest.mark.xfail,
        ),
        (
            "vulpix",
            "vulpix",
            "",
            "drought",
            "sunnyday",
            True,
        ),
        (
            # Non-default forms should be rejected
            "vulpix",
            "vulpix-alola",
            "",
            "snowwarning",
            "hail",
            False,
        ),
        (
            "vulpix-alola",
            "vulpix-alola",
            "",
            "snowwarning",
            "hail",
            True,
        ),
        (
            # Default forms should be rejected
            "vulpix-alola",
            "vulpix",
            "",
            "drought",
            "sunnyday",
            False,
        ),
    ),
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
