import csv

with open('./data/veekun/encounter_condition_value_map.csv', 'r') as f:
  ENCOUNTER_CONDITION_VALUE_MAP = list(csv.DictReader(f))

with open('./data/veekun/encounter_condition_value_prose.csv', 'r') as f:
  ENCOUNTER_CONDITION_VALUE_PROSE = list(csv.DictReader(f))

with open('./data/veekun/encounter_method_prose.csv', 'r') as f:
  ENCOUNTER_METHOD_PROSE = list(csv.DictReader(f))

with open('./data/veekun/encounter_methods.csv', 'r') as f:
  ENCOUNTER_METHODS = list(csv.DictReader(f))

with open('./data/veekun/encounter_slots.csv', 'r') as f:
  ENCOUNTER_SLOTS = list(csv.DictReader(f))

with open('./data/veekun/encounters.csv', 'r') as f:
  ENCOUNTERS = list(csv.DictReader(f))

with open('./data/veekun/location_names.csv', 'r') as f:
  LOCATION_NAMES = list(csv.DictReader(f))

with open('./data/veekun/location_area_prose.csv', 'r') as f:
  LOCATION_AREA_PROSE = list(csv.DictReader(f))

with open('./data/veekun/location_areas.csv', 'r') as f:
  LOCATION_AREAS = list(csv.DictReader(f))

with open('./data/veekun/pokemon.csv', 'r') as f:
  POKEMON = list(csv.DictReader(f))

with open('./data/veekun/version_names.csv', 'r') as f:
  VERSION_NAMES = list(csv.DictReader(f))
