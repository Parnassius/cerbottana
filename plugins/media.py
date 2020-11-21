from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(helpstr="Visualizza/riproduci un file multimediale.")
async def media(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Specificare un URL")
        return

    try:
        headers = {"Accept": "audio/*; video/*"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(msg.arg) as response:
                macrotype = response.content_type.split("/")[0]
                if macrotype == "audio":
                    await msg.reply_htmlbox(f'<audio controls src="{msg.arg}"></audio>')
                elif macrotype == "video":
                    # pylint: disable=line-too-long
                    await msg.reply_htmlbox(
                        f'<video style="max-width: 100%; max-height: 300px;" controls src="{msg.arg}"></video>'
                    )
                elif macrotype == "image" or utils.is_youtube_link(msg.arg):
                    # This command isn't needed for images and youtube links, force to
                    # use `!show` if possible.
                    await msg.reply("Usa ``!show`` per immagini e video YouTube.")
                else:
                    await msg.reply("URL non valido")
    except aiohttp.ClientError:
        await msg.reply("URL non valido")
