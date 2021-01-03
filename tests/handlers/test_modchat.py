from models.room import Room


def test_modchat(mock_connection) -> None:
    conn, recv_queue, _ = mock_connection()

    recv_queue.add_messages(
        [
            ">room1",
            "|init|chat",
            "|title|Room 1",
            "|users|1,*cerbottana",
            "|:|1500000000",
        ]
    )

    room1 = Room.get(conn, "room1")

    # by default no_mods_online is None
    assert room1.no_mods_online is None

    # a mod enters the room, no_mods_online should still be None
    recv_queue.add_user_join("room1", "mod", "@")
    assert room1.no_mods_online is None

    # a regular user joins then leaves the room, no_mods_online should still be None
    recv_queue.add_user_join("room1", "reg")
    assert room1.no_mods_online is None
    recv_queue.add_user_leave("room1", "reg")
    assert room1.no_mods_online is None

    # another mod enters the room, no_mods_online should still be None
    recv_queue.add_user_join("room1", "mod2", "@")
    assert room1.no_mods_online is None

    # mod2 leaves the room, no_mods_online should still be None
    recv_queue.add_user_leave("room1", "mod2")
    assert room1.no_mods_online is None

    # the first mod leaves the room as well, no_mods_online should no longer be None
    recv_queue.add_user_leave("room1", "mod")
    assert room1.no_mods_online is not None

    time = room1.no_mods_online  # type: ignore
    # see https://github.com/python/mypy/issues/9457

    # another regular user joins then leaves the room, no_mods_online shouldn't change
    recv_queue.add_user_join("room1", "reg2")
    assert room1.no_mods_online == time
    recv_queue.add_user_leave("room1", "reg2")
    assert room1.no_mods_online == time

    # a mod comes back then leaves again, no_mods_online should be different
    recv_queue.add_user_join("room1", "mod", "@")
    assert room1.no_mods_online is None
    recv_queue.add_user_leave("room1", "mod")
    assert room1.no_mods_online is not None
    assert room1.no_mods_online != time

    # a mod under alt joins the room
    recv_queue.add_user_join("room1", "modalt")
    assert room1.no_mods_online is not None

    # then changes name
    recv_queue.add_user_namechange("room1", "mod", "modalt", "@")
    assert room1.no_mods_online is None

    # then changes name again
    recv_queue.add_user_namechange("room1", "modalt", "mod")
    assert room1.no_mods_online is not None

    # same as before, but while another mod is online
    recv_queue.add_user_join("room1", "mod2", "@")
    assert room1.no_mods_online is None

    recv_queue.add_user_namechange("room1", "mod", "modalt", "@")
    assert room1.no_mods_online is None

    recv_queue.add_user_namechange("room1", "modalt", "mod")
    assert room1.no_mods_online is None

    # finally they both leave
    recv_queue.add_user_leave("room1", "modalt")
    recv_queue.add_user_leave("room1", "mod2")
    assert room1.no_mods_online is not None

    # a gmod enters the room, no_mods_online should still be not None because gstaff is
    # ignored
    recv_queue.add_user_join("room1", "gmod", group="@")
    assert room1.no_mods_online is not None

    recv_queue.close()
