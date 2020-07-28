from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import joinedload

import databases.veekun as v
import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(aliases=["locations"])
async def location(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    arg = utils.to_user_id(utils.remove_accents(arg.lower()))

    db = Database.open("veekun")

    with db.get_session() as session:
        results = dict()

        pokemon_species = (
            session.query(v.PokemonSpecies)
            .options(
                joinedload(v.PokemonSpecies.pokemon)
                .joinedload(v.Pokemon.encounters)
                .joinedload(v.Encounters.version)
                .joinedload(v.Versions.version_names)
                .raiseload("*")
            )
            .filter_by(identifier=arg)
            .first()
        )

        for pokemon in pokemon_species.pokemon:

            for encounter in pokemon.encounters:

                version = encounter.version
                version_name = next(
                    (i.name for i in version.version_names if i.local_language_id == 9),
                    None,
                )

                area = encounter.location_area
                area_name = next(
                    (
                        i.name
                        for i in area.location_area_prose
                        if i.local_language_id == 9
                    ),
                    None,
                )

                location = area.location
                location_name = next(
                    (
                        i.name
                        for i in location.location_names
                        if i.local_language_id == 9
                    ),
                    None,
                )
                location_subtitle = next(
                    (
                        i.subtitle
                        for i in location.location_names
                        if i.local_language_id == 9
                    ),
                    None,
                )

                full_location_name = location_name
                if location_subtitle:
                    full_location_name += " - " + location_subtitle
                if area_name:
                    full_location_name += " (" + area_name + ")"

                encounter_slot = encounter.encounter_slot

                method = encounter_slot.encounter_method
                method_name = next(
                    (
                        i.name
                        for i in method.encounter_method_prose
                        if i.local_language_id == 9
                    ),
                    None,
                )

                condition_names = dict()
                for condition_value_map in encounter.encounter_condition_value_map:
                    condition = condition_value_map.encounter_condition_value
                    condition_names[condition.id] = next(
                        (
                            i.name
                            for i in condition.encounter_condition_value_prose
                            if i.local_language_id == 9
                        ),
                        None,
                    )

                if version.id not in results:
                    results[version.id] = {"name": version_name, "slots": dict()}

                key = (area.id, method.id)

                if key not in results[version.id]["slots"]:
                    results[version.id]["slots"][key] = {
                        "location": full_location_name,
                        "method": method_name,
                        "min_level": 100,
                        "max_level": 0,
                        "conditions": dict(),
                        "rarity": 0,
                    }

                results[version.id]["slots"][key]["min_level"] = min(
                    results[version.id]["slots"][key]["min_level"], encounter.min_level
                )
                results[version.id]["slots"][key]["max_level"] = max(
                    results[version.id]["slots"][key]["max_level"], encounter.max_level
                )

                if condition_names:
                    key_conditions = tuple(sorted(condition_names.keys()))
                    if (
                        key_conditions
                        not in results[version.id]["slots"][key]["conditions"]
                    ):
                        results[version.id]["slots"][key]["conditions"][
                            key_conditions
                        ] = {
                            "rarity": 0,
                            "description": ", ".join(condition_names.values()),
                        }
                    results[version.id]["slots"][key]["conditions"][key_conditions][
                        "rarity"
                    ] += encounter_slot.rarity
                else:
                    results[version.id]["slots"][key]["rarity"] += encounter_slot.rarity

    html = ""

    for version in sorted(results.keys()):
        html += (
            "<details><summary><b><big>"
            + utils.html_escape(results[version]["name"])
            + "</big></b></summary>"
        )
        html += "<table><tbody>"
        html += "<tr>"
        html += "  <th>Location</th>"
        html += "  <th>Method</th>"
        html += "  <th>Level</th>"
        html += '  <th colspan="2">Rarity</th>'
        html += "</tr>"

        for slot in sorted(results[version]["slots"].keys()):
            levels = "L" + str(results[version]["slots"][slot]["min_level"])
            if (
                results[version]["slots"][slot]["min_level"]
                < results[version]["slots"][slot]["max_level"]
            ):
                levels += "-" + str(results[version]["slots"][slot]["max_level"])

            conditions = "\n".join(
                [
                    "+" + str(i["rarity"]) + "% " + i["description"]
                    for i in results[version]["slots"][slot]["conditions"].values()
                ]
            )

            html += "<tr>"
            html += (
                "  <td>"
                + utils.html_escape(results[version]["slots"][slot]["location"])
                + "</td>"
            )
            html += (
                "  <td>"
                + utils.html_escape(results[version]["slots"][slot]["method"])
                + "</td>"
            )
            html += "  <td>" + utils.html_escape(levels) + "</td>"
            html += (
                "  <td"
                + (
                    ' colspan="2"'
                    if not results[version]["slots"][slot]["conditions"]
                    else ""
                )
                + ">"
                + utils.html_escape(
                    str(results[version]["slots"][slot]["rarity"]) + "%"
                )
                + "</td>"
            )
            if len(results[version]["slots"][slot]["conditions"]):
                html += "  <td>" + utils.html_escape(conditions) + "</td>"
            html += "</tr>"

        html += "</tbody></table>"
        html += "</details>"

    if not html:
        await conn.send_reply(room, user, "Nessun dato")
        return

    await conn.send_htmlbox(room, user, '<div class="ladder">' + html + "</div>")


@command_wrapper(aliases=["encounters"])
async def encounter(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    arg = utils.to_user_id(utils.remove_accents(arg.lower()))

    db = Database.open("veekun")

    with db.get_session() as session:
        results = dict()

        location = (
            session.query(v.Locations)
            .options(
                joinedload(v.Locations.location_areas)
                .joinedload(v.LocationAreas.location_area_prose)
                .raiseload("*")
            )
            .filter_by(identifier=arg)
            .first()
        )

        for area in location.location_areas:

            area_name = next(
                (i.name for i in area.location_area_prose if i.local_language_id == 9),
                None,
            )

            for encounter in area.encounters:

                version = encounter.version
                version_name = next(
                    (i.name for i in version.version_names if i.local_language_id == 9),
                    None,
                )

                pokemon = encounter.pokemon
                pokemon_species = pokemon.species
                pokemon_species_name = next(
                    (
                        i.name
                        for i in pokemon_species.pokemon_species_name
                        if i.local_language_id == 9
                    ),
                    None,
                )

                encounter_slot = encounter.encounter_slot

                method = encounter_slot.encounter_method
                method_name = next(
                    (
                        i.name
                        for i in method.encounter_method_prose
                        if i.local_language_id == 9
                    ),
                    None,
                )

                condition_names = dict()
                for condition_value_map in encounter.encounter_condition_value_map:
                    condition = condition_value_map.encounter_condition_value
                    condition_names[condition.id] = next(
                        (
                            i.name
                            for i in condition.encounter_condition_value_prose
                            if i.local_language_id == 9
                        ),
                        None,
                    )

                if version.id not in results:
                    results[version.id] = {"name": version_name, "areas": dict()}

                if area.id not in results[version.id]["areas"]:
                    results[version.id]["areas"][area.id] = {
                        "name": area_name,
                        "slots": dict(),
                    }

                key = (method.id, pokemon.id)

                if key not in results[version.id]["areas"][area.id]["slots"]:
                    results[version.id]["areas"][area.id]["slots"][key] = {
                        "pokemon": pokemon_species_name,
                        "method": method_name,
                        "min_level": 100,
                        "max_level": 0,
                        "conditions": dict(),
                        "rarity": 0,
                    }

                results[version.id]["areas"][area.id]["slots"][key]["min_level"] = min(
                    results[version.id]["areas"][area.id]["slots"][key]["min_level"],
                    encounter.min_level,
                )
                results[version.id]["areas"][area.id]["slots"][key]["max_level"] = max(
                    results[version.id]["areas"][area.id]["slots"][key]["max_level"],
                    encounter.max_level,
                )

                if condition_names:
                    key_conditions = tuple(sorted(condition_names.keys()))
                    if (
                        key_conditions
                        not in results[version.id]["areas"][area.id]["slots"][key][
                            "conditions"
                        ]
                    ):
                        results[version.id]["areas"][area.id]["slots"][key][
                            "conditions"
                        ][key_conditions] = {
                            "rarity": 0,
                            "description": ", ".join(condition_names.values()),
                        }
                    results[version.id]["areas"][area.id]["slots"][key]["conditions"][
                        key_conditions
                    ]["rarity"] += encounter_slot.rarity
                else:
                    results[version.id]["areas"][area.id]["slots"][key][
                        "rarity"
                    ] += encounter_slot.rarity

    html = ""

    for version in sorted(results.keys()):
        html += (
            "<details><summary><b><big>"
            + utils.html_escape(results[version]["name"])
            + "</big></b></summary>"
        )
        html += "<table><tbody>"

        for area in sorted(results[version]["areas"].keys()):
            html += "<tr>"
            html += (
                "  <th>"
                + utils.html_escape(results[version]["areas"][area]["name"])
                + "</th>"
            )
            html += "  <th>Method</th>"
            html += "  <th>Level</th>"
            html += '  <th colspan="2">Rarity</th>'
            html += "</tr>"

            for slot in sorted(results[version]["areas"][area]["slots"].keys()):
                levels = "L" + str(
                    results[version]["areas"][area]["slots"][slot]["min_level"]
                )
                if (
                    results[version]["areas"][area]["slots"][slot]["min_level"]
                    < results[version]["areas"][area]["slots"][slot]["max_level"]
                ):
                    levels += "-" + str(
                        results[version]["areas"][area]["slots"][slot]["max_level"]
                    )

                conditions = "\n".join(
                    [
                        "+" + str(i["rarity"]) + "% " + i["description"]
                        for i in results[version]["areas"][area]["slots"][slot][
                            "conditions"
                        ].values()
                    ]
                )

                html += "<tr>"
                html += (
                    "  <td>"
                    + utils.html_escape(
                        results[version]["areas"][area]["slots"][slot]["pokemon"]
                    )
                    + "</td>"
                )
                html += (
                    "  <td>"
                    + utils.html_escape(
                        results[version]["areas"][area]["slots"][slot]["method"]
                    )
                    + "</td>"
                )
                html += "  <td>" + utils.html_escape(levels) + "</td>"
                html += (
                    "  <td"
                    + (
                        ' colspan="2"'
                        if not results[version]["areas"][area]["slots"][slot][
                            "conditions"
                        ]
                        else ""
                    )
                    + ">"
                    + utils.html_escape(
                        str(results[version]["areas"][area]["slots"][slot]["rarity"])
                        + "%"
                    )
                    + "</td>"
                )
                if len(results[version]["areas"][area]["slots"][slot]["conditions"]):
                    html += "  <td>" + utils.html_escape(conditions) + "</td>"
                html += "</tr>"

        html += "</tbody></table>"
        html += "</details>"

    if not html:
        await conn.send_reply(room, user, "Nessun dato")
        return

    await conn.send_htmlbox(room, user, '<div class="ladder">' + html + "</div>")
