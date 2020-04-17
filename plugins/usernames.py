import random

import utils


async def acher(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "lo acher che bontà ♫")


async def aethernum(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "da decidere")


async def alpha(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "Italian luck jajaja")


async def consecutio(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    text = "opss{} ho lasciato il pc acceso tutta notte".format(
        "s" * random.randint(0, 3)
    )
    await self.send_reply(room, user, text)


async def duck(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "quack")


async def edgummet(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "soccontro")


async def francyy(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "aiuto ho riso irl")


async def haund(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "( ͡° ͜ʖ ͡°)")


async def howkings(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "Che si vinca o si perda, v0lca merda :3")


async def inflikted(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    letters = {1: "I", 2: "N", 3: "F", 4: "L", 5: "I", 6: "K", 7: "T", 8: "E", 9: "D"}
    shuffled = sorted(letters, key=lambda x: random.random() * x / len(letters))
    text = ""
    for i in shuffled:
        text += letters[i]
    await self.send_reply(room, user, "ciao {}".format(text))


async def lange(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "Haund mi traduci questo post?")


async def mammalu(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "clicca la stab")


async def megagr(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "GRRRRRR")


async def milak(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "No Maria io esco")


async def mister(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "Master")


async def mistercantiere(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "MasterCantiere")


async def oizys(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "no")


async def r0spe(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "buondì")


async def silver97(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    tier = random.choice(self.tiers)["name"]
    await self.send_reply(room, user, "qualcuno mi passa un team {}".format(tier))


async def smilzo(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "mai na gioia")


async def specn(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "Vi muto tutti")


async def swculone(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "hue")


async def thequasar(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "Basta con le pupazzate")


async def trev(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "gioco di merda")


async def ultrasuca(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "%Ultrasuca left")


async def uselesstrainer(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "kek")


async def v0lca(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return
    await self.send_reply(room, user, "Porco mele...")


commands = {
    "acher": acher,
    "aeth": aethernum,
    "aethernum": aethernum,
    "eterno": aethernum,
    "alpha": alpha,
    "alphawittem": alpha,
    "wittem": alpha,
    "cinse": consecutio,
    "cobse": consecutio,
    "conse": consecutio,
    "consecutio": consecutio,
    "duck": duck,
    "ed": edgummet,
    "edgummet": edgummet,
    "francy": francyy,
    "francyy": francyy,
    "haund": haund,
    "howkings": howkings,
    "infli": inflikted,
    "inflikted": inflikted,
    "lange": lange,
    "mammalu": mammalu,
    "megagr": megagr,
    "gr": megagr,
    "milak": milak,
    "mister": mister,
    "mistercantiere": mistercantiere,
    "azyz": oizys,
    "oizys": oizys,
    "r0spe": r0spe,
    "rospe": r0spe,
    "silver": silver97,
    "silver97": silver97,
    "smilzo": smilzo,
    "spec": specn,
    "specn": specn,
    "cul1": swculone,
    "culone": swculone,
    "kul1": swculone,
    "swcul1": swculone,
    "swculone": swculone,
    "swkul1": swculone,
    "quas": thequasar,
    "quasar": thequasar,
    "thequasar": thequasar,
    "3v": trev,
    "trev": trev,
    "vvv": trev,
    "ultrasuca": ultrasuca,
    "uselesstrainer": uselesstrainer,
    "usy": uselesstrainer,
    "v0lca": v0lca,
    "volca": v0lca,
}
