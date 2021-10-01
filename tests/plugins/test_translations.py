import pytest

from plugins.translations import _get_translations

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "word, languages, results",
    (
        (
            "azione",
            (8, 9),
            {("move", "tackle"): {"Tackle"}},
        ),
        (
            "tackle",
            (8, 9),
            {("move", "azione"): {"Azione"}},
        ),
        (
            "metronome",
            (8, 9),
            {
                ("item", "plessimetro"): {"Plessimetro"},
                ("move", "metronomo"): {"Metronomo"},
            },
        ),
        (
            "pound",
            (6, 9),
            {("move", "klaps"): {"Klaps"}},
        ),
        (
            "klaps",
            (6, 9),
            {("move", "pound"): {"Pound"}},
        ),
        (
            "klaps",
            (6, 5),
            {("move", "ecrasface"): {"Écras’Face"}},
        ),
        (
            "charge",
            (5, 9),
            {("move", "chargeur"): {"Chargeur"}, ("move", "tackle"): {"Tackle"}},
        ),
        (
            "hdb",
            (8, 9),
            {("item", "scarponirobusti"): {"Scarponi robusti"}},
        ),
    ),
)
async def test_translations(
    word: str, languages: tuple[int, int], results: dict[tuple[str, str], set[str]]
) -> None:
    assert _get_translations(word, languages) == results


async def test_translations_conn(mock_connection):
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
