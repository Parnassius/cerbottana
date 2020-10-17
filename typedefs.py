from typing_extensions import Literal, NewType, TypedDict

RoomId = NewType("RoomId", str)
UserId = NewType("UserId", str)
Role = Literal[
    "admin", "owner", "bot", "host", "mod", "driver", "player", "voice", "prizewinner"
]

TiersDict = TypedDict(
    "TiersDict",
    {
        "name": str,
        "section": str,
        "random": bool,
    },
)
