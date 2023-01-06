from __future__ import annotations

from cerbottana.plugins import eightball


async def test_eightball(mock_connection) -> None:
    async with mock_connection() as conn:

        await conn.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await conn.add_user_join("room1", "user1", "+")
        await conn.add_user_join("room1", "mod", "@")
        await conn.add_user_join("room1", "cerbottana", "*")
        await conn.get_messages()

        await conn.add_messages(
            [
                f"|pm| user1| {conn.username}|.8ball",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert (
            next(iter(reply)).replace("|/w user1, ", "")
            in eightball.DEFAULT_ANSWERS["English"]
        )

        for lang in eightball.DEFAULT_ANSWERS:
            await conn.add_messages(
                [
                    ">room1",
                    f"This room's primary language is {lang}",
                ]
            )
            await conn.add_messages(
                [
                    ">room1",
                    "|c|+user1|.8ball",
                ]
            )
            reply = await conn.get_messages()
            assert len(reply) == 1
            assert (
                next(iter(reply)).replace("room1|", "")
                in eightball.DEFAULT_ANSWERS[lang]
            )

        await conn.add_messages(
            [
                ">room1",
                "This room's primary language is Japanese",
            ]
        )
        await conn.add_messages(
            [
                ">room1",
                "|c|+user1|.8ball",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert (
            next(iter(reply)).replace("room1|", "")
            in eightball.DEFAULT_ANSWERS["English"]
        )

        eightball.DEFAULT_ANSWERS = {"English": []}

        await conn.add_messages(
            [
                ">room1",
                "|c|@mod|.add8ballanswer answ",
            ]
        )
        await conn.get_messages()
        await conn.add_messages(
            [
                ">room1",
                "|c|+user1|.8ball",
            ]
        )
        reply = await conn.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "answ"
