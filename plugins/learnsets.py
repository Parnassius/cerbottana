from __future__ import annotations

from typing import TYPE_CHECKING, Optional

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

    db = Database("veekun")

    sql = "SELECT id FROM version_groups WHERE identifier = ?"
    version_group_id = db.execute(sql, [version_group]).fetchone()
    if version_group_id is None:
        sql = "SELECT version_group_id FROM versions WHERE identifier = ?"
        version_group_id = db.execute(sql, [version_group]).fetchone()
        if version_group_id is None:
            return
    version_group_id = version_group_id[0]
    sql = """SELECT pokemon_moves.version_group_id, pokemon_moves.pokemon_move_method_id,
           (SELECT GROUP_CONCAT(IFNULL(version_names.name, ''), '/')
            FROM versions
            LEFT JOIN version_names ON version_names.version_id = versions.id AND version_names.local_language_id = 9
            WHERE versions.version_group_id = pokemon_moves.version_group_id
            ORDER BY versions.id) AS version_group,
           IFNULL(move_names.name, '') AS move_name,
           IFNULL(pokemon_move_method_prose.name, '') AS method_name,
           IFNULL(pokemon_moves.level, 0) AS level, IFNULL(item_names.name, '') AS machine
           FROM pokemon_species
           LEFT JOIN pokemon ON pokemon.species_id = pokemon_species.id
           LEFT JOIN pokemon_moves ON pokemon_moves.pokemon_id = pokemon.id
           JOIN version_groups ON version_groups.id = pokemon_moves.version_group_id
           JOIN moves ON moves.id = pokemon_moves.move_id
           LEFT JOIN move_names ON move_names.move_id = moves.id AND move_names.local_language_id = 9
           JOIN pokemon_move_methods ON pokemon_move_methods.id = pokemon_moves.pokemon_move_method_id
           LEFT JOIN pokemon_move_method_prose ON pokemon_move_method_prose.pokemon_move_method_id = pokemon_move_methods.id AND pokemon_move_method_prose.local_language_id = 9
           LEFT JOIN machines ON machines.move_id = moves.id AND pokemon_move_methods.id = 4 AND machines.version_group_id = version_groups.id
           LEFT JOIN item_names ON item_names.item_id = machines.item_id AND item_names.local_language_id = 9
           WHERE pokemon_species.identifier = ? AND version_groups.id = ?
           ORDER BY pokemon_moves.pokemon_move_method_id, pokemon_moves.level, machines.machine_number, move_names.name"""

    html = ""

    current_move_method_id = 0
    for row in db.execute(sql, [pokemon, version_group_id]):
        if current_move_method_id != row["pokemon_move_method_id"]:
            if current_move_method_id != 0:
                html += "</tbody></table>"
                html += "</details>"
            html += (
                "<details><summary><b><big>"
                + utils.html_escape(row["method_name"])
                + "</big></b></summary>"
            )
            html += '<table style="margin: 5px 0"><tbody>'
            html += "<tr>"
            html += "  <th>Move</th>"
            if row["pokemon_move_method_id"] == 1:  # level-up
                html += "  <th>Level</th>"
            elif row["pokemon_move_method_id"] == 2:  # egg
                pass
            elif row["pokemon_move_method_id"] == 4:  # machine
                html += "  <th>Machine</th>"
            html += "</tr>"
            current_move_method_id = row["pokemon_move_method_id"]

        html += "<tr>"
        html += "  <td>" + utils.html_escape(row["move_name"]) + "</td>"
        if current_move_method_id == 1:  # level-up
            html += (
                '  <td style="text-align: right">'
                + utils.html_escape(str(row["level"]))
                + "</td>"
            )
        elif current_move_method_id == 2:  # egg
            pass
        elif current_move_method_id == 4:  # machine
            html += "  <td>" + utils.html_escape(row["machine"]) + "</td>"
        html += "</tr>"

    if current_move_method_id != 0:
        html += "</tbody></table>"
        html += "</details>"

    if not html:
        await conn.send_reply(room, user, "Nessun dato")
        return

    await conn.send_htmlbox(room, user, '<div class="ladder">' + html + "</div>")
