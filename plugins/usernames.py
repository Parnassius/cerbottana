from datetime import datetime
import pytz
import random

from plugin_loader import plugin_wrapper


@plugin_wrapper()
async def acher(self, room, user, arg):
    await self.send_reply(room, user, "lo acher che bontà ♫")


@plugin_wrapper(aliases=["aeth", "eterno"])
async def aethernum(self, room, user, arg):
    await self.send_reply(room, user, "__eterno__ indeciso :^)")


@plugin_wrapper(aliases=["alphawittem", "wittem"])
async def alpha(self, room, user, arg):
    await self.send_reply(room, user, "Italian luck jajaja")


@plugin_wrapper(aliases=["cinse", "cobse", "conse"])
async def consecutio(self, room, user, arg):
    text = "opss{} ho lasciato il pc acceso tutta notte".format(
        "s" * random.randint(0, 3)
    )
    await self.send_reply(room, user, text)


@plugin_wrapper()
async def duck(self, room, user, arg):
    await self.send_reply(room, user, "quack")


@plugin_wrapper(aliases=["ed"])
async def edgummet(self, room, user, arg):
    await self.send_reply(room, user, "soccontro")


@plugin_wrapper(aliases=["francy"])
async def francyy(self, room, user, arg):
    await self.send_reply(room, user, "aiuto ho riso irl")


@plugin_wrapper()
async def haund(self, room, user, arg):
    await self.send_reply(room, user, "( ͡° ͜ʖ ͡°)")


@plugin_wrapper()
async def howkings(self, room, user, arg):
    await self.send_reply(room, user, "Che si vinca o si perda, v0lca merda :3")


@plugin_wrapper(aliases=["infli"])
async def inflikted(self, room, user, arg):
    letters = {1: "I", 2: "N", 3: "F", 4: "L", 5: "I", 6: "K", 7: "T", 8: "E", 9: "D"}
    shuffled = sorted(letters, key=lambda x: random.random() * x / len(letters))
    text = ""
    for i in shuffled:
        text += letters[i]
    await self.send_reply(room, user, "ciao {}".format(text))


@plugin_wrapper()
async def lange(self, room, user, arg):
    await self.send_reply(room, user, "Haund mi traduci questo post?")


@plugin_wrapper()
async def mammalu(self, room, user, arg):
    await self.send_reply(room, user, "clicca la stab")


@plugin_wrapper(aliases=["gr"])
async def megagr(self, room, user, arg):
    await self.send_reply(room, user, "GRRRRRR")


@plugin_wrapper()
async def milak(self, room, user, arg):
    await self.send_reply(room, user, "No Maria io esco")


@plugin_wrapper()
async def mister(self, room, user, arg):
    await self.send_reply(room, user, "Master")


@plugin_wrapper()
async def mistercantiere(self, room, user, arg):
    await self.send_reply(room, user, "MasterCantiere")


@plugin_wrapper(aliases=["azyz"])
async def oizys(self, room, user, arg):
    await self.send_reply(room, user, "no")


@plugin_wrapper(aliases=["palt0", "palto", "plato"])
async def plat0(self, room, user, arg):
    text = "oh {} non mi spoilerare".format(
        random.choice(["basta", "senti", "smettila"])
    )
    tz = pytz.timezone("Europe/Rome")
    timestamp = datetime.now(tz)
    if 3 <= timestamp.hour <= 5:
        text += ", che mi sono appena svegliato"
    await self.send_reply(room, user, text)


@plugin_wrapper(aliases=["rospe"])
async def r0spe(self, room, user, arg):
    await self.send_reply(room, user, "buondì")


@plugin_wrapper(aliases=["boiler"])
async def roiler(self, room, user, arg):
    await self.send_reply(room, user, "ehm volevo dire")


@plugin_wrapper(aliases=["silver"])
async def silver97(self, room, user, arg):
    tier = random.choice(self.tiers)["name"]
    await self.send_reply(room, user, "qualcuno mi passa un team {}".format(tier))


@plugin_wrapper()
async def smilzo(self, room, user, arg):
    await self.send_reply(room, user, "mai na gioia")


@plugin_wrapper(aliases=["spec"])
async def specn(self, room, user, arg):
    await self.send_reply(room, user, "Vi muto tutti")


@plugin_wrapper(aliases=["cul1", "culone", "kul1", "swcul1", "swkul1"])
async def swculone(self, room, user, arg):
    await self.send_reply(room, user, "hue")


@plugin_wrapper(aliases=["quas"])
async def thequasar(self, room, user, arg):
    await self.send_reply(room, user, "Basta con le pupazzate")


@plugin_wrapper(aliases=["3v", "vvv"])
async def trev(self, room, user, arg):
    await self.send_reply(room, user, "gioco di merda")


@plugin_wrapper()
async def ultrasuca(self, room, user, arg):
    await self.send_reply(room, user, "@Ultrasuca left")


@plugin_wrapper(aliases=["useless", "usy"])
async def uselesstrainer(self, room, user, arg):
    await self.send_reply(room, user, "kek")


@plugin_wrapper(aliases=["volca"])
async def v0lca(self, room, user, arg):
    await self.send_reply(room, user, "Porco mele...")
