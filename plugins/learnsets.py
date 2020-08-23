from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy.orm import joinedload
from typing_extensions import TypedDict

import databases.veekun as v
import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper()
async def learnset(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    args = arg.split(",")
    if len(args) < 2:
        return

    pokemon_id = utils.to_user_id(utils.remove_accents(args[0].lower()))
    version = utils.to_user_id(utils.remove_accents(args[1].lower()))

    db = Database.open("veekun")

    with db.get_session() as session:
        version_group_id: Optional[int] = (
            session.query(v.VersionGroups.id)  # type: ignore  # sqlalchemy
            .filter_by(identifier=version)
            .scalar()
        )

        if version_group_id is None:
            version_group_id = (
                session.query(v.Versions.version_group_id)  # type: ignore  # sqlalchemy
                .filter_by(identifier=version)
                .scalar()
            )
            if version_group_id is None:
                return

        class MovesDict(TypedDict):
            name: str
            level: Optional[int]
            machine: Optional[str]

        class ResultsDict(TypedDict):
            name: str
            moves: List[MovesDict]

        results: Dict[int, ResultsDict] = dict()

        pokemon_species = (
            session.query(v.PokemonSpecies)  # type: ignore  # sqlalchemy
            .options(
                joinedload(v.PokemonSpecies.pokemon)
                .joinedload(v.Pokemon.pokemon_moves)
                .joinedload(v.PokemonMoves.version_group)
                .raiseload("*")
            )
            .filter_by(identifier=pokemon_id)
            .first()
        )

        if pokemon_species:

            for pokemon in pokemon_species.pokemon:

                for pokemon_move in pokemon.pokemon_moves:

                    version_group = pokemon_move.version_group

                    if version_group.id != version_group_id:
                        continue

                    move = pokemon_move.move
                    move_name = next(
                        (i.name for i in move.move_names if i.local_language_id == 9),
                        "",
                    )

                    method = pokemon_move.pokemon_move_method
                    method_name = next(
                        (
                            i.name
                            for i in method.pokemon_move_method_prose
                            if i.local_language_id == 9
                        ),
                        "",
                    )

                    data: MovesDict = {
                        "name": move_name,
                        "level": None,
                        "machine": None,
                    }

                    if method.id == 1:  # level-up
                        data["level"] = pokemon_move.level
                    elif method.id == 4:  # machine
                        machine = next(
                            (
                                i
                                for i in move.machines
                                if i.version_group_id == version_group.id
                            ),
                            None,
                        )
                        if machine:
                            machine_name = next(
                                (
                                    i.name
                                    for i in machine.item.item_names
                                    if i.local_language_id == 9
                                ),
                                None,
                            )
                            data["machine"] = machine_name

                    if method.id not in results:
                        results[method.id] = {"name": method_name, "moves": list()}

                    results[method.id]["moves"].append(data)

        for method_id in sorted(results.keys()):
            if method_id == 1:  # level-up
                results[method_id]["moves"].sort(key=lambda x: (x["level"], x["name"]))
            elif method_id == 4:  # machine
                results[method_id]["moves"].sort(
                    key=lambda x: (x["machine"], x["name"])
                )
            else:
                results[method_id]["moves"].sort(key=lambda x: x["name"])

        html = utils.render_template(
            "commands/learnsets.html", methods=sorted(results.keys()), results=results
        )

        if not html:
            await conn.send_reply(room, user, "Nessun dato")
            return

        await conn.send_htmlbox(room, user, '<div class="ladder">' + html + "</div>")
