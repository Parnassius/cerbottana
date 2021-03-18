from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped
from typing_extensions import Protocol

import databases.veekun as v
import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


class TranslatableTableNames(Protocol):
    # pylint: disable=too-few-public-methods,unsubscriptable-object
    local_language_id: Mapped[int]
    name_normalized: Mapped[str | None]


@command_wrapper(
    aliases=("translation", "trad"), helpstr="Traduce abilità, mosse e strumenti."
)
async def translate(msg: Message) -> None:
    if len(msg.args) > 3:
        return

    parola = utils.to_user_id(utils.remove_diacritics(msg.args[0]))
    if parola == "":
        await msg.reply("Cosa devo tradurre?")
        return

    languages_list: list[int] = []
    for lang in msg.args[1:]:  # Get language ids from the command parameters
        languages_list.append(utils.get_language_id(lang))
    languages_list.append(msg.language_id)  # Add the room language
    languages_list.extend([9, 8])  # Hardcode english and italian as fallbacks

    # Get the first two unique languages
    languages = tuple(dict.fromkeys(languages_list))[:2]

    results: dict[tuple[str, str], set[str]] = {}

    db = Database.open("veekun")

    with db.get_session() as session:

        tables: dict[
            str, tuple[type[v.TranslatableMixin], type[TranslatableTableNames]]
        ] = {
            "ability": (v.Abilities, v.AbilityNames),
            "item": (v.Items, v.ItemNames),
            "move": (v.Moves, v.MoveNames),
            "nature": (v.Natures, v.NatureNames),
        }

        for category_name, t in tables.items():
            rs: list[tuple[v.TranslatableMixin, int]] = (
                session.query(t[0], t[1].local_language_id)
                .select_from(t[0])  # type: ignore  # sqlalchemy
                .join(t[1])
                .filter(
                    t[1].local_language_id.in_(languages),
                    t[1].name_normalized == parola,
                )
                .all()
            )
            for row, language_id in rs:
                translation = row.get_translation(
                    f"{category_name}_names",
                    language_id=list(set(languages) - {language_id})[0],
                    fallback_english=False,
                )

                if translation is not None:
                    res = (category_name, utils.to_id(translation))
                    if res not in results:
                        results[res] = set()
                    results[res].add(translation)

    if results:
        if len(results) == 1:
            await msg.reply(" / ".join(sorted(list(results.values())[0])))
            return
        resultstext = ""
        for key, val in results.items():
            if resultstext != "":
                resultstext += ", "
            resultstext += "{trad} ({cat})".format(
                trad=" / ".join(sorted(val)), cat=key[0]
            )
        await msg.reply(resultstext)
        return

    await msg.reply("Non trovato")
