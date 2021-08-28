from __future__ import annotations

from typing import TYPE_CHECKING

import utils
from handlers import handler_wrapper

if TYPE_CHECKING:
    from connection import Connection
    from models.protocol_message import ProtocolMessage
    from models.room import Room
    from typedefs import TiersDict


@handler_wrapper(["formats"], required_parameters=1)
async def formats(msg: ProtocolMessage) -> None:
    formatslist = msg.params

    tiers: dict[str, TiersDict] = {}
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
            tier_id = utils.to_id(parts[0])
            tiers[tier_id] = {
                "id": tier_id,
                "name": parts[0],
                "section": section,
                "random": bool(int(parts[1], 16) & 1),
            }
    msg.conn.tiers = tiers
