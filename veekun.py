from typing import List, Dict, Iterable, Any
from typing_extensions import TypedDict

import csv
import sqlite3


TablesDict = TypedDict(
    "TablesDict", {"name": str, "columns": Dict[str, str], "keys": List[str]}
)


class Veekun:
    def __init__(self) -> None:
        self.db = sqlite3.connect("./veekun.sqlite")
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

    @property
    def connection(self) -> sqlite3.Connection:
        return self.db

    def executemany(
        self, sql: str, params: Iterable[Iterable[Any]] = []
    ) -> sqlite3.Cursor:
        return self.cursor.executemany(sql, params)

    def executenow(self, sql: str, params: Iterable[Any] = []) -> sqlite3.Cursor:
        cur = self.execute(sql, params)
        self.commit()
        return cur

    def execute(self, sql: str, params: Iterable[Any] = []) -> sqlite3.Cursor:
        return self.cursor.execute(sql, params)

    def commit(self) -> None:
        self.db.commit()

    def __del__(self) -> None:
        self.db.close()


def csv_to_sqlite() -> None:
    open("./veekun.sqlite", "w").close()
    create_stmt = "CREATE TABLE {table} ({columns}, {keys});"
    insert_stmt = "INSERT INTO {table} ({columns}) VALUES ({values});"
    update_stmt_identifier = (
        'UPDATE {table} SET identifier = REPLACE(identifier, "-", "");'
    )

    tables: List[TablesDict] = [
        {
            "name": "encounter_condition_value_map",
            "columns": {
                "encounter_id": "INTEGER",
                "encounter_condition_value_id": "INTEGER",
            },
            "keys": ["PRIMARY KEY (encounter_id, encounter_condition_value_id)"],
        },
        {
            "name": "encounter_condition_value_prose",
            "columns": {
                "encounter_condition_value_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
            },
            "keys": ["PRIMARY KEY (encounter_condition_value_id, local_language_id)"],
        },
        {
            "name": "encounter_method_prose",
            "columns": {
                "encounter_method_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
            },
            "keys": ["PRIMARY KEY (encounter_method_id, local_language_id)"],
        },
        {
            "name": "encounter_methods",
            "columns": {"id": "INTEGER", "identifier": "TEXT", "order": "INTEGER"},
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "encounter_slots",
            "columns": {
                "id": "INTEGER",
                "version_group_id": "INTEGER",
                "encounter_method_id": "INTEGER",
                "slot": "INTEGER",
                "rarity": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "encounters",
            "columns": {
                "id": "INTEGER",
                "version_id": "INTEGER",
                "location_area_id": "INTEGER",
                "encounter_slot_id": "INTEGER",
                "pokemon_id": "INTEGER",
                "min_level": "INTEGER",
                "max_level": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "item_names",
            "columns": {
                "item_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
            },
            "keys": ["PRIMARY KEY (item_id, local_language_id)"],
        },
        {
            "name": "items",
            "columns": {
                "id": "INTEGER",
                "identifier": "TEXT",
                "category_id": "INTEGER",
                "cost": "INTEGER",
                "fling_power": "INTEGER",
                "fling_effect_id": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "location_names",
            "columns": {
                "location_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
                "subtitle": "TEXT",
            },
            "keys": ["PRIMARY KEY (location_id, local_language_id)"],
        },
        {
            "name": "location_area_prose",
            "columns": {
                "location_area_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
            },
            "keys": ["PRIMARY KEY (location_area_id, local_language_id)"],
        },
        {
            "name": "location_areas",
            "columns": {
                "id": "INTEGER",
                "location_id": "INTEGER",
                "game_index": "INTEGER",
                "identifier": "TEXT",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "locations",
            "columns": {"id": "INTEGER", "region_id": "INTEGER", "identifier": "TEXT"},
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "machines",
            "columns": {
                "machine_number": "INTEGER",
                "version_group_id": "INTEGER",
                "item_id": "INTEGER",
                "move_id": "INTEGER",
            },
            "keys": ["PRIMARY KEY (machine_number, version_group_id)"],
        },
        {
            "name": "move_names",
            "columns": {
                "move_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
            },
            "keys": ["PRIMARY KEY (move_id, local_language_id)"],
        },
        {
            "name": "moves",
            "columns": {
                "id": "INTEGER",
                "identifier": "TEXT",
                "generation_id": "INTEGER",
                "type_id": "INTEGER",
                "power": "INTEGER",
                "pp": "INTEGER",
                "accuracy": "INTEGER",
                "priority": "INTEGER",
                "target_id": "INTEGER",
                "damage_class_id": "INTEGER",
                "effect_id": "INTEGER",
                "effect_chance": "INTEGER",
                "contest_type_id": "INTEGER",
                "contest_effect_id": "INTEGER",
                "super_contest_effect_id": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "pokemon",
            "columns": {
                "id": "INTEGER",
                "identifier": "TEXT",
                "species_id": "INTEGER",
                "height": "INTEGER",
                "weight": "INTEGER",
                "base_experience": "INTEGER",
                "order": "INTEGER",
                "is_default": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "pokemon_form_names",
            "columns": {
                "pokemon_form_id": "INTEGER",
                "local_language_id": "INTEGER",
                "form_name": "INTEGER",
                "pokemon_name": "INTEGER",
            },
            "keys": ["PRIMARY KEY (pokemon_form_id, local_language_id)"],
        },
        {
            "name": "pokemon_forms",
            "columns": {
                "id": "INTEGER",
                "identifier": "TEXT",
                "form_identifier": "TEXT",
                "pokemon_id": "INTEGER",
                "introduced_in_version_group_id": "INTEGER",
                "is_default": "INTEGER",
                "is_battle_only": "INTEGER",
                "is_mega": "INTEGER",
                "form_order": "INTEGER",
                "order": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "pokemon_move_method_prose",
            "columns": {
                "pokemon_move_method_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
                "description": "TEXT",
            },
            "keys": ["PRIMARY KEY (pokemon_move_method_id, local_language_id)"],
        },
        {
            "name": "pokemon_move_methods",
            "columns": {"id": "INTEGER", "identifier": "TEXT"},
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "pokemon_moves",
            "columns": {
                "pokemon_id": "INTEGER",
                "version_group_id": "INTEGER",
                "move_id": "INTEGER",
                "pokemon_move_method_id": "INTEGER",
                "level": "INTEGER",
                "order": "INTEGER",
            },
            "keys": [
                "PRIMARY KEY (pokemon_id, version_group_id, move_id, pokemon_move_method_id, level)"
            ],
        },
        {
            "name": "pokemon_species",
            "columns": {
                "id": "INTEGER",
                "identifier": "TEXT",
                "generation_id": "INTEGER",
                "evolves_from_species_id": "INTEGER",
                "evolution_chain_id": "INTEGER",
                "color_id": "INTEGER",
                "shape_id": "INTEGER",
                "habitat_id": "INTEGER",
                "gender_rate": "INTEGER",
                "capture_rate": "INTEGER",
                "base_happiness": "INTEGER",
                "is_baby": "INTEGER",
                "hatch_counter": "INTEGER",
                "has_gender_differences": "INTEGER",
                "growth_rate_id": "INTEGER",
                "forms_switchable": "INTEGER",
                "is_legendary": "INTEGER",
                "is_mythical": "INTEGER",
                "order": "INTEGER",
                "conquest_order": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "pokemon_species_names",
            "columns": {
                "pokemon_species_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
                "genus": "TEXT",
            },
            "keys": ["PRIMARY KEY (pokemon_species_id, local_language_id)"],
        },
        {
            "name": "version_names",
            "columns": {
                "version_id": "INTEGER",
                "local_language_id": "INTEGER",
                "name": "TEXT",
            },
            "keys": ["PRIMARY KEY (version_id, local_language_id)"],
        },
        {
            "name": "version_groups",
            "columns": {
                "id": "INTEGER",
                "identifier": "TEXT",
                "generation_id": "INTEGER",
                "order": "INTEGER",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
        {
            "name": "versions",
            "columns": {
                "id": "INTEGER",
                "version_group_id": "INTEGER",
                "identifier": "TEXT",
            },
            "keys": ["PRIMARY KEY (id)"],
        },
    ]

    db = Veekun()

    for table in tables:
        columns = ["`" + i + "` " + table["columns"][i] for i in table["columns"]]
        keys = table["keys"]
        db.execute(
            create_stmt.format(
                table=table["name"], columns=", ".join(columns), keys=", ".join(keys)
            )
        )
        with open("./data/veekun/" + table["name"] + ".csv", "r") as f:
            data = csv.DictReader(f)
            csv_keys = data.fieldnames
            if csv_keys is not None:
                values = [list(i.values()) for i in data]
                db.executemany(
                    insert_stmt.format(
                        table=table["name"],
                        columns="`" + "`, `".join(csv_keys) + "`",
                        values=", ".join(list("?" * len(csv_keys))),
                    ),
                    values,
                )
                if "identifier" in table["columns"]:
                    db.execute(update_stmt_identifier.format(table=table["name"]))
                db.commit()
