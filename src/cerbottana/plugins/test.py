from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message, RawMessage


@command_wrapper(
    helpstr="Test",
    is_unlisted=True,
    allow_pm=False,
    single_instance=True,
)
class Test:
    @classmethod
    async def cmd_func(cls, msg: Message) -> None:
        await msg.reply("we")
        await asyncio.sleep(10)
        await msg.reply("bye")

    @classmethod
    async def on_message(cls, msg: RawMessage) -> None:
        await msg.reply(msg.message)
