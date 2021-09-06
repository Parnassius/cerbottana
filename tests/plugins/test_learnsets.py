import pytest

pytestmark = pytest.mark.asyncio


async def test_learnsets(mock_connection, veekun_database):
    async with mock_connection() as conn:

        await conn.recv_queue.add_messages(
            [
                ">room1",
                "|init|chat",
            ]
        )

        await conn.recv_queue.add_user_join("room1", "user1")
        await conn.recv_queue.add_user_join("room1", "cerbottana", "*")
        conn.send_queue.get_all()

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pikachu",
            ]
        )
        assert len(conn.send_queue.get_all()) == 0

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset abc",
            ]
        )
        assert len(conn.send_queue.get_all()) == 0

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset abc, red",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pikachu, red",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.learnset pichu, red",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))
