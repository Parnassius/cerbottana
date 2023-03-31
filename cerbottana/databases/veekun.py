from __future__ import annotations

from functools import total_ordering
from typing import Annotated, Literal, cast, overload

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

intpk = Annotated[int, mapped_column(primary_key=True)]


class Base(DeclarativeBase):
    pass


@total_ordering
class HashableMixin:
    @property
    def _id(self) -> int:
        # Tables without an `id` column should override this property.
        return self.id  # type: ignore[attr-defined, no-any-return]

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

    crc: Mapped[intpk]


class Abilities(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "abilities"

    id: Mapped[intpk]
    identifier: Mapped[str]
    generation_id: Mapped[int] = mapped_column(ForeignKey("generations.id"))
    is_main_series: Mapped[int] = mapped_column(index=True)

    generation: Mapped[Generations] = relationship("Generations", viewonly=True)

    ability_names: Mapped[list[AbilityNames]] = relationship(
        "AbilityNames", viewonly=True
    )

    @property
    def name(self) -> str:
        return self.get_translation("ability_names")


class AbilityNames(Base):
    __tablename__ = "ability_names"

    ability_id: Mapped[intpk] = mapped_column(ForeignKey("abilities.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)

    name_normalized: Mapped[str | None]

    ability: Mapped[Abilities] = relationship("Abilities", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class EncounterConditionValueMap(Base):
    __tablename__ = "encounter_condition_value_map"

    encounter_id: Mapped[intpk] = mapped_column(ForeignKey("encounters.id"))
    encounter_condition_value_id: Mapped[intpk] = mapped_column(
        ForeignKey("encounter_condition_values.id")
    )

    encounter: Mapped[Encounters] = relationship("Encounters", viewonly=True)
    encounter_condition_value: Mapped[EncounterConditionValues] = relationship(
        "EncounterConditionValues", viewonly=True
    )


class EncounterConditionValueProse(Base):
    __tablename__ = "encounter_condition_value_prose"

    encounter_condition_value_id: Mapped[intpk] = mapped_column(
        ForeignKey("encounter_condition_values.id")
    )
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)

    encounter_condition_value: Mapped[EncounterConditionValues] = relationship(
        "EncounterConditionValues", viewonly=True
    )
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class EncounterConditionValues(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "encounter_condition_values"

    id: Mapped[intpk]
    encounter_condition_id: Mapped[int] = mapped_column(
        ForeignKey("encounter_conditions.id")
    )
    identifier: Mapped[str]
    is_default: Mapped[int]

    encounter_condition: Mapped[EncounterConditions] = relationship(
        "EncounterConditions", viewonly=True
    )

    encounter_condition_value_prose: Mapped[
        list[EncounterConditionValueProse]
    ] = relationship("EncounterConditionValueProse", viewonly=True)

    @property
    def prose(self) -> str:
        return self.get_translation("encounter_condition_value_prose")


class EncounterConditions(HashableMixin, Base):
    __tablename__ = "encounter_conditions"

    id: Mapped[intpk]
    identifier: Mapped[str]

    encounter_condition_values: Mapped[list[EncounterConditionValues]] = relationship(
        "EncounterConditionValues", viewonly=True
    )


class EncounterMethodProse(Base):
    __tablename__ = "encounter_method_prose"

    encounter_method_id: Mapped[intpk] = mapped_column(
        ForeignKey("encounter_methods.id")
    )
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)

    encounter_method: Mapped[EncounterMethods] = relationship(
        "EncounterMethods", viewonly=True
    )
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class EncounterMethods(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "encounter_methods"

    id: Mapped[intpk]
    identifier: Mapped[str] = mapped_column(unique=True)
    order: Mapped[int] = mapped_column(unique=True)

    encounter_method_prose: Mapped[list[EncounterMethodProse]] = relationship(
        "EncounterMethodProse", viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("encounter_method_prose")


class EncounterSlots(HashableMixin, Base):
    __tablename__ = "encounter_slots"

    id: Mapped[intpk]
    version_group_id: Mapped[int] = mapped_column(ForeignKey("version_groups.id"))
    encounter_method_id: Mapped[int] = mapped_column(ForeignKey("encounter_methods.id"))
    slot: Mapped[int | None]
    rarity: Mapped[int | None]

    version_group: Mapped[VersionGroups] = relationship("VersionGroups", viewonly=True)
    encounter_method: Mapped[EncounterMethods] = relationship(
        "EncounterMethods", viewonly=True
    )

    encounter: Mapped[Encounters] = relationship("Encounters", viewonly=True)


class Encounters(HashableMixin, Base):
    __tablename__ = "encounters"

    id: Mapped[intpk]
    version_id: Mapped[int] = mapped_column(ForeignKey("versions.id"))
    location_area_id: Mapped[int] = mapped_column(ForeignKey("location_areas.id"))
    encounter_slot_id: Mapped[int] = mapped_column(ForeignKey("encounter_slots.id"))
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"))
    min_level: Mapped[int]
    max_level: Mapped[int]

    version: Mapped[Versions] = relationship("Versions", viewonly=True)
    location_area: Mapped[LocationAreas] = relationship("LocationAreas", viewonly=True)
    encounter_slot: Mapped[EncounterSlots] = relationship(
        "EncounterSlots", viewonly=True
    )
    pokemon: Mapped[Pokemon] = relationship("Pokemon", viewonly=True)

    encounter_condition_value_map: Mapped[
        list[EncounterConditionValueMap]
    ] = relationship("EncounterConditionValueMap", viewonly=True)


class EvolutionChains(HashableMixin, Base):
    __tablename__ = "evolution_chains"

    id: Mapped[intpk]
    baby_trigger_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))

    baby_trigger_item: Mapped[Items] = relationship("Items", viewonly=True)

    pokemon_species: Mapped[PokemonSpecies] = relationship(
        "PokemonSpecies", viewonly=True
    )


class Generations(HashableMixin, Base):
    __tablename__ = "generations"

    id: Mapped[intpk]
    main_region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"))
    identifier: Mapped[str]

    main_region: Mapped[Regions] = relationship("Regions", viewonly=True)

    version_groups: Mapped[list[VersionGroups]] = relationship(
        "VersionGroups", viewonly=True
    )


class ItemNames(Base):
    __tablename__ = "item_names"

    item_id: Mapped[intpk] = mapped_column(ForeignKey("items.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)

    name_normalized: Mapped[str | None]

    item: Mapped[Items] = relationship("Items", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class Items(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "items"

    id: Mapped[intpk]
    identifier: Mapped[str]
    category_id: Mapped[int]
    cost: Mapped[int]
    fling_power: Mapped[int | None]
    fling_effect_id: Mapped[int | None]

    item_names: Mapped[list[ItemNames]] = relationship("ItemNames", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("item_names")


class Languages(HashableMixin, Base):
    __tablename__ = "languages"

    id: Mapped[intpk]
    iso639: Mapped[str]
    iso3166: Mapped[str]
    identifier: Mapped[str]
    official: Mapped[int] = mapped_column(index=True)
    order: Mapped[int | None]


class LocationAreaProse(Base):
    __tablename__ = "location_area_prose"

    location_area_id: Mapped[intpk] = mapped_column(ForeignKey("location_areas.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str | None] = mapped_column(index=True)

    location_area: Mapped[LocationAreas] = relationship("LocationAreas", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class LocationAreas(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "location_areas"
    __table_opts__ = (UniqueConstraint("location_id", "identifier"),)

    id: Mapped[intpk]
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    game_index: Mapped[int]
    identifier: Mapped[str | None]

    location: Mapped[Locations] = relationship("Locations", viewonly=True)
    location_area_prose: Mapped[list[LocationAreaProse]] = relationship(
        "LocationAreaProse", viewonly=True
    )

    encounters: Mapped[list[Encounters]] = relationship("Encounters", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("location_area_prose")


class LocationNames(Base):
    __tablename__ = "location_names"

    location_id: Mapped[intpk] = mapped_column(ForeignKey("locations.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)
    subtitle: Mapped[str | None]

    location: Mapped[Locations] = relationship("Locations", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class Locations(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "locations"

    id: Mapped[intpk]
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"))
    identifier: Mapped[str] = mapped_column(unique=True)

    route_number: Mapped[int | None]

    region: Mapped[Regions] = relationship("Regions", viewonly=True)

    location_names: Mapped[list[LocationNames]] = relationship(
        "LocationNames", viewonly=True
    )
    location_areas: Mapped[list[LocationAreas]] = relationship(
        "LocationAreas", viewonly=True
    )

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

    machine_number: Mapped[intpk]
    version_group_id: Mapped[intpk] = mapped_column(ForeignKey("version_groups.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    move_id: Mapped[int] = mapped_column(ForeignKey("moves.id"))

    version_group: Mapped[VersionGroups] = relationship("VersionGroups", viewonly=True)
    item: Mapped[Items] = relationship("Items", viewonly=True)
    move: Mapped[Moves] = relationship("Moves", viewonly=True)

    @property
    def _id(self) -> int:
        return self.machine_number


class MoveNames(Base):
    __tablename__ = "move_names"

    move_id: Mapped[intpk] = mapped_column(ForeignKey("moves.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)

    name_normalized: Mapped[str | None]

    move: Mapped[Moves] = relationship("Moves", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class Moves(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "moves"

    id: Mapped[intpk]
    identifier: Mapped[str]
    generation_id: Mapped[int] = mapped_column(ForeignKey("generations.id"))
    type_id: Mapped[int]
    power: Mapped[int | None]
    pp: Mapped[int | None]
    accuracy: Mapped[int | None]
    priority: Mapped[int]
    target_id: Mapped[int]
    damage_class_id: Mapped[int]
    effect_id: Mapped[int]
    effect_chance: Mapped[int | None]
    contest_type_id: Mapped[int | None]
    contest_effect_id: Mapped[int | None]
    super_contest_effect_id: Mapped[int | None]

    generation: Mapped[Generations] = relationship("Generations", viewonly=True)

    move_names: Mapped[list[MoveNames]] = relationship("MoveNames", viewonly=True)
    machines: Mapped[list[Machines]] = relationship("Machines", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("move_names")


class NatureNames(Base):
    __tablename__ = "nature_names"

    nature_id: Mapped[intpk] = mapped_column(ForeignKey("natures.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)

    name_normalized: Mapped[str | None]

    nature: Mapped[Natures] = relationship("Natures", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class Natures(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "natures"

    id: Mapped[intpk]
    identifier: Mapped[str]
    decreased_stat_id: Mapped[int]
    increased_stat_id: Mapped[int]
    hates_flavor_id: Mapped[int]
    likes_flavor_id: Mapped[int]
    game_index: Mapped[int] = mapped_column(unique=True)

    nature_names: Mapped[list[NatureNames]] = relationship("NatureNames", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("nature_names")


class Pokemon(HashableMixin, Base):
    __tablename__ = "pokemon"

    id: Mapped[intpk]
    identifier: Mapped[str]
    species_id: Mapped[int] = mapped_column(ForeignKey("pokemon_species.id"))
    height: Mapped[int]
    weight: Mapped[int]
    base_experience: Mapped[int]
    order: Mapped[int] = mapped_column(index=True)
    is_default: Mapped[int] = mapped_column(index=True)

    species: Mapped[PokemonSpecies] = relationship("PokemonSpecies", viewonly=True)

    encounters: Mapped[list[Encounters]] = relationship("Encounters", viewonly=True)
    pokemon_forms: Mapped[list[PokemonForms]] = relationship(
        "PokemonForms", viewonly=True
    )
    pokemon_moves: Mapped[list[PokemonMoves]] = relationship(
        "PokemonMoves", viewonly=True
    )

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

    pokemon_form_id: Mapped[intpk] = mapped_column(ForeignKey("pokemon_forms.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    form_name: Mapped[str | None] = mapped_column(index=True)
    pokemon_name: Mapped[str | None] = mapped_column(index=True)

    pokemon_form: Mapped[PokemonForms] = relationship("PokemonForms", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class PokemonForms(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_forms"

    id: Mapped[intpk]
    identifier: Mapped[str]
    form_identifier: Mapped[str | None]
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"))
    introduced_in_version_group_id: Mapped[int] = mapped_column(
        ForeignKey("version_groups.id")
    )
    is_default: Mapped[int]
    is_battle_only: Mapped[int]
    is_mega: Mapped[int]
    form_order: Mapped[int]
    order: Mapped[int]

    pokemon: Mapped[Pokemon] = relationship("Pokemon", viewonly=True)
    introduced_in_version_group: Mapped[VersionGroups] = relationship(
        "VersionGroups", viewonly=True
    )

    pokemon_form_names: Mapped[list[PokemonFormNames]] = relationship(
        "PokemonFormNames", viewonly=True
    )

    @property
    def name(self) -> str:
        return self.get_translation(
            "pokemon_form_names", translation_column="form_name"
        )


class PokemonMoveMethodProse(Base):
    __tablename__ = "pokemon_move_method_prose"

    pokemon_move_method_id: Mapped[intpk] = mapped_column(
        ForeignKey("pokemon_move_methods.id")
    )
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str | None] = mapped_column(index=True)
    description: Mapped[str | None]

    pokemon_move_method: Mapped[PokemonMoveMethods] = relationship(
        "PokemonMoveMethods", viewonly=True
    )
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class PokemonMoveMethods(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_move_methods"

    id: Mapped[intpk]
    identifier: Mapped[str]

    pokemon_move_method_prose: Mapped[list[PokemonMoveMethodProse]] = relationship(
        "PokemonMoveMethodProse", viewonly=True
    )

    @property
    def prose(self) -> str:
        return self.get_translation("pokemon_move_method_prose")


class PokemonMoves(Base):
    __tablename__ = "pokemon_moves"

    pokemon_id: Mapped[intpk] = mapped_column(ForeignKey("pokemon.id"), index=True)
    version_group_id: Mapped[intpk] = mapped_column(
        ForeignKey("version_groups.id"), index=True
    )
    move_id: Mapped[intpk] = mapped_column(ForeignKey("moves.id"), index=True)
    pokemon_move_method_id: Mapped[intpk] = mapped_column(
        ForeignKey("pokemon_move_methods.id"), index=True
    )
    level: Mapped[intpk] = mapped_column(index=True)
    order: Mapped[int | None]

    pokemon: Mapped[Pokemon] = relationship("Pokemon", viewonly=True)
    version_group: Mapped[VersionGroups] = relationship("VersionGroups", viewonly=True)
    move: Mapped[Moves] = relationship("Moves", viewonly=True)
    pokemon_move_method: Mapped[PokemonMoveMethods] = relationship(
        "PokemonMoveMethods", viewonly=True
    )


class PokemonSpecies(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "pokemon_species"

    id: Mapped[intpk]
    identifier: Mapped[str]
    generation_id: Mapped[int] = mapped_column(ForeignKey("generations.id"))
    evolves_from_species_id: Mapped[int | None] = mapped_column(
        ForeignKey("pokemon_species.id")
    )
    evolution_chain_id: Mapped[int] = mapped_column(ForeignKey("evolution_chains.id"))
    color_id: Mapped[int]
    shape_id: Mapped[int | None]
    habitat_id: Mapped[int | None]
    gender_rate: Mapped[int]
    capture_rate: Mapped[int]
    base_happiness: Mapped[int]
    is_baby: Mapped[int]
    hatch_counter: Mapped[int]
    has_gender_differences: Mapped[int]
    growth_rate_id: Mapped[int]
    forms_switchable: Mapped[int]
    is_legendary: Mapped[int]
    is_mythical: Mapped[int]
    order: Mapped[int] = mapped_column(index=True)
    conquest_order: Mapped[int | None] = mapped_column(index=True)

    generation: Mapped[Generations] = relationship("Generations", viewonly=True)
    evolves_from_species: Mapped[PokemonSpecies] = relationship(
        "PokemonSpecies", viewonly=True
    )
    evolution_chain: Mapped[EvolutionChains] = relationship(
        "EvolutionChains", viewonly=True
    )

    pokemon_species_flavor_text: Mapped[list[PokemonSpeciesFlavorText]] = relationship(
        "PokemonSpeciesFlavorText", viewonly=True
    )
    pokemon_species_names: Mapped[list[PokemonSpeciesNames]] = relationship(
        "PokemonSpeciesNames", viewonly=True
    )
    pokemon: Mapped[list[Pokemon]] = relationship("Pokemon", viewonly=True)

    @property
    def name(self) -> str:
        return self.get_translation("pokemon_species_names")


class PokemonSpeciesFlavorText(Base):
    __tablename__ = "pokemon_species_flavor_text"

    species_id: Mapped[intpk] = mapped_column(ForeignKey("pokemon_species.id"))
    version_id: Mapped[intpk] = mapped_column(ForeignKey("versions.id"))
    language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    flavor_text: Mapped[str]

    species: Mapped[PokemonSpecies] = relationship("PokemonSpecies", viewonly=True)
    version: Mapped[Versions] = relationship("Versions", viewonly=True)
    language: Mapped[Languages] = relationship("Languages", viewonly=True)


class PokemonSpeciesNames(Base):
    __tablename__ = "pokemon_species_names"

    pokemon_species_id: Mapped[intpk] = mapped_column(ForeignKey("pokemon_species.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str | None] = mapped_column(index=True)
    genus: Mapped[str | None]

    pokemon_species: Mapped[PokemonSpecies] = relationship(
        "PokemonSpecies", viewonly=True
    )
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class Regions(HashableMixin, Base):
    __tablename__ = "regions"

    id: Mapped[intpk]
    identifier: Mapped[str]

    locations: Mapped[list[Locations]] = relationship("Locations", viewonly=True)


class VersionGroups(HashableMixin, Base):
    __tablename__ = "version_groups"

    id: Mapped[intpk]
    identifier: Mapped[str] = mapped_column(unique=True)
    generation_id: Mapped[int] = mapped_column(ForeignKey("generations.id"))
    order: Mapped[int | None]

    generation: Mapped[Generations] = relationship("Generations", viewonly=True)

    versions: Mapped[list[Versions]] = relationship("Versions", viewonly=True)


class VersionNames(Base):
    __tablename__ = "version_names"

    version_id: Mapped[intpk] = mapped_column(ForeignKey("versions.id"))
    local_language_id: Mapped[intpk] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(index=True)

    version: Mapped[Versions] = relationship("Versions", viewonly=True)
    local_language: Mapped[Languages] = relationship("Languages", viewonly=True)


class Versions(HashableMixin, TranslatableMixin, Base):
    __tablename__ = "versions"

    id: Mapped[intpk]
    version_group_id: Mapped[int] = mapped_column(ForeignKey("version_groups.id"))
    identifier: Mapped[str]

    version_group: Mapped[VersionGroups] = relationship("VersionGroups", viewonly=True)

    version_names: Mapped[list[VersionNames]] = relationship(
        "VersionNames", viewonly=True
    )

    @property
    def name(self) -> str:
        return self.get_translation("version_names")
