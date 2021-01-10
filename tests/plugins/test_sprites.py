from __future__ import annotations

import pytest

import plugins.sprites as sprites


@pytest.mark.parametrize(
    "pokemon, dexname",
    (
        ("Litten", "litten"),
        ("Nidoran-F", "nidoranf"),
        ("Ninetales-Alola", "ninetales-alola"),
        ("Mewtwo-Mega-Y", "mewtwo-megay"),
        ("Kommo-O-Totem", "kommoo-totem"),  # Will be the correct syntax in the future.
    ),
)
def test_generate_sprite_url(pokemon: str, dexname: str) -> None:
    """Tests PS sprite URLs are generated correctly from pokemon names."""
    expected_url = f"https://play.pokemonshowdown.com/sprites/ani/{dexname}.gif"
    assert sprites.generate_sprite_url(pokemon, False) == expected_url
