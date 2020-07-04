from time import time

from plugin_loader import plugin_wrapper


@plugin_wrapper()
async def uptime(self, room: str, user: str, arg: str) -> None:
    s = int(time() - self.connection_start)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    days = "{} day{}, ".format(d, "" if d == 1 else "s") if d > 0 else ""
    hours = "{} hour{}, ".format(h, "" if h == 1 else "s") if h > 0 else ""
    minutes = "{} minute{}, ".format(m, "" if m == 1 else "s") if m > 0 else ""
    seconds = "{} second{}".format(s, "" if s == 1 else "s")

    await self.send_reply(room, user, days + hours + minutes + seconds)
