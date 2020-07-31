from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(aliases=["locations"])
async def location(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    arg = utils.to_user_id(utils.remove_accents(arg.lower()))
    sql = """SELECT b.version_id, MIN(b.min_level) AS min_level, MAX(b.max_level) AS max_level,
           b.version, b.location_area_id, b.location_area, b.location_name, b.location_subtitle,
           SUM(CASE WHEN b.encounter_condition IS NULL THEN b.rarity ELSE 0 END) AS rarity,
           b.encounter_method_id, b.encounter_method,
           IFNULL(GROUP_CONCAT('+' || b.rarity || '% ' || b.encounter_condition, '\n'), '') AS conditions
           FROM (SELECT a.version_id, MIN(a.min_level) AS min_level, MAX(a.max_level) AS max_level,
                 a.version, a.location_area_id, a.location_area, a.location_name, a.location_subtitle,
                 SUM(a.rarity) AS rarity,
                 a.encounter_method_id, a.encounter_method, a.encounter_condition
                 FROM (SELECT encounters.version_id, encounters.min_level, encounters.max_level,
                       encounters.version_id, version_names.name AS version,
                       location_areas.id AS location_area_id, IFNULL(location_area_prose.name, '') AS location_area,
                       IFNULL(location_names.name, '') AS location_name,
                       IFNULL(location_names.subtitle, '') AS location_subtitle,
                       encounter_slots.rarity,
                       encounter_methods.id AS encounter_method_id,
                       IFNULL(encounter_method_prose.name, '') AS encounter_method,
                       GROUP_CONCAT(encounter_condition_value_prose.name, ', ') AS encounter_condition
                       FROM pokemon_species
                       LEFT JOIN pokemon ON pokemon.species_id = pokemon_species.id
                       LEFT JOIN encounters ON encounters.pokemon_id = pokemon.id
                       LEFT JOIN version_names ON version_names.version_id = encounters.version_id AND version_names.local_language_id = 9
                       JOIN location_areas ON location_areas.id = encounters.location_area_id
                       LEFT JOIN location_area_prose ON location_area_prose.location_area_id = location_areas.id AND location_area_prose.local_language_id = 9
                       LEFT JOIN location_names ON location_names.location_id = location_areas.location_id AND location_names.local_language_id = 9
                       JOIN encounter_slots ON encounter_slots.id = encounters.encounter_slot_id
                       JOIN encounter_methods ON encounter_methods.id = encounter_slots.encounter_method_id
                       LEFT JOIN encounter_method_prose ON encounter_method_prose.encounter_method_id = encounter_methods.id AND  encounter_method_prose.local_language_id = 9
                       LEFT JOIN encounter_condition_value_map ON encounter_condition_value_map.encounter_id = encounters.id
                       LEFT JOIN encounter_condition_value_prose ON encounter_condition_value_prose.encounter_condition_value_id = encounter_condition_value_map.encounter_condition_value_id AND encounter_condition_value_prose.local_language_id = 9
                       WHERE pokemon_species.identifier = ?
                       GROUP BY encounters.id) AS a
                 GROUP BY version_id, location_area_id, encounter_method_id, encounter_condition) AS b
           GROUP BY version_id, location_area_id, encounter_method_id
           ORDER BY version_id, location_area_id, encounter_method_id"""

    db = Database("veekun")

    html = ""

    current_version_id = 0
    for row in db.execute(sql, [arg]):
        if current_version_id != row["version_id"]:
            if current_version_id != 0:
                html += "</tbody></table>"
                html += "</details>"
            html += (
                "<details><summary><b><big>"
                + utils.html_escape(row["version"])
                + "</big></b></summary>"
            )
            html += "<table><tbody>"
            html += "<tr>"
            html += "  <th>Location</th>"
            html += "  <th>Method</th>"
            html += "  <th>Level</th>"
            html += '  <th colspan="2">Rarity</th>'
            html += "</tr>"
            current_version_id = row["version_id"]

        location_name = row["location_name"]
        if row["location_subtitle"]:
            location_name += " - " + row["location_subtitle"]
        if row["location_area"]:
            location_name += " (" + row["location_area"] + ")"
        levels = "L" + str(row["min_level"])
        if row["min_level"] < row["max_level"]:
            levels += "-" + str(row["max_level"])

        html += "<tr>"
        html += "  <td>" + utils.html_escape(location_name) + "</td>"
        html += "  <td>" + utils.html_escape(row["encounter_method"]) + "</td>"
        html += "  <td>" + utils.html_escape(levels) + "</td>"
        html += (
            "  <td"
            + (' colspan="2"' if not len(row["conditions"]) else "")
            + ">"
            + utils.html_escape(str(row["rarity"]) + "%")
            + "</td>"
        )
        if len(row["conditions"]):
            html += "  <td>" + utils.html_escape(row["conditions"]) + "</td>"
        html += "</tr>"

    if current_version_id != 0:
        html += "</tbody></table>"
        html += "</details>"

    if not html:
        await conn.send_reply(room, user, "Nessun dato")
        return

    await conn.send_htmlbox(room, user, '<div class="ladder">' + html + "</div>")


@command_wrapper(aliases=["encounters"])
async def encounter(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if room is not None and not utils.is_voice(user):
        return

    arg = utils.to_user_id(utils.remove_accents(arg.lower()))
    sql = """SELECT b.version_id, MIN(b.min_level) AS min_level, MAX(b.max_level) AS max_level,
           b.version, b.pokemon_id, b.pokemon, b.location_area_id, b.location_area, b.location_name, b.location_subtitle,
           SUM(CASE WHEN b.encounter_condition IS NULL THEN b.rarity ELSE 0 END) AS rarity,
           b.encounter_method_id, b.encounter_method,
           IFNULL(GROUP_CONCAT('+' || b.rarity || '% ' || b.encounter_condition, '\n'), '') AS conditions
           FROM (SELECT a.version_id, MIN(a.min_level) AS min_level, MAX(a.max_level) AS max_level,
                 a.version, a.pokemon_id, a.pokemon, a.location_area_id, a.location_area, a.location_name, a.location_subtitle,
                 SUM(a.rarity) AS rarity,
                 a.encounter_method_id, a.encounter_method, a.encounter_condition
                 FROM (SELECT encounters.id AS encounter_id, encounters.version_id,
                       encounters.min_level, encounters.max_level,
                       encounters.version_id, version_names.name AS version,
                       pokemon.id AS pokemon_id, pokemon_species_names.name AS pokemon,
                       location_areas.id AS location_area_id, IFNULL(location_area_prose.name, '') AS location_area,
                       IFNULL(location_names.name, '') AS location_name,
                       IFNULL(location_names.subtitle, '') AS location_subtitle,
                       encounter_slots.rarity,
                       encounter_methods.id AS encounter_method_id,
                       IFNULL(encounter_method_prose.name, '') AS encounter_method,
                       GROUP_CONCAT(encounter_condition_value_prose.name, ', ') AS encounter_condition
                       FROM locations
                       JOIN location_areas ON location_areas.location_id = locations.id
                       LEFT JOIN encounters ON encounters.location_area_id = location_areas.id
                       LEFT JOIN version_names ON version_names.version_id = encounters.version_id AND version_names.local_language_id = 9
                       LEFT JOIN pokemon ON pokemon.id = encounters.pokemon_id
                       JOIN pokemon_species ON pokemon_species.id = pokemon.species_id
                       LEFT JOIN pokemon_species_names ON pokemon_species_names.pokemon_species_id = pokemon_species.id AND pokemon_species_names.local_language_id = 9
                       LEFT JOIN location_area_prose ON location_area_prose.location_area_id = location_areas.id AND location_area_prose.local_language_id = 9
                       LEFT JOIN location_names ON location_names.location_id = location_areas.location_id AND location_names.local_language_id = 9
                       JOIN encounter_slots ON encounter_slots.id = encounters.encounter_slot_id
                       JOIN encounter_methods ON encounter_methods.id = encounter_slots.encounter_method_id
                       LEFT JOIN encounter_method_prose ON encounter_method_prose.encounter_method_id = encounter_methods.id AND  encounter_method_prose.local_language_id = 9
                       LEFT JOIN encounter_condition_value_map ON encounter_condition_value_map.encounter_id = encounters.id
                       LEFT JOIN encounter_condition_value_prose ON encounter_condition_value_prose.encounter_condition_value_id = encounter_condition_value_map.encounter_condition_value_id AND encounter_condition_value_prose.local_language_id = 9
                       WHERE locations.identifier = ?
                       GROUP BY encounters.id) AS a
                 GROUP BY version_id, location_area_id, pokemon_id, encounter_method_id, encounter_condition) AS b
           GROUP BY version_id, location_area_id, pokemon_id, encounter_method_id
           ORDER BY version_id, location_area_id, encounter_method_id, rarity DESC, pokemon_id"""

    db = Database("veekun")

    html = ""

    current_version_id = 0
    current_location_area = None
    for row in db.execute(sql, [arg]):
        if current_version_id != row["version_id"]:
            if current_version_id != 0:
                html += "</tbody></table>"
                html += "</details>"
            html += (
                "<details><summary><b><big>"
                + utils.html_escape(row["version"])
                + "</big></b></summary>"
            )
            html += "<table><tbody>"
            current_version_id = row["version_id"]
            current_location_area = None

        if current_location_area != row["location_area"]:
            html += "<tr>"
            html += "  <th>" + utils.html_escape(row["location_area"]) + "</th>"
            html += "  <th>Method</th>"
            html += "  <th>Level</th>"
            html += '  <th colspan="2">Rarity</th>'
            html += "</tr>"
            current_location_area = row["location_area"]

        levels = "L" + str(row["min_level"])
        if row["min_level"] < row["max_level"]:
            levels += "-" + str(row["max_level"])

        html += "<tr>"
        html += "  <td>" + utils.html_escape(row["pokemon"]) + "</td>"
        html += "  <td>" + utils.html_escape(row["encounter_method"]) + "</td>"
        html += "  <td>" + utils.html_escape(levels) + "</td>"
        html += (
            "  <td"
            + (' colspan="2"' if not len(row["conditions"]) else "")
            + ">"
            + utils.html_escape(str(row["rarity"]) + "%")
            + "</td>"
        )
        if len(row["conditions"]):
            html += "  <td>" + utils.html_escape(row["conditions"]) + "</td>"
        html += "</tr>"

    if current_version_id != 0:
        html += "</tbody></table>"
        html += "</details>"

    if not html:
        await conn.send_reply(room, user, "Nessun dato")
        return

    await conn.send_htmlbox(room, user, '<div class="ladder">' + html + "</div>")
