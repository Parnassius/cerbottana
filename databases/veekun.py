# pylint: disable=too-few-public-methods

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Languages(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True)
    iso639 = Column(String)
    iso3166 = Column(String)
    identifier = Column(String)
    official = Column(Integer)
    order = Column(Integer)


class EncounterMethods(Base):
    __tablename__ = "encounter_methods"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    order = Column(Integer)

    encounter_method_prose = relationship("EncounterMethodProse")


class Regions(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)

    locations = relationship("Locations")


class Locations(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    identifier = Column(String)

    region = relationship("Regions")

    location_names = relationship("LocationNames")
    location_areas = relationship("LocationAreas")


class LocationNames(Base):
    __tablename__ = "location_names"

    location_id = Column(Integer, ForeignKey("locations.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)
    subtitle = Column(String)

    location = relationship("Locations")
    local_language = relationship("Languages")


class Generations(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True)
    main_region_id = Column(Integer, ForeignKey("regions.id"))
    identifier = Column(String)

    main_region = relationship("Regions")

    version_groups = relationship("VersionGroups")


class VersionGroups(Base):
    __tablename__ = "version_groups"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    generation_id = Column(Integer, ForeignKey("generations.id"))
    order = Column(Integer)

    generation = relationship("Generations")

    versions = relationship("Versions")


class Versions(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True)
    version_group_id = Column(Integer, ForeignKey("version_groups.id"))
    identifier = Column(String)

    version_group = relationship("VersionGroups")

    version_names = relationship("VersionNames")


class LocationAreas(Base):
    __tablename__ = "location_areas"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    game_index = Column(Integer)
    identifier = Column(String)

    location = relationship("Locations")
    location_area_prose = relationship("LocationAreaProse")

    encounters = relationship("Encounters")


class LocationAreaProse(Base):
    __tablename__ = "location_area_prose"

    location_area_id = Column(
        Integer, ForeignKey("location_areas.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)

    location_area = relationship("LocationAreas")
    local_language = relationship("Languages")


class EncounterSlots(Base):
    __tablename__ = "encounter_slots"

    id = Column(Integer, primary_key=True)
    version_group_id = Column(Integer, ForeignKey("version_groups.id"))
    encounter_method_id = Column(Integer, ForeignKey("encounter_methods.id"))
    slot = Column(Integer)
    rarity = Column(Integer)

    version_group = relationship("VersionGroups")
    encounter_method = relationship("EncounterMethods")

    encounter = relationship("Encounters")


class Items(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    category_id = Column(Integer)
    cost = Column(Integer)
    fling_power = Column(Integer)
    fling_effect_id = Column(Integer)

    item_names = relationship("ItemNames")


class ItemNames(Base):
    __tablename__ = "item_names"

    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)

    item = relationship("Items")
    local_language = relationship("Languages")


class EvolutionChains(Base):
    __tablename__ = "evolution_chains"

    id = Column(Integer, primary_key=True)
    baby_trigger_item_id = Column(Integer, ForeignKey("items.id"))

    baby_trigger_item = relationship("Items")

    pokemon_species = relationship("PokemonSpecies")


class PokemonSpecies(Base):
    __tablename__ = "pokemon_species"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    generation_id = Column(Integer, ForeignKey("generations.id"))
    evolves_from_species_id = Column(Integer)
    evolution_chain_id = Column(Integer, ForeignKey("evolution_chains.id"))
    color_id = Column(Integer)
    shape_id = Column(Integer)
    habitat_id = Column(Integer)
    gender_rate = Column(Integer)
    capture_rate = Column(Integer)
    base_happiness = Column(Integer)
    is_baby = Column(Integer)
    hatch_counter = Column(Integer)
    has_gender_differences = Column(Integer)
    growth_rate_id = Column(Integer)
    forms_switchable = Column(Integer)
    is_legendary = Column(Integer)
    is_mythical = Column(Integer)
    order = Column(Integer)
    conquest_order = Column(Integer)

    generation = relationship("Generations")
    evolution_chain = relationship("EvolutionChains")

    pokemon_species_name = relationship("PokemonSpeciesNames")
    pokemon = relationship("Pokemon")


class PokemonSpeciesNames(Base):
    __tablename__ = "pokemon_species_names"

    pokemon_species_id = Column(
        Integer, ForeignKey("pokemon_species.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)
    genus = Column(String)

    pokemon_species = relationship("PokemonSpecies")
    local_language = relationship("Languages")


class Pokemon(Base):
    __tablename__ = "pokemon"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    species_id = Column(Integer, ForeignKey("pokemon_species.id"))
    height = Column(Integer)
    weight = Column(Integer)
    base_experience = Column(Integer)
    order = Column(Integer)
    is_default = Column(Integer)

    species = relationship("PokemonSpecies")

    encounters = relationship("Encounters")
    pokemon_forms = relationship("PokemonForms")
    pokemon_moves = relationship("PokemonMoves")


class Encounters(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("versions.id"))
    location_area_id = Column(Integer, ForeignKey("location_areas.id"))
    encounter_slot_id = Column(Integer, ForeignKey("encounter_slots.id"))
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"))
    min_level = Column(Integer)
    max_level = Column(Integer)

    version = relationship("Versions")
    location_area = relationship("LocationAreas")
    encounter_slot = relationship("EncounterSlots")
    pokemon = relationship("Pokemon")

    encounter_condition_value_map = relationship("EncounterConditionValueMap")


class EncounterConditions(Base):
    __tablename__ = "encounter_conditions"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)

    encounter_condition_values = relationship("EncounterConditionValues")


class EncounterConditionValues(Base):
    __tablename__ = "encounter_condition_values"

    id = Column(Integer, primary_key=True)
    encounter_condition_id = Column(Integer, ForeignKey("encounter_conditions.id"))
    identifier = Column(String)
    is_default = Column(Integer)

    encounter_condition = relationship("EncounterConditions")

    encounter_condition_value_prose = relationship("EncounterConditionValueProse")


class EncounterConditionValueMap(Base):
    __tablename__ = "encounter_condition_value_map"

    encounter_id = Column(Integer, ForeignKey("encounters.id"), primary_key=True)
    encounter_condition_value_id = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )

    encounter = relationship("Encounters")
    encounter_condition_value = relationship("EncounterConditionValues")


class EncounterConditionValueProse(Base):
    __tablename__ = "encounter_condition_value_prose"

    encounter_condition_value_id = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)

    encounter_condition_value = relationship("EncounterConditionValues")
    local_language = relationship("Languages")


class EncounterMethodProse(Base):
    __tablename__ = "encounter_method_prose"

    encounter_method_id = Column(
        Integer, ForeignKey("encounter_methods.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)

    encounter_method = relationship("EncounterMethods")
    local_language = relationship("Languages")


class Moves(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    generation_id = Column(Integer, ForeignKey("generations.id"))
    type_id = Column(Integer)
    power = Column(Integer)
    pp = Column(Integer)
    accuracy = Column(Integer)
    priority = Column(Integer)
    target_id = Column(Integer)
    damage_class_id = Column(Integer)
    effect_id = Column(Integer)
    effect_chance = Column(Integer)
    contest_type_id = Column(Integer)
    contest_effect_id = Column(Integer)
    super_contest_effect_id = Column(Integer)

    generation = relationship("Generations")

    move_names = relationship("MoveNames")
    machines = relationship("Machines")


class MoveNames(Base):
    __tablename__ = "move_names"

    move_id = Column(Integer, ForeignKey("moves.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)

    move = relationship("Moves")
    local_language = relationship("Languages")


class Machines(Base):
    __tablename__ = "machines"

    machine_number = Column(Integer, primary_key=True)
    version_group_id = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True
    )
    item_id = Column(Integer, ForeignKey("items.id"))
    move_id = Column(Integer, ForeignKey("moves.id"))

    version_group = relationship("VersionGroups")
    item = relationship("Items")
    move = relationship("Moves")


class PokemonForms(Base):
    __tablename__ = "pokemon_forms"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    form_identifier = Column(String)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"))
    introduced_in_version_group_id = Column(Integer, ForeignKey("version_groups.id"))
    is_default = Column(Integer)
    is_battle_only = Column(Integer)
    is_mega = Column(Integer)
    form_order = Column(Integer)
    order = Column(Integer)

    pokemon = relationship("Pokemon")
    introduced_in_version_group = relationship("VersionGroups")

    pokemon_form_names = relationship("PokemonFormNames")


class PokemonFormNames(Base):
    __tablename__ = "pokemon_form_names"

    pokemon_form_id = Column(Integer, ForeignKey("pokemon_forms.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    form_name = Column(Integer)
    pokemon_name = Column(Integer)

    pokemon_form = relationship("PokemonForms")
    local_language = relationship("Languages")


class PokemonMoveMethods(Base):
    __tablename__ = "pokemon_move_methods"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)

    pokemon_move_method_prose = relationship("PokemonMoveMethodProse")


class PokemonMoves(Base):
    __tablename__ = "pokemon_moves"

    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), primary_key=True)
    version_group_id = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True
    )
    move_id = Column(Integer, ForeignKey("moves.id"), primary_key=True)
    pokemon_move_method_id = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True
    )
    level = Column(Integer, primary_key=True)
    order = Column(String)

    pokemon = relationship("Pokemon")
    version_group = relationship("VersionGroups")
    move = relationship("Moves")
    pokemon_move_method = relationship("PokemonMoveMethods")


class PokemonMoveMethodProse(Base):
    __tablename__ = "pokemon_move_method_prose"

    pokemon_move_method_id = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True
    )
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)
    description = Column(String)

    pokemon_move_method = relationship("PokemonMoveMethods")
    local_language = relationship("Languages")


class VersionNames(Base):
    __tablename__ = "version_names"

    version_id = Column(Integer, ForeignKey("versions.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String)

    version = relationship("Versions")
    local_language = relationship("Languages")
