from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from freezegun import freeze_time

if TYPE_CHECKING:
    from tests.conftest import ServerWs, TestConnection


async def test_usernames(mock_connection):
    async def handler(ws: ServerWs, conn: TestConnection) -> None:

        await ws.add_messages(
            [
                ">publicroom",
                "|init|chat",
            ],
            [
                ">privateroom",
                "|init|chat",
            ],
        )

        await ws.add_user_join("publicroom", "user1", "+")
        await ws.add_user_join("publicroom", "cerbottana", "*")
        await ws.add_user_join("privateroom", "user1", "+")
        await ws.add_user_join("privateroom", "cerbottana", "*")

        # Add a couple of formats, needed for .silver97
        await ws.add_messages(
            ["|formats|,LL|,1|Sw/Sh Singles|Random Battle,f|OU,e|Custom Game,c"]
        )

        # Set public rooms, needed for .annika, .averardo, and .francyy
        data = {
            "chat": [{"title": "Public Room", "desc": "", "userCount": 2}],
            "userCount": 2,
            "battleCount": 0,
        }
        await ws.add_messages([f"|queryresponse|rooms|{json.dumps(data)}"])

        await ws.get_messages()

        username_commands = [
            i
            for i in conn.commands.values()
            if i.module == "cerbottana.plugins.usernames"
        ]

        for cmd in username_commands:
            await ws.add_messages(
                [
                    ">publicroom",
                    f"|c|+user1|.{cmd.name}",
                ]
            )
            reply_public = await ws.get_messages()
            await ws.add_messages(
                [
                    ">privateroom",
                    f"|c|+user1|.{cmd.name}",
                ]
            )
            reply_private = await ws.get_messages()
            await ws.add_messages(
                [
                    f"|pm|+user1|*cerbottana|.{cmd.name}",
                ]
            )
            reply_pm = await ws.get_messages()

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
        tz = ZoneInfo("Europe/Rome")
        with freeze_time(datetime(2020, 1, 1, hour=10, tzinfo=tz)):
            await ws.add_messages(
                [
                    ">publicroom",
                    "|c|+user1|.plat0",
                ]
            )
            reply_plat0_daytime = await ws.get_messages()
        with freeze_time(datetime(2020, 1, 1, hour=4, tzinfo=tz)):
            await ws.add_messages(
                [
                    ">publicroom",
                    "|c|+user1|.plat0",
                ]
            )
            reply_plat0_nighttime = await ws.get_messages()
        assert not next(iter(reply_plat0_daytime)).endswith("appena svegliato")
        assert next(iter(reply_plat0_nighttime)).endswith("appena svegliato")

    await mock_connection(handler)
