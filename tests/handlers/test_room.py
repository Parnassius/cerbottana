from __future__ import annotations

from collections import Counter

from cerbottana.models.room import Room
from cerbottana.models.user import User


async def test_room(mock_connection) -> None:
    async with mock_connection() as conn:

        # Join a room with only an user in it
        await conn.add_messages(
            [
                ">room1",
                "|init|chat",
                "|title|Room 1",
                "|users|1,*cerbottana",
                "|:|1500000000",
            ]
        )

        assert await conn.get_messages() == Counter(
            [
                "|/cmd roominfo room1",
                "room1|/roomlanguage",
                "|/cmd userdetails cerbottana",
            ]
        )

        room1 = Room.get(conn, "room1")
        # Check if the room has been added to the list of the rooms
        assert set(conn.rooms.keys()) == {"room1"}
        # Check the room title
        assert room1.title == "Room 1"
        # Check if the only user in the room has been added to the room
        assert User.get(conn, "cerbottana") in room1

        # Users enter the room
        await conn.add_messages(
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
        assert await conn.get_messages() == Counter(
            [
                "|/cmd userdetails user1",
                "|/cmd userdetails user2",
                "|/cmd userdetails user3",
            ]
        )
        assert User.get(conn, "user1") in room1
        assert User.get(conn, "user2") in room1
        assert User.get(conn, "user3") in room1

        # Users change names
        await conn.add_messages(
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
        assert await conn.get_messages() == Counter(
            [
                "|/cmd userdetails user4",
                "|/cmd userdetails user5",
                "|/cmd userdetails user6",
            ]
        )
        assert User.get(conn, "user1") not in room1
        assert User.get(conn, "user2") not in room1
        assert User.get(conn, "user3") not in room1
        assert User.get(conn, "user4") in room1
        assert User.get(conn, "user5") in room1
        assert User.get(conn, "user6") in room1

        # Users change names without changing userid
        await conn.add_messages(
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
        assert await conn.get_messages() == Counter(
            [
                "|/cmd userdetails user4",
                "|/cmd userdetails user5",
                "|/cmd userdetails user6",
            ]
        )
        assert User.get(conn, "user4") in room1
        assert User.get(conn, "user5") in room1
        assert User.get(conn, "user6") in room1

        # Users leave the room
        await conn.add_messages(
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
        assert await conn.get_messages() == Counter()
        assert User.get(conn, "user4") not in room1
        assert User.get(conn, "user5") not in room1
        assert User.get(conn, "user6") not in room1

        # Global and room rank
        await conn.add_queryresponse_userdetails(
            "cerbottana", group="+", rooms={"room1": "*"}
        )
        assert await conn.get_messages() == Counter()
        assert User.get(conn, "cerbottana").global_rank == "+"
        assert User.get(conn, "cerbottana").rank(room1) == "*"
