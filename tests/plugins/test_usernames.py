import json
from datetime import datetime

import pytest
import pytz
from freezegun import freeze_time

pytestmark = pytest.mark.asyncio


async def test_usernames(mock_connection):
    conn, recv_queue, send_queue = await mock_connection()

    await recv_queue.add_messages(
        [
            ">publicroom",
            "|init|chat",
        ],
        [
            ">privateroom",
            "|init|chat",
        ],
    )

    await recv_queue.add_user_join("publicroom", "user1", "+")
    await recv_queue.add_user_join("publicroom", "cerbottana", "*")
    await recv_queue.add_user_join("privateroom", "user1", "+")
    await recv_queue.add_user_join("privateroom", "cerbottana", "*")

    # Add a couple of formats, needed for .silver97
    await recv_queue.add_messages(
        ["|formats|,LL|,1|Sw/Sh Singles|Random Battle,f|OU,e|Custom Game,c"]
    )

    # Set public rooms, needed for .annika, .averardo, and .francyy
    data = {
        "chat": [{"title": "Public Room", "desc": "", "userCount": 2}],
        "userCount": 2,
        "battleCount": 0,
    }
    await recv_queue.add_messages([f"|queryresponse|rooms|{json.dumps(data)}"])

    send_queue.get_all()

    username_commands = [
        i for i in conn.commands.values() if i.module == "plugins.usernames"
    ]

    for cmd in username_commands:
        await recv_queue.add_messages(
            [
                ">publicroom",
                f"|c|+user1|.{cmd.name}",
            ]
        )
        reply_public = send_queue.get_all()
        await recv_queue.add_messages(
            [
                ">privateroom",
                f"|c|+user1|.{cmd.name}",
            ]
        )
        reply_private = send_queue.get_all()
        await recv_queue.add_messages(
            [
                f"|pm|+user1|*cerbottana|.{cmd.name}",
            ]
        )
        reply_pm = send_queue.get_all()

        if cmd.name == "annika":
            assert len(reply_public) == len(reply_pm) == 0
            assert len(reply_private) == 1
        elif cmd.name == "averardo":
            assert len(reply_public) == 0
            assert len(reply_private) == len(reply_pm) == 1
            assert reply_private != reply_pm
        else:
            assert len(reply_public) == len(reply_private) == len(reply_pm) == 1

            if cmd.name == "ultrasuca":
                assert reply_public != reply_pm

    # I hate you plato
    tz = pytz.timezone("Europe/Rome")
    with freeze_time(datetime(2020, 1, 1, hour=10, tzinfo=tz)):
        await recv_queue.add_messages(
            [
                ">publicroom",
                "|c|+user1|.plat0",
            ]
        )
        reply_plat0_daytime = send_queue.get_all()
    with freeze_time(datetime(2020, 1, 1, hour=4, tzinfo=tz)):
        await recv_queue.add_messages(
            [
                ">publicroom",
                "|c|+user1|.plat0",
            ]
        )
        reply_plat0_nighttime = send_queue.get_all()
    assert not next(iter(reply_plat0_daytime)).endswith("appena svegliato")
    assert next(iter(reply_plat0_nighttime)).endswith("appena svegliato")

    await recv_queue.close()
