from __future__ import annotations

from typing import TYPE_CHECKING

from cerbottana.plugins import eightball

if TYPE_CHECKING:
    from tests.conftest import ServerWs, TestConnection


async def test_eightball(mock_connection) -> None:
    async def handler(ws: ServerWs, conn: TestConnection) -> None:

        await ws.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await ws.add_user_join("room1", "user1", "+")
        await ws.add_user_join("room1", "mod", "@")
        await ws.add_user_join("room1", "cerbottana", "*")
        await ws.get_messages()

        await ws.add_messages(
            [
                f"|pm| user1| {conn.username}|.8ball",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert (
            next(iter(reply)).replace("|/w user1, ", "")
            in eightball.DEFAULT_ANSWERS["English"]
        )

        for lang in eightball.DEFAULT_ANSWERS:
            await ws.add_messages(
                [
                    ">room1",
                    f"This room's primary language is {lang}",
                ]
            )
            await ws.add_messages(
                [
                    ">room1",
                    "|c|+user1|.8ball",
                ]
            )
            reply = await ws.get_messages()
            assert len(reply) == 1
            assert (
                next(iter(reply)).replace("room1|", "")
                in eightball.DEFAULT_ANSWERS[lang]
            )

        await ws.add_messages(
            [
                ">room1",
                "This room's primary language is Japanese",
            ]
        )
        await ws.add_messages(
            [
                ">room1",
                "|c|+user1|.8ball",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert (
            next(iter(reply)).replace("room1|", "")
            in eightball.DEFAULT_ANSWERS["English"]
        )

        eightball.DEFAULT_ANSWERS = {"English": []}

        await ws.add_messages(
            [
                ">room1",
                "|c|@mod|.add8ballanswer answ",
            ]
        )
        await ws.get_messages()
        await ws.add_messages(
            [
                ">room1",
                "|c|+user1|.8ball",
            ]
        )
        reply = await ws.get_messages()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "answ"

    await mock_connection(handler)
