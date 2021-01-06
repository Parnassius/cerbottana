from typing import Any, Dict

from typing_extensions import Literal, NewType, TypedDict

RoomId = NewType("RoomId", str)
UserId = NewType("UserId", str)
Role = Literal[
    "admin", "owner", "bot", "host", "mod", "driver", "player", "voice", "prizewinner"
]

JsonDict = Dict[str, Any]  # type: ignore[misc]


class TiersDict(TypedDict):
    name: str
    section: str
    random: bool
