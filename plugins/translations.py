from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, List

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(helpstr="Traduce abilità, mosse e strumenti.")
async def trad(msg: Message) -> None:
    parola = utils.to_user_id(utils.remove_accents(msg.arg.lower()))
    if parola == "":
        await msg.reply("Cosa devo tradurre?")
        return

    results: List[Dict[str, str]] = []

    for i in TRANSLATIONS:
        for j in TRANSLATIONS[i]:
            if utils.to_user_id(utils.remove_accents(j["en"].lower())) == parola:
                results.append({"trad": j["it"], "cat": i})
            elif utils.to_user_id(utils.remove_accents(j["it"].lower())) == parola:
                results.append({"trad": j["en"], "cat": i})

    if results:
        if len(results) == 1:
            await msg.reply(results[0]["trad"])
            return
        resultstext = ""
        for k in results:
            if resultstext != "":
                resultstext += ", "
            resultstext += "{trad} ({cat})".format(trad=k["trad"], cat=k["cat"])
        await msg.reply(resultstext)
        return

    await msg.reply("Non trovato")


with open("./data/translations.json", "r") as f:
    TRANSLATIONS: Dict[str, List[Dict[str, str]]] = json.load(f)
