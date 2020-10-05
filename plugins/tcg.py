from __future__ import annotations

import urllib
from typing import TYPE_CHECKING

import aiohttp

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


def to_card_id(card_name: str) -> str:
    """Transform a MtG card name into a string ID.

    Args:
        card_name (str): MtG card name. Case insensitive.

    Returns:
        str: Card ID. Lowercase, alphanumeric characters.
    """
    return "".join(ch.lower() for ch in card_name if ch.isalpha())


@command_wrapper(
    aliases=("carta", "magic", "mtg"),
    helpstr="Mostra una carta di Magic: the Gathering",
)
async def card(msg: Message) -> None:
    if msg.room is None:
        return

    if not msg.arg:
        await msg.reply("Che carta devo cercare?")
        return

    query = urllib.parse.quote(msg.arg)
    url = "https://api.scryfall.com/cards/search?order=name&q=" + query

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await msg.reply("Nome non valido")
                return
            json_body = await resp.json()

    # API error handling ~ Response should be a non-empty list of Card objects.
    resp_type = json_body["object"]
    if resp_type != "list":
        print(f'Scryfall API error: Response object is "{resp_type}", expected "list"')
        return

    cards = json_body["data"]
    if not cards:
        print("Scryfall API error: Response data is an empty list.")
        return

    if len(cards) == 1:
        card_ = cards[0]
    else:
        # If there is an exact match, discard other results.
        # Use case: "Black Lotus" -> ["Black Lotus", "Blacker Lotus"]
        my_card_id = to_card_id(msg.arg)
        card_ = next((c for c in cards if to_card_id(c["name"]) == my_card_id), None)

    if card_:
        # Show card thumbnail(s) if there's only 1 query result.

        # img_uris ~ URI for card thumbnail(s): Double-faced cards have 2 thumbnails.
        # Example of a double-faced card query: "Search for Azcanta"
        if "card_faces" in card_:
            img_uris = [face["image_uris"]["normal"] for face in card_["card_faces"]]
        else:
            img_uris = [card_["image_uris"]["normal"]]

        # scryfall_uri: Images are clickable and redirect to the card's Scryfall page.
        scryfall_uri = card_["scryfall_uri"]

        html = utils.render_template(
            "commands/mtg_card.html", img_uris=img_uris, scryfall_uri=scryfall_uri
        )
        await msg.reply_htmlbox(html)
    elif len(cards) <= 40:
        # Show a list of all query results.

        link = '<a href="{}">{}</a>'
        links = [link.format(c["scryfall_uri"], c["name"]) for c in cards]
        await msg.reply_htmlbox("<br>".join(links))
    else:
        await msg.reply(f"**{len(cards)}** risultati! Usa un nome più specifico...")
