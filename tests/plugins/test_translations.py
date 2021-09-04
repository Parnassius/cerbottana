def test_translations(mock_connection):
    conn, recv_queue, send_queue = mock_connection()

    recv_queue.add_messages(
        [
            ">room1",
            "|init|chat",
        ]
    )

    recv_queue.add_user_join("room1", "user1", "+")
    recv_queue.add_user_join("room1", "cerbottana", "*")
    send_queue.get_all()

    recv_queue.add_messages(
        [
            f"|pm| user1| {conn.username}|.translate azione",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("|/w user1, ", "") == "Tackle"

    recv_queue.add_messages(
        [
            f"|pm| user1| {conn.username}|.translate Tackle",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("|/w user1, ", "") == "Azione"

    recv_queue.add_messages(
        [
            f"|pm| user1| {conn.username}|.translate Metronome",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert {
        i.strip() for i in next(iter(reply)).replace("|/w user1, ", "").split(",")
    } == {"Metronomo (move)", "Plessimetro (item)"}

    recv_queue.add_messages(
        [
            ">room1",
            "This room's primary language is German",
        ]
    )
    send_queue.get_all()

    recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.translate Pound",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "Klaps"

    recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.translate Klaps",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "Pound"

    recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.translate Klaps, fr",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "Écras’Face"

    recv_queue.add_messages(
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

    recv_queue.close()
