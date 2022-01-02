from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "pokemon1, pokemon2",
    (
        pytest.param(
            ("venonat", "compoundeyes", "rest"),
            # `Past` pokemon should be rejected
            ("unown", "levitate", "hiddenpower"),
            marks=pytest.mark.xfail,
        ),
        (
            ("vulpix", "drought", "sunnyday"),
            # Non-default forms should be rejected
            ("vulpix-alola", "snowwarning", "hail"),
        ),
        (
            ("vulpix-alola", "snowwarning", "hail"),
            # Default forms should be rejected
            ("vulpix", "drought", "sunnyday"),
        ),
    ),
)
async def test_monopoke(
    showdown_connection, pokemon1: tuple[str, str, str], pokemon2: tuple[str, str, str]
) -> None:
    async with showdown_connection() as (bot, mod):
        # Create the tournament
        await mod.send(f"lobby|.monopoke {pokemon1[0]}")
        await mod.await_message(
            "|tournament|create|gen8nationaldex|Single Elimination|0|MONOPOKE TOUR"
        )

        # The first pokemon should be accepted
        await mod.send(
            f"|/utm {pokemon1[0]}|||{pokemon1[1]}|{pokemon1[2]}||4,,,,,|||||"
        )
        await mod.send("lobby|/tournament vtm")
        msg_accept = await mod.await_message("|popup|", startswith=True)

        # The second pokemon should be rejected
        await mod.send(
            f"|/utm {pokemon2[0]}|||{pokemon2[1]}|{pokemon2[2]}||4,,,,,|||||"
        )
        await mod.send("lobby|/tournament vtm")
        msg_reject = await mod.await_message("|popup|", startswith=True)

        # Close the tournament
        await bot.send("lobby|/tournament end")
        await bot.await_message("|tournament|forceend")

        # Assertions
        assert msg_accept.startswith("|popup|Your team is valid")
        assert msg_reject.startswith("|popup|Your team was rejected")
