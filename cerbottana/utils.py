from __future__ import annotations

import json
import re
import string
import unicodedata
from html import escape
from pathlib import Path

from .typedefs import JsonDict, Role, RoomId, UserId


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


def is_youtube_link(url: str) -> bool:
    """Returns True if url is a youtube link, based on PS' regex."""
    # Note: You should let PS display youtube links natively with "!show {url}".
    youtube_regex = r"^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)(\/|$)"
    return re.match(youtube_regex, url, re.IGNORECASE) is not None


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

        entry["id"] = species

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
        entry["female"] = _female

        return entry

    if not _female and query[-1] == "f":
        return get_ps_dex_entry(query[:-1], _female=True)

    return None


def _escape(text: str) -> str:
    text = remove_diacritics(text)
    text = to_id(text)
    return text


def get_config_file(path: str) -> Path:
    return Path(__file__).parent.parent / path


def get_data_file(path: str) -> Path:
    return Path(__file__).parent / "data" / path


with get_data_file("avatars.json").open(encoding="utf-8") as f:
    AVATAR_IDS: dict[str, str] = json.load(f)
with get_data_file("showdown/aliases.json").open(encoding="utf-8") as f:
    ALIASES: dict[str, str] = json.load(f)
with get_data_file("showdown/pokedex.json").open(encoding="utf-8") as f:
    POKEDEX: dict[str, JsonDict] = json.load(f)
with get_data_file("showdown/pokedex-mini-bw.json").open(encoding="utf-8") as f:
    POKEDEX_MINI_BW: JsonDict = json.load(f)
with get_data_file("showdown/pokedex-mini.json").open(encoding="utf-8") as f:
    POKEDEX_MINI: JsonDict = json.load(f)
