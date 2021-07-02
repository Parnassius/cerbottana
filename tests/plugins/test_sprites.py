from __future__ import annotations

import pytest

import utils
from plugins import sprites


@pytest.mark.parametrize(
    "pokemon, dexname",
    (
        ("Litten", "litten"),
        ("Nidoran-F", "nidoranf"),
        ("Ninetales-Alola", "ninetales-alola"),
        ("Mewtwo-Mega-Y", "mewtwo-megay"),
        ("Kommo-O-Totem", "kommoo-totem"),
        ("Unown-B", "unown-b"),
        ("Alcremie-Lemon-Cream", "alcremie-lemoncream"),
    ),
)
def test_generate_sprite_url(pokemon: str, dexname: str) -> None:
    """Tests that PS sprite URLs are generated correctly from pokemon names."""
    dex_entry = utils.get_ps_dex_entry(pokemon)
    assert dex_entry is not None

    expected_url = f"https://play.pokemonshowdown.com/sprites/ani/{dexname}.gif"
    assert sprites.generate_sprite_url(dex_entry, search_query=pokemon) == expected_url
