import pytest

import plugins.eightball

pytestmark = pytest.mark.asyncio


async def test_eightball(mock_connection):
    conn, recv_queue, send_queue = await mock_connection()

    await recv_queue.add_messages(
        [
            ">room1",
            "|init|chat",
        ]
    )

    await recv_queue.add_user_join("room1", "user1", "+")
    await recv_queue.add_user_join("room1", "mod", "@")
    await recv_queue.add_user_join("room1", "cerbottana", "*")
    send_queue.get_all()

    await recv_queue.add_messages(
        [
            f"|pm| user1| {conn.username}|.8ball",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert (
        next(iter(reply)).replace("|/w user1, ", "")
        in plugins.eightball.DEFAULT_ANSWERS["English"]
    )

    for lang in plugins.eightball.DEFAULT_ANSWERS:
        await recv_queue.add_messages(
            [
                ">room1",
                f"This room's primary language is {lang}",
            ]
        )
        await recv_queue.add_messages(
            [
                ">room1",
                "|c|+user1|.8ball",
            ]
        )
        reply = send_queue.get_all()
        assert len(reply) == 1
        assert (
            next(iter(reply)).replace("room1|", "")
            in plugins.eightball.DEFAULT_ANSWERS[lang]
        )

    await recv_queue.add_messages(
        [
            ">room1",
            "This room's primary language is Japanese",
        ]
    )
    await recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.8ball",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert (
        next(iter(reply)).replace("room1|", "")
        in plugins.eightball.DEFAULT_ANSWERS["English"]
    )

    plugins.eightball.DEFAULT_ANSWERS = {"English": []}

    await recv_queue.add_messages(
        [
            ">room1",
            "|c|@mod|.add8ballanswer answ",
        ]
    )
    send_queue.get_all()
    await recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.8ball",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "answ"

    await recv_queue.close()
