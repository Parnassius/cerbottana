from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import joinedload

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

    pokemon = utils.to_user_id(utils.remove_accents(args[0].lower()))
    version_group = utils.to_user_id(utils.remove_accents(args[1].lower()))

    db = Database.open("veekun")

    with db.get_session() as session:
        version_group_id = (
            session.query(v.VersionGroups.id)
            .filter_by(identifier=version_group)
            .scalar()
        )

        if version_group_id is None:
            version_group_id = (
                session.query(v.Versions.version_group_id)
                .filter_by(identifier=version_group)
                .scalar()
            )
            if version_group_id is None:
                return

        results = dict()

        pokemon_species = (
            session.query(v.PokemonSpecies)
            .options(
                joinedload(v.PokemonSpecies.pokemon)
                .joinedload(v.Pokemon.pokemon_moves)
                .joinedload(v.PokemonMoves.version_group)
                .raiseload("*")
            )
            .filter_by(identifier=pokemon)
            .first()
        )

        for pokemon in pokemon_species.pokemon:

            for pokemon_move in pokemon.pokemon_moves:

                version_group = pokemon_move.version_group

                if version_group.id != version_group_id:
                    continue

                move = pokemon_move.move
                move_name = next(
                    (i.name for i in move.move_names if i.local_language_id == 9), None
                )

                method = pokemon_move.pokemon_move_method
                method_name = next(
                    (
                        i.name
                        for i in method.pokemon_move_method_prose
                        if i.local_language_id == 9
                    ),
                    None,
                )

                data = {
                    "name": move_name,
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

        html = ""

        for method_id in sorted(results.keys()):
            html += (
                "<details><summary><b><big>"
                + utils.html_escape(results[method_id]["name"])
                + "</big></b></summary>"
            )
            html += '<table style="margin: 5px 0"><tbody>'
            html += "<tr>"
            html += "  <th>Move</th>"
            if method_id == 1:  # level-up
                html += "  <th>Level</th>"
            elif method_id == 4:  # machine
                html += "  <th>Machine</th>"
            html += "</tr>"

            if method_id == 1:  # level-up
                results[method_id]["moves"].sort(key=lambda x: (x["level"], x["name"]))
            elif method_id == 4:  # machine
                results[method_id]["moves"].sort(
                    key=lambda x: (x["machine"], x["name"])
                )
            else:
                results[method_id]["moves"].sort(key=lambda x: x["name"])

            for move in results[method_id]["moves"]:
                html += "<tr>"
                html += "  <td>" + utils.html_escape(move["name"]) + "</td>"
                if method_id == 1:  # level-up
                    html += (
                        '  <td style="text-align: right">'
                        + utils.html_escape(str(move["level"]))
                        + "</td>"
                    )
                elif method_id == 4:  # machine
                    html += "  <td>" + utils.html_escape(move["machine"]) + "</td>"
                html += "</tr>"

            html += "</tbody></table>"
            html += "</details>"

        if not html:
            await conn.send_reply(room, user, "Nessun dato")
            return

        await conn.send_htmlbox(room, user, '<div class="ladder">' + html + "</div>")
