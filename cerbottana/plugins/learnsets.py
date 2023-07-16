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


@dataclass
class LearnsetMove:
    move: v.Moves
    level: int
    order: int
    machine: v.Machines | None
    forms: set[v.Pokemon] = field(default_factory=set)

    @property
    def _order_tuple(self) -> tuple[int, int, v.Machines | None, int]:
        return self.level, self.order, self.machine, self.move.id

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LearnsetMove):
            raise NotImplementedError
        return self._order_tuple < other._order_tuple


@dataclass
class LearnsetMethod:
    method: v.PokemonMoveMethods
    moves: dict[int, LearnsetMove] = field(default_factory=dict)
    form_column: bool = False

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LearnsetMethod):
            raise NotImplementedError
        return self.method.id < other.method.id


@dataclass
class Learnset:
    methods: dict[int, LearnsetMethod] = field(default_factory=dict)

    def add_move(self, pokemon: v.Pokemon, pokemon_move: v.PokemonMoves) -> None:
        method = pokemon_move.pokemon_move_method
        if method.id not in self.methods:
            self.methods[method.id] = LearnsetMethod(method)

        move = pokemon_move.move
        if move.id not in self.methods[method.id].moves:
            self.methods[method.id].moves[move.id] = LearnsetMove(
                move,
                int(pokemon_move.level or 0),
                int(pokemon_move.order or 0),
                move.machines[0] if move.machines else None,
            )
        self.methods[method.id].moves[move.id].forms.add(pokemon)


class LearnsetHTML(BaseHTMLCommand):
    _STYLES = {  # noqa: RUF012
        "table": {
            "margin": "5px 0",
        },
        "align_right": {
            "text-align": "right",
        },
    }

    def __init__(self, *, learnset_data: Learnset) -> None:
        super().__init__()

        if not learnset_data.methods:
            return

        with self.doc, e.Div(class_="ladder"):
            for method in sorted(learnset_data.methods.values()):
                with e.Details():
                    e.Summary(e.B(method.method.prose))
                    self._add_table(method)

    def _add_table(self, method: LearnsetMethod) -> None:
        with e.Table(style=self._get_css("table")):
            with e.Tr():
                e.Th("Move")
                if method.method.id == 1:
                    e.Th("Level")
                elif method.method.id == 4:
                    e.Th("Machine")
                if method.form_column:
                    e.Th("Form")

            for move in sorted(method.moves.values()):
                with e.Tr():
                    e.Td(move.move.name)
                    if method.method.id == 1:
                        e.Td(move.level, style=self._get_css("align_right"))
                    elif method.method.id == 4:
                        e.Td(getattr(getattr(move.machine, "item", None), "name", ""))
                    if method.form_column:
                        e.Td(", ".join([x.name for x in sorted(move.forms)]))


@command_wrapper()
async def learnset(msg: Message) -> None:
    if len(msg.args) < 2:
        return

    pokemon_id = utils.to_id(utils.remove_diacritics(msg.args[0].lower()))
    version_id = utils.to_id(utils.remove_diacritics(msg.args[1].lower()))

    language_id = msg.language_id
    if len(msg.args) >= 3:
        language_id = utils.get_language_id(msg.args[2], fallback=language_id)

    db = Database.open("veekun")

    with db.get_session(language_id) as session:
        stmt_version_group = select(v.VersionGroups).filter_by(identifier=version_id)
        version_group = session.scalar(stmt_version_group)

        if version_group is None:
            stmt_version = select(v.Versions).filter_by(identifier=version_id)
            version = session.scalar(stmt_version)
            if version is None:
                await msg.reply("Game version not found.")
                return
            version_group = version.version_group

        stmt = (
            select(v.PokemonSpecies)
            .options(
                selectinload(v.PokemonSpecies.pokemon)
                .selectinload(
                    v.Pokemon.pokemon_moves.and_(
                        v.PokemonMoves.version_group_id == version_group.id
                    )
                )
                .options(
                    selectinload(v.PokemonMoves.move).options(
                        selectinload(v.Moves.move_names),
                        selectinload(
                            v.Moves.machines.and_(
                                v.Machines.version_group_id == version_group.id
                            )
                        )
                        .selectinload(v.Machines.item)
                        .selectinload(v.Items.item_names),
                    ),
                    selectinload(v.PokemonMoves.pokemon_move_method).selectinload(
                        v.PokemonMoveMethods.pokemon_move_method_prose
                    ),
                )
            )
            .filter_by(identifier=pokemon_id)
        )
        pokemon_species = session.scalar(stmt)
        if pokemon_species is None:
            await msg.reply("Pokémon not found.")
            return

        results = Learnset()

        all_forms = set(pokemon_species.pokemon)

        for pokemon in pokemon_species.pokemon:
            for pokemon_move in pokemon.pokemon_moves:
                results.add_move(pokemon, pokemon_move)

        for method_data in results.methods.values():
            for move_data in method_data.moves.values():
                if move_data.forms == all_forms:
                    move_data.forms = set()
                else:
                    method_data.form_column = True

        html = LearnsetHTML(learnset_data=results)

        if not html:
            await msg.reply("No data available.")
            return

        await msg.reply_htmlbox(html.doc)
