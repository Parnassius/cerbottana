from typing import Any, Dict, Literal, NewType, TypedDict

RoomId = NewType("RoomId", str)
UserId = NewType("UserId", str)
Role = Literal[
    "disabled",
    "admin",
    "owner",
    "bot",
    "host",
    "mod",
    "driver",
    "player",
    "voice",
    "prizewinner",
    "regularuser",
]

JsonDict = Dict[str, Any]  # type: ignore[misc]


class TiersDict(TypedDict):
    id: str
    name: str
    section: str
    random: bool
