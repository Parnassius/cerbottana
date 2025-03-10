from __future__ import annotations

import ast
import inspect
import textwrap

from cerbottana.plugins import commands


def test_parametrize_room() -> None:
    """Checks if msg.parametrized_room is only used in properly decorated commands."""
    for command in commands.values():
        func_source = textwrap.dedent(
            inspect.getsource(command.cls or command.callback)  # type: ignore[arg-type]
        )
        func_ast = ast.parse(func_source)

        decorator = next(
            (
                i
                for i in func_ast.body[0].decorator_list  # type: ignore[attr-defined]
                if i.func.id == "command_wrapper"
            ),
            None,
        )
        if not decorator:
            continue

        has_parametrize_room = next(
            (
                i
                for i in decorator.keywords
                if i.arg == "parametrize_room" and i.value.value
            ),
            False,
        )
        if not has_parametrize_room:
            uses_parametrized_room = next(
                (
                    i
                    for i in ast.walk(func_ast.body[0])
                    if isinstance(i, ast.Attribute)
                    and isinstance(i.value, ast.Name)
                    and i.value.id == "msg"
                    and i.attr == "parametrized_room"
                ),
                False,
            )
            assert not uses_parametrized_room, (
                f"{command.name} shouldn't use msg.parametrized_room"
            )
