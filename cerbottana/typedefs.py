from dataclasses import dataclass
from typing import Any, Literal, NewType

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


@dataclass
class Tier:
    id: str
    name: str
    section: str
    random: bool
    tournament: bool
