from typing import Any, Literal, NewType, TypedDict

RoomId = NewType("RoomId", str)
UserId = NewType("UserId", str)
Role = Literal[
    "disabled",
    "admin",
    "sectionleader",
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

JsonDict = dict[str, Any]  # type: ignore[misc]


class TiersDict(TypedDict):
    id: str
    name: str
    section: str
    random: bool
