import pytest

pytestmark = pytest.mark.asyncio


async def test_translations(mock_connection):
    async with mock_connection() as conn:

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await conn.recv_queue.add_user_join("room1", "user1", "+")
        await conn.recv_queue.add_user_join("room1", "cerbottana", "*")
        conn.send_queue.get_all()

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.translate azione",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert next(iter(reply)).replace("|/w user1, ", "") == "Tackle"

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.translate Tackle",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert next(iter(reply)).replace("|/w user1, ", "") == "Azione"

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.translate Metronome",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert {
            i.strip() for i in next(iter(reply)).replace("|/w user1, ", "").split(",")
        } == {"Metronomo (move)", "Plessimetro (item)"}

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "This room's primary language is German",
            ]
        )
        conn.send_queue.get_all()

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Pound",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "Klaps"

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Klaps",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "Pound"

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Klaps, fr",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert next(iter(reply)).replace("room1|", "") == "Écras’Face"

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|c|+user1|.translate Charge, fr, en",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert {
            i.strip() for i in next(iter(reply)).replace("room1|", "").split(",")
        } == {"Chargeur (move)", "Tackle (move)"}
