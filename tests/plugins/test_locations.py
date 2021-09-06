import pytest

pytestmark = pytest.mark.asyncio


async def test_locations(mock_connection, veekun_database):
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
                f"|pm| user1| {conn.username}|.locations abc",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.locations pikachu",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.locations nidoranf",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))


async def test_encounters(mock_connection, veekun_database):
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
                f"|pm| user1| {conn.username}|.encounters abc",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " not in next(iter(reply))

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.encounters kantoroute1",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))

        await conn.recv_queue.add_messages(
            [
                f"|pm| user1| {conn.username}|.encounters sootopolis city",
            ]
        )
        reply = conn.send_queue.get_all()
        assert len(reply) == 1
        assert "/pminfobox " in next(iter(reply))
