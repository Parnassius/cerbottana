# pylint: disable=too-few-public-methods

from __future__ import annotations

from functools import total_ordering
from typing import Literal, cast, overload

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


@total_ordering
class HashableMixin:
    id: Column[int]

    @property
    def _id(self) -> int:
        # Tables without an `id` column should override this property.
        return self.id

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if not isinstance(other, type(self)):
            raise NotImplementedError
        return self._id == other._id

    def __lt__(self, other: object) -> bool:
        if other is None:
            return True
        if not isinstance(other, type(self)):
            raise NotImplementedError
        return self._id < other._id

    def __hash__(self) -> int:
        return hash(self._id)


class TranslatableMixin:
    @overload
    def get_translation(
        self,
        translation_table: str,
        *,
        language_id: int | None = None,
        translation_column: str | None = None,
        language_column: str | None = None,
        fallback_column: str | None = None,
        fallback_english: Literal[True] = True,
        fallback: str | None = None,
    ) -> str:
        ...

    @overload
    def get_translation(
        self,
        translation_table: str,
        *,
        language_id: int | None = None,
        translation_column: str | None = None,
        language_column: str | None = None,
        fallback_column: str | None = None,
        fallback_english: Literal[False] = False,
        fallback: str | None = None,
    ) -> str | None:
        ...

    def get_translation(
        self,
        translation_table: str,
        *,
        language_id: int | None = None,
        translation_column: str | None = None,
        language_column: str | None = None,
        fallback_column: str | None = None,
        fallback_english: bool = True,
        fallback: str | None = None,
    ) -> str | None:
        if language_id is None:
            language_id = (
                self._sa_instance_state.session.info.get(  # type: ignore[attr-defined]
                    "language_id", 9
                )
            )
            language_id = cast(int, language_id)
        if translation_column is None:
            translation_column = "name"
        if language_column is None:
            language_column = "local_language_id"
        if fallback_column is None:
            fallback_column = "identifier"

        languages = [language_id]
        if fallback_english and language_id != 9:
            languages.append(9)  # Fallback to english.
        for lang in languages:
            if name := next(
                (
                    getattr(i, translation_column)
                    for i in getattr(self, translation_table)
                    if getattr(i, language_column) == lang
                ),
                None,
            ):
                return str(name)

        if not fallback_english:
            return None

        if fallback is not None:
            return fallback

        # If both the localized and the english name are unavailable then simply return
        # the identifier.
        return str(getattr(self, fallback_column))


class LatestCommit(Base):
    __tablename__ = "latest_commit"

    commit_id = Column(String, primary_key=True)


class Abilities(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "abilities"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=False)
    is_main_series = Column(Integer, index=True, nullable=False)

    generation = relationship("Generations", uselist=False, viewonly=True)

    ability_names = relationship("AbilityNames", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("ability_names")


class AbilityNames(Base):
    __tablename__ = "ability_names"

    ability_id = Column(Integer, ForeignKey("abilities.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    name_normalized = Column(String)

    ability = relationship("Abilities", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class EncounterConditionValueMap(Base):
    __tablename__ = "encounter_condition_value_map"

    encounter_id = Column(Integer, ForeignKey("encounters.id"), primary_key=True)
    encounter_condition_value_id = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )

    encounter = relationship("Encounters", uselist=False, viewonly=True)
    encounter_condition_value = relationship(
        "EncounterConditionValues", uselist=False, viewonly=True
    )


class EncounterConditionValueProse(Base):
    __tablename__ = "encounter_condition_value_prose"

    encounter_condition_value_id = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    encounter_condition_value = relationship(
        "EncounterConditionValues", uselist=False, viewonly=True
    )
    local_language = relationship("Languages", uselist=False, viewonly=True)


class EncounterConditionValues(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "encounter_condition_values"

    id = Column(Integer, primary_key=True)
    encounter_condition_id = Column(
        Integer, ForeignKey("encounter_conditions.id"), nullable=False
    )
    identifier = Column(String, nullable=False)
    is_default = Column(Integer, nullable=False)

    encounter_condition = relationship(
        "EncounterConditions", uselist=False, viewonly=True
    )

    encounter_condition_value_prose = relationship(
        "EncounterConditionValueProse", uselist=True, viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("encounter_condition_value_prose")


class EncounterConditions(HashableMixin, Base):
    __tablename__ = "encounter_conditions"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)

    encounter_condition_values = relationship(
        "EncounterConditionValues", uselist=True, viewonly=True
    )


class EncounterMethodProse(Base):
    __tablename__ = "encounter_method_prose"

    encounter_method_id = Column(
        Integer, ForeignKey("encounter_methods.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    encounter_method = relationship("EncounterMethods", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class EncounterMethods(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "encounter_methods"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, unique=True, nullable=False)
    order = Column(Integer, unique=True, nullable=False)

    encounter_method_prose = relationship(
        "EncounterMethodProse", uselist=True, viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("encounter_method_prose")


class EncounterSlots(HashableMixin, Base):
    __tablename__ = "encounter_slots"

    id = Column(Integer, primary_key=True)
    version_group_id = Column(Integer, ForeignKey("version_groups.id"), nullable=False)
    encounter_method_id = Column(
        Integer, ForeignKey("encounter_methods.id"), nullable=False
    )
    slot = Column(Integer)
    rarity = Column(Integer)

    version_group = relationship("VersionGroups", uselist=False, viewonly=True)
    encounter_method = relationship("EncounterMethods", uselist=False, viewonly=True)

    encounter = relationship("Encounters", uselist=False, viewonly=True)


class Encounters(HashableMixin, Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("versions.id"), nullable=False)
    location_area_id = Column(Integer, ForeignKey("location_areas.id"), nullable=False)
    encounter_slot_id = Column(
        Integer, ForeignKey("encounter_slots.id"), nullable=False
    )
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    min_level = Column(Integer, nullable=False)
    max_level = Column(Integer, nullable=False)

    version = relationship("Versions", uselist=False, viewonly=True)
    location_area = relationship("LocationAreas", uselist=False, viewonly=True)
    encounter_slot = relationship("EncounterSlots", uselist=False, viewonly=True)
    pokemon = relationship("Pokemon", uselist=False, viewonly=True)

    encounter_condition_value_map = relationship(
        "EncounterConditionValueMap", uselist=True, viewonly=True
    )


class EvolutionChains(HashableMixin, Base):
    __tablename__ = "evolution_chains"

    id = Column(Integer, primary_key=True)
    baby_trigger_item_id = Column(Integer, ForeignKey("items.id"))

    baby_trigger_item = relationship("Items", uselist=False, viewonly=True)

    pokemon_species = relationship("PokemonSpecies", uselist=False, viewonly=True)


class Generations(HashableMixin, Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True)
    main_region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    identifier = Column(String, nullable=False)

    main_region = relationship("Regions", uselist=False, viewonly=True)

    version_groups = relationship("VersionGroups", uselist=True, viewonly=True)


class ItemNames(Base):
    __tablename__ = "item_names"

    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    name_normalized = Column(String)

    item = relationship("Items", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Items(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    category_id = Column(Integer, nullable=False)
    cost = Column(Integer, nullable=False)
    fling_power = Column(Integer)
    fling_effect_id = Column(Integer)

    item_names = relationship("ItemNames", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("item_names")


class Languages(HashableMixin, Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True)
    iso639 = Column(String, nullable=False)
    iso3166 = Column(String, nullable=False)
    identifier = Column(String, nullable=False)
    official = Column(Integer, index=True, nullable=False)
    order = Column(Integer)


class LocationAreaProse(Base):
    __tablename__ = "location_area_prose"

    location_area_id = Column(
        Integer, ForeignKey("location_areas.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True)

    location_area = relationship("LocationAreas", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class LocationAreas(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "location_areas"
    __table_opts__ = (UniqueConstraint("location_id", "identifier"),)

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    game_index = Column(Integer, nullable=False)
    identifier = Column(String)

    location = relationship("Locations", uselist=False, viewonly=True)
    location_area_prose = relationship("LocationAreaProse", uselist=True, viewonly=True)

    encounters = relationship("Encounters", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("location_area_prose")


class LocationNames(Base):
    __tablename__ = "location_names"

    location_id = Column(Integer, ForeignKey("locations.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)
    subtitle = Column(String)

    location = relationship("Locations", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Locations(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    identifier = Column(String, unique=True, nullable=False)

    route_number = Column(Integer)

    region = relationship("Regions", uselist=False, viewonly=True)

    location_names = relationship("LocationNames", uselist=True, viewonly=True)
    location_areas = relationship("LocationAreas", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("location_names")

    @property
    def subtitle(self) -> str:
        return self.get_translation(
            "location_names", translation_column="subtitle", fallback=""
        )


class Machines(HashableMixin, Base):
    __tablename__ = "machines"

    machine_number = Column(Integer, primary_key=True)
    version_group_id = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    move_id = Column(Integer, ForeignKey("moves.id"), nullable=False)

    version_group = relationship("VersionGroups", uselist=False, viewonly=True)
    item = relationship("Items", uselist=False, viewonly=True)
    move = relationship("Moves", uselist=False, viewonly=True)

    @property
    def _id(self) -> int:
        return self.machine_number


class MoveNames(Base):
    __tablename__ = "move_names"

    move_id = Column(Integer, ForeignKey("moves.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    name_normalized = Column(String)

    move = relationship("Moves", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Moves(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=False)
    type_id = Column(Integer, nullable=False)
    power = Column(Integer)
    pp = Column(Integer)
    accuracy = Column(Integer)
    priority = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    damage_class_id = Column(Integer, nullable=False)
    effect_id = Column(Integer, nullable=False)
    effect_chance = Column(Integer)
    contest_type_id = Column(Integer)
    contest_effect_id = Column(Integer)
    super_contest_effect_id = Column(Integer)

    generation = relationship("Generations", uselist=False, viewonly=True)

    move_names = relationship("MoveNames", uselist=True, viewonly=True)
    machines = relationship("Machines", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("move_names")


class NatureNames(Base):
    __tablename__ = "nature_names"

    nature_id = Column(Integer, ForeignKey("natures.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    name_normalized = Column(String)

    nature = relationship("Natures", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Natures(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "natures"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    decreased_stat_id = Column(Integer, nullable=False)
    increased_stat_id = Column(Integer, nullable=False)
    hates_flavor_id = Column(Integer, nullable=False)
    likes_flavor_id = Column(Integer, nullable=False)
    game_index = Column(Integer, unique=True, nullable=False)

    nature_names = relationship("NatureNames", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("nature_names")


class Pokemon(HashableMixin, Base):
    __tablename__ = "pokemon"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    species_id = Column(Integer, ForeignKey("pokemon_species.id"))
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    base_experience = Column(Integer, nullable=False)
    order = Column(Integer, index=True, nullable=False)
    is_default = Column(Integer, index=True, nullable=False)

    species = relationship("PokemonSpecies", uselist=False, viewonly=True)

    encounters = relationship("Encounters", uselist=True, viewonly=True)
    pokemon_forms = relationship("PokemonForms", uselist=True, viewonly=True)
    pokemon_moves = relationship("PokemonMoves", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        pokemon_name = self.species.name
        for form in self.pokemon_forms:
            if not form.is_default:
                continue
            pokemon_name = form.get_translation(
                "pokemon_form_names",
                translation_column="form_name",
                fallback=pokemon_name,
            )
        return pokemon_name


class PokemonFormNames(Base):
    __tablename__ = "pokemon_form_names"

    pokemon_form_id = Column(Integer, ForeignKey("pokemon_forms.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    form_name = Column(String, index=True)
    pokemon_name = Column(String, index=True)

    pokemon_form = relationship("PokemonForms", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class PokemonForms(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_forms"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    form_identifier = Column(String)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    introduced_in_version_group_id = Column(Integer, ForeignKey("version_groups.id"))
    is_default = Column(Integer, nullable=False)
    is_battle_only = Column(Integer, nullable=False)
    is_mega = Column(Integer, nullable=False)
    form_order = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)

    pokemon = relationship("Pokemon", uselist=False, viewonly=True)
    introduced_in_version_group = relationship(
        "VersionGroups", uselist=False, viewonly=True
    )

    pokemon_form_names = relationship("PokemonFormNames", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation(
            "pokemon_form_names", translation_column="form_name"
        )


class PokemonMoveMethodProse(Base):
    __tablename__ = "pokemon_move_method_prose"

    pokemon_move_method_id = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True)
    description = Column(String)

    pokemon_move_method = relationship(
        "PokemonMoveMethods", uselist=False, viewonly=True
    )
    local_language = relationship("Languages", uselist=False, viewonly=True)


class PokemonMoveMethods(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_move_methods"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)

    pokemon_move_method_prose = relationship(
        "PokemonMoveMethodProse", uselist=True, viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("pokemon_move_method_prose")


class PokemonMoves(Base):
    __tablename__ = "pokemon_moves"

    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), primary_key=True, index=True)
    version_group_id = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True, index=True
    )
    move_id = Column(Integer, ForeignKey("moves.id"), primary_key=True, index=True)
    pokemon_move_method_id = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True, index=True
    )
    level = Column(Integer, primary_key=True, index=True, nullable=True)
    order = Column(Integer)

    pokemon = relationship("Pokemon", uselist=False, viewonly=True)
    version_group = relationship("VersionGroups", uselist=False, viewonly=True)
    move = relationship("Moves", uselist=False, viewonly=True)
    pokemon_move_method = relationship(
        "PokemonMoveMethods", uselist=False, viewonly=True
    )


class PokemonSpecies(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_species"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"))
    evolves_from_species_id = Column(Integer, ForeignKey("pokemon_species.id"))
    evolution_chain_id = Column(Integer, ForeignKey("evolution_chains.id"))
    color_id = Column(Integer, nullable=False)
    shape_id = Column(Integer)
    habitat_id = Column(Integer)
    gender_rate = Column(Integer, nullable=False)
    capture_rate = Column(Integer, nullable=False)
    base_happiness = Column(Integer, nullable=False)
    is_baby = Column(Integer, nullable=False)
    hatch_counter = Column(Integer, nullable=False)
    has_gender_differences = Column(Integer, nullable=False)
    growth_rate_id = Column(Integer, nullable=False)
    forms_switchable = Column(Integer, nullable=False)
    is_legendary = Column(Integer, nullable=False)
    is_mythical = Column(Integer, nullable=False)
    order = Column(Integer, index=True, nullable=False)
    conquest_order = Column(Integer, index=True)

    generation = relationship("Generations", uselist=False, viewonly=True)
    evolves_from_species = relationship("PokemonSpecies", uselist=False, viewonly=True)
    evolution_chain = relationship("EvolutionChains", uselist=False, viewonly=True)

    pokemon_species_flavor_text = relationship(
        "PokemonSpeciesFlavorText", uselist=True, viewonly=True
    )
    pokemon_species_names = relationship(
        "PokemonSpeciesNames", uselist=True, viewonly=True
    )
    pokemon = relationship("Pokemon", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("pokemon_species_names")


class PokemonSpeciesFlavorText(Base):
    __tablename__ = "pokemon_species_flavor_text"

    species_id = Column(Integer, ForeignKey("pokemon_species.id"), primary_key=True)
    version_id = Column(Integer, ForeignKey("versions.id"), primary_key=True)
    language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    flavor_text = Column(String, nullable=False)

    species = relationship("PokemonSpecies", uselist=False, viewonly=True)
    version = relationship("Versions", uselist=False, viewonly=True)
    language = relationship("Languages", uselist=False, viewonly=True)


class PokemonSpeciesNames(Base):
    __tablename__ = "pokemon_species_names"

    pokemon_species_id = Column(
        Integer, ForeignKey("pokemon_species.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True)
    genus = Column(String)

    pokemon_species = relationship("PokemonSpecies", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Regions(HashableMixin, Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)

    locations = relationship("Locations", uselist=True, viewonly=True)


class VersionGroups(HashableMixin, Base):
    __tablename__ = "version_groups"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, unique=True, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=False)
    order = Column(Integer)

    generation = relationship("Generations", uselist=False, viewonly=True)

    versions = relationship("Versions", uselist=True, viewonly=True)


class VersionNames(Base):
    __tablename__ = "version_names"

    version_id = Column(Integer, ForeignKey("versions.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    version = relationship("Versions", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Versions(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True)
    version_group_id = Column(Integer, ForeignKey("version_groups.id"), nullable=False)
    identifier = Column(String, nullable=False)

    version_group = relationship("VersionGroups", uselist=False, viewonly=True)

    version_names = relationship("VersionNames", uselist=True, viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("version_names")
