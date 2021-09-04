import pytest

pytestmark = pytest.mark.asyncio


async def test_translations(mock_connection):
    conn, recv_queue, send_queue = await mock_connection()

    await recv_queue.add_messages(
        [
            ">room1",
            "|init|chat",
        ]
    )

    await recv_queue.add_user_join("room1", "user1", "+")
    await recv_queue.add_user_join("room1", "cerbottana", "*")
    send_queue.get_all()

    await recv_queue.add_messages(
        [
            f"|pm| user1| {conn.username}|.translate azione",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("|/w user1, ", "") == "Tackle"

    await recv_queue.add_messages(
        [
            f"|pm| user1| {conn.username}|.translate Tackle",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("|/w user1, ", "") == "Azione"

    await recv_queue.add_messages(
        [
            f"|pm| user1| {conn.username}|.translate Metronome",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert {
        i.strip() for i in next(iter(reply)).replace("|/w user1, ", "").split(",")
    } == {"Metronomo (move)", "Plessimetro (item)"}

    await recv_queue.add_messages(
        [
            ">room1",
            "This room's primary language is German",
        ]
    )
    send_queue.get_all()

    await recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.translate Pound",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "Klaps"

    await recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.translate Klaps",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "Pound"

    await recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.translate Klaps, fr",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "Écras’Face"

    await recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.translate Charge, fr, en",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert {i.strip() for i in next(iter(reply)).replace("room1|", "").split(",")} == {
        "Chargeur (move)",
        "Tackle (move)",
    }

    await recv_queue.close()
