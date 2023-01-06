from __future__ import annotations


async def test_learnsets(mock_connection, veekun_database):
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
                f"|pm| user1| {conn.username}|.learnset pikachu",
            ]
        )
        assert len(await conn.get_messages()) == 0

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset abc",
            ]
        )
        assert len(await conn.get_messages()) == 0

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset abc, red",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pikachu, red",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pichu, red",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))
