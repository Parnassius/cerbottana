from __future__ import annotations

from functools import total_ordering
from typing import Literal, cast, overload

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, declarative_base, relationship

Base = declarative_base()


@total_ordering
class HashableMixin:
    id: Mapped[int]

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


class LatestVersion(Base):
    __tablename__ = "latest_version"

    crc: int = Column(Integer, primary_key=True)


class Abilities(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "abilities"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)
    generation_id: int = Column(Integer, ForeignKey("generations.id"), nullable=False)
    is_main_series: int = Column(Integer, index=True, nullable=False)

    generation: Generations = relationship("Generations", viewonly=True)

    ability_names: list[AbilityNames] = relationship("AbilityNames", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("ability_names")


class AbilityNames(Base):
    __tablename__ = "ability_names"

    ability_id: int = Column(Integer, ForeignKey("abilities.id"), primary_key=True)
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)

    name_normalized: str | None = Column(String)

    ability: Abilities = relationship("Abilities", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class EncounterConditionValueMap(Base):
    __tablename__ = "encounter_condition_value_map"

    encounter_id: int = Column(Integer, ForeignKey("encounters.id"), primary_key=True)
    encounter_condition_value_id: int = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )

    encounter: Encounters = relationship("Encounters", viewonly=True)
    encounter_condition_value: EncounterConditionValues = relationship(
        "EncounterConditionValues", viewonly=True
    )


class EncounterConditionValueProse(Base):
    __tablename__ = "encounter_condition_value_prose"

    encounter_condition_value_id: int = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)

    encounter_condition_value: EncounterConditionValues = relationship(
        "EncounterConditionValues", viewonly=True
    )
    local_language: Languages = relationship("Languages", viewonly=True)


class EncounterConditionValues(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "encounter_condition_values"

    id: int = Column(Integer, primary_key=True)
    encounter_condition_id: int = Column(
        Integer, ForeignKey("encounter_conditions.id"), nullable=False
    )
    identifier: str = Column(String, nullable=False)
    is_default: int = Column(Integer, nullable=False)

    encounter_condition: EncounterConditions = relationship(
        "EncounterConditions", viewonly=True
    )

    encounter_condition_value_prose: list[EncounterConditionValueProse] = relationship(
        "EncounterConditionValueProse", viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("encounter_condition_value_prose")


class EncounterConditions(HashableMixin, Base):
    __tablename__ = "encounter_conditions"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)

    encounter_condition_values: list[EncounterConditionValues] = relationship(
        "EncounterConditionValues", viewonly=True
    )


class EncounterMethodProse(Base):
    __tablename__ = "encounter_method_prose"

    encounter_method_id: int = Column(
        Integer, ForeignKey("encounter_methods.id"), primary_key=True
    )
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)

    encounter_method: EncounterMethods = relationship("EncounterMethods", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class EncounterMethods(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "encounter_methods"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, unique=True, nullable=False)
    order: int = Column(Integer, unique=True, nullable=False)

    encounter_method_prose: list[EncounterMethodProse] = relationship(
        "EncounterMethodProse", viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("encounter_method_prose")


class EncounterSlots(HashableMixin, Base):
    __tablename__ = "encounter_slots"

    id: int = Column(Integer, primary_key=True)
    version_group_id: int = Column(
        Integer, ForeignKey("version_groups.id"), nullable=False
    )
    encounter_method_id: int = Column(
        Integer, ForeignKey("encounter_methods.id"), nullable=False
    )
    slot: int | None = Column(Integer)
    rarity: int | None = Column(Integer)

    version_group: VersionGroups = relationship("VersionGroups", viewonly=True)
    encounter_method: EncounterMethods = relationship("EncounterMethods", viewonly=True)

    encounter: Encounters = relationship("Encounters", viewonly=True)


class Encounters(HashableMixin, Base):
    __tablename__ = "encounters"

    id: int = Column(Integer, primary_key=True)
    version_id: int = Column(Integer, ForeignKey("versions.id"), nullable=False)
    location_area_id: int = Column(
        Integer, ForeignKey("location_areas.id"), nullable=False
    )
    encounter_slot_id: int = Column(
        Integer, ForeignKey("encounter_slots.id"), nullable=False
    )
    pokemon_id: int = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    min_level: int = Column(Integer, nullable=False)
    max_level: int = Column(Integer, nullable=False)

    version: Versions = relationship("Versions", viewonly=True)
    location_area: LocationAreas = relationship("LocationAreas", viewonly=True)
    encounter_slot: EncounterSlots = relationship("EncounterSlots", viewonly=True)
    pokemon: Pokemon = relationship("Pokemon", viewonly=True)

    encounter_condition_value_map: list[EncounterConditionValueMap] = relationship(
        "EncounterConditionValueMap", viewonly=True
    )


class EvolutionChains(HashableMixin, Base):
    __tablename__ = "evolution_chains"

    id: int = Column(Integer, primary_key=True)
    baby_trigger_item_id: int = Column(Integer, ForeignKey("items.id"))

    baby_trigger_item: Items = relationship("Items", viewonly=True)

    pokemon_species: PokemonSpecies = relationship("PokemonSpecies", viewonly=True)


class Generations(HashableMixin, Base):
    __tablename__ = "generations"

    id: int = Column(Integer, primary_key=True)
    main_region_id: int = Column(Integer, ForeignKey("regions.id"), nullable=False)
    identifier: str = Column(String, nullable=False)

    main_region: Regions = relationship("Regions", viewonly=True)

    version_groups: list[VersionGroups] = relationship("VersionGroups", viewonly=True)


class ItemNames(Base):
    __tablename__ = "item_names"

    item_id: int = Column(Integer, ForeignKey("items.id"), primary_key=True)
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)

    name_normalized: str | None = Column(String)

    item: Items = relationship("Items", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class Items(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "items"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)
    category_id: int = Column(Integer, nullable=False)
    cost: int = Column(Integer, nullable=False)
    fling_power: int | None = Column(Integer)
    fling_effect_id: int | None = Column(Integer)

    item_names: list[ItemNames] = relationship("ItemNames", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("item_names")


class Languages(HashableMixin, Base):
    __tablename__ = "languages"

    id: int = Column(Integer, primary_key=True)
    iso639 = Column(String, nullable=False)
    iso3166 = Column(String, nullable=False)
    identifier: str = Column(String, nullable=False)
    official: int = Column(Integer, index=True, nullable=False)
    order: int | None = Column(Integer)


class LocationAreaProse(Base):
    __tablename__ = "location_area_prose"

    location_area_id: int = Column(
        Integer, ForeignKey("location_areas.id"), primary_key=True
    )
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str | None = Column(String, index=True)

    location_area: LocationAreas = relationship("LocationAreas", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class LocationAreas(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "location_areas"
    __table_opts__ = (UniqueConstraint("location_id", "identifier"),)

    id: int = Column(Integer, primary_key=True)
    location_id: int = Column(Integer, ForeignKey("locations.id"), nullable=False)
    game_index: int = Column(Integer, nullable=False)
    identifier: str | None = Column(String)

    location: Locations = relationship("Locations", viewonly=True)
    location_area_prose: list[LocationAreaProse] = relationship(
        "LocationAreaProse", viewonly=True
    )

    encounters: list[Encounters] = relationship("Encounters", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("location_area_prose")


class LocationNames(Base):
    __tablename__ = "location_names"

    location_id: int = Column(Integer, ForeignKey("locations.id"), primary_key=True)
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)
    subtitle: str | None = Column(String)

    location: Locations = relationship("Locations", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class Locations(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "locations"

    id: int = Column(Integer, primary_key=True)
    region_id: int = Column(Integer, ForeignKey("regions.id"))
    identifier: str = Column(String, unique=True, nullable=False)

    route_number: int | None = Column(Integer)

    region: Regions = relationship("Regions", viewonly=True)

    location_names: list[LocationNames] = relationship("LocationNames", viewonly=True)
    location_areas: list[LocationAreas] = relationship("LocationAreas", viewonly=True)

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

    machine_number: int = Column(Integer, primary_key=True)
    version_group_id: int = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True
    )
    item_id: int = Column(Integer, ForeignKey("items.id"), nullable=False)
    move_id: int = Column(Integer, ForeignKey("moves.id"), nullable=False)

    version_group: VersionGroups = relationship("VersionGroups", viewonly=True)
    item: Items = relationship("Items", viewonly=True)
    move: Moves = relationship("Moves", viewonly=True)

    @property
    def _id(self) -> int:
        return self.machine_number


class MoveNames(Base):
    __tablename__ = "move_names"

    move_id: int = Column(Integer, ForeignKey("moves.id"), primary_key=True)
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)

    name_normalized: str | None = Column(String)

    move: Moves = relationship("Moves", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class Moves(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "moves"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)
    generation_id: int = Column(Integer, ForeignKey("generations.id"), nullable=False)
    type_id: int = Column(Integer, nullable=False)
    power: int | None = Column(Integer)
    pp: int | None = Column(Integer)
    accuracy: int | None = Column(Integer)
    priority: int = Column(Integer, nullable=False)
    target_id: int = Column(Integer, nullable=False)
    damage_class_id: int = Column(Integer, nullable=False)
    effect_id: int = Column(Integer, nullable=False)
    effect_chance: int | None = Column(Integer)
    contest_type_id: int | None = Column(Integer)
    contest_effect_id: int | None = Column(Integer)
    super_contest_effect_id: int | None = Column(Integer)

    generation: Generations = relationship("Generations", viewonly=True)

    move_names: list[MoveNames] = relationship("MoveNames", viewonly=True)
    machines: list[Machines] = relationship("Machines", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("move_names")


class NatureNames(Base):
    __tablename__ = "nature_names"

    nature_id: int = Column(Integer, ForeignKey("natures.id"), primary_key=True)
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)

    name_normalized: str | None = Column(String)

    nature: Natures = relationship("Natures", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class Natures(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "natures"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)
    decreased_stat_id: int = Column(Integer, nullable=False)
    increased_stat_id: int = Column(Integer, nullable=False)
    hates_flavor_id: int = Column(Integer, nullable=False)
    likes_flavor_id: int = Column(Integer, nullable=False)
    game_index: int = Column(Integer, unique=True, nullable=False)

    nature_names: list[NatureNames] = relationship("NatureNames", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("nature_names")


class Pokemon(HashableMixin, Base):
    __tablename__ = "pokemon"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)
    species_id: int = Column(Integer, ForeignKey("pokemon_species.id"))
    height: int = Column(Integer, nullable=False)
    weight: int = Column(Integer, nullable=False)
    base_experience: int = Column(Integer, nullable=False)
    order: int = Column(Integer, index=True, nullable=False)
    is_default: int = Column(Integer, index=True, nullable=False)

    species: PokemonSpecies = relationship("PokemonSpecies", viewonly=True)

    encounters: list[Encounters] = relationship("Encounters", viewonly=True)
    pokemon_forms: list[PokemonForms] = relationship("PokemonForms", viewonly=True)
    pokemon_moves: list[PokemonMoves] = relationship("PokemonMoves", viewonly=True)

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

    pokemon_form_id: int = Column(
        Integer, ForeignKey("pokemon_forms.id"), primary_key=True
    )
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    form_name: str | None = Column(String, index=True)
    pokemon_name: str | None = Column(String, index=True)

    pokemon_form: PokemonForms = relationship("PokemonForms", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class PokemonForms(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_forms"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)
    form_identifier: str | None = Column(String)
    pokemon_id: int = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    introduced_in_version_group_id: int = Column(
        Integer, ForeignKey("version_groups.id")
    )
    is_default: int = Column(Integer, nullable=False)
    is_battle_only: int = Column(Integer, nullable=False)
    is_mega: int = Column(Integer, nullable=False)
    form_order: int = Column(Integer, nullable=False)
    order: int = Column(Integer, nullable=False)

    pokemon: Pokemon = relationship("Pokemon", viewonly=True)
    introduced_in_version_group: VersionGroups = relationship(
        "VersionGroups", viewonly=True
    )

    pokemon_form_names: list[PokemonFormNames] = relationship(
        "PokemonFormNames", viewonly=True
    )

    @property
    def name(self) -> str:
        return self.get_translation(
            "pokemon_form_names", translation_column="form_name"
        )


class PokemonMoveMethodProse(Base):
    __tablename__ = "pokemon_move_method_prose"

    pokemon_move_method_id: int = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True
    )
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str | None = Column(String, index=True)
    description: str | None = Column(String)

    pokemon_move_method: PokemonMoveMethods = relationship(
        "PokemonMoveMethods", viewonly=True
    )
    local_language: Languages = relationship("Languages", viewonly=True)


class PokemonMoveMethods(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_move_methods"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)

    pokemon_move_method_prose: list[PokemonMoveMethodProse] = relationship(
        "PokemonMoveMethodProse", viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("pokemon_move_method_prose")


class PokemonMoves(Base):
    __tablename__ = "pokemon_moves"

    pokemon_id: int = Column(
        Integer, ForeignKey("pokemon.id"), primary_key=True, index=True
    )
    version_group_id: int = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True, index=True
    )
    move_id: int = Column(Integer, ForeignKey("moves.id"), primary_key=True, index=True)
    pokemon_move_method_id: int = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True, index=True
    )
    level: int = Column(Integer, primary_key=True, index=True, nullable=True)
    order: int | None = Column(Integer)

    pokemon: Pokemon = relationship("Pokemon", viewonly=True)
    version_group: VersionGroups = relationship("VersionGroups", viewonly=True)
    move: Moves = relationship("Moves", viewonly=True)
    pokemon_move_method: PokemonMoveMethods = relationship(
        "PokemonMoveMethods", viewonly=True
    )


class PokemonSpecies(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_species"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)
    generation_id: int = Column(Integer, ForeignKey("generations.id"))
    evolves_from_species_id: int = Column(Integer, ForeignKey("pokemon_species.id"))
    evolution_chain_id: int = Column(Integer, ForeignKey("evolution_chains.id"))
    color_id: int = Column(Integer, nullable=False)
    shape_id: int | None = Column(Integer)
    habitat_id: int | None = Column(Integer)
    gender_rate: int = Column(Integer, nullable=False)
    capture_rate: int = Column(Integer, nullable=False)
    base_happiness: int = Column(Integer, nullable=False)
    is_baby: int = Column(Integer, nullable=False)
    hatch_counter: int = Column(Integer, nullable=False)
    has_gender_differences: int = Column(Integer, nullable=False)
    growth_rate_id: int = Column(Integer, nullable=False)
    forms_switchable: int = Column(Integer, nullable=False)
    is_legendary: int = Column(Integer, nullable=False)
    is_mythical: int = Column(Integer, nullable=False)
    order: int = Column(Integer, index=True, nullable=False)
    conquest_order: int | None = Column(Integer, index=True)

    generation: Generations = relationship("Generations", viewonly=True)
    evolves_from_species: PokemonSpecies = relationship("PokemonSpecies", viewonly=True)
    evolution_chain: EvolutionChains = relationship("EvolutionChains", viewonly=True)

    pokemon_species_flavor_text: list[PokemonSpeciesFlavorText] = relationship(
        "PokemonSpeciesFlavorText", viewonly=True
    )
    pokemon_species_names: list[PokemonSpeciesNames] = relationship(
        "PokemonSpeciesNames", viewonly=True
    )
    pokemon: list[Pokemon] = relationship("Pokemon", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("pokemon_species_names")


class PokemonSpeciesFlavorText(Base):
    __tablename__ = "pokemon_species_flavor_text"

    species_id: int = Column(
        Integer, ForeignKey("pokemon_species.id"), primary_key=True
    )
    version_id: int = Column(Integer, ForeignKey("versions.id"), primary_key=True)
    language_id: int = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    flavor_text: str = Column(String, nullable=False)

    species: PokemonSpecies = relationship("PokemonSpecies", viewonly=True)
    version: Versions = relationship("Versions", viewonly=True)
    language: Languages = relationship("Languages", viewonly=True)


class PokemonSpeciesNames(Base):
    __tablename__ = "pokemon_species_names"

    pokemon_species_id: int = Column(
        Integer, ForeignKey("pokemon_species.id"), primary_key=True
    )
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str | None = Column(String, index=True)
    genus: str | None = Column(String)

    pokemon_species: PokemonSpecies = relationship("PokemonSpecies", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class Regions(HashableMixin, Base):
    __tablename__ = "regions"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, nullable=False)

    locations: list[Locations] = relationship("Locations", viewonly=True)


class VersionGroups(HashableMixin, Base):
    __tablename__ = "version_groups"

    id: int = Column(Integer, primary_key=True)
    identifier: str = Column(String, unique=True, nullable=False)
    generation_id: int = Column(Integer, ForeignKey("generations.id"), nullable=False)
    order: int | None = Column(Integer)

    generation: Generations = relationship("Generations", viewonly=True)

    versions: list[Versions] = relationship("Versions", viewonly=True)


class VersionNames(Base):
    __tablename__ = "version_names"

    version_id: int = Column(Integer, ForeignKey("versions.id"), primary_key=True)
    local_language_id: int = Column(
        Integer, ForeignKey("languages.id"), primary_key=True
    )
    name: str = Column(String, index=True, nullable=False)

    version: Versions = relationship("Versions", viewonly=True)
    local_language: Languages = relationship("Languages", viewonly=True)


class Versions(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "versions"

    id: int = Column(Integer, primary_key=True)
    version_group_id: int = Column(
        Integer, ForeignKey("version_groups.id"), nullable=False
    )
    identifier: str = Column(String, nullable=False)

    version_group: VersionGroups = relationship("VersionGroups", viewonly=True)

    version_names: list[VersionNames] = relationship("VersionNames", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("version_names")
