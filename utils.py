from __future__ import annotations

import json
import random
import re
import string
import unicodedata
from html import escape
from typing import Any

import htmlmin  # type: ignore[import]
from imageprobe import probe
from jinja2 import Environment, FileSystemLoader, select_autoescape

from typedefs import JsonDict, Role, RoomId, UserId


def to_id(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def to_user_id(user: str) -> UserId:
    userid = UserId(to_id(user))
    return userid


def to_room_id(room: str, fallback: RoomId = RoomId("lobby")) -> RoomId:
    roomid = RoomId(re.sub(r"[^a-z0-9-]", "", room.lower()))
    if not roomid:
        roomid = fallback
    return roomid


def remove_diacritics(text: str) -> str:
    return "".join(
        [c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)]
    )


def has_role(role: Role, user: str, strict_voice_check: bool = False) -> bool:
    """Checks if a user has a PS role or higher.

    Args:
        role (Role): PS role (i.e. "voice", "driver").
        user (str): User to check.
        strict_voice_check (bool): True if custom rank symbols should not be
            considered voice. Defaults to False.

    Returns:
        bool: True if user meets the required criteria.
    """
    roles: dict[Role, str] = {
        "admin": "~&",
        "sectionleader": "~&§",
        "owner": "~&#",
        "bot": "*",
        "host": "★",
        "mod": "~&§#@",
        "driver": "~&§#@%",
        "player": "☆",
        "voice": "~&§#@%+",
        "prizewinner": "^",
    }
    if user:
        if role == "disabled":
            return False
        if role == "regularuser":
            return True
        if user[0] in roles[role]:
            return True
        if (
            role == "voice"
            and not strict_voice_check
            and user[0] not in "*★☆^ "
            and user[0] not in string.ascii_letters + string.digits
        ):
            return True
    return False


def html_escape(text: str | None) -> str:
    if text is None:
        return ""
    return escape(text).replace("\n", "<br>")


async def image_url_to_html(url: str) -> str:
    """Generates an <img> tag from an image url."""
    image = await probe(url)
    return f'<img src="{url}" width="{image.width}" height="{image.height}">'


def is_youtube_link(url: str) -> bool:
    """Returns True if url is a youtube link, based on PS' regex."""
    # Note: You should let PS display youtube links natively with "!show {url}".
    youtube_regex = r"^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)(\/|$)"
    return re.match(youtube_regex, url, re.IGNORECASE) is not None


def linkify(text: str) -> str:
    """Transforms a text containing URLs into HTML code.

    Args:
        text (str): Raw text.

    Returns:
        str: Escaped HTML, possibly containing <a> tags.
    """
    # Partially translated from https://github.com/smogon/pokemon-showdown, chat parser.
    # The original code is released under the MIT License.

    # linkify requires a custom translation table because "/" is left unescaped.
    table = {ord(char): escape(char) for char in "&<>\"'"}
    table[ord("\n")] = "<br>"
    text = text.translate(table)

    # pylint: disable=line-too-long
    url_regex = r'(?i)(?:(?:https?:\/\/[a-z0-9-]+(?:\.[a-z0-9-]+)*|www\.[a-z0-9-]+(?:\.[a-z0-9-]+)+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com?|org|net|edu|info|us|jp|[a-z]{2,3}(?=[:/])))(?::[0-9]+)?(?:\/(?:(?:[^\s()&<>]|&amp;|&quot;|\((?:[^\\s()<>&]|&amp;)*\))*(?:[^\s()[\]{}".,!?;:&<>*`^~\\]|\((?:[^\s()<>&]|&amp;)*\)))?)?|[a-z0-9.]+@[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,})(?![^ ]*&gt;)'
    return re.sub(url_regex, lambda m: _linkify_uri(m.group()), text)


def _linkify_uri(uri: str) -> str:
    # Partially translated from https://github.com/smogon/pokemon-showdown, chat parser.
    # The original code is released under the MIT License.

    if re.match(r"^[a-z0-9.]+@", uri, re.IGNORECASE):
        fulluri = f"mailto:{uri}"
    else:
        fulluri = re.sub(r"^([a-z]*[^a-z:])", r"http://\1", uri)
        if uri.startswith(("https://docs.google.com/", "docs.google.com/")):
            if uri.startswith("https"):
                uri = uri[8:]
            if uri.endswith(("?usp=sharing", "&usp=sharing")):
                uri = uri[:-12]
            if uri.endswith("#gid=0"):
                uri = uri[:-6]

            slash_index = uri.rindex("/")
            if len(uri) - slash_index > 18:
                slash_index = len(uri)
            if slash_index - 4 > 22:
                uri = (
                    uri[:19]
                    + '<small class="message-overflow">'
                    + uri[19 : slash_index - 4]
                    + "</small>"
                    + uri[slash_index - 4 :]
                )
    return f'<a href="{fulluri}">{uri}</a>'


def render_template(  # type: ignore[misc]  # allow any
    template_name: str, **template_vars: Any
) -> str:
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    html = template.render(**template_vars)
    return htmlmin.minify(html, convert_charrefs=False)  # type: ignore[no-any-return]


def to_obfuscated_html(text: str | None) -> str:
    """Converts a string to HTML code and adds invisible obfuscation text."""
    if text is None:
        return ""

    obfuscated = ""
    for ch in text:
        obfuscated += html_escape(ch)
        randstr = ""
        for _ in range(random.randrange(3, 10)):
            randstr += random.choice(string.ascii_letters + string.digits)
        obfuscated += f'<span style="position: absolute; top: -999vh">{randstr}</span>'
    return obfuscated


def get_language_id(language_name: str, *, fallback: int = 9) -> int:
    language_name = to_user_id(language_name)
    table = {
        # "japanese": 1,
        # "traditionalchinese": 4,
        "fr": 5,
        "french": 5,
        "de": 6,
        "german": 6,
        "es": 7,
        "spanish": 7,
        "it": 8,
        "italian": 8,
        "en": 9,
        "english": 9,
        # "simplifiedchinese": 12,
    }
    if language_name in table:
        return table[language_name]
    return fallback


def get_alias(text: str) -> str:
    return ALIASES.get(_escape(text), text)


def get_ps_dex_entry(query: str, *, _female: bool = False) -> JsonDict | None:
    """Retrieves a pokemon entry from the PS pokedex.

    Args:
        query (str): Pokemon name (or forme variant).

    Returns:
        JsonDict | None: Dict with pokemon information or None if no pokemon was
            recognized.
    """
    query = _escape(query)
    species = _escape(get_alias(query))

    if species in POKEDEX:
        entry = POKEDEX[species]

        base_id: str
        forme_id: str | None = None

        if "baseSpecies" in entry:  # Alternate form, e.g. mega, gmax
            base_id = to_id(entry["baseSpecies"])
            forme_id = to_id(entry["forme"])
        else:  # Base form
            base_id = to_id(entry["name"])

        if "cosmeticFormes" in entry:  # Cosmetic form, e.g. unown, alcremie
            forme_id = next(
                (
                    to_id(i[len(base_id) + 1 :])
                    for i in entry["cosmeticFormes"]
                    if to_id(i) == query
                ),
                None,
            )

        dex_name = base_id
        if forme_id:
            dex_name += f"-{forme_id}"
        if _female:
            dex_name += "-f"
        entry["dex_name"] = dex_name

        return entry

    if not _female and query[-1] == "f":
        return get_ps_dex_entry(query[:-1], _female=True)

    return None


def _escape(text: str) -> str:
    text = remove_diacritics(text)
    text = to_id(text)
    return text


with open("./data/avatars.json", encoding="utf-8") as f:
    AVATAR_IDS: dict[str, str] = json.load(f)
with open("./data/showdown/aliases.json", encoding="utf-8") as f:
    ALIASES: dict[str, str] = json.load(f)
with open("./data/showdown/pokedex.json", encoding="utf-8") as f:
    POKEDEX: dict[str, JsonDict] = json.load(f)
