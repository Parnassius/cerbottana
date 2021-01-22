from collections import Counter

from models.room import Room
from models.user import User


def test_room(mock_connection) -> None:
    conn, recv_queue, send_queue = mock_connection()

    # Join a room with only an user in it
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

    # Check if the room has been added to the list of the rooms (lobby is special here)
    assert set(conn.rooms.keys()) == {"lobby", "room1"}
    # Check the room title
    assert room1.title == "Room 1"
    # Check if the only user in the room has been added to the room
    assert User.get(conn, "cerbottana") in room1

    assert send_queue.get_all() == Counter(
        [
            "|/cmd roominfo room1",
            "room1|/roomlanguage",
            "|/cmd userdetails cerbottana",
        ]
    )

    # Users enter the room
    recv_queue.add_messages(
        [
            ">room1",
            "|j| User 1",
        ],
        [
            ">room1",
            "|J| User 2",
        ],
        [
            ">room1",
            "|join| User 3",
        ],
    )
    assert User.get(conn, "user1") in room1
    assert User.get(conn, "user2") in room1
    assert User.get(conn, "user3") in room1

    assert send_queue.get_all() == Counter(
        [
            "|/cmd userdetails User 1",
            "|/cmd userdetails User 2",
            "|/cmd userdetails User 3",
        ]
    )

    # Users change names
    recv_queue.add_messages(
        [
            ">room1",
            "|n| User 4|user1",
        ],
        [
            ">room1",
            "|N| User 5|user2",
        ],
        [
            ">room1",
            "|name| User 6|user3",
        ],
    )
    assert User.get(conn, "user1") not in room1
    assert User.get(conn, "user2") not in room1
    assert User.get(conn, "user3") not in room1
    assert User.get(conn, "user4") in room1
    assert User.get(conn, "user5") in room1
    assert User.get(conn, "user6") in room1

    assert send_queue.get_all() == Counter(
        [
            "|/cmd userdetails User 4",
            "|/cmd userdetails User 5",
            "|/cmd userdetails User 6",
        ]
    )

    # Users change names without changing userid
    recv_queue.add_messages(
        [
            ">room1",
            "|n| USER 4|user4",
        ],
        [
            ">room1",
            "|N| USER 5|user5",
        ],
        [
            ">room1",
            "|name| USER 6|user6",
        ],
    )
    assert User.get(conn, "user4") in room1
    assert User.get(conn, "user5") in room1
    assert User.get(conn, "user6") in room1

    assert send_queue.get_all() == Counter(
        [
            "|/cmd userdetails USER 4",
            "|/cmd userdetails USER 5",
            "|/cmd userdetails USER 6",
        ]
    )

    # Users leave the room
    recv_queue.add_messages(
        [
            ">room1",
            "|l| User 4",
        ],
        [
            ">room1",
            "|L| User 5",
        ],
        [
            ">room1",
            "|leave| User 6",
        ],
    )
    assert User.get(conn, "user4") not in room1
    assert User.get(conn, "user5") not in room1
    assert User.get(conn, "user6") not in room1

    assert send_queue.get_all() == Counter()

    # Global and room rank
    recv_queue.add_queryresponse_userdetails(
        "cerbottana", group="+", rooms={"room1": "*"}
    )
    assert User.get(conn, "cerbottana").global_rank == "+"
    assert User.get(conn, "cerbottana").rank(room1) == "*"

    assert send_queue.get_all() == Counter()

    recv_queue.close()
