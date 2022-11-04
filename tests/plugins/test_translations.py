from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cerbottana.plugins.translations import _get_translations

if TYPE_CHECKING:
    from tests.conftest import ServerWs, TestConnection


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
            {("move", "ecrasface"): {"Écras’Face"}},
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
    async def handler(ws: ServerWs, conn: TestConnection) -> None:

        await ws.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await ws.add_user_join("room1", "user1", "+")
        await ws.add_user_join("room1", "cerbottana", "*")
        await ws.get_messages()

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.translate azione",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("|/w user1, ", "") == "Tackle"

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.translate Metronome",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert {
            i.strip() for i in next(iter(reply)).replace("|/w user1, ", "").split(",")
        } == {"Metronomo (move)", "Plessimetro (item)"}

        await ws.add_messages(
            [
                ">room1",
                "This room's primary language is German",
            ]
        )
        await ws.get_messages()

        await ws.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Pound",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "Klaps"

        await ws.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Klaps, fr",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "Écras’Face"

        await ws.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Charge, fr, en",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert {
            i.strip() for i in next(iter(reply)).replace("room1|", "").split(",")
        } == {"Chargeur (move)", "Tackle (move)"}

    await mock_connection(handler)
