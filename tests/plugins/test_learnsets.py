from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import ServerWs, TestConnection


async def test_learnsets(mock_connection, veekun_database):
    async def handler(ws: ServerWs, conn: TestConnection) -> None:

        await ws.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await ws.add_user_join("room1", "user1")
        await ws.add_user_join("room1", "cerbottana", "*")
        await ws.get_messages()

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pikachu",
            ]
        )
        assert len(await ws.get_messages()) == 0

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset abc",
            ]
        )
        assert len(await ws.get_messages()) == 0

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset abc, red",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pikachu, red",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pichu, red",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

    await mock_connection(handler)
