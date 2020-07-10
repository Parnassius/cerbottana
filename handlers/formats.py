from __future__ import annotations

from typing import Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection

from . import handler_wrapper


@handler_wrapper(["formats"])
async def formats(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 1:
        return

    formatslist = args

    tiers: List[Dict[str, str]] = []
    section: Optional[str] = None
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
            tiers.append({"name": parts[0], "section": section})
    conn.tiers = tiers
