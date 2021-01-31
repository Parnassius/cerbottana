from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, TypedDict

from sqlalchemy.orm import selectinload

import databases.veekun as v
import utils
from database import Database
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("location",))
async def locations(msg: Message) -> None:
    if len(msg.args) < 1:
        return

    pokemon_id = utils.to_id(utils.remove_diacritics(msg.args[0].lower()))

    language_id = msg.language_id
    if len(msg.args) >= 2:
        language_id = utils.get_language_id(msg.args[1], fallback=language_id)

    db = Database.open("veekun")

    with db.get_session(language_id) as session:

        class SlotsKeyTuple(NamedTuple):
            area: v.LocationAreas
            method: v.EncounterMethods
            min_level: int
            max_level: int
            conditions: frozenset[v.EncounterConditionValues]

        class SlotsDict(TypedDict):
            route_number: int
            location: str
            rarity: int

        class ResultsDict(TypedDict):
            slots: dict[SlotsKeyTuple, SlotsDict]

        pokemon_species: v.PokemonSpecies | None = (
            session.query(v.PokemonSpecies)
            .options(  # type: ignore  # sqlalchemy
                selectinload(v.PokemonSpecies.pokemon)
                .selectinload(v.Pokemon.encounters)
                .options(
                    selectinload(v.Encounters.version).selectinload(
                        v.Versions.version_names
                    ),
                    selectinload(v.Encounters.location_area).options(
                        selectinload(v.LocationAreas.location_area_prose),
                        selectinload(v.LocationAreas.location).selectinload(
                            v.Locations.location_names
                        ),
                    ),
                    selectinload(v.Encounters.encounter_slot)
                    .selectinload(v.EncounterSlots.encounter_method)
                    .selectinload(v.EncounterMethods.encounter_method_prose),
                    selectinload(v.Encounters.encounter_condition_value_map)
                    .selectinload(
                        v.EncounterConditionValueMap.encounter_condition_value
                    )
                    .selectinload(
                        v.EncounterConditionValues.encounter_condition_value_prose
                    ),
                )
            )
            .filter_by(identifier=pokemon_id)
            .one_or_none()
        )
        if pokemon_species is None:
            await msg.reply("Pokémon not found.")
            return

        results: dict[v.Versions, ResultsDict] = {}

        for pokemon in pokemon_species.pokemon:
            for encounter in pokemon.encounters:

                version = encounter.version
                if version not in results:
                    results[version] = {"slots": {}}

                area = encounter.location_area
                location = area.location
                full_location_name = ""
                if location.name:
                    full_location_name += location.name
                if location.subtitle:
                    full_location_name += " - " + location.subtitle
                if area.name:
                    full_location_name += " (" + area.name + ")"

                conditions = frozenset(
                    i.encounter_condition_value
                    for i in encounter.encounter_condition_value_map
                )

                slots_key = SlotsKeyTuple(
                    area,
                    encounter.encounter_slot.encounter_method,
                    encounter.min_level,
                    encounter.max_level,
                    conditions,
                )

                if slots_key not in results[version]["slots"]:
                    results[version]["slots"][slots_key] = {
                        "route_number": location.route_number or 0,
                        "location": full_location_name,
                        "rarity": 0,
                    }

                results[version]["slots"][slots_key]["rarity"] += (
                    encounter.encounter_slot.rarity or 0
                )

        html = utils.render_template("commands/locations.html", results=results)

        if not html:
            await msg.reply("No data available.")
            return

        await msg.reply_htmlbox('<div class="ladder">' + html + "</div>")


@command_wrapper(aliases=("encounter",))
async def encounters(msg: Message) -> None:
    if len(msg.args) < 1:
        return

    location_id = utils.to_id(utils.remove_diacritics(msg.args[0].lower()))

    language_id = msg.language_id
    if len(msg.args) >= 2:
        language_id = utils.get_language_id(msg.args[1], fallback=language_id)

    db = Database.open("veekun")

    with db.get_session(language_id) as session:

        class SlotsKeyTuple(NamedTuple):
            pokemon: v.Pokemon
            method: v.EncounterMethods
            min_level: int
            max_level: int
            conditions: frozenset[v.EncounterConditionValues]

        class SlotsDict(TypedDict):
            rarity: int

        class AreasDict(TypedDict):
            slots: dict[SlotsKeyTuple, SlotsDict]

        class ResultsDict(TypedDict):
            areas: dict[v.LocationAreas, AreasDict]

        location: v.Locations | None = (
            session.query(v.Locations)
            .options(  # type: ignore  # sqlalchemy
                selectinload(v.Locations.location_areas).options(
                    selectinload(v.LocationAreas.location_area_prose),
                    selectinload(v.LocationAreas.encounters).options(
                        selectinload(v.Encounters.version).selectinload(
                            v.Versions.version_names
                        ),
                        selectinload(v.Encounters.pokemon)
                        .selectinload(v.Pokemon.species)
                        .selectinload(v.PokemonSpecies.pokemon_species_names),
                        selectinload(v.Encounters.encounter_slot)
                        .selectinload(v.EncounterSlots.encounter_method)
                        .selectinload(v.EncounterMethods.encounter_method_prose),
                        selectinload(v.Encounters.encounter_condition_value_map)
                        .selectinload(
                            v.EncounterConditionValueMap.encounter_condition_value
                        )
                        .selectinload(
                            v.EncounterConditionValues.encounter_condition_value_prose
                        ),
                    ),
                )
            )
            .filter_by(identifier=location_id)
            .one_or_none()
        )
        if location is None:
            await msg.reply("Location not found.")
            return

        results: dict[v.Versions, ResultsDict] = {}

        for area in location.location_areas:
            for encounter in area.encounters:

                version = encounter.version
                if version not in results:
                    results[version] = {"areas": {}}

                if area not in results[version]["areas"]:
                    results[version]["areas"][area] = {"slots": {}}

                conditions = frozenset(
                    i.encounter_condition_value
                    for i in encounter.encounter_condition_value_map
                )

                slots_key = SlotsKeyTuple(
                    encounter.pokemon,
                    encounter.encounter_slot.encounter_method,
                    encounter.min_level,
                    encounter.max_level,
                    conditions,
                )

                if slots_key not in results[version]["areas"][area]["slots"]:
                    results[version]["areas"][area]["slots"][slots_key] = {"rarity": 0}

                results[version]["areas"][area]["slots"][slots_key]["rarity"] += (
                    encounter.encounter_slot.rarity or 0
                )

        html = utils.render_template("commands/encounters.html", results=results)

        if not html:
            await msg.reply("No data available.")
            return

        await msg.reply_htmlbox('<div class="ladder">' + html + "</div>")
