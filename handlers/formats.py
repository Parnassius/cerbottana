from typing import Optional, List, Dict

from handler_loader import handler_wrapper


@handler_wrapper(["formats"])
async def formats(self, roomid: str, *formatslist: str) -> None:
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
    self.tiers = tiers
