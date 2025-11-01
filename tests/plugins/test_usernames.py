import json
from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time


async def test_usernames(mock_connection):
    async with mock_connection() as conn:
        await conn.add_messages(
            [
                ">publicroom",
                "|init|chat",
            ],
            [
                ">privateroom",
                "|init|chat",
            ],
        )

        await conn.add_user_join("publicroom", "user1", "+")
        await conn.add_user_join("publicroom", "cerbottana", "*")
        await conn.add_user_join("privateroom", "user1", "+")
        await conn.add_user_join("privateroom", "cerbottana", "*")

        # Add a couple of formats, needed for .silver97
        await conn.add_messages(
            ["|formats|,LL|,1|Sw/Sh Singles|Random Battle,f|OU,e|Custom Game,c"]
        )

        # Set public rooms, needed for .annika, .averardo, and .francyy
        data = {
            "chat": [{"title": "Public Room", "desc": "", "userCount": 2}],
            "userCount": 2,
            "battleCount": 0,
        }
        await conn.add_messages([f"|queryresponse|rooms|{json.dumps(data)}"])

        await conn.get_messages()

        username_commands = [
            i
            for i in conn.commands.values()
            if i.module == "cerbottana.plugins.usernames"
        ]

        for cmd in username_commands:
            await conn.add_messages(
                [
                    ">publicroom",
                    f"|c|+user1|.{cmd.name}",
                ]
            )
            reply_public = await conn.get_messages()
            await conn.add_messages(
                [
                    ">privateroom",
                    f"|c|+user1|.{cmd.name}",
                ]
            )
            reply_private = await conn.get_messages()
            await conn.add_messages(
                [
                    f"|pm|+user1|*cerbottana|.{cmd.name}",
                ]
            )
            reply_pm = await conn.get_messages()

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
            await conn.add_messages(
                [
                    ">publicroom",
                    "|c|+user1|.plat0",
                ]
            )
            reply_plat0_daytime = await conn.get_messages()
        with freeze_time(datetime(2020, 1, 1, hour=4, tzinfo=tz)):
            await conn.add_messages(
                [
                    ">publicroom",
                    "|c|+user1|.plat0",
                ]
            )
            reply_plat0_nighttime = await conn.get_messages()
        assert not next(iter(reply_plat0_daytime)).endswith("appena svegliato")
        assert next(iter(reply_plat0_nighttime)).endswith("appena svegliato")
