from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pokedex import pokedex
from pokedex import tables as t
from pokedex.enums import Language
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from cerbottana import utils
from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


async def _get_translations(
    word: str, languages: tuple[Language, Language]
) -> dict[tuple[str, str], set[str]]:
    results: dict[tuple[str, str], set[str]] = {}

    async with pokedex.async_session() as session:
        tables: dict[str, tuple[Any, Any]] = {  # type: ignore[misc]
            "ability": (t.Ability, t.AbilityName),
            "item": (t.Item, t.ItemName),
            "move": (t.Move, t.MoveName),
            "nature": (t.Nature, t.NatureName),
        }

        for category_name, (entity_table, entity_name_table) in tables.items():
            stmt = (
                select(entity_table, entity_name_table.language_identifier)
                .select_from(entity_table)
                .join(entity_table.names)
                .where(
                    entity_name_table.language_identifier.in_(languages),
                    entity_name_table.normalized_name == word,
                )
                .group_by(entity_table, entity_name_table.language_identifier)
                .options(selectinload(entity_table.names))
            )
            async for row, language in await session.stream(stmt):
                other_language = next(iter(set(languages) - {language}))
                translation = row.names.get(language=other_language).name

                if translation is not None:
                    res = (
                        category_name,
                        utils.to_id(utils.remove_diacritics(translation)),
                    )
                    if res not in results:
                        results[res] = set()
                    results[res].add(translation)

    if not results and Language.ENGLISH in languages:
        # Use aliases if english is one of the languages
        new_word = utils.to_id(utils.remove_diacritics(utils.get_alias(word)))
        if new_word != word:
            return await _get_translations(new_word, languages)

    return results


@command_wrapper(
    aliases=("translation", "trad"), helpstr="Traduce abilità, mosse e strumenti."
)
async def translate(msg: Message) -> None:
    if len(msg.args) > 3:
        return

    word = utils.to_id(utils.remove_diacritics(msg.args[0]))
    if word == "":
        await msg.reply("Cosa devo tradurre?")
        return

    languages_list: list[Language] = []
    for lang_name in msg.args[1:]:  # Get language ids from the command parameters
        lang = Language.get(lang_name)
        if lang:
            languages_list.append(lang)
    languages_list.append(msg.language)  # Add the room language
    languages_list.extend(  # Hardcode english and italian as fallbacks
        [Language.ENGLISH, Language.ITALIAN]
    )

    # Get the first two unique languages
    languages = tuple(dict.fromkeys(languages_list))[:2]
    languages = cast(tuple[Language, Language], languages)

    results = await _get_translations(word, languages)

    if results:
        if len(results) == 1:
            await msg.reply(" / ".join(sorted(next(iter(results.values())))))
            return
        resultstext = ""
        for key, val in results.items():
            if resultstext != "":
                resultstext += ", "
            resultstext += f"{' / '.join(sorted(val))} ({key[0]})"
        await msg.reply(resultstext)
        return

    await msg.reply("Non trovato")
