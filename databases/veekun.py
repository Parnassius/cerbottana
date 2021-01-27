# pylint: disable=too-few-public-methods

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class LatestCommit(Base):
    __tablename__ = "latest_commit"

    commit_id = Column(String, primary_key=True)


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


class EncounterConditionValues(Base):
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


class EncounterConditions(Base):
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


class EncounterMethods(Base):
    __tablename__ = "encounter_methods"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, unique=True, nullable=False)
    order = Column(Integer, unique=True, nullable=False)

    encounter_method_prose = relationship(
        "EncounterMethodProse", uselist=True, viewonly=True
    )


class EncounterSlots(Base):
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


class Encounters(Base):
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


class EvolutionChains(Base):
    __tablename__ = "evolution_chains"

    id = Column(Integer, primary_key=True)
    baby_trigger_item_id = Column(Integer, ForeignKey("items.id"))

    baby_trigger_item = relationship("Items", uselist=False, viewonly=True)

    pokemon_species = relationship("PokemonSpecies", uselist=False, viewonly=True)


class Generations(Base):
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

    item = relationship("Items", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Items(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    category_id = Column(Integer, nullable=False)
    cost = Column(Integer, nullable=False)
    fling_power = Column(Integer)
    fling_effect_id = Column(Integer)

    item_names = relationship("ItemNames", uselist=True, viewonly=True)


class Languages(Base):
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


class LocationAreas(Base):
    __tablename__ = "location_areas"
    __table_opts__ = (UniqueConstraint("location_id", "identifier"),)

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    game_index = Column(Integer, nullable=False)
    identifier = Column(String)

    location = relationship("Locations", uselist=False, viewonly=True)
    location_area_prose = relationship("LocationAreaProse", uselist=True, viewonly=True)

    encounters = relationship("Encounters", uselist=True, viewonly=True)


class LocationNames(Base):
    __tablename__ = "location_names"

    location_id = Column(Integer, ForeignKey("locations.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)
    subtitle = Column(String)

    location = relationship("Locations", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Locations(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    identifier = Column(String, unique=True, nullable=False)

    region = relationship("Regions", uselist=False, viewonly=True)

    location_names = relationship("LocationNames", uselist=True, viewonly=True)
    location_areas = relationship("LocationAreas", uselist=True, viewonly=True)


class Machines(Base):
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


class MoveNames(Base):
    __tablename__ = "move_names"

    move_id = Column(Integer, ForeignKey("moves.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    name = Column(String, index=True, nullable=False)

    move = relationship("Moves", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class Moves(Base):
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


class Pokemon(Base):
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


class PokemonFormNames(Base):
    __tablename__ = "pokemon_form_names"

    pokemon_form_id = Column(Integer, ForeignKey("pokemon_forms.id"), primary_key=True)
    local_language_id = Column(Integer, ForeignKey("languages.id"), primary_key=True)
    form_name = Column(String, index=True)
    pokemon_name = Column(String, index=True)

    pokemon_form = relationship("PokemonForms", uselist=False, viewonly=True)
    local_language = relationship("Languages", uselist=False, viewonly=True)


class PokemonForms(Base):
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


class PokemonMoveMethods(Base):
    __tablename__ = "pokemon_move_methods"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)

    pokemon_move_method_prose = relationship(
        "PokemonMoveMethodProse", uselist=True, viewonly=True
    )


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


class PokemonSpecies(Base):
    __tablename__ = "pokemon_species"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)
    generation_id = Column(Integer, ForeignKey("generations.id"))
    evolves_from_species_id = Column(Integer, ForeignKey("pokemon_species.id"))
    evolution_chain_id = Column(Integer, ForeignKey("evolution_chains.id"))
    color_id = Column(Integer, nullable=False)
    shape_id = Column(Integer, nullable=False)
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


class Regions(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False)

    locations = relationship("Locations", uselist=True, viewonly=True)


class VersionGroups(Base):
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


class Versions(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True)
    version_group_id = Column(Integer, ForeignKey("version_groups.id"), nullable=False)
    identifier = Column(String, nullable=False)

    version_group = relationship("VersionGroups", uselist=False, viewonly=True)

    version_names = relationship("VersionNames", uselist=True, viewonly=True)
