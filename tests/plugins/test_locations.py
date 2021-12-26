from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import ServerWs, TestConnection


async def test_locations(mock_connection, veekun_database):
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
                f"|pm| user1| {conn.username}|.locations abc",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.locations pikachu",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.locations nidoranf",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

    await mock_connection(handler)


async def test_encounters(mock_connection, veekun_database):
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
                f"|pm| user1| {conn.username}|.encounters abc",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.encounters kantoroute1",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.encounters sootopolis city",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

    await mock_connection(handler)
