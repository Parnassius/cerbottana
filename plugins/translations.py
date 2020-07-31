from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, List, Optional

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(helpstr="Traduce abilità, mosse e strumenti.")
async def trad(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    parola = utils.to_user_id(utils.remove_accents(arg.lower()))
    if parola == "":
        await conn.send_reply(room, user, "Cosa devo tradurre?")
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
            await conn.send_reply(room, user, results[0]["trad"])
            return
        resultstext = ""
        for k in results:
            if resultstext != "":
                resultstext += ", "
            resultstext += "{trad} ({cat})".format(trad=k["trad"], cat=k["cat"])
        await conn.send_reply(room, user, resultstext)
        return

    await conn.send_reply(room, user, "Non trovato")


with open("./data/translations.json", "r") as f:
    TRANSLATIONS: Dict[str, List[Dict[str, str]]] = json.load(f)
