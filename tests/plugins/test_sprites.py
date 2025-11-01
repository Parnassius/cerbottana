import pytest

from cerbottana import utils
from cerbottana.plugins.sprites import SPRITE_CATEGORIES, generate_sprite_url


@pytest.mark.parametrize(
    ("pokemon", "dex_name", "category", "fallback"),
    [
        ("Litten", "litten", "ani", False),
        ("Nidoran-F", "nidoranf", "ani", False),
        ("Ninetales-Alola", "ninetales-alola", "ani", False),
        ("Mewtwo-Mega-Y", "mewtwo-megay", "ani", False),
        ("Unown-B", "unown-b", "ani", False),
        ("Alcremie-Lemon-Cream", "alcremie-lemoncream", "ani", False),
        ("Venusaur-Mega", "venusaur-mega", "gen5", True),
        ("Arghonaut", "arghonaut", "ani", True),
    ],
)
def test_generate_sprite_url(
    pokemon: str, dex_name: str, category: str, fallback: bool
) -> None:
    """Tests that PS sprite URLs are generated correctly from pokemon names."""
    for back in (False, True):
        for shiny in (False, True):
            category = SPRITE_CATEGORIES.get(category, category)

            dex_entry = utils.get_ps_dex_entry(pokemon)
            assert dex_entry is not None

            url = generate_sprite_url(
                dex_entry, back=back, shiny=shiny, category=category
            )

            dir_name = category
            if fallback:
                dir_name = "gen5"
            if back:
                dir_name += "-back"
            if shiny:
                dir_name += "-shiny"

            ext = "png"
            if dir_name.startswith(("gen5ani", "ani")):
                ext = "gif"
            expected_url = (
                f"https://play.pokemonshowdown.com/sprites/{dir_name}/{dex_name}.{ext}"
            )

            assert url == expected_url
