# Author: Plato (palt0)

from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
from domify import html_elements as e

from cerbottana import utils
from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from domify.base_element import BaseElement

    from cerbottana.models.message import Message


@command_wrapper(
    helpstr="Visualizza/riproduci un file multimediale.", required_rank_editable=True
)
async def media(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Specificare un URL")
        return

    try:
        headers = {"Accept": "audio/*; video/*"}
        async with msg.conn.client_session.get(msg.arg, headers=headers) as response:
            macrotype = response.content_type.split("/")[0]
            html: BaseElement
            if macrotype == "audio":
                html = e.Audio(controls=True, src=msg.arg)
                await msg.reply_htmlbox(html)
            elif macrotype == "video":
                html = e.Video(
                    controls=True,
                    src=msg.arg,
                    style="max-width: 100%; max-height: 300px",
                )
                await msg.reply_htmlbox(html)
            elif macrotype == "image" or utils.is_youtube_link(msg.arg):
                # This command isn't needed for images and youtube links, force to
                # use `!show` if possible.
                await msg.reply("Usa ``!show`` per immagini e video YouTube.")
            else:
                await msg.reply("URL non valido")
    except aiohttp.ClientError:
        await msg.reply("URL non valido")
