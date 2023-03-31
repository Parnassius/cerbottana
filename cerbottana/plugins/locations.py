from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from domify import html_elements as e
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import cerbottana.databases.veekun as v
from cerbottana import utils
from cerbottana.database import Database
from cerbottana.html_utils import BaseHTMLCommand
from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


LocationsSlotKey = tuple[
    int,  # location_area
    int,  # encounter_method
    int,  # min_level
    int,  # max_level
    frozenset[int],  # conditions
]


@dataclass
class LocationsSlot:
    route_number: int
    location: str
    method: v.EncounterMethods
    min_level: int
    max_level: int
    conditions: frozenset[v.EncounterConditionValues]
    rarity: int = 0

    @property
    def _order_tuple(self) -> tuple[int, str, int, int, int, int]:
        return (
            self.route_number,
            self.location,
            self.method.id,
            self.min_level,
            self.max_level,
            -self.rarity,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LocationsSlot):
            raise NotImplementedError
        return self._order_tuple < other._order_tuple


@dataclass
class LocationsVersion:
    version: v.Versions
    slots: dict[LocationsSlotKey, LocationsSlot] = field(default_factory=dict)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LocationsVersion):
            raise NotImplementedError
        return self.version.id < other.version.id


@dataclass
class Locations:
    versions: dict[int, LocationsVersion] = field(default_factory=dict)

    def add_encounter_slot(self, encounter: v.Encounters) -> None:
        version = encounter.version
        if version.id not in self.versions:
            self.versions[version.id] = LocationsVersion(version)

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
            i.encounter_condition_value for i in encounter.encounter_condition_value_map
        )

        slot_key = (
            area.id,
            encounter.encounter_slot.encounter_method.id,
            encounter.min_level,
            encounter.max_level,
            frozenset(i.id for i in conditions),
        )

        if slot_key not in self.versions[version.id].slots:
            self.versions[version.id].slots[slot_key] = LocationsSlot(
                location.route_number or 0,
                full_location_name,
                encounter.encounter_slot.encounter_method,
                encounter.min_level,
                encounter.max_level,
                conditions,
            )

        self.versions[version.id].slots[slot_key].rarity += (
            encounter.encounter_slot.rarity or 0
        )


class LocationsHTML(BaseHTMLCommand):
    _STYLES = {
        "table": {
            "margin": "5px 0",
        },
    }

    def __init__(self, *, locations_data: Locations) -> None:
        super().__init__()

        if not locations_data.versions:
            return

        with self.doc, e.Div(class_="ladder"):
            for version in sorted(locations_data.versions.values()):
                with e.Details():
                    e.Summary(e.B(version.version.name))
                    self._add_table(version)

    def _add_table(self, version: LocationsVersion) -> None:
        with e.Table(style=self._get_css("table")):
            with e.Tr():
                e.Th("Location")
                e.Th("Method")
                e.Th("Level")
                e.Th("Rarity", colspan=2)

            for slot in sorted(version.slots.values()):
                with e.Tr():
                    e.Td(slot.location)
                    e.Td(slot.method.prose)
                    with e.Td(f"L{slot.min_level}"):
                        if slot.min_level < slot.max_level:
                            e.TextNode(f"-{slot.max_level}")
                    e.Td(f"{slot.rarity}%", colspan=None if slot.conditions else 2)
                    if slot.conditions:
                        e.Td(", ".join([x.prose for x in slot.conditions]))


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
        stmt = (
            select(v.PokemonSpecies)
            .options(
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
        )
        pokemon_species = session.scalar(stmt)
        if pokemon_species is None:
            await msg.reply("Pokémon not found.")
            return

        results = Locations()

        for pokemon in pokemon_species.pokemon:
            for encounter in pokemon.encounters:
                results.add_encounter_slot(encounter)

        html = LocationsHTML(locations_data=results)

        if not html:
            await msg.reply("No data available.")
            return

        await msg.reply_htmlbox(html.doc)


EncountersSlotKey = tuple[
    int,  # pokemon
    int,  # encounter_method
    int,  # min_level
    int,  # max_level
    frozenset[int],  # conditions
]


@dataclass
class EncountersSlot:
    pokemon: v.Pokemon
    method: v.EncounterMethods
    min_level: int
    max_level: int
    conditions: frozenset[v.EncounterConditionValues]
    rarity: int = 0

    @property
    def _order_tuple(self) -> tuple[int, int, int, int, int, int]:
        return (
            self.pokemon.species.order,
            self.pokemon.order,
            self.method.id,
            self.min_level,
            self.max_level,
            -self.rarity,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EncountersSlot):
            raise NotImplementedError
        return self._order_tuple < other._order_tuple


@dataclass
class EncountersArea:
    area: v.LocationAreas
    slots: dict[EncountersSlotKey, EncountersSlot] = field(default_factory=dict)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EncountersArea):
            raise NotImplementedError
        return self.area.name < other.area.name


@dataclass
class EncountersVersion:
    version: v.Versions
    areas: dict[int, EncountersArea] = field(default_factory=dict)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EncountersVersion):
            raise NotImplementedError
        return self.version.id < other.version.id


@dataclass
class Encounters:
    versions: dict[int, EncountersVersion] = field(default_factory=dict)

    def add_encounter_slot(
        self, area: v.LocationAreas, encounter: v.Encounters
    ) -> None:
        version = encounter.version
        if version.id not in self.versions:
            self.versions[version.id] = EncountersVersion(version)

        if area.id not in self.versions[version.id].areas:
            self.versions[version.id].areas[area.id] = EncountersArea(area)

        conditions = frozenset(
            i.encounter_condition_value for i in encounter.encounter_condition_value_map
        )

        slot_key = (
            encounter.pokemon.id,
            encounter.encounter_slot.encounter_method.id,
            encounter.min_level,
            encounter.max_level,
            frozenset(i.id for i in conditions),
        )

        if slot_key not in self.versions[version.id].areas[area.id].slots:
            self.versions[version.id].areas[area.id].slots[slot_key] = EncountersSlot(
                encounter.pokemon,
                encounter.encounter_slot.encounter_method,
                encounter.min_level,
                encounter.max_level,
                conditions,
            )

        self.versions[version.id].areas[area.id].slots[slot_key].rarity += (
            encounter.encounter_slot.rarity or 0
        )


class EncountersHTML(BaseHTMLCommand):
    _STYLES = {
        "table": {
            "margin": "5px 0",
        },
    }

    def __init__(self, *, encounters_data: Encounters) -> None:
        super().__init__()

        if not encounters_data.versions:
            return

        with self.doc, e.Div(class_="ladder"):
            for version in sorted(encounters_data.versions.values()):
                with e.Details():
                    e.Summary(e.B(version.version.name))
                    self._add_table(version)

    def _add_table(self, version: EncountersVersion) -> None:
        with e.Table(style=self._get_css("table")):
            for area in sorted(version.areas.values()):
                with e.Tr():
                    e.Th(area.area.name)
                    e.Th("Method")
                    e.Th("Level")
                    e.Th("Rarity", colspan=2)

                for slot in sorted(area.slots.values()):
                    with e.Tr():
                        e.Td(slot.pokemon.name)
                        e.Td(slot.method.prose)
                        with e.Td(f"L{slot.min_level}"):
                            if slot.min_level < slot.max_level:
                                e.TextNode(f"-{slot.max_level}")
                        e.Td(f"{slot.rarity}%", colspan=None if slot.conditions else 2)
                        if slot.conditions:
                            e.Td(", ".join([x.prose for x in slot.conditions]))


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
        stmt = (
            select(v.Locations)
            .options(
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
        )
        location = session.scalar(stmt)
        if location is None:
            await msg.reply("Location not found.")
            return

        results = Encounters()

        for area in location.location_areas:
            for encounter in area.encounters:
                results.add_encounter_slot(area, encounter)

        html = EncountersHTML(encounters_data=results)

        if not html:
            await msg.reply("No data available.")
            return

        await msg.reply_htmlbox(html.doc)
