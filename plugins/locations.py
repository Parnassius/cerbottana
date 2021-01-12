from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from sqlalchemy.orm import joinedload

import databases.veekun as v
import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("location",))
async def locations(msg: Message) -> None:
    pokemon_id = utils.to_user_id(utils.remove_accents(msg.arg.lower()))

    db = Database.open("veekun")

    with db.get_session() as session:

        class ConditionsDict(TypedDict):
            rarity: int
            description: str

        class SlotsDict(TypedDict):
            location: str
            method: str
            min_level: int
            max_level: int
            conditions: dict[tuple[int, ...], ConditionsDict]
            rarity: int

        class ResultsDict(TypedDict):
            name: str
            slots: dict[tuple[int, int], SlotsDict]

        results: dict[int, ResultsDict] = {}

        pokemon_species = (
            session.query(v.PokemonSpecies)  # type: ignore  # sqlalchemy
            .options(
                joinedload(v.PokemonSpecies.pokemon)
                .joinedload(v.Pokemon.encounters)
                .joinedload(v.Encounters.version)
                .joinedload(v.Versions.version_names)
                .raiseload("*")
            )
            .filter_by(identifier=pokemon_id)
            .first()
        )

        if pokemon_species:

            for pokemon in pokemon_species.pokemon:

                for encounter in pokemon.encounters:

                    version = encounter.version
                    version_name = next(
                        (
                            i.name
                            for i in version.version_names
                            if i.local_language_id == 9
                        ),
                        "",
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

                    full_location_name = ""
                    if location_name:
                        full_location_name += location_name
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
                        "",
                    )

                    condition_names = {}
                    for condition_value_map in encounter.encounter_condition_value_map:
                        condition = condition_value_map.encounter_condition_value
                        condition_names[condition.id] = next(
                            (
                                i.name
                                for i in condition.encounter_condition_value_prose
                                if i.local_language_id == 9
                            ),
                            "",
                        )

                    if version.id not in results:
                        results[version.id] = {"name": version_name, "slots": {}}

                    key = (area.id, method.id)

                    if key not in results[version.id]["slots"]:
                        results[version.id]["slots"][key] = {
                            "location": full_location_name,
                            "method": method_name,
                            "min_level": 100,
                            "max_level": 0,
                            "conditions": {},
                            "rarity": 0,
                        }

                    results[version.id]["slots"][key]["min_level"] = min(
                        results[version.id]["slots"][key]["min_level"],
                        encounter.min_level,
                    )
                    results[version.id]["slots"][key]["max_level"] = max(
                        results[version.id]["slots"][key]["max_level"],
                        encounter.max_level,
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
                        results[version.id]["slots"][key][
                            "rarity"
                        ] += encounter_slot.rarity

    for version_id in sorted(results.keys()):
        results[version_id]["slots"] = dict(
            sorted(results[version_id]["slots"].items())
        )

    html = utils.render_template(
        "commands/locations.html", versions=sorted(results.keys()), results=results
    )

    if not html:
        await msg.reply("Nessun dato")
        return

    await msg.reply_htmlbox('<div class="ladder">' + html + "</div>")


@command_wrapper(aliases=("encounter",))
async def encounters(msg: Message) -> None:
    location_id = utils.to_user_id(utils.remove_accents(msg.arg.lower()))

    db = Database.open("veekun")

    with db.get_session() as session:

        class ConditionsDict(TypedDict):
            rarity: int
            description: str

        class SlotsDict(TypedDict):
            pokemon: str
            method: str
            min_level: int
            max_level: int
            conditions: dict[tuple[int, ...], ConditionsDict]
            rarity: int

        class AreasDict(TypedDict):
            name: str
            slots: dict[tuple[int, int], SlotsDict]

        class ResultsDict(TypedDict):
            name: str
            areas: dict[int, AreasDict]

        results: dict[int, ResultsDict] = {}

        location = (
            session.query(v.Locations)  # type: ignore  # sqlalchemy
            .options(
                joinedload(v.Locations.location_areas)
                .joinedload(v.LocationAreas.location_area_prose)
                .raiseload("*")
            )
            .filter_by(identifier=location_id)
            .first()
        )

        if location:

            for area in location.location_areas:

                area_name = next(
                    (
                        i.name
                        for i in area.location_area_prose
                        if i.local_language_id == 9
                    ),
                    "",
                )

                for encounter in area.encounters:

                    version = encounter.version
                    version_name = next(
                        (
                            i.name
                            for i in version.version_names
                            if i.local_language_id == 9
                        ),
                        "",
                    )

                    pokemon = encounter.pokemon
                    pokemon_species = pokemon.species
                    pokemon_species_name = next(
                        (
                            i.name
                            for i in pokemon_species.pokemon_species_name
                            if i.local_language_id == 9
                        ),
                        "",
                    )

                    encounter_slot = encounter.encounter_slot

                    method = encounter_slot.encounter_method
                    method_name = next(
                        (
                            i.name
                            for i in method.encounter_method_prose
                            if i.local_language_id == 9
                        ),
                        "",
                    )

                    condition_names = {}
                    for condition_value_map in encounter.encounter_condition_value_map:
                        condition = condition_value_map.encounter_condition_value
                        condition_names[condition.id] = next(
                            (
                                i.name
                                for i in condition.encounter_condition_value_prose
                                if i.local_language_id == 9
                            ),
                            "",
                        )

                    if version.id not in results:
                        results[version.id] = {"name": version_name, "areas": {}}

                    if area.id not in results[version.id]["areas"]:
                        results[version.id]["areas"][area.id] = {
                            "name": area_name,
                            "slots": {},
                        }

                    key = (method.id, pokemon.id)

                    if key not in results[version.id]["areas"][area.id]["slots"]:
                        results[version.id]["areas"][area.id]["slots"][key] = {
                            "pokemon": pokemon_species_name,
                            "method": method_name,
                            "min_level": 100,
                            "max_level": 0,
                            "conditions": {},
                            "rarity": 0,
                        }

                    results[version.id]["areas"][area.id]["slots"][key][
                        "min_level"
                    ] = min(
                        results[version.id]["areas"][area.id]["slots"][key][
                            "min_level"
                        ],
                        encounter.min_level,
                    )
                    results[version.id]["areas"][area.id]["slots"][key][
                        "max_level"
                    ] = max(
                        results[version.id]["areas"][area.id]["slots"][key][
                            "max_level"
                        ],
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
                        results[version.id]["areas"][area.id]["slots"][key][
                            "conditions"
                        ][key_conditions]["rarity"] += encounter_slot.rarity
                    else:
                        results[version.id]["areas"][area.id]["slots"][key][
                            "rarity"
                        ] += encounter_slot.rarity

    for version_id in sorted(results.keys()):
        results[version_id]["areas"] = dict(
            sorted(results[version_id]["areas"].items())
        )
        for area_id in results[version_id]["areas"].keys():
            results[version_id]["areas"][area_id]["slots"] = dict(
                sorted(results[version_id]["areas"][area_id]["slots"].items())
            )

    html = utils.render_template(
        "commands/encounters.html", versions=sorted(results.keys()), results=results
    )

    if not html:
        await msg.reply("Nessun dato")
        return

    await msg.reply_htmlbox('<div class="ladder">' + html + "</div>")
