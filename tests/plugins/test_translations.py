from __future__ import annotations

import pytest

from cerbottana.plugins.translations import _get_translations


@pytest.mark.parametrize(
    "word, languages, results",
    (
        (
            "azione",
            (8, 9),
            {("move", "tackle"): {"Tackle"}},
        ),
        (
            "tackle",
            (8, 9),
            {("move", "azione"): {"Azione"}},
        ),
        (
            "metronome",
            (8, 9),
            {
                ("item", "plessimetro"): {"Plessimetro"},
                ("move", "metronomo"): {"Metronomo"},
            },
        ),
        (
            "pound",
            (6, 9),
            {("move", "klaps"): {"Klaps"}},
        ),
        (
            "klaps",
            (6, 9),
            {("move", "pound"): {"Pound"}},
        ),
        (
            "klaps",
            (6, 5),
            {("move", "ecrasface"): {"Écras’Face"}},  # noqa: RUF001
        ),
        (
            "charge",
            (5, 9),
            {("move", "chargeur"): {"Chargeur"}, ("move", "tackle"): {"Tackle"}},
        ),
        (
            "hdb",
            (8, 9),
            {("item", "scarponirobusti"): {"Scarponi robusti"}},
        ),
        (
            "sub",
            (8, 9),
            {("move", "dive"): {"Dive"}},
        ),
        (
            "sub",
            (9, 5),
            {("move", "clonage"): {"Clonage"}},
        ),
        (
            "aaaa",
            (8, 5),
            {},
        ),
        (
            "aaaa",
            (9, 5),
            {},
        ),
    ),
)
async def test_translations(
    word: str, languages: tuple[int, int], results: dict[tuple[str, str], set[str]]
) -> None:
    assert _get_translations(word, languages) == results


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
