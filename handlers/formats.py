from handler_loader import handler_wrapper


@handler_wrapper(["formats"])
async def formats(self, roomid, *formatslist):
    tiers = []
    section = None
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
        tiers.append({"name": parts[0], "section": section})
    self.tiers = tiers
