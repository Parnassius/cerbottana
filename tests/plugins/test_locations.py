from __future__ import annotations


async def test_locations(mock_connection, veekun_database):
    async with mock_connection() as conn:
        await conn.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await conn.add_user_join("room1", "user1")
        await conn.add_user_join("room1", "cerbottana", "*")
        await conn.get_messages()

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.locations abc",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.locations pikachu",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.locations nidoranf",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))


async def test_encounters(mock_connection, veekun_database):
    async with mock_connection() as conn:
        await conn.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await conn.add_user_join("room1", "user1")
        await conn.add_user_join("room1", "cerbottana", "*")
        await conn.get_messages()

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.encounters abc",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.encounters kantoroute1",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.encounters sootopolis city",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))
