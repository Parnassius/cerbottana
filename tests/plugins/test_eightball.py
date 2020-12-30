import plugins.eightball


def test_eightball(mock_connection):
    conn, recv_queue, send_queue = mock_connection()

    recv_queue.add_user_join("room1", "user1", "+")
    recv_queue.add_user_join("room1", "mod", "@")
    recv_queue.add_user_join("room1", "cerbottana", "*")
    send_queue.get_all()

    recv_queue.add_messages(
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
        recv_queue.add_messages(
            [
                ">room1",
                f"This room's primary language is {lang}",
            ]
        )
        recv_queue.add_messages(
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

    recv_queue.add_messages(
        [
            ">room1",
            "This room's primary language is Japanese",
        ]
    )
    recv_queue.add_messages(
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

    recv_queue.add_messages(
        [
            ">room1",
            "|c|@mod|.add8ballanswer answ",
        ]
    )
    send_queue.get_all()
    recv_queue.add_messages(
        [
            ">room1",
            "|c|+user1|.8ball",
        ]
    )
    reply = send_queue.get_all()
    assert len(reply) == 1
    assert next(iter(reply)).replace("room1|", "") == "answ"

    recv_queue.close()
