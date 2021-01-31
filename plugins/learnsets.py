from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from sqlalchemy.orm import selectinload

import databases.veekun as v
import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper()
async def learnset(msg: Message) -> None:
    if len(msg.args) < 2:
        return

    pokemon_id = utils.to_id(utils.remove_diacritics(msg.args[0].lower()))
    version_id = utils.to_id(utils.remove_diacritics(msg.args[1].lower()))

    language_id = msg.language_id
    if len(msg.args) >= 3:
        language_id = utils.get_language_id(msg.args[2], fallback=language_id)

    db = Database.open("veekun")

    with db.get_session(language_id) as session:

        class MovesDict(TypedDict):
            level: int
            order: int
            machine: v.Machines | None
            forms: set[v.Pokemon]

        class ResultsDict(TypedDict):
            moves: dict[v.Moves, MovesDict]
            form_column: bool

        version_group = (
            session.query(v.VersionGroups)
            .filter_by(identifier=version_id)
            .one_or_none()
        )

        if version_group is None:
            version = (
                session.query(v.Versions)
                .filter(v.Versions.identifier == version_id)
                .one_or_none()
            )
            if version is None:
                await msg.reply("Game version not found.")
                return
            version_group = version.version_group

        pokemon_species: v.PokemonSpecies | None = (
            session.query(v.PokemonSpecies)
            .options(  # type: ignore  # sqlalchemy
                selectinload(v.PokemonSpecies.pokemon)
                .selectinload(
                    v.Pokemon.pokemon_moves.and_(
                        v.PokemonMoves.version_group_id == version_group.id
                    )
                )
                .options(
                    selectinload(v.PokemonMoves.move).options(
                        selectinload(v.Moves.move_names),
                        selectinload(
                            v.Moves.machines.and_(
                                v.Machines.version_group_id == version_group.id
                            )
                        )
                        .selectinload(v.Machines.item)
                        .selectinload(v.Items.item_names),
                    ),
                    selectinload(v.PokemonMoves.pokemon_move_method).selectinload(
                        v.PokemonMoveMethods.pokemon_move_method_prose
                    ),
                )
            )
            .filter_by(identifier=pokemon_id)
            .one_or_none()
        )
        if pokemon_species is None:
            await msg.reply("Pokémon not found.")
            return

        results: dict[v.PokemonMoveMethods, ResultsDict] = {}

        all_forms = set(pokemon_species.pokemon)

        for pokemon in pokemon_species.pokemon:
            for pokemon_move in pokemon.pokemon_moves:

                method = pokemon_move.pokemon_move_method
                if method not in results:
                    results[method] = {
                        "moves": {},
                        "form_column": False,
                    }

                move = pokemon_move.move
                if move not in results[method]["moves"]:
                    results[method]["moves"][move] = {
                        "level": int(pokemon_move.level or 0),
                        "order": int(pokemon_move.order or 0),
                        "machine": move.machines[0] if move.machines else None,
                        "forms": set(),
                    }
                results[method]["moves"][move]["forms"].add(pokemon)

        for method in results:
            for move in results[method]["moves"]:
                if results[method]["moves"][move]["forms"] == all_forms:
                    results[method]["moves"][move]["forms"] = set()
                else:
                    results[method]["form_column"] = True

        html = utils.render_template("commands/learnsets.html", results=results)

        if not html:
            await msg.reply("No data available.")
            return

        await msg.reply_htmlbox('<div class="ladder">' + html + "</div>")
