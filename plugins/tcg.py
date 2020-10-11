from __future__ import annotations

import urllib
from typing import TYPE_CHECKING, Any, Dict, Optional

import aiohttp

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


JsonDict = Dict[str, Any]  # type: ignore[misc]


async def query_scryfall(url: str, resp_type: str) -> Optional[JsonDict]:
    """Queries the Scryfall API.

    Args:
        url (str): Query.
        resp_type (str): Expected Scryfall API object type.

    Returns:
        Optional[JsonDict]: Valid JSON received from the API, None if data is not valid.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            json_body: JsonDict = await resp.json()

    # API error handling
    # Check response type and trust the API that it has the required parameters.
    if json_body["object"] != resp_type:
        print(f'Scryfall API error: Response object is "{resp_type}", expected "list"')
        return None

    return json_body


def to_card_id(card_name: str) -> str:
    """Transform a MtG card name into a string ID.

    Args:
        card_name (str): MtG card name. Case insensitive.

    Returns:
        str: Card ID. Lowercase, alphanumeric characters.
    """
    return "".join(ch.lower() for ch in card_name if ch.isalpha())


def to_card_thumbnail(card_json: JsonDict) -> str:
    """Generates HTML that shows card thumbnail(s).

    Args:
        card_json (JsonDict): JSON of a Scryfall Card object.

    Returns:
        str: htmlbox code.
    """
    # img_uris ~ URI for card thumbnail(s)
    if "card_faces" in card_json and "image_uris" in card_json["card_faces"][0]:
        # Double-faced cards have 2 thumbnails, i.e. transform cards.
        img_uris = [face["image_uris"]["normal"] for face in card_json["card_faces"]]
    elif "image_uris" in card_json:
        # Most cards have 1 thumbnail. Split cards fall under this category.
        img_uris = [card_json["image_uris"]["normal"]]
    else:
        # Fallback: image_uris isn't guaranteed to exist or be non-null but the previous
        # conditional cases should cover most cards.
        return 'Immagine per <a href="{}">{}</a> non disponibile.'.format(
            card_json["scryfall_uri"],
            card_json["name"],
        )

    return utils.render_template(
        "commands/mtg_card.html",
        img_uris=img_uris,
        scryfall_uri=card_json["scryfall_uri"],
    )


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
    url = "https://api.scryfall.com/cards/search?include_multilingual=true&q=" + query

    json_body = await query_scryfall(url, "list")
    if json_body is None:
        await msg.reply("Nome non valido")
        return
    cards = json_body["data"]  # Scryfall lists are always non-empty.

    if len(cards) == 1:
        card_ = cards[0]
    else:
        # If there is an exact match, discard other results.
        # Use case: "Black Lotus" -> ["Black Lotus", "Blacker Lotus"]
        my_card_id = to_card_id(msg.arg)
        card_ = next((c for c in cards if to_card_id(c["name"]) == my_card_id), None)

    if card_:
        # Show card thumbnail(s) if there's only 1 query result.
        await msg.reply_htmlbox(to_card_thumbnail(card_))
    elif len(cards) <= 40:
        # Show a list of all query results.
        link = '<a href="{}">{}</a>'
        links = [link.format(c["scryfall_uri"], c["name"]) for c in cards]
        await msg.reply_htmlbox("<br>".join(links))
    else:
        await msg.reply(f"**{len(cards)}** risultati! Usa un nome più specifico...")


@command_wrapper(aliases=("randomcard",))
async def randcard(msg: Message) -> None:
    if msg.room is None:
        return

    url = "https://api.scryfall.com/cards/random"
    if msg.arg:
        # Users can input an optional query to restrict the cardpool.
        url += "?q=" + urllib.parse.quote(msg.arg)

    card_ = await query_scryfall(url, "card")
    if card_ is None:
        await msg.reply("Ricerca non valida")
        return

    await msg.reply_htmlbox(to_card_thumbnail(card_))
