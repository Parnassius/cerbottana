# pylint: disable=too-few-public-methods

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class LatestCommit(Base):
    __tablename__ = "latest_commit"

    commit_id = Column(String, primary_key=True, nullable=False)


class Languages(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, nullable=False)
    iso639 = Column(String, nullable=False)
    iso3166 = Column(String, nullable=False)
    identifier = Column(String, nullable=False)
    official = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)


class EncounterMethods(Base):
    __tablename__ = "encounter_methods"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)
    order = Column(Integer, nullable=False)

    encounter_method_prose = relationship("EncounterMethodProse", uselist=True)


class Regions(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)

    locations = relationship("Locations", uselist=True)


class Locations(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    identifier = Column(String, nullable=False)

    region = relationship("Regions", uselist=False)

    location_names = relationship("LocationNames", uselist=True)
    location_areas = relationship("LocationAreas", uselist=True)


class LocationNames(Base):
    __tablename__ = "location_names"

    location_id = Column(
        Integer, ForeignKey("locations.id"), primary_key=True, nullable=False
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)

    location = relationship("Locations", uselist=False)
    local_language = relationship("Languages", uselist=False)


class Generations(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, nullable=False)
    main_region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    identifier = Column(String, nullable=False)

    main_region = relationship("Regions", uselist=False)

    version_groups = relationship("VersionGroups", uselist=True)


class VersionGroups(Base):
    __tablename__ = "version_groups"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=False)
    order = Column(Integer, nullable=False)

    generation = relationship("Generations", uselist=False)

    versions = relationship("Versions", uselist=True)


class Versions(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, nullable=False)
    version_group_id = Column(Integer, ForeignKey("version_groups.id"), nullable=False)
    identifier = Column(String, nullable=False)

    version_group = relationship("VersionGroups", uselist=False)

    version_names = relationship("VersionNames", uselist=True)


class LocationAreas(Base):
    __tablename__ = "location_areas"

    id = Column(Integer, primary_key=True, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    game_index = Column(Integer, nullable=False)
    identifier = Column(String, nullable=False)

    location = relationship("Locations", uselist=False)
    location_area_prose = relationship("LocationAreaProse", uselist=True)

    encounters = relationship("Encounters", uselist=True)


class LocationAreaProse(Base):
    __tablename__ = "location_area_prose"

    location_area_id = Column(
        Integer, ForeignKey("location_areas.id"), primary_key=True
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)

    location_area = relationship("LocationAreas", uselist=False)
    local_language = relationship("Languages", uselist=False)


class EncounterSlots(Base):
    __tablename__ = "encounter_slots"

    id = Column(Integer, primary_key=True, nullable=False)
    version_group_id = Column(Integer, ForeignKey("version_groups.id"), nullable=False)
    encounter_method_id = Column(
        Integer, ForeignKey("encounter_methods.id"), nullable=False
    )
    slot = Column(Integer, nullable=False)
    rarity = Column(Integer, nullable=False)

    version_group = relationship("VersionGroups", uselist=False)
    encounter_method = relationship("EncounterMethods", uselist=False)

    encounter = relationship("Encounters", uselist=False)


class Items(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)
    category_id = Column(Integer, nullable=False)
    cost = Column(Integer, nullable=False)
    fling_power = Column(Integer, nullable=False)
    fling_effect_id = Column(Integer, nullable=False)

    item_names = relationship("ItemNames", uselist=True)


class ItemNames(Base):
    __tablename__ = "item_names"

    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True, nullable=False)
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)

    item = relationship("Items", uselist=False)
    local_language = relationship("Languages", uselist=False)


class EvolutionChains(Base):
    __tablename__ = "evolution_chains"

    id = Column(Integer, primary_key=True, nullable=False)
    baby_trigger_item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    baby_trigger_item = relationship("Items", uselist=False)

    pokemon_species = relationship("PokemonSpecies", uselist=False)


class PokemonSpecies(Base):
    __tablename__ = "pokemon_species"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=False)
    evolves_from_species_id = Column(Integer, nullable=False)
    evolution_chain_id = Column(
        Integer, ForeignKey("evolution_chains.id"), nullable=False
    )
    color_id = Column(Integer, nullable=False)
    shape_id = Column(Integer, nullable=False)
    habitat_id = Column(Integer, nullable=False)
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
    order = Column(Integer, nullable=False)
    conquest_order = Column(Integer, nullable=False)

    generation = relationship("Generations", uselist=False)
    evolution_chain = relationship("EvolutionChains", uselist=False)

    pokemon_species_flavor_text = relationship("PokemonSpeciesFlavorText", uselist=True)
    pokemon_species_names = relationship("PokemonSpeciesNames", uselist=True)
    pokemon = relationship("Pokemon", uselist=True)


class PokemonSpeciesFlavorText(Base):
    __tablename__ = "pokemon_species_flavor_text"

    species_id = Column(
        Integer, ForeignKey("pokemon_species.id"), primary_key=True, nullable=False
    )
    version_id = Column(
        Integer, ForeignKey("versions.id"), primary_key=True, nullable=False
    )
    language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    flavor_text = Column(String, nullable=False)

    species = relationship("PokemonSpecies", uselist=False)
    version = relationship("Versions", uselist=False)
    language = relationship("Languages", uselist=False)


class PokemonSpeciesNames(Base):
    __tablename__ = "pokemon_species_names"

    pokemon_species_id = Column(
        Integer, ForeignKey("pokemon_species.id"), primary_key=True
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)
    genus = Column(String, nullable=False)

    pokemon_species = relationship("PokemonSpecies", uselist=False)
    local_language = relationship("Languages", uselist=False)


class Pokemon(Base):
    __tablename__ = "pokemon"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)
    species_id = Column(Integer, ForeignKey("pokemon_species.id"), nullable=False)
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    base_experience = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)
    is_default = Column(Integer, nullable=False)

    species = relationship("PokemonSpecies", uselist=False)

    encounters = relationship("Encounters", uselist=True)
    pokemon_forms = relationship("PokemonForms", uselist=True)
    pokemon_moves = relationship("PokemonMoves", uselist=True)


class Encounters(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, nullable=False)
    version_id = Column(Integer, ForeignKey("versions.id"), nullable=False)
    location_area_id = Column(Integer, ForeignKey("location_areas.id"), nullable=False)
    encounter_slot_id = Column(
        Integer, ForeignKey("encounter_slots.id"), nullable=False
    )
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    min_level = Column(Integer, nullable=False)
    max_level = Column(Integer, nullable=False)

    version = relationship("Versions", uselist=False)
    location_area = relationship("LocationAreas", uselist=False)
    encounter_slot = relationship("EncounterSlots", uselist=False)
    pokemon = relationship("Pokemon", uselist=False)

    encounter_condition_value_map = relationship(
        "EncounterConditionValueMap", uselist=True
    )


class EncounterConditions(Base):
    __tablename__ = "encounter_conditions"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)

    encounter_condition_values = relationship("EncounterConditionValues", uselist=True)


class EncounterConditionValues(Base):
    __tablename__ = "encounter_condition_values"

    id = Column(Integer, primary_key=True, nullable=False)
    encounter_condition_id = Column(
        Integer, ForeignKey("encounter_conditions.id"), nullable=False
    )
    identifier = Column(String, nullable=False)
    is_default = Column(Integer, nullable=False)

    encounter_condition = relationship("EncounterConditions", uselist=False)

    encounter_condition_value_prose = relationship(
        "EncounterConditionValueProse", uselist=True
    )


class EncounterConditionValueMap(Base):
    __tablename__ = "encounter_condition_value_map"

    encounter_id = Column(
        Integer, ForeignKey("encounters.id"), primary_key=True, nullable=False
    )
    encounter_condition_value_id = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )

    encounter = relationship("Encounters", uselist=False)
    encounter_condition_value = relationship("EncounterConditionValues", uselist=False)


class EncounterConditionValueProse(Base):
    __tablename__ = "encounter_condition_value_prose"

    encounter_condition_value_id = Column(
        Integer, ForeignKey("encounter_condition_values.id"), primary_key=True
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)

    encounter_condition_value = relationship("EncounterConditionValues", uselist=False)
    local_language = relationship("Languages", uselist=False)


class EncounterMethodProse(Base):
    __tablename__ = "encounter_method_prose"

    encounter_method_id = Column(
        Integer, ForeignKey("encounter_methods.id"), primary_key=True
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)

    encounter_method = relationship("EncounterMethods", uselist=False)
    local_language = relationship("Languages", uselist=False)


class Moves(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=False)
    type_id = Column(Integer, nullable=False)
    power = Column(Integer, nullable=False)
    pp = Column(Integer, nullable=False)
    accuracy = Column(Integer, nullable=False)
    priority = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    damage_class_id = Column(Integer, nullable=False)
    effect_id = Column(Integer, nullable=False)
    effect_chance = Column(Integer, nullable=False)
    contest_type_id = Column(Integer, nullable=False)
    contest_effect_id = Column(Integer, nullable=False)
    super_contest_effect_id = Column(Integer, nullable=False)

    generation = relationship("Generations", uselist=False)

    move_names = relationship("MoveNames", uselist=True)
    machines = relationship("Machines", uselist=True)


class MoveNames(Base):
    __tablename__ = "move_names"

    move_id = Column(Integer, ForeignKey("moves.id"), primary_key=True, nullable=False)
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)

    move = relationship("Moves", uselist=False)
    local_language = relationship("Languages", uselist=False)


class Machines(Base):
    __tablename__ = "machines"

    machine_number = Column(Integer, primary_key=True, nullable=False)
    version_group_id = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    move_id = Column(Integer, ForeignKey("moves.id"), nullable=False)

    version_group = relationship("VersionGroups", uselist=False)
    item = relationship("Items", uselist=False)
    move = relationship("Moves", uselist=False)


class PokemonForms(Base):
    __tablename__ = "pokemon_forms"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)
    form_identifier = Column(String, nullable=False)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    introduced_in_version_group_id = Column(
        Integer, ForeignKey("version_groups.id"), nullable=False
    )
    is_default = Column(Integer, nullable=False)
    is_battle_only = Column(Integer, nullable=False)
    is_mega = Column(Integer, nullable=False)
    form_order = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)

    pokemon = relationship("Pokemon", uselist=False)
    introduced_in_version_group = relationship("VersionGroups", uselist=False)

    pokemon_form_names = relationship("PokemonFormNames", uselist=True)


class PokemonFormNames(Base):
    __tablename__ = "pokemon_form_names"

    pokemon_form_id = Column(
        Integer, ForeignKey("pokemon_forms.id"), primary_key=True, nullable=False
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    form_name = Column(String, nullable=False)
    pokemon_name = Column(String, nullable=False)

    pokemon_form = relationship("PokemonForms", uselist=False)
    local_language = relationship("Languages", uselist=False)


class PokemonMoveMethods(Base):
    __tablename__ = "pokemon_move_methods"

    id = Column(Integer, primary_key=True, nullable=False)
    identifier = Column(String, nullable=False)

    pokemon_move_method_prose = relationship("PokemonMoveMethodProse", uselist=True)


class PokemonMoves(Base):
    __tablename__ = "pokemon_moves"

    pokemon_id = Column(
        Integer, ForeignKey("pokemon.id"), primary_key=True, nullable=False
    )
    version_group_id = Column(
        Integer, ForeignKey("version_groups.id"), primary_key=True
    )
    move_id = Column(Integer, ForeignKey("moves.id"), primary_key=True, nullable=False)
    pokemon_move_method_id = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True
    )
    level = Column(Integer, primary_key=True, nullable=False)
    order = Column(String, nullable=False)

    pokemon = relationship("Pokemon", uselist=False)
    version_group = relationship("VersionGroups", uselist=False)
    move = relationship("Moves", uselist=False)
    pokemon_move_method = relationship("PokemonMoveMethods", uselist=False)


class PokemonMoveMethodProse(Base):
    __tablename__ = "pokemon_move_method_prose"

    pokemon_move_method_id = Column(
        Integer, ForeignKey("pokemon_move_methods.id"), primary_key=True
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    pokemon_move_method = relationship("PokemonMoveMethods", uselist=False)
    local_language = relationship("Languages", uselist=False)


class VersionNames(Base):
    __tablename__ = "version_names"

    version_id = Column(
        Integer, ForeignKey("versions.id"), primary_key=True, nullable=False
    )
    local_language_id = Column(
        Integer, ForeignKey("languages.id"), primary_key=True, nullable=False
    )
    name = Column(String, nullable=False)

    version = relationship("Versions", uselist=False)
    local_language = relationship("Languages", uselist=False)
