import pytest

from cerbottana.plugins import tours

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


@pytest.mark.parametrize(
    "pokemon_data", [obtainable, past, default_form, regional_form]
)
async def test_obtainability(pokemon_showdown, *, pokemon_data: dict[str, str]) -> None:
    valid = "species" in pokemon_data

    species = pokemon_data["species" if valid else "species_past"]
    ability = pokemon_data["ability"]
    move = pokemon_data["move"]

    team = f"{species}|||{ability}|{move}||4,,,,,|||||"
    pokemon_showdown.validate_team("ou", team, valid)

    if "move_past" in pokemon_data:
        move_past = pokemon_data["move_past"]

        team = f"|/utm {species}|||{ability}|{move_past}||4,,,,,|||||"
        pokemon_showdown.validate_team("ou", team, False)


@pytest.mark.parametrize(
    ("monopoke", "species", "item", "ability", "moves", "valid"),
    [
        pytest.param(
            # `Past` pokemon should be accepted
            past["species_past"],
            past["species_past"],
            "",
            past["ability"],
            past["move"],
            True,
            marks=pytest.mark.xfail,
        ),
        pytest.param(
            # Pokemon with `Past` moves should be accepted
            obtainable["species"],
            obtainable["species"],
            "",
            obtainable["ability"],
            obtainable["move_past"],
            True,
            marks=pytest.mark.xfail,
        ),
        (
            # `Past` pokemon should be rejected
            obtainable["species"],
            past["species_past"],
            "",
            past["ability"],
            past["move"],
            False,
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
async def test_monopoketour(
    pokemon_showdown,
    *,
    monopoke: str,
    species: str,
    item: str,
    ability: str,
    moves: str,
    valid: bool,
) -> None:
    cmd = tours.Monopoketour.cls  # type: ignore[attr-defined]
    formatid = cmd.formatid
    rules = [*cmd.rules, f"+{monopoke}-base"]
    rules_str = ",".join(rules)
    team = f"{species}||{item}|{ability}|{moves}||4,,,,,|||||"
    pokemon_showdown.validate_team(f"{formatid} @@@ {rules_str}", team, valid)


async def test_tier_info(mock_connection) -> None:
    async with mock_connection() as conn:
        await conn.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )
        await conn.add_user_join("room1", "mod", "@")

        # Send dummy tier information
        await conn.add_messages(
            [
                "|formats|,1|S/V Singles|"
                "[Gen 9] Random Battle,4f|[Gen 9] OU,e|[Gen 9] National Dex,e",
            ]
        )
        await conn.get_messages()

        # Random tiers should not trigger a tier info message
        await conn.add_messages(
            [
                ">room1",
                "|tournament|create|gen9randombattle|Single Elimination|0",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 0

        # Non random tiers should trigger a tier info message
        await conn.add_messages(
            [
                ">room1",
                "|tournament|create|gen9ou|Single Elimination|0",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)) == "room1|!tier [Gen 9] OU"

        # Tours started with custom commands should not trigger a tier info message
        await conn.add_messages(
            [
                ">room1",
                "|c|@mod|.monopoke pikachu",
            ]
        )
        await conn.get_messages()
        await conn.add_messages(
            [
                ">room1",
                "|tournament|create|gen9nationaldex|Single Elimination|0",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 0
