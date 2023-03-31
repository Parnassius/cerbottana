# Author: Plato (palt0)

from __future__ import annotations

import re
import urllib
from typing import TYPE_CHECKING

import aiohttp
from domify import html_elements as e
from domify.base_element import BaseElement

from cerbottana.plugins import command_wrapper
from cerbottana.typedefs import JsonDict

if TYPE_CHECKING:
    from cerbottana.models.message import Message


async def query_scryfall(url: str, resp_type: str) -> JsonDict | None:
    """Queries the Scryfall API.

    Args:
        url (str): Query.
        resp_type (str): Expected Scryfall API object type.

    Returns:
        JsonDict | None: Valid JSON received from the API, None if data is not valid.
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


def to_card_thumbnail(card_json: JsonDict) -> BaseElement:
    """Generates HTML that shows card thumbnail(s).

    Args:
        card_json (JsonDict): JSON of a Scryfall Card object.

    Returns:
        BaseElement: htmlbox code.
    """

    html: BaseElement

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
        html = (
            "Immagine per "
            + e.A(card_json["name"], href=card_json["scryfall_uri"])
            + " non disponibile."
        )
        return html

    html = e.A(href=card_json["scryfall_uri"])
    for img_uri in img_uris:
        html.add(
            e.Img(
                src=img_uri,
                width=251,
                height=350,
                style="border-radius: 4.75% / 3.5%; margin-right: 5px",
            )
        )
    return html


@command_wrapper(
    aliases=("carta", "magic", "mtg"),
    helpstr="Mostra una carta di Magic: the Gathering",
    allow_pm=False,
)
async def card(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Che carta devo cercare?")
        return

    query = urllib.parse.quote(msg.arg)
    url = "https://api.scryfall.com/cards/search?include_multilingual=true&q=" + query
    json_body = await query_scryfall(url, "list")

    # If the search didn't match any cards, broaden the scope to include extras (tokens,
    # planes, ...).
    if json_body is None:
        url += "&include_extras=true"
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
        html = BaseElement()
        for c in cards:
            html.add(e.A(c["name"], href=c["scryfall_uri"]) + e.Br())
        await msg.reply_htmlbox(html)
    else:
        await msg.reply(f"**{len(cards)}** risultati! Usa un nome più specifico...")


@command_wrapper(
    aliases=("cardhangman", "gtc", "hangmancard"),
    helpstr="Indovina una carta di Magic: the Gathering!",
    allow_pm=False,
)
async def guessthecard(msg: Message) -> None:
    filters = (
        "legal:standard",
        "-type:basic",  # Basic lands
    )
    query = "+".join([urllib.parse.quote(param) for param in filters])
    url = "https://api.scryfall.com/cards/random?q=" + query

    card_ = await query_scryfall(url, "card")
    if card_ is None:  # Safety check. Error is propagated from query_scryfall().
        return

    # Strip PS parameter separators from cardname.
    cardname = re.sub(",|", "", card_["name"])

    # Hint generation logic: type line, mana cost, flavor text
    if "planeswalker" in card_["type_line"].lower():
        # Type lines of planeswalkers contain their name.
        hint = "Planeswalker"
    else:
        hint = card_["type_line"]
    if "mana_cost" in card_ and card_["mana_cost"]:
        hint += ", " + card_["mana_cost"]
    if "flavor_text" in card_ and card_["flavor_text"]:
        # Add flavor text if the hint won't exceed PS' limits.
        hint_with_flavor = hint + " ~ " + card_["flavor_text"]
        hint = hint_with_flavor if len(hint_with_flavor) <= 150 else hint
    hint = hint.replace("\n", " ")

    await msg.reply(f"/hangman create {cardname}, {hint}", False)


@command_wrapper(aliases=("randomcard",), allow_pm=False)
async def randcard(msg: Message) -> None:
    url = "https://api.scryfall.com/cards/random"
    if msg.arg:
        # Users can input an optional query to restrict the cardpool.
        url += "?q=" + urllib.parse.quote(msg.arg)

    card_ = await query_scryfall(url, "card")
    if card_ is None:
        await msg.reply("Ricerca non valida")
        return

    await msg.reply_htmlbox(to_card_thumbnail(card_))
