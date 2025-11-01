import pytest
from pokedex.enums import Language

from cerbottana.plugins.translations import _get_translations


@pytest.mark.parametrize(
    ("word", "languages", "results"),
    [
        (
            "azione",
            (Language.ITALIAN, Language.ENGLISH),
            {("move", "tackle"): {"Tackle"}},
        ),
        (
            "tackle",
            (Language.ITALIAN, Language.ENGLISH),
            {("move", "azione"): {"Azione"}},
        ),
        (
            "metronome",
            (Language.ITALIAN, Language.ENGLISH),
            {
                ("item", "plessimetro"): {"Plessimetro"},
                ("move", "metronomo"): {"Metronomo"},
            },
        ),
        (
            "pound",
            (Language.GERMAN, Language.ENGLISH),
            {("move", "klaps"): {"Klaps"}},
        ),
        (
            "klaps",
            (Language.GERMAN, Language.ENGLISH),
            {("move", "pound"): {"Pound"}},
        ),
        (
            "klaps",
            (Language.GERMAN, Language.FRENCH),
            {("move", "ecrasface"): {"Écras’Face"}},  # noqa: RUF001
        ),
        (
            "charge",
            (Language.FRENCH, Language.ENGLISH),
            {("move", "chargeur"): {"Chargeur"}, ("move", "tackle"): {"Tackle"}},
        ),
        (
            "hdb",
            (Language.ITALIAN, Language.ENGLISH),
            {("item", "scarponirobusti"): {"Scarponi robusti"}},
        ),
        (
            "sub",
            (Language.ITALIAN, Language.ENGLISH),
            {("move", "dive"): {"Dive"}},
        ),
        (
            "sub",
            (Language.ENGLISH, Language.FRENCH),
            {("move", "clonage"): {"Clonage"}},
        ),
        (
            "fee",
            (Language.GERMAN, Language.ENGLISH),
            {("egg_group", "fairy"): {"Fairy"}, ("type", "fairy"): {"Fairy"}},
        ),
        (
            "dragon",
            (Language.ENGLISH, Language.FRENCH),
            {
                ("egg_group", "draconique"): {"Draconique"},
                ("type", "dragon"): {"Dragon"},
            },
        ),
        (
            "ditto",
            (Language.SPANISH, Language.ITALIAN),
            {("egg_group", "ditto"): {"Ditto"}, ("pokemon", "ditto"): {"Ditto"}},
        ),
        (
            "flygon",
            (Language.ENGLISH, Language.FRENCH),
            {("pokemon", "libegon"): {"Libégon"}},
        ),
        (
            "aaaa",
            (Language.ITALIAN, Language.FRENCH),
            {},
        ),
        (
            "aaaa",
            (Language.ENGLISH, Language.FRENCH),
            {},
        ),
    ],
)
async def test_translations(
    word: str,
    languages: tuple[Language, Language],
    results: dict[tuple[str, str], set[str]],
) -> None:
    assert await _get_translations(word, languages) == results


async def test_translations_conn(mock_connection):
    async with mock_connection() as conn:
        await conn.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await conn.add_user_join("room1", "user1", "+")
        await conn.add_user_join("room1", "cerbottana", "*")
        await conn.get_messages()

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.translate azione",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("|/w user1, ", "") == "Tackle"

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.translate Metronome",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert {
            i.strip() for i in next(iter(reply)).replace("|/w user1, ", "").split(",")
        } == {"Metronomo (move)", "Plessimetro (item)"}

        await conn.add_messages(
            [
                ">room1",
                "This room's primary language is German",
            ]
        )
        await conn.get_messages()

        await conn.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Pound",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "Klaps"

        await conn.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Klaps, fr",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "Écras’Face"  # noqa: RUF001

        await conn.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Charge, fr, en",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert {
            i.strip() for i in next(iter(reply)).replace("room1|", "").split(",")
        } == {"Chargeur (move)", "Tackle (move)"}
