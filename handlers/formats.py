from __future__ import annotations

import re
from typing import TYPE_CHECKING

from handlers import handler_wrapper

if TYPE_CHECKING:
    from connection import Connection
    from models.room import Room
    from typedefs import TiersDict


@handler_wrapper(["formats"])
async def formats(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    formatslist = args

    tiers: list[TiersDict] = []
    section: str | None = None
    section_next = False
    for tier in formatslist:
        if tier[0] == ",":
            section_next = True
            continue
        if section_next:
            section = tier
            section_next = False
            continue
        parts = tier.split(",")
        if section is not None:
            tiers.append(
                {
                    "id": re.sub(r"[^a-z0-9]", "", parts[0].lower()),
                    "name": parts[0],
                    "section": section,
                    "random": bool(int(parts[1], 16) & 1),
                }
            )
    conn.tiers = tiers
