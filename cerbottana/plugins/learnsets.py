from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import selectinload

import cerbottana.databases.veekun as v
from cerbottana import utils
from cerbottana.database import Database

from . import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


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

        stmt = select(v.VersionGroups).filter_by(identifier=version_id)
        # TODO: remove annotation
        version_group: v.VersionGroups | None = session.scalar(stmt)

        if version_group is None:
            stmt = select(v.Versions).filter_by(identifier=version_id)
            # TODO: remove annotation
            version: v.Versions | None = session.scalar(stmt)
            if version is None:
                await msg.reply("Game version not found.")
                return
            version_group = version.version_group

        stmt = (
            select(v.PokemonSpecies)
            .options(
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
        )
        # TODO: remove annotation
        pokemon_species: v.PokemonSpecies | None = session.scalar(stmt)
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

        for method_data in results.values():
            for move_data in method_data["moves"].values():
                if move_data["forms"] == all_forms:
                    move_data["forms"] = set()
                else:
                    method_data["form_column"] = True

        html = utils.render_template("commands/learnsets.html", results=results)

        if not html:
            await msg.reply("No data available.")
            return

        await msg.reply_htmlbox('<div class="ladder">' + html + "</div>")