from __future__ import annotations

from typing import TYPE_CHECKING

from cerbottana import utils
from cerbottana.handlers import handler_wrapper
from cerbottana.typedefs import Tier

if TYPE_CHECKING:
    from cerbottana.models.protocol_message import ProtocolMessage


@handler_wrapper(["formats"], required_parameters=1)
async def formats(msg: ProtocolMessage) -> None:
    formatslist = msg.params

    tiers: dict[str, Tier] = {}
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
            code = int(parts[1], 16)
            tiers[tier_id] = Tier(
                tier_id,
                parts[0],  # name
                section,
                bool(code & 1),  # random
                # bool(code & 2),  # ladder
                # bool(code & 4),  # challenge
                bool(code & 8),  # tournament
                # bool(code & 16),  # teambuilder_level
            )
    msg.conn.tiers = tiers
