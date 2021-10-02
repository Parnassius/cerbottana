import pytest

from cerbottana.plugins import eightball

pytestmark = pytest.mark.asyncio


async def test_eightball(mock_connection):
    async with mock_connection() as conn:

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await conn.recv_queue.add_user_join("room1", "user1", "+")
        await conn.recv_queue.add_user_join("room1", "mod", "@")
        await conn.recv_queue.add_user_join("room1", "cerbottana", "*")
        conn.send_queue.get_all()

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.8ball",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert (
            next(iter(reply)).replace("|/w user1, ", "")
            in eightball.DEFAULT_ANSWERS["English"]
        )

        for lang in eightball.DEFAULT_ANSWERS:
            await conn.recv_queue.add_messages(
                [
                    ">room1",
                    f"This room's primary language is {lang}",
                ]
            )
            await conn.recv_queue.add_messages(
                [
                    ">room1",
                    "|c|+user1|.8ball",
                ]
            )
            reply = conn.send_queue.get_all()
            assert len(reply) == 1
            assert (
                next(iter(reply)).replace("room1|", "")
                in eightball.DEFAULT_ANSWERS[lang]
            )

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "This room's primary language is Japanese",
            ]
        )
        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|c|+user1|.8ball",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert (
            next(iter(reply)).replace("room1|", "")
            in eightball.DEFAULT_ANSWERS["English"]
        )

        eightball.DEFAULT_ANSWERS = {"English": []}

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|c|@mod|.add8ballanswer answ",
            ]
        )
        conn.send_queue.get_all()
        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|c|+user1|.8ball",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "answ"
